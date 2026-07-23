"""Structural integrity tests for the R5 hand-validation review packet.

THE POINT OF THIS FILE
=======================
R5_review_packet.md is human-edited markdown parsed by regex
(src/r5_tabulate.py). It has already failed once in production: an edit
dropped two closing ``` fences (after the Q19 and Q14 Notes lines), and
because markdown fences toggle open/closed in raw sequence, that shifted
every fenced block from Q36 through Q07, swallowing headers, chunk quotes
and answers into code blocks. r5_tabulate.py's own parser did not catch
this shape of corruption -- it only checks box counts within whatever text
falls between two headers, and does not verify the headers themselves
survived.

These tests assert the properties that failure broke, independent of
r5_tabulate.py's parsing, so a future editing accident is caught by CI
before anyone runs the tabulator:

    - Fence count is even (every ``` opened is closed)
    - Every "### Qnn -- stratum" header sits outside any fenced block
      (a header swallowed into a fence is exactly the earlier failure mode)
    - Every block has exactly 4 verdict checkboxes, exactly one checked
    - The set of question IDs matches the packet's own documented sample

Run:  pytest -v
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from r5_tabulate import BLOCK_RE, BOX_RE, parse_packet  # noqa: E402

PACKET_PATH = Path(__file__).resolve().parents[1] / "benchmarks" / "generation" / "R5_review_packet.md"

# The 13-item priority sample the packet was built to contain (DECISIONS.md
# risk R5). If this set drifts, someone changed the sample and that is worth
# a deliberate review, not a silent pass.
EXPECTED_IDS = [
    "Q19", "Q36", "Q37", "Q38", "Q15", "Q32", "Q33", "Q34", "Q01", "Q05", "Q07", "Q14", "Q21",
]


def _read_packet() -> str:
    return PACKET_PATH.read_text()


def test_fences_are_balanced():
    text = _read_packet()
    fences = re.findall(r"^```\s*$", text, re.M)
    assert len(fences) % 2 == 0, (
        f"odd number of ``` fences ({len(fences)}) -- one was added or removed "
        "without its pair, which shifts every later fenced block"
    )


def test_headers_are_never_inside_a_fenced_block():
    text = _read_packet()
    lines = text.split("\n")
    in_fence = False
    swallowed = []
    for i, line in enumerate(lines, start=1):
        if line.strip() == "```":
            in_fence = not in_fence
        elif line.startswith("### Q") and in_fence:
            swallowed.append(i)
    assert not swallowed, f"header(s) swallowed into a fenced block at line(s): {swallowed}"


def test_every_block_has_four_boxes_exactly_one_checked():
    # parse_packet itself raises loudly on any malformed/unfilled/multi-checked
    # block -- if this packet doesn't parse cleanly, that IS the test failure.
    items = parse_packet(_read_packet())
    assert len(items) == len(EXPECTED_IDS)
    for item in items:
        assert item["human_verdict"] in {"CORRECT", "UNGROUNDED", "WRONG", "LABEL ISSUE"}


def test_question_id_set_matches_expected_sample():
    text = _read_packet()
    headers = BLOCK_RE.findall(text)
    ids = [qid for qid, _stratum in headers]
    assert ids == EXPECTED_IDS, f"packet's question order/set changed: {ids}"


def test_box_regex_matches_the_actual_mark_style_used():
    # BOX_RE only recognises 'x'/'X' as checked. This test fails loudly if a
    # future fill-in uses a different mark (e.g. '*'), which would otherwise
    # silently read as zero boxes checked in every block.
    text = _read_packet()
    all_marks = re.findall(r"\[(.)\]\s+(?:CORRECT|UNGROUNDED|WRONG|LABEL ISSUE)", text)
    unexpected = {m for m in all_marks if m not in (" ", "x", "X")}
    assert not unexpected, f"checkbox mark(s) not recognised by BOX_RE: {unexpected}"
