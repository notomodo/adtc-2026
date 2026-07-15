"""The verdict must never contradict its own table.

Regression for the defect where eval_retriever gated the verdict on Recall@5
(a tie at 89% on the SME corpus) and printed "Hybrid does NOT beat BM25" while
every hybrid beat BM25 on Recall@1 and MRR. The gate is now Recall@1.

Run:  pytest -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eval_retriever import verdict_lines  # noqa: E402


def _res(r1, r3, r5, r10, mrr):
    return {"recall": {1: r1, 3: r3, 5: r5, 10: r10}, "mrr": mrr,
            "strata": {}, "failures": []}


# The real SME bake-off numbers (n = 19), the ones that exposed the bug.
SME = {
    "BM25 only": _res(10 / 19, 15 / 19, 17 / 19, 18 / 19, 0.664),
    "HYBRID: BM25+e5-small-v2": _res(12 / 19, 15 / 19, 16 / 19, 19 / 19, 0.717),
    "HYBRID: BM25+bge-small-en-v1.5": _res(11 / 19, 16 / 19, 17 / 19, 18 / 19, 0.703),
    "HYBRID: BM25+gte-small": _res(11 / 19, 15 / 19, 17 / 19, 18 / 19, 0.687),
    "HYBRID: BM25+all-MiniLM-L6-v2": _res(12 / 19, 14 / 19, 17 / 19, 17 / 19, 0.712),
}


def test_verdict_does_not_contradict_its_table():
    """R@5 is tied at 89%, but hybrids win on R@1 — the verdict must say so."""
    text = "\n".join(verdict_lines(SME))
    assert "does NOT beat" not in text
    assert "beats BM25 on Recall@1" in text


def test_best_hybrid_selected_by_r1_then_mrr():
    """e5 and MiniLM tie on R@1 (12/19); e5 wins on the MRR tiebreak."""
    text = "\n".join(verdict_lines(SME))
    assert "best hybrid (by R@1): HYBRID: BM25+e5-small-v2" in text


def test_verdict_can_still_fire_negative():
    """The gate is not hard-wired to 'beats' — a genuinely worse hybrid must be
    reported as a loss."""
    res = {
        "BM25 only": _res(10 / 19, 15 / 19, 17 / 19, 18 / 19, 0.664),
        "HYBRID: BM25+weak": _res(8 / 19, 13 / 19, 15 / 19, 17 / 19, 0.55),
    }
    text = "\n".join(verdict_lines(res))
    assert "does NOT beat BM25 on Recall@1" in text


def test_verdict_when_no_dense_model_ran():
    res = {"BM25 only": _res(10 / 19, 15 / 19, 17 / 19, 18 / 19, 0.664)}
    text = "\n".join(verdict_lines(res))
    assert "no dense model ran" in text
