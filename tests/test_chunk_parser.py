"""Chunk-dump parser byte-fidelity + fingerprint-gate controls.

STANDING LESSON (see tests/test_extraction.py, tests/test_index.py): a test that
only passes on correct input proves nothing. The v1 extraction defect and the
.strip() parser defect both shipped behind green happy-path tests. So the
load-bearing test here is a KNOWN-BAD control — a parser that .strip()s the
chunk text MUST be rejected by the gate. A gate that never fires is a placebo.

The header `len=` field is independent corroboration: ingest_sme.py writes it
from the true chunk length, so matching it byte-for-byte across all 47 chunks is
a strong invariant, not a tautology of the parser under test.

The core invariants run on a STDLIB parser (label_questions.load_chunks) so they
need no numpy / retrieval stack; a separate test cross-checks the canonical
eval_retriever parser and skips if that stack is unavailable.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DUMP = ROOT / "benchmarks" / "chunks_sme.txt"
RAW_FP = "c7f23f29b738b08d"       # over the true (raw) bodies — what ingest stamps
STRIPPED_FP = "592a602f845dce20"  # what a .strip()ing parser produces — the defect

from chunk_dump import (  # noqa: E402
    ParserFidelityError,
    compute_fingerprint,
    embedded_fingerprint,
    verify_fidelity,
)


def _header_lens() -> dict[int, int]:
    """The `len=` field ingest_sme.py stamped for every chunk, parsed directly
    from the dump header (independent of the parser under test)."""
    hdr = re.compile(r"^\[(\d+)\] .* len=(\d+) tokens=")
    out: dict[int, int] = {}
    for line in DUMP.read_text(encoding="utf-8").splitlines():
        m = hdr.match(line)
        if m:
            out[int(m.group(1))] = int(m.group(2))
    return out


def _stdlib_parse() -> tuple[list[int], list[str], list[dict]]:
    """The stdlib parser (no numpy). label_questions.load_chunks runs the gate
    internally; if it were not byte-faithful this call would already raise."""
    from label_questions import load_chunks
    return load_chunks(str(DUMP))


# --- known-good control -----------------------------------------------------

def test_real_dump_parses_clean_and_matches_stamp():
    ids, texts, _ = _stdlib_parse()
    assert len(texts) == 47
    assert compute_fingerprint(texts) == RAW_FP
    assert embedded_fingerprint(DUMP) == RAW_FP


def test_canonical_parser_agrees():
    """The canonical eval_retriever parser must reproduce the same bytes."""
    pytest.importorskip("numpy")
    try:
        from eval_retriever import load_chunks
    except Exception as e:  # retrieval stack (retriever.py) unavailable
        pytest.skip(f"eval_retriever import unavailable: {e}")
    ids, texts, _ = load_chunks(str(DUMP), None)
    assert compute_fingerprint(texts) == RAW_FP


# --- known-bad control (the load-bearing test) ------------------------------

def test_stripping_parser_is_rejected_by_the_gate():
    ids, texts, _ = _stdlib_parse()
    stripped = [t.strip() for t in texts]
    # sanity: stripping actually changes the fingerprint, else the test is vacuous
    assert compute_fingerprint(stripped) == STRIPPED_FP
    assert STRIPPED_FP != RAW_FP
    with pytest.raises(ParserFidelityError):
        verify_fidelity(stripped, DUMP)


# --- byte-fidelity invariants -----------------------------------------------

def test_affected_chunks_retain_trailing_space():
    ids, texts, _ = _stdlib_parse()
    by_id = dict(zip(ids, texts))
    assert by_id[0].endswith(" "), "chunk 0 lost its real trailing space"
    assert by_id[22].endswith(" "), "chunk 22 lost its real trailing space"


def test_len_matches_header_for_all_47_chunks():
    ids, texts, _ = _stdlib_parse()
    lens = _header_lens()
    assert len(lens) == 47
    mism = [(i, lens[i], len(t)) for i, t in zip(ids, texts) if len(t) != lens[i]]
    assert not mism, f"len(text) != header len= for: {mism}"


# --- gate behaviour on a stampless dump -------------------------------------

def test_gate_is_noop_without_a_stamp(tmp_path):
    """No `# corpus_fingerprint:` -> nothing to verify against -> no raise, ''."""
    d = tmp_path / "nostamp.txt"
    d.write_text("# a header with no fingerprint\n\nCHUNKS\n", encoding="utf-8")
    assert verify_fidelity(["anything at all"], d) == ""
