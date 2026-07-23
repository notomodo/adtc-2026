#!/usr/bin/env python3
"""Canonical corpus-fingerprint gate for the chunk dump.

WHY THIS MODULE EXISTS
======================
ingest_sme.py stamps a `# corpus_fingerprint:` line into the dump — a sha256
over every (position, chunk_text) pair. The benchmark harnesses already gate on
it, but that gate only checks the FILE against the question set (dump stamp ==
labels stamp). Nothing checked that the *parser* reproduced the stamped text.

That gap was not hypothetical. Every dump parser used `"\n".join(buf).strip()`,
which deleted a real trailing space on 2 of 47 chunks, so the parsed corpus
hashed to 592a602f845dce20 while the dump stamped c7f23f29b738b08d. The file
passed its gate; the text was then altered *after* the gate — the exact failure
mode the gate exists to prevent, discovered only by hand.

This module closes the hole permanently: recompute the fingerprint over the
PARSED texts and assert it equals the stamp. Fatal on mismatch, at load time,
so any future parser mutation is caught immediately instead of months later.

Stdlib only, by design: the offline hand-tools (label_questions.py,
autolabel.py) import this, and must not be coupled to numpy / the retrieval
stack just to parse a text file.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# Chunk header stamped by ingest_sme.py, e.g.
#   [0] source=General_Terms...pdf type=clause page=1 len=74 tokens=20
_HEADER_RE = re.compile(
    r"^\[(\d+)\] source=(\S+) type=(\S+) page=(\d+) len=(\d+) tokens=(\d+)"
)


class ParserFidelityError(RuntimeError):
    """The parser did not reproduce the dump's stamped corpus fingerprint."""


def compute_fingerprint(texts: list[str]) -> str:
    """The canonical corpus fingerprint ingest_sme.py defines: sha256 over
    (position, text) pairs, first 16 hex — recomputed from PARSED text.

    Must stay byte-identical to ingest_sme.py's formula (search: CORPUS
    FINGERPRINT there). `texts` MUST be the full dump in dump order, because the
    position index here is what the stamp was computed against; hashing a
    source-filtered subset would produce a different, meaningless value.
    """
    joined = "\n".join(f"{i}\x00{t}" for i, t in enumerate(texts))
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


def embedded_fingerprint(path: str | Path) -> str:
    """Return the `# corpus_fingerprint:` value stamped in the dump header, or
    '' if the dump carries none (legacy pre-fingerprint artifacts)."""
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("# corpus_fingerprint:"):
            return line.split(":", 1)[1].strip()
        if not line.startswith("#"):
            break
    return ""


def verify_fidelity(texts: list[str], path: str | Path) -> str:
    """FATAL parser-fidelity gate.

    The fingerprint recomputed over `texts` (the parser's output, full dump in
    order) must equal the `# corpus_fingerprint:` stamped in `path`. Raises
    ParserFidelityError on mismatch — deliberately fatal, never a warning: a
    warning is discovered by hand months later, whereas the whole point is to
    catch a parser regression at the instant it loads a dump.

    If the dump carries no stamp, fidelity cannot be checked, so this returns
    '' without raising. The FILE-level gates in the callers still refuse to run
    a stampless corpus, so this is not a hole — it only declines to invent a
    check it has no reference for.

    Returns the stamped fingerprint (or '') so callers can reuse it.
    """
    stamped = embedded_fingerprint(path)
    if not stamped:
        return stamped
    got = compute_fingerprint(texts)
    if got != stamped:
        raise ParserFidelityError(
            f"parser fidelity FAILED for {path}:\n"
            f"    stamped corpus_fingerprint : {stamped}\n"
            f"    recomputed over parsed text: {got}\n"
            f"The parser did not reproduce the dump byte-for-byte (a stray "
            f".strip() dropping a real trailing space is the known cause). "
            f"Chunk ids are positional; every gold label and every benchmark "
            f"number keyed by them would be suspect. Refusing to proceed."
        )
    return stamped


def parse_dump(
    path: str | Path, source: str | None = None
) -> tuple[list[int], list[str], list[dict]]:
    """The one canonical, byte-faithful chunk-dump parser.

    Returns (ids, texts, metas) in dump order. The parser-fidelity gate runs
    over the FULL corpus first (the stamp is computed over every chunk in
    order, so a source-filtered subset could not be checked against it), THEN
    the optional `source` filter is applied to the returned rows.

    Byte-faithful: the writer (ingest_sme.py) emits one trailing blank spacer
    line between chunks; that "" is dropped and NOTHING else. No .strip() — two
    chunks (ids 0, 22) carry a real trailing space that is part of their text
    and counted in the header's len= field.
    """
    ids: list[int] = []
    texts: list[str] = []
    metas: list[dict] = []

    cur_id: int | None = None
    cur_meta: dict = {}
    buf: list[str] = []
    in_body = False

    def flush() -> None:
        nonlocal cur_id, buf
        if cur_id is not None:
            body = buf[:-1] if buf and buf[-1] == "" else buf
            ids.append(cur_id)
            texts.append("\n".join(body))
            metas.append(dict(cur_meta))
        cur_id, buf = None, []

    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = _HEADER_RE.match(line)
            if m:
                flush()
                cur_id = int(m.group(1))
                cur_meta = {
                    "source": m.group(2),
                    "type": m.group(3),
                    "page": int(m.group(4)),
                    "tokens": int(m.group(6)),
                }
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

    verify_fidelity(texts, path)

    if source is None:
        return ids, texts, metas
    keep = [i for i, meta in enumerate(metas) if meta["source"] == source]
    return (
        [ids[i] for i in keep],
        [texts[i] for i in keep],
        [metas[i] for i in keep],
    )


def load_chunk_map(path: str | Path) -> dict[int, str]:
    """{chunk_id: text} in dump order — byte-faithful and gated. The shape the
    generation/judging harnesses want."""
    ids, texts, _ = parse_dump(path)
    return dict(zip(ids, texts))
