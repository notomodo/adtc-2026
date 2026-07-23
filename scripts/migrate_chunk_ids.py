#!/usr/bin/env python3
"""Positional-to-stable chunk ID migration mapping.

Builds a NEW persistent index (src/core/index.py) from data/raw/*.pdf,
reusing ingest_sme.py's extraction and chunking unmodified, and emits a
mapping {old_positional_id: new_stable_id} against the CURRENT
benchmarks/chunks_sme.txt dump. VERIFIES every mapped chunk's text is
byte-identical between the old dump and the new chunks.jsonl before writing
anything -- refuses to write the mapping if even one chunk differs.

Does NOT rewrite question sets. This only reports what WOULD change.

WHY char_start/char_end ARE DERIVED HERE, NOT IN ingest_sme.py
================================================================
ingest_sme.py's chunker tracks only a page number per chunk, not a
character range within the document, and this task does not touch
ingest_sme.py. Each chunk's body text (everything after the synthetic
heading line chunk_document() prepends) is located via `str.find` in a
per-document reconstruction of ingest_sme.py's own internal "stream" (the
whitespace-joined, furniture-stripped page lines -- see
ingest_sme.chunk_document's own docstring). Verified empirically against
the real 47-chunk corpus before writing this: every chunk's body locates
cleanly. If a future corpus ever fails to locate, that is FATAL here, not a
warning -- an approximated offset is a citation-accuracy defect, and this
project's standing rule is to fail loud on that class of thing.

ENCODER: REAL BY DEFAULT, --stub-embedder AS A LOUD, LABELLED ESCAPE HATCH
=============================================================================
This mapping/verification report is fundamentally about TEXT identity, not
embedding quality -- but Index.append_document requires an encoder to run
at all. As of DECISION-002 SS9, bge-small has not yet been exported to
ONNX int8 anywhere in this repo. --onnx-path is required by default (fails
loudly if unset, same as ingest_sme.py's tokenizer gate); --stub-embedder
is an explicit, clearly-labelled opt-in for verifying the ID mapping and
text-identity check without a real encoder -- mirroring ingest_sme.py's
own --allow-estimate escape hatch (loud, opt-in, never the silent default).

USAGE
  python scripts/migrate_chunk_ids.py --onnx-path path/to/bge-small-int8.onnx
  python scripts/migrate_chunk_ids.py --stub-embedder   # text-identity dry run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

import ingest_sme  # noqa: E402 -- reuse extract_lines/chunk_document, do not reimplement
from eval_retriever import HEADER_RE  # noqa: E402 -- reuse the existing header regex
from core.index import EncoderHandle, ExtractedChunk, ExtractedDoc, Index  # noqa: E402


def _load_old_dump_raw(path: str) -> tuple[list[int], list[str]]:
    """Parse the old dump's (id, text) pairs WITHOUT eval_retriever.load_chunks's
    `.strip()`.

    Empirically found while writing this script: eval_retriever.load_chunks's
    flush() does `"\\n".join(buf).strip()`, which silently drops leading/
    trailing whitespace that is genuinely present in the on-disk dump for at
    least 2 of 47 chunks (the first chunk of any document whose first
    segment has no preceding section-marker cut -- e.g. chunk [0]'s text
    ends ' General Terms for Sellers and Buyers ' with a real trailing
    space, verified against the raw file bytes). That's a previously-
    unnoticed, pre-existing discrepancy between "what's on disk" (what the
    fingerprint hash and every gold label are computed against) and "what
    the benchmark harness's own parser feeds to BM25/dense retrieval" --
    worth reporting, not silently inheriting into this migration's
    byte-identity check, which the task specifies against the dump FILE.
    """
    ids: list[int] = []
    texts: list[str] = []
    cur_id: int | None = None
    buf: list[str] = []
    in_body = False

    def flush() -> None:
        nonlocal cur_id, buf
        if cur_id is not None:
            ids.append(cur_id)
            # ingest_sme.py's writer always emits [..., c.text, ""] -- the
            # blank spacer line is ALWAYS the last line collected here,
            # never part of c.text itself. Drop exactly that one line
            # (not .strip(), which also eats real trailing whitespace
            # that's part of c.text -- see docstring above) to reconstruct
            # c.text byte-for-byte.
            if buf and buf[-1] == "":
                buf = buf[:-1]
            texts.append("\n".join(buf))
        cur_id, buf = None, []

    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = HEADER_RE.match(line)
        if m:
            flush()
            cur_id = int(m.group(1))
            in_body = False
            continue
        if cur_id is None:
            continue
        if line.startswith("---"):
            in_body = True
            continue
        if in_body:
            buf.append(line)
    flush()
    return ids, texts


class _StubEncoder:
    """Deterministic, seeded, NOT a real embedding model. Only used behind
    --stub-embedder for a text-identity dry run when no ONNX model file
    exists (see module docstring)."""

    def encode(self, texts, is_query: bool = False) -> np.ndarray:
        vecs = np.zeros((len(texts), 384), dtype=np.float32)
        for i, t in enumerate(texts):
            seed = int.from_bytes(hashlib.sha256(t.encode()).digest()[:8], "little")
            rng = np.random.default_rng(seed)
            vecs[i] = rng.normal(size=384)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return (vecs / np.clip(norms, 1e-9, None)).astype(np.float32)


def _build_encoder(args: argparse.Namespace) -> EncoderHandle:
    if args.stub_embedder:
        print(
            "[WARN] --stub-embedder: embeddings are NOT from a real model. "
            "This is a text-identity / ID-mapping dry run only -- never use "
            "this index for retrieval quality. Re-run with --onnx-path for "
            "the real thing.",
            file=sys.stderr,
        )
        return EncoderHandle(
            encoder=_StubEncoder(),
            embedder_id="STUB-NOT-FOR-PRODUCTION",
            tokenizer_sha256="stub",
        )

    if not args.onnx_path:
        sys.exit(
            "FATAL: no --onnx-path given and --stub-embedder not set.\n"
            "       This migration builds a REAL index by default. Per "
            "DECISION-002 SS9, bge-small has not yet been exported to ONNX "
            "int8 anywhere in this repo, so you must supply one with "
            "--onnx-path, or explicitly opt into a text-only dry run with "
            "--stub-embedder (embeddings will NOT be meaningful)."
        )

    from retriever import OnnxEncoder

    tok_path = Path(args.tokenizer_path)
    if not tok_path.exists():
        sys.exit(f"FATAL: vendored tokenizer not found at {tok_path}")
    tokenizer_sha256 = hashlib.sha256(tok_path.read_bytes()).hexdigest()
    enc = OnnxEncoder(
        args.onnx_path, args.tokenizer_name, model_name=args.embed_model,
        tokenizer_path=tok_path,
    )
    return EncoderHandle(
        encoder=enc, embedder_id=args.embed_model, tokenizer_sha256=tokenizer_sha256,
    )


def _page_count(path: Path) -> int:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        return len(pdf.pages)


def _char_offsets(stream: str, body: str, pdf_name: str, page: int) -> tuple[int, int]:
    start = stream.find(body)
    if start == -1:
        raise AssertionError(
            f"{pdf_name} page {page}: chunk body not found verbatim in the "
            f"reconstructed document stream -- char offsets cannot be trusted "
            f"for this chunk. Refusing to guess an approximate offset."
        )
    return start, start + len(body)


def _extract_doc(pdf_path: Path, budget: int, tok) -> ExtractedDoc:
    sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    lines = ingest_sme.extract_lines(pdf_path)
    stream = " ".join(line for _, line in lines)
    chunks = ingest_sme.chunk_document(pdf_path, budget, tok)

    extracted = []
    for c in chunks:
        head, body = c.text.split("\n", 1)  # chunk_document always emits exactly one \n
        start, end = _char_offsets(stream, body, pdf_path.name, c.page)
        extracted.append(ExtractedChunk(
            page=c.page, char_start=start, char_end=end,
            text=c.text, n_tokens=ingest_sme.count_tokens(c.text, tok),
        ))

    return ExtractedDoc(
        sha256=sha256, filename=pdf_path.name, pages=_page_count(pdf_path), chunks=extracted,
    )


def _load_new_chunks(index_dir: Path) -> list[dict]:
    records = []
    chunks_path = index_dir / "chunks.jsonl"
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdfs-dir", default="data/raw")
    ap.add_argument("--old-dump", default="benchmarks/chunks_sme.txt")
    ap.add_argument("--index-dir", default="benchmarks/migration_index",
                     help="fresh throwaway index built for this report; NOT the production index path")
    ap.add_argument("--budget", type=int, default=400)
    ap.add_argument("--tokenizer-name", default="BAAI/bge-small-en-v1.5")
    ap.add_argument("--tokenizer-path", default=str(SRC / "tokenizer.json"))
    ap.add_argument("--embed-model", default="BAAI/bge-small-en-v1.5")
    ap.add_argument("--onnx-path", default=None)
    ap.add_argument("--stub-embedder", action="store_true",
                     help="text-identity dry run only; embeddings are not meaningful")
    ap.add_argument("--out-map", default="benchmarks/chunk_id_migration_map.json")
    ap.add_argument("--out-report", default="benchmarks/CHUNK_ID_MIGRATION_REPORT.md")
    args = ap.parse_args()

    pdf_paths = sorted(Path(args.pdfs_dir).glob("*.pdf"))
    if not pdf_paths:
        sys.exit(f"FATAL: no PDFs found under {args.pdfs_dir}")

    try:
        from tokenizers import Tokenizer
        tok = Tokenizer.from_file(args.tokenizer_path)
    except Exception as e:
        sys.exit(f"FATAL: cannot load tokenizer at {args.tokenizer_path}: {e}")

    encoder = _build_encoder(args)

    index_dir = Path(args.index_dir)
    if index_dir.exists() and any(index_dir.iterdir()):
        sys.exit(
            f"FATAL: {index_dir} already exists and is non-empty. This script "
            f"builds a fresh index for the migration report; remove it or pass "
            f"a different --index-dir."
        )
    idx = Index.open(index_dir)

    for pdf_path in pdf_paths:
        doc = _extract_doc(pdf_path, args.budget, tok)
        result = idx.append_document(doc, encoder)
        status = "already indexed" if result.already_indexed else (
            f"{result.n_chunks_added} chunks appended (rows {result.chunk_id_range})"
        )
        print(f"  {pdf_path.name}: {status}")

    old_ids, old_texts = _load_old_dump_raw(args.old_dump)
    new_records = _load_new_chunks(index_dir)

    if len(old_ids) != len(new_records):
        sys.exit(
            f"FATAL: old dump has {len(old_ids)} chunks, new index has "
            f"{len(new_records)}. Refusing to build a mapping between "
            f"mismatched corpora -- something about the chunker, tokenizer, "
            f"or PDF set has changed since {args.old_dump} was produced."
        )

    mapping: dict[str, str] = {}
    mismatches = []
    for pos, (old_id, old_text) in enumerate(zip(old_ids, old_texts)):
        new_rec = new_records[pos]
        mapping[str(old_id)] = new_rec["id"]
        if old_text != new_rec["text"]:
            mismatches.append({
                "old_id": old_id, "new_id": new_rec["id"],
                "old_text_prefix": old_text[:80], "new_text_prefix": new_rec["text"][:80],
            })

    if mismatches:
        lines = [f"# Chunk ID migration -- REFUSED\n", f"{len(mismatches)} chunk(s) differ between "
                 f"`{args.old_dump}` and `{index_dir}/chunks.jsonl`. Mapping NOT written.\n"]
        for m in mismatches:
            lines.append(f"- old[{m['old_id']}] != new[{m['new_id']}]")
            lines.append(f"    old: {m['old_text_prefix']!r}")
            lines.append(f"    new: {m['new_text_prefix']!r}")
        Path(args.out_report).write_text("\n".join(lines) + "\n")
        print(f"FATAL: {len(mismatches)} chunk text mismatch(es) -- mapping NOT written. "
              f"See {args.out_report}", file=sys.stderr)
        return 2

    Path(args.out_map).write_text(json.dumps(mapping, indent=2))

    docs_summary = []
    for pdf_path in pdf_paths:
        sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        docs_summary.append((pdf_path.name, sha256, idx.manifest["documents"][sha256]))

    items = list(mapping.items())
    sample = items[:5] + (items[-5:] if len(items) > 10 else items[5:])

    lines = [
        "# Chunk ID migration report\n",
        f"Old dump: `{args.old_dump}` ({len(old_ids)} chunks, positional integer ids)",
        f"New index: `{index_dir}` ({len(new_records)} chunks, stable string ids)\n",
        "**Verification: PASSED.** Every mapped chunk's text is byte-identical "
        "between the old dump and the new chunks.jsonl.\n",
        "## Per-document ranges\n",
        "| document | old id range | new id range | n_chunks |",
        "|---|---|---|---|",
    ]
    for name, sha256, info in docs_summary:
        s, e = info["chunk_id_range"]
        lines.append(
            f"| {name} | [{s}, {e - 1}] | {sha256[:8]}:0 .. {sha256[:8]}:{info['n_chunks'] - 1} | {info['n_chunks']} |"
        )
    lines += [
        "\n## Sample mappings (first 5, last 5)\n",
    ]
    for old_id, new_id in sample:
        lines.append(f"- `{old_id}` -> `{new_id}`")
    lines += [
        "\n## What this changes if adopted\n",
        "- Every `gold_chunks`/`retrieved` reference in the question sets "
        "(`data/questions/*.json`) and every benchmark result keyed by a "
        "positional id would need remapping through `chunk_id_migration_map.json`.",
        "- `benchmarks/chunks_sme.txt`'s positional dump format and its "
        "corpus-fingerprint gate would be superseded by "
        f"`{index_dir}/manifest.json` + `chunks.jsonl` (which carries its own "
        "per-document identity via doc_sha256, not a whole-corpus fingerprint).",
        "- **Not done here.** Question sets are NOT rewritten by this script.",
    ]
    Path(args.out_report).write_text("\n".join(lines) + "\n")

    print(f"\nVerified {len(mapping)} chunks byte-identical.")
    print(f"Mapping -> {args.out_map}")
    print(f"Report  -> {args.out_report}")
    print("Question sets NOT rewritten -- review the mapping/report before rewriting anything.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
