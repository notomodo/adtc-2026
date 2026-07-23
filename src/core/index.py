#!/usr/bin/env python3
"""Persistent, append-only chunk index — the storage contract everything else
depends on. No CLI, no UI, no printing here: this module returns structured
data and raises on error.

WHY STABLE STRING IDS, NOT POSITIONAL INTEGERS
===============================================
`ingest_sme.py` assigns chunk ids by `enumerate()` over the whole corpus, and
its corpus fingerprint hashes `(position, text)` pairs — the id scheme and the
reproducibility gate are the same mechanism. That is fine for a one-shot batch
dump, but it means appending a document renumbers every chunk after it, which
would silently invalidate every existing gold label and every citation ever
shown to a user. Chunk ids here are `f"{doc_sha256[:8]}:{ordinal}"`, where
`ordinal` is per-document and zero-based — appending a document can only ever
add new ids, never touch an old one.

WHY THIS DOES NOT REUSE `HybridRetriever`
==========================================
`src/retriever.py`'s `HybridRetriever` is the class DECISION-002 measured, but
its constructor unconditionally calls `encoder.encode(self.chunks)` on the
*entire* corpus and holds the resulting matrix fully resident. That is
incompatible with "embed only the new document's chunks" and "load embeddings
via mmap; do not hold the full array resident." So this module reuses the
actual locked pieces directly — `retriever.BM25` (the class) and
`retriever.rrf_fuse` (the function) — and does its own thin orchestration
(candidate-list building, mmapped dot product) instead of wrapping
`HybridRetriever`. The BM25 *scoring formula* is never reimplemented: at
search time a `BM25` instance is reconstructed by bypassing `__init__`
(`BM25.__new__`, attributes populated from `bm25.json`) and its real,
unmodified `.scores()` method is called. `BM25.scores()` only reads
`n/idf/tf/doc_len/avgdl/k1/b` — never `self.docs` — so this reconstruction is
exact, not an approximation.

WHY BM25 IS REBUILT ON EVERY APPEND, NOT PATCHED INCREMENTALLY
================================================================
BM25's IDF is a corpus-global statistic: adding one document changes the
document frequency, and therefore the IDF weight, of every term in the
corpus. There is no correct incremental IDF update — "patching" one would
mean re-deriving the same formula by hand, which is exactly the
reimplementation the task forbids. So `bm25.json` is fully rebuilt from the
committed chunk texts on every append (O(corpus), append-time only, never on
the search hot path) by calling the real `BM25(texts)` constructor.

WHY ENCODERS NEED A SEPARATE IDENTITY WRAPPER
==============================================
`retriever.Encoder` only requires `.encode()`; `OnnxEncoder` does not even
retain its own `model_name` as an attribute. The manifest's fatal
embedder/tokenizer mismatch check needs something to compare against, so this
module defines its own `IdentifiedEncoder` protocol and `EncoderHandle`
adapter here, rather than modifying `retriever.py`.

ATOMIC APPEND, AND WHY MANIFEST IS WRITTEN LAST
================================================
Each of the four files (chunks.jsonl, embeddings.npy, bm25.json,
manifest.json) is written to a temp file, fsync'd, then renamed into place —
each individual rename is atomic on POSIX, so no single file is ever observed
half-written. But a crash *between* two of those renames is still possible,
and manifest.json is the source of truth for "what is committed": it is
written last, so a crash before it leaves chunks.jsonl and/or embeddings.npy
and/or bm25.json one document ahead of what the manifest (and therefore
`has_document()`) admits to. `Index.open()` reconciles this on every open:
if chunks.jsonl (or embeddings.npy) has more rows than the manifest's
declared chunk count, the orphaned tail is truncated away; if bm25.json's
recorded chunk count does not match, it is rebuilt from the (now consistent)
chunk texts. This makes the crash window fully self-healing without ever
needing a separate repair tool.
"""

from __future__ import annotations

import hashlib
import json
import os
import resource
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, Sequence

import numpy as np

