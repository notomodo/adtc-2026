"""Extraction regression tests.

THE POINT OF THIS FILE
======================
Every defect in this project's history passed a structural check. These tests
assert SEMANTIC properties, and they assert them in BOTH directions:

    - Gates must FIRE on known-bad input   (negative control)
    - Gates must stay SILENT on known-good  (positive control)

The v2.0 gate had only the first. It was therefore proven able to FAIL but never
proven able to PASS -- and it over-fired on a table of contents. Both directions,
always.

Run:  pytest -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "ingestion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_extraction import (  # noqa: E402
    is_orphan_number_block,
    is_garbled,
    has_ambiguous_headers,
    is_front_matter,
    digit_density,
)
from extract import serialise_table, find_header_span, merge_header_stack  # noqa: E402


# =============================================================================
# GATE 1 — unlabelled digit-walls (the original v1 defect)
# =============================================================================

V1_BROKEN = (
    "Total revenue 1,522,676 1,267,089 20.2% 772,184 639,161 20.8%\n"
    "Service revenue 1,505,398 1,250,059 20.4% 764,029 628,948 21.5%"
)

#: Permanent negative control committed to the repo. This is the project's
#: defining bug frozen on disk: a financial table whose column headers were lost
#: in extraction, leaving unlabelled numbers. A gate that has never failed is
#: untested, so this fixture stays in the repo forever.
CORRUPTED_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "CORRUPTED_v1_output.txt"


def test_gate1_fires_on_v1_defect():
    """NEGATIVE CONTROL — the defining bug of this project.

    Six numbers, zero column headers. Which is H1 2024? Unanswerable. No
    embedding model can retrieve what is not semantically present.
    """
    assert is_orphan_number_block(V1_BROKEN)


def test_gate1_fires_on_corrupted_fixture():
    """NEGATIVE CONTROL, pinned to disk — the permanent regression fixture.

    Reads tests/fixtures/CORRUPTED_v1_output.txt (the real v1 defect: a table
    whose headers were lost in extraction) and asserts GATE 1 FIRES on it. If
    this ever stops firing, the gate has silently stopped protecting against the
    bug the whole project exists to prevent.
    """
    corrupted = CORRUPTED_FIXTURE.read_text(encoding="utf-8")
    assert is_orphan_number_block(corrupted)


@pytest.mark.parametrize("text", [
    "Total revenue | H1 2024: 1,522,676 | H1 2023: 1,267,089 | YoY: 20.2%",
    "Service revenue | 2025: 3,566,206 | 2024: 3,143,587",
    "Service revenue grew by 20.4% driven by resilience in connectivity.",
])
def test_gate1_silent_on_good(text):
    """POSITIVE CONTROL — fixed output and ordinary prose must pass."""
    assert not is_orphan_number_block(text)


@pytest.mark.parametrize("text", [
    "5.1 Conclusion . . . . . . . . . . . . . . . . . 28\n"
    "5.2 Recommendations . . . . . . . . . . . . . . . 29",
    "List of Figures\n2.1 On-Off Shift Keying [6]. . . . . . . . . . . 6",
    "List of Tables\n2.1 Operational Comparison of Low-Power Protocols . . . . 5",
])
def test_gate1_silent_on_front_matter(text):
    """REGRESSION — v2.0 fired on these.

    Root cause: the numeric-token regex matched a BARE DOT, so dot-leader lines
    scored 0.90 density. Front matter is correctly extracted content.
    """
    assert is_front_matter(text)
    assert not is_orphan_number_block(text)


def test_bare_dot_is_not_a_number():
    """The exact v2.0 bug, pinned."""
    toc = "5.1 Conclusion . . . . . . . . . . . . . . . . . 28"
    assert digit_density(toc) < 0.35


# =============================================================================
# GATE 3 — labels present but MEANINGLESS
# =============================================================================

@pytest.mark.parametrize("text", [
    # Real annual-report output. "XGU" is "UGX" reversed; "col1" means header
    # detection failed entirely.
    "1.1 tn XGU | col1: UGX 947.5 bn UGX 811.8 bn",
    "Profit after tax rose Taxes contribu 678.8 XG 1.6 XG | .7 bn: ted",
])
def test_gate3_fires_on_garbled(text):
    """NEGATIVE CONTROL — rotated/curved source text, character-level garbling."""
    assert is_garbled(text)


@pytest.mark.parametrize("text", [
    "Service revenue | 2025: 3,566,206 | 2024: 3,143,587",
    "Total revenue | H1 2024: 1,522,676 | YoY: 20.2%",
    # A vocabulary-based detector wrongly flagged this. Domain acronyms are NOT
    # garbling. GATE 3 must key on corruption artifacts, never on vocabulary.
    "ASK/OOK | Frequency Band: 433.92 MHz | Typical Range: 50m - 100m",
])
def test_gate3_silent_on_good(text):
    assert not is_garbled(text)


# =============================================================================
# GATE 4 — duplicate headers (values labelled but UNRESOLVABLE)
# =============================================================================

def test_gate4_fires_on_duplicate_headers():
    """NEGATIVE CONTROL — v3.0 took the UNITS row as the header.

    Three columns, three identical headers. Every value is labelled, so GATE 1
    and GATE 3 both PASS -- and nothing says which column is June 2024.
    """
    bad = ("Property, plant and equipment | Shs '000: 1,200,858,421 "
           "| Shs '000: 1,031,959,769 | Shs '000: 1,086,547,617")
    assert has_ambiguous_headers(bad)


def test_gate4_silent_on_merged_stack():
    """POSITIVE CONTROL — v3.1 merges the full header stack."""
    good = ("Property, plant and equipment | June 2024 Reviewed Shs '000: 1,200,858,421 "
            "| June 2023 Reviewed Shs '000: 1,031,959,769")
    assert not has_ambiguous_headers(good)


# =============================================================================
# Header-stack detection — the four real shapes
# =============================================================================

def test_header_stack_three_rows():
    """Statutory statements: period / audit status / units."""
    rows = [
        ["", "June 2024", "June 2023"],
        ["", "Reviewed", "Reviewed"],
        ["", "Shs '000", "Shs '000"],
        ["PPE", "1,200,858,421", "1,031,959,769"],
    ]
    s, e = find_header_span(rows)
    assert (s, e) == (0, 3)
    hdr = merge_header_stack(rows, s, e)
    assert hdr[1] == "June 2024 Reviewed Shs '000"


def test_header_row_of_years_is_not_data():
    """REGRESSION — a 'headers are non-numeric' heuristic FAILED here.

    In financial tables the header row is often YEARS. The heuristic broke on
    the exact document class it existed to serve. The working signal is
    structural: a blank stub cell.
    """
    rows = [
        ["", "2025", "2024", "2023"],
        ["Service revenue", "3,566,206", "3,143,587", "2,629,863"],
    ]
    s, e = find_header_span(rows)
    assert (s, e) == (0, 1)
    assert merge_header_stack(rows, s, e)[1] == "2025"


def test_labelled_stub_column():
    """Ruled tables usually DO label the stub ('Ush million')."""
    rows = [
        ["Ush million", "H1 2024", "H1 2023", "YoY"],
        ["Total revenue", "1,522,676", "1,267,089", "20.2%"],
    ]
    s, e = find_header_span(rows)
    assert s is not None
    assert merge_header_stack(rows, s, e)[1] == "H1 2024"


# =============================================================================
# End-to-end serialisation — the core fix
# =============================================================================

def test_serialise_attaches_headers_to_every_value():
    """THE CORE FIX.

    Every number must travel with BOTH its column name and its row name, in the
    same chunk, in plain text. The embedding encodes the association; a bare
    digit-wall does not.
    """
    rows = [
        ["Ush million", "H1 2024", "H1 2023"],
        ["Service revenue", "1,505,398", "1,250,059"],
    ]
    out = serialise_table(rows)
    assert "Service revenue" in out
    assert "H1 2024: 1,505,398" in out
    assert "H1 2023: 1,250,059" in out
    # And the result must survive its own gates.
    assert not is_orphan_number_block(out)
    assert not has_ambiguous_headers(out)


def test_serialised_output_passes_all_gates():
    """Closing the loop: the extractor's output must pass the gates that exist
    to catch the extractor's failures."""
    rows = [
        ["", "June 2024", "June 2023"],
        ["", "Shs '000", "Shs '000"],
        ["Revenue", "1,522,675,972", "1,267,089,363"],
    ]
    out = serialise_table(rows)
    assert not is_orphan_number_block(out)
    assert not is_garbled(out)
    assert not has_ambiguous_headers(out)
    assert "June 2024" in out and "June 2023" in out
