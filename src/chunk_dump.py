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
from pathlib import Path


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