# retriever.py is a flat top-level module in src/, not a package — mirror the
# import pattern gen_answer.py already uses for the same module.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retriever import BM25, rrf_fuse  # noqa: E402  — LOCKED by DECISION-002, not reimplemented

SCHEMA_VERSION = 1
EMBED_DIM = 384
DEFAULT_INDEX_DIR = Path.home() / ".adtc" / "index"
DEFAULT_CANDIDATE_DEPTH = 50
DEFAULT_CONSIDERED = 5
RRF_K = 60.0  # DECISION-002: Cormack et al. 2009's constant, not tuned per-corpus.


# =============================================================================
# Input contract — what a caller must have already produced
# =============================================================================


@dataclass(frozen=True)
class ExtractedChunk:
    """One chunk of an already-extracted, already-chunked document.

    char_start/char_end are offsets into that document's own reconstructed
    text stream (never the whole corpus) — see scripts/migrate_chunk_ids.py
    for how ingest_sme.py's chunker output is adapted into this shape, since
    ingest_sme.py itself does not track character offsets today.
    """

    page: int
    char_start: int
    char_end: int
    text: str
    n_tokens: int


@dataclass(frozen=True)
class ExtractedDoc:
    """What a caller (an ingestion script) must produce before calling
    Index.append_document. This module does not extract or chunk PDFs —
    see ingest_sme.py for that — it only persists the result."""

    sha256: str
    filename: str
    pages: int
    chunks: list[ExtractedChunk]


# =============================================================================
# Encoder identity
# =============================================================================


class IdentifiedEncoder(Protocol):
    """Anything retriever.Encoder can already do, plus the identity strings
    the manifest needs to detect a re-embed with the wrong model or
    tokenizer. Wrap a plain retriever.Encoder with EncoderHandle to satisfy
    this without modifying retriever.py."""

    embedder_id: str
    tokenizer_sha256: str

    def encode(self, texts: Sequence[str], is_query: bool = False) -> np.ndarray: ...


@dataclass
class EncoderHandle:
    """Adapts any retriever.Encoder to IdentifiedEncoder.

    embedder_id should name the model + revision actually producing vectors
    (e.g. "BAAI/bge-small-en-v1.5"). tokenizer_sha256 should be
    hashlib.sha256(Path("src/tokenizer.json").read_bytes()).hexdigest() —
    the vendored tokenizer file's own content hash, so a re-vendor with a
    different tokenizer is caught even if embedder_id string is left
    unchanged by mistake.
    """

    encoder: object
    embedder_id: str
    tokenizer_sha256: str

    def encode(self, texts: Sequence[str], is_query: bool = False) -> np.ndarray:
        return self.encoder.encode(texts, is_query=is_query)


# =============================================================================
# Results
# =============================================================================


@dataclass
class AppendResult:
    doc_sha256: str
    already_indexed: bool
    n_chunks_added: int
    chunk_id_range: tuple[int, int]  # [start, end) row-span in chunks.jsonl / embeddings.npy


@dataclass
class Hit:
    id: str
    text: str
    filename: str
    page: int
    char_start: int
    char_end: int
    rrf_score: float
    bm25_rank: int | None
    dense_rank: int | None


@dataclass
class SearchResult:
    hits: list[Hit]
    considered: list[Hit]
    timings: dict[str, float]


@dataclass
class IndexStats:
    n_documents: int
    n_chunks: int
    bytes_on_disk: dict[str, int]
    bm25_load_rss_delta_bytes: int


