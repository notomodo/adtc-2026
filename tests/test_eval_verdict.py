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
    assert "Beats BM25 on Recall@1 and never regresses" in text


def test_selection_prefers_non_regressing_hybrid():
    """Selection is 'non-negative on every metric', not raw R@1.

    e5 and MiniLM have the top R@1 (12/19) but each regress somewhere (e5 loses
    R@5, MiniLM loses R@3), so they are excluded. bge and gte both never
    regress; bge wins the R@1->MRR tiebreak. This is the DECISION-002 choice.
    """
    text = "\n".join(verdict_lines(SME))
    assert "best hybrid (non-negative on every metric): HYBRID: BM25+bge-small-en-v1.5" in text
    # the higher-R@1 but regressing models must NOT be selected
    assert "e5-small-v2" not in text
    assert "all-MiniLM-L6-v2" not in text


def test_falls_back_to_best_r1_when_all_hybrids_regress():
    """If no hybrid is clean, report the best-by-R@1 and flag the regression."""
    res = {
        "BM25 only": _res(10 / 19, 15 / 19, 17 / 19, 18 / 19, 0.664),
        # beats R@1 but loses R@5 -> not clean
        "HYBRID: BM25+risky": _res(12 / 19, 15 / 19, 15 / 19, 18 / 19, 0.70),
    }
    text = "\n".join(verdict_lines(res))
    assert "best R@1 — regresses elsewhere" in text
    assert "weigh the trade-off" in text


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