# =============================================================================
# Small stateless helpers
# =============================================================================


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tmp_path(path: Path) -> Path:
    return path.parent / f"{path.name}.tmp{os.getpid()}"


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write-fsync-rename. A crash mid-write leaves `path` exactly as it
    was — the temp file is simply orphaned, never partially visible at the
    real path, because os.replace is atomic on POSIX."""
    tmp = _tmp_path(path)
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _atomic_write_text(path: Path, text: str) -> None:
    _atomic_write_bytes(path, text.encode("utf-8"))


def _atomic_write_npy(path: Path, arr: np.ndarray) -> None:
    tmp = _tmp_path(path)
    with open(tmp, "wb") as f:
        np.save(f, arr)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _l2_normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return (vecs / np.clip(norms, 1e-9, None)).astype(np.float32)


def _bm25_rank_positions(bm25: BM25 | None, query: str, depth: int) -> list[int]:
    """Mirrors HybridRetriever._bm25_ranking's orchestration exactly — the
    scoring formula lives in bm25.scores(), reused unmodified; this is just
    the argsort-and-filter glue needed to call it against a persisted index
    instead of an in-memory HybridRetriever."""
    if bm25 is None:
        return []
    scores = bm25.scores(query)
    idx = np.argsort(scores)[::-1][:depth]
    return [int(i) for i in idx if scores[i] > 0.0]


def _dense_rank_positions(emb: np.ndarray, q_vec: np.ndarray, depth: int) -> list[int]:
    """Both sides are L2-normalised, so the dot product IS cosine similarity
    — no per-query normalisation pass needed."""
    sims = emb @ q_vec
    idx = np.argsort(sims)[::-1][:depth]
    return [int(i) for i in idx]


# =============================================================================
# The index
# =============================================================================


class Index:
    """A persistent, append-only chunk index. Construct via `Index.open()`,
    not directly."""

    def __init__(self, path: Path, manifest: dict) -> None:
        self.path = path
        self.manifest = manifest

    # -- paths -----------------------------------------------------------

    @property
    def _manifest_path(self) -> Path:
        return self.path / "manifest.json"

    @property
    def _chunks_path(self) -> Path:
        return self.path / "chunks.jsonl"

    @property
    def _embeddings_path(self) -> Path:
        return self.path / "embeddings.npy"

    @property
    def _bm25_path(self) -> Path:
        return self.path / "bm25.json"

    # -- construction ------------------------------------------------------

    @classmethod
    def open(cls, path: Path | None = None) -> "Index":
        """Open an existing index, or initialise an empty one at `path`
        (default ~/.adtc/index). Reconciles any crash-orphaned state left by
        a previous append_document call before returning."""
        path = Path(path).expanduser() if path is not None else DEFAULT_INDEX_DIR
        path.mkdir(parents=True, exist_ok=True)

        manifest_path = path / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("schema_version") != SCHEMA_VERSION:
                raise AssertionError(
                    f"Index at {path} has schema_version={manifest.get('schema_version')!r}, "
                    f"this code expects {SCHEMA_VERSION!r}. Refusing to open — a silent "
                    f"schema mismatch is exactly the failure class this module exists to prevent."
                )
        else:
            now = _now_iso()
            manifest = {
                "schema_version": SCHEMA_VERSION,
                "embedder_id": None,
                "tokenizer_sha256": None,
                "created_at": now,
                "updated_at": now,
                "documents": {},
            }

        idx = cls(path, manifest)
        idx._recover()
        return idx

    # -- crash recovery ------------------------------------------------------

    def _expected_n_chunks(self) -> int:
        return sum(d["n_chunks"] for d in self.manifest["documents"].values())

    def _read_all_chunks(self) -> list[dict]:
        p = self._chunks_path
        if not p.exists():
            return []
        out: list[dict] = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def _write_chunks_file(self, records: list[dict]) -> None:
        body = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
        if records:
            body += "\n"
        _atomic_write_text(self._chunks_path, body)

    def _write_bm25_file(self, bm25: BM25 | None, n: int) -> None:
        if bm25 is None or n == 0:
            payload = {
                "n": 0, "k1": 1.5, "b": 0.75, "avgdl": 0.0,
                "doc_len": [], "idf": {}, "inverted": {},
            }
        else:
            # "inverted index": term -> {ordinal: term_frequency}. Reconstructed
            # into bm25.tf (list[Counter], one per chunk) on load — the shape
            # BM25.scores() actually reads.
            inverted: dict[str, dict[str, int]] = {}
            for doc_idx, tf in enumerate(bm25.tf):
                for term, count in tf.items():
                    inverted.setdefault(term, {})[str(doc_idx)] = count
            payload = {
                "n": bm25.n,
                "k1": bm25.k1,
                "b": bm25.b,
                "avgdl": bm25.avgdl,
                "doc_len": bm25.doc_len.tolist(),
                "idf": bm25.idf,
                "inverted": inverted,
            }
        _atomic_write_text(self._bm25_path, json.dumps(payload))

    def _load_bm25(self) -> BM25 | None:
        """Reconstruct the real retriever.BM25 object by bypassing __init__
        (which retokenises the whole corpus) and populating its attributes
        from the persisted bm25.json instead. .scores() is then the actual,
        unmodified DECISION-002 method — see module docstring."""
        if not self._bm25_path.exists():
            return None
        payload = json.loads(self._bm25_path.read_text())
        if payload["n"] == 0:
            return None
        bm25 = BM25.__new__(BM25)
        bm25.k1 = payload["k1"]
        bm25.b = payload["b"]
        bm25.n = payload["n"]
        bm25.avgdl = payload["avgdl"]
        bm25.doc_len = np.array(payload["doc_len"], dtype=np.float32)
        bm25.idf = payload["idf"]
        tf: list[Counter] = [Counter() for _ in range(bm25.n)]
        for term, per_doc in payload["inverted"].items():
            for doc_idx_str, count in per_doc.items():
                tf[int(doc_idx_str)][term] = count
        bm25.tf = tf
        bm25.docs = None  # never read by .scores(); not worth reconstructing
        return bm25

    def _recover(self) -> None:
        expected = self._expected_n_chunks()

        if expected == 0 and not self._chunks_path.exists() and not self._bm25_path.exists():
            return  # pristine, never-appended index — nothing to reconcile

        chunks = self._read_all_chunks()
        actual = len(chunks)

        if actual < expected:
            raise AssertionError(
                f"Index at {self.path} is corrupt: manifest declares {expected} chunks "
                f"but chunks.jsonl has only {actual}. A crash can only leave EXTRA "
                f"orphaned rows (never fewer than committed) — this is beyond the "
                f"recoverable crash window. Do not open this index; restore from backup."
            )

        if actual > expected:
            # Orphaned tail from a crash between the embeddings write and the
            # manifest write of a previous append_document call.
            chunks = chunks[:expected]
            self._write_chunks_file(chunks)
            if self._embeddings_path.exists():
                emb = np.load(self._embeddings_path)
                if emb.shape[0] > expected:
                    _atomic_write_npy(self._embeddings_path, np.ascontiguousarray(emb[:expected]))

        bm25_n = None
        if self._bm25_path.exists():
            try:
                bm25_n = json.loads(self._bm25_path.read_text())["n"]
            except Exception:
                bm25_n = None
        if bm25_n != expected:
            texts = [c["text"] for c in chunks]
            bm25 = BM25(texts) if texts else None
            self._write_bm25_file(bm25, len(texts))

        if self._embeddings_path.exists():
            emb = np.load(self._embeddings_path, mmap_mode="r")
            assert emb.shape[0] == expected, (
                f"embeddings.npy has {emb.shape[0]} rows, expected {expected} after recovery"
            )
        ids = [c["id"] for c in chunks]
        assert len(ids) == len(set(ids)), "duplicate chunk id survived recovery"

    # -- encoder identity ------------------------------------------------

    def _assert_encoder_matches(self, encoder: IdentifiedEncoder) -> None:
        want_embedder = self.manifest.get("embedder_id")
        want_tok = self.manifest.get("tokenizer_sha256")
        if want_embedder is None:
            return  # empty index — this call defines the identity
        if encoder.embedder_id != want_embedder or encoder.tokenizer_sha256 != want_tok:
            raise AssertionError(
                f"Encoder identity mismatch: index at {self.path} was built with "
                f"embedder_id={want_embedder!r} tokenizer_sha256={want_tok!r}, but the "
                f"encoder passed here is embedder_id={encoder.embedder_id!r} "
                f"tokenizer_sha256={encoder.tokenizer_sha256!r}. This is FATAL, not a "
                f"silent re-embed: mixing embedding spaces in one index makes every "
                f"dense score meaningless."
            )

    # -- public API --------------------------------------------------------

    def has_document(self, sha256: str) -> bool:
        return sha256 in self.manifest["documents"]

    def append_document(self, doc: ExtractedDoc, encoder: IdentifiedEncoder) -> AppendResult:
        if doc.sha256 in self.manifest["documents"]:
            existing = self.manifest["documents"][doc.sha256]
            return AppendResult(
                doc_sha256=doc.sha256,
                already_indexed=True,
                n_chunks_added=0,
                chunk_id_range=tuple(existing["chunk_id_range"]),
            )

        if not doc.chunks:
            raise ValueError(f"{doc.filename}: ExtractedDoc has zero chunks, nothing to append")

        self._assert_encoder_matches(encoder)

        sha8 = doc.sha256[:8]
        for existing_sha in self.manifest["documents"]:
            if existing_sha[:8] == sha8 and existing_sha != doc.sha256:
                raise AssertionError(
                    f"sha256 prefix collision: {doc.sha256} and {existing_sha} share the "
                    f"first 8 hex characters. Stable chunk ids would collide "
                    f"({sha8}:N for both documents). Refusing to append."
                )

        existing_records = self._read_all_chunks()
        start = len(existing_records)

        new_records = []
        for ordinal, ch in enumerate(doc.chunks):
            new_records.append({
                "id": f"{sha8}:{ordinal}",
                "doc_sha256": doc.sha256,
                "filename": doc.filename,
                "page": ch.page,
                "char_start": ch.char_start,
                "char_end": ch.char_end,
                "text": ch.text,
                "n_tokens": ch.n_tokens,
            })

        # --- step 1: chunks.jsonl (atomic) ---
        all_records = existing_records + new_records
        self._write_chunks_file(all_records)

        # --- step 2: embeddings.npy (atomic) — incremental: embed only the new chunks ---
        texts_new = [r["text"] for r in new_records]
        new_vecs = _l2_normalize(encoder.encode(texts_new, is_query=False))
        assert new_vecs.shape == (len(new_records), EMBED_DIM), (
            f"encoder produced shape {new_vecs.shape}, expected "
            f"({len(new_records)}, {EMBED_DIM})"
        )
        assert np.allclose(np.linalg.norm(new_vecs, axis=1), 1.0, atol=1e-5), (
            "embeddings are not unit-norm after normalisation — encoder likely "
            "produced a zero or NaN vector"
        )

        if existing_records:
            old_vecs = np.load(self._embeddings_path)
            full_vecs = np.concatenate([old_vecs, new_vecs], axis=0)
        else:
            full_vecs = new_vecs
        _atomic_write_npy(self._embeddings_path, full_vecs.astype(np.float32))
        assert full_vecs.shape[0] == len(all_records), (
            f"embeddings row count {full_vecs.shape[0]} != chunk count {len(all_records)}"
        )

        # --- step 3: bm25.json (atomic) — full rebuild, see module docstring ---
        all_texts = [r["text"] for r in all_records]
        bm25 = BM25(all_texts)
        self._write_bm25_file(bm25, len(all_texts))

        # --- step 4: manifest.json (atomic, LAST — the commit point) ---
        # Build a NEW dict and only swap it into self.manifest after the
        # durable write succeeds. Mutating self.manifest before the write
        # would leave this object's in-memory state claiming a document is
        # indexed even if the write below raises (e.g. the crash this
        # module is designed to survive) — has_document() must never lie.
        end = len(all_records)
        now = _now_iso()
        new_manifest = dict(self.manifest)
        new_manifest["documents"] = dict(self.manifest["documents"])
        if new_manifest["embedder_id"] is None:
            new_manifest["embedder_id"] = encoder.embedder_id
            new_manifest["tokenizer_sha256"] = encoder.tokenizer_sha256
            new_manifest["created_at"] = now
        new_manifest["documents"][doc.sha256] = {
            "filename": doc.filename,
            "pages": doc.pages,
            "n_chunks": len(new_records),
            "chunk_id_range": [start, end],
            "ingested_at": now,
        }
        new_manifest["updated_at"] = now
        _atomic_write_text(self._manifest_path, json.dumps(new_manifest, indent=2))
        self.manifest = new_manifest

        ids = [r["id"] for r in all_records]
        assert len(ids) == len(set(ids)), "duplicate chunk id after append"

        return AppendResult(
            doc_sha256=doc.sha256,
            already_indexed=False,
            n_chunks_added=len(new_records),
            chunk_id_range=(start, end),
        )

    def search(self, query: str, k: int, encoder: IdentifiedEncoder) -> SearchResult:
        t_start = time.perf_counter()
        self._assert_encoder_matches(encoder)

        n_chunks = self._expected_n_chunks()
        if n_chunks == 0:
            return SearchResult(
                hits=[], considered=[],
                timings={"bm25_ms": 0.0, "dense_ms": 0.0, "fuse_ms": 0.0, "total_ms": 0.0},
            )

        depth = min(DEFAULT_CANDIDATE_DEPTH, n_chunks)

        t0 = time.perf_counter()
        bm25 = self._load_bm25()
        bm_ranking = _bm25_rank_positions(bm25, query, depth)
        t1 = time.perf_counter()

        q_vec = encoder.encode([query], is_query=True)[0]
        # mmap: search must not hold the full embeddings matrix resident — only
        # the pages the dot product actually touches get paged in.
        emb = np.load(self._embeddings_path, mmap_mode="r")
        assert emb.shape[0] == n_chunks, (
            f"embeddings.npy has {emb.shape[0]} rows, manifest expects {n_chunks}"
        )
        dn_ranking = _dense_rank_positions(emb, q_vec, depth)
        t2 = time.perf_counter()

        fused = rrf_fuse([bm_ranking, dn_ranking], k=RRF_K)
        t3 = time.perf_counter()

        bm_rank_of = {d: r for r, d in enumerate(bm_ranking, 1)}
        dn_rank_of = {d: r for r, d in enumerate(dn_ranking, 1)}

        records = self._read_all_chunks()

        def make_hit(pos: int, score: float) -> Hit:
            r = records[pos]
            return Hit(
                id=r["id"], text=r["text"], filename=r["filename"], page=r["page"],
                char_start=r["char_start"], char_end=r["char_end"],
                rrf_score=score, bm25_rank=bm_rank_of.get(pos), dense_rank=dn_rank_of.get(pos),
            )

        hits = [make_hit(pos, score) for pos, score in fused[:k]]
        considered = [make_hit(pos, score) for pos, score in fused[k:k + DEFAULT_CONSIDERED]]

        total_ms = (time.perf_counter() - t_start) * 1000
        timings = {
            "bm25_ms": (t1 - t0) * 1000,
            "dense_ms": (t2 - t1) * 1000,
            "fuse_ms": (t3 - t2) * 1000,
            "total_ms": total_ms,
        }
        return SearchResult(hits=hits, considered=considered, timings=timings)

    def stats(self) -> IndexStats:
        n_docs = len(self.manifest["documents"])
        n_chunks = self._expected_n_chunks()

        bytes_on_disk = {}
        for name in ("manifest.json", "chunks.jsonl", "embeddings.npy", "bm25.json"):
            p = self.path / name
            bytes_on_disk[name] = p.stat().st_size if p.exists() else 0

        # ru_maxrss is a HIGH-WATER MARK that never falls within a process, so
        # this delta is only meaningful measured immediately around the call —
        # which is exactly what it is here: a rough scaling number, not a
        # profiler. Linux reports KB; Darwin reports bytes.
        rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self._load_bm25()
        rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        unit = 1 if sys.platform == "darwin" else 1024
        rss_delta = max(0, rss_after - rss_before) * unit

        return IndexStats(
            n_documents=n_docs,
            n_chunks=n_chunks,
            bytes_on_disk=bytes_on_disk,
            bm25_load_rss_delta_bytes=rss_delta,
        )
