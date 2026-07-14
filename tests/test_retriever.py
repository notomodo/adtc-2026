"""Unit tests for the hybrid retriever.

Covers the pure, deterministic logic — tokenisation, BM25, RRF fusion, and the
HybridRetriever search path — with a stub encoder, so nothing here needs a
network, a model download, or PyTorch. The two heavy encoders
(SentenceTransformerEncoder, OnnxEncoder) are integration surface and are not
exercised here.

Several tests pin defects called out in src/retriever.py: the period-code
tokenisation bug ("H1" -> "h","1"), the document-side alias asymmetry, and the
IDF floor that stops common terms scoring negative.

Run:  pytest -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retriever import BM25, HybridRetriever, Hit, rrf_fuse, tokenize  # noqa: E402


# =============================================================================
# Tokenisation
# =============================================================================

def test_period_codes_stay_whole():
    r"""REGRESSION — the [a-z]+\d+ branch must precede [a-z]+.

    Otherwise 'h1' tokenises to 'h' + '1', which made every period reference
    ('H1', 'Q2', 'FY25') unfindable across the index.
    """
    assert tokenize("H1 revenue") == ["h1", "revenue"]
    assert "q2" in tokenize("Q2 2024 results")


def test_numeric_literals_stay_whole():
    """A grouped figure must not shatter into digit confetti."""
    assert "1,505,398" in tokenize("Service revenue 1,505,398")
    assert "51.5" in tokenize("margin 51.5 percent")


def test_query_side_is_not_expanded():
    """Aliases apply to DOCUMENTS, not queries (expand defaults to False)."""
    assert tokenize("h1 revenue") == ["h1", "revenue"]


def test_document_side_expansion_adds_aliases():
    """A doc containing 'H1' is also indexed under 'first'/'half' so a user's
    natural phrasing finds it. 'fibre'/'fiber' bridges the spelling gap."""
    expanded = tokenize("H1 fibre rollout", expand=True)
    assert {"h1", "first", "half"} <= set(expanded)
    assert "fiber" in expanded


# =============================================================================
# BM25
# =============================================================================

CORPUS = [
    "Returns must be initiated within two days of delivery.",
    "The privacy policy explains how we handle your personal data.",
    "Sellers warrant they are the legal owner of the goods.",
]


def test_bm25_ranks_relevant_document_first():
    bm = BM25(CORPUS)
    scores = bm.scores("privacy policy personal data")
    assert int(np.argmax(scores)) == 1  # the privacy clause


def test_bm25_oov_term_contributes_nothing():
    """A query of terms absent from the corpus scores every doc zero."""
    bm = BM25(CORPUS)
    assert np.count_nonzero(bm.scores("quantum chromodynamics")) == 0


def test_bm25_idf_is_floored_non_negative():
    """A term appearing in a majority of docs must not get NEGATIVE idf and
    penalise the docs that contain it."""
    corpus = ["revenue grew", "revenue fell", "revenue flat", "revenue up"]
    bm = BM25(corpus)
    assert min(bm.idf.values()) >= 0.0
    # And the common term never drives a score below zero.
    assert (bm.scores("revenue") >= 0).all()


def test_bm25_alias_bridges_vocabulary_gap():
    """End-to-end lexical bridge: a query saying 'first half' finds a document
    that only ever says 'H1', because documents are alias-expanded at index
    time."""
    corpus = ["Group H1 performance was strong.", "Board meeting minutes."]
    bm = BM25(corpus)  # expand_docs=True by default
    scores = bm.scores("first half performance")
    assert int(np.argmax(scores)) == 0


# =============================================================================
# Reciprocal Rank Fusion
# =============================================================================

def test_rrf_rewards_agreement_across_retrievers():
    """A doc ranked highly by BOTH retrievers should win over one ranked highly
    by only a single retriever."""
    fused = dict(rrf_fuse([[1, 2, 3], [1, 3, 2]]))
    assert max(fused, key=fused.get) == 1


def test_rrf_formula_is_sum_of_reciprocal_ranks():
    """RRF(d) = sum 1/(k+rank). With k=60 and doc 7 at rank 1 in both lists."""
    fused = dict(rrf_fuse([[7], [7]], k=60.0))
    assert fused[7] == pytest.approx(2.0 / 61.0)


def test_rrf_absent_document_is_not_penalised():
    """A doc missing from one list simply gains nothing from it — it is not
    pushed down. This is what makes RRF robust to differing recall profiles."""
    fused = dict(rrf_fuse([[5], []]))
    assert fused[5] == pytest.approx(1.0 / 61.0)


def test_rrf_weights_length_must_match():
    with pytest.raises(ValueError):
        rrf_fuse([[1], [2]], weights=[1.0])


# =============================================================================
# HybridRetriever
# =============================================================================

class StubEncoder:
    """Deterministic bag-of-words encoder over a fixed vocabulary. No model, no
    network — just enough real cosine geometry to exercise the dense path."""

    VOCAB = ("refund", "return", "money", "credit", "voucher", "privacy", "data")

    def encode(self, texts, is_query: bool = False) -> np.ndarray:
        vecs = np.zeros((len(texts), len(self.VOCAB)), dtype=np.float32)
        for i, t in enumerate(texts):
            low = t.lower()
            for j, term in enumerate(self.VOCAB):
                vecs[i, j] = low.count(term)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.clip(norms, 1e-9, None)


def test_bm25_only_fallback_has_identical_api():
    """encoder=None gives a pure-BM25 retriever — the offline shipping fallback.
    search() must still return Hits in BM25 order."""
    r = HybridRetriever(CORPUS, encoder=None)
    hits = r.search("privacy data returns", top_k=2)
    assert [type(h) for h in hits] == [Hit, Hit]
    assert hits[0].chunk_id == 1  # privacy+data outweighs the single 'returns'
    assert hits[0].text == CORPUS[1]
    assert len(hits) == 2


def test_search_respects_top_k():
    r = HybridRetriever(CORPUS, encoder=None)
    assert len(r.search("privacy", top_k=1)) == 1


def test_hybrid_recovers_a_chunk_bm25_misses():
    """The headline finding: the dense half rescues a question with near-zero
    lexical overlap. 'reimbursement refund' shares no *token* with a chunk that
    says 'refunds ... store credit, vouchers, money' (refund != refunds), so
    BM25 leaves it out of the results — while the dense half surfaces it into
    the fused top-k."""
    chunks = [
        "Registration requires email verification and a password.",
        "Refunds issue as store credit, vouchers, or mobile money.",   # target
        "Website terms govern acceptable content and usage.",
        "Privacy notice explains personal data handling.",
        "Delivery timelines depend on your location.",
    ]
    query = "delivery reimbursement refund"  # 'delivery' hits chunk 4 lexically

    bm_only = HybridRetriever(chunks, encoder=None)
    hybrid = HybridRetriever(chunks, encoder=StubEncoder())

    bm_ids = [h.chunk_id for h in bm_only.search(query, top_k=3)]
    hybrid_ids = [h.chunk_id for h in hybrid.search(query, top_k=3)]

    assert 1 not in bm_ids       # BM25 alone misses the refund chunk
    assert 1 in hybrid_ids       # fusion pulls it into the top-k


def test_candidate_depth_never_exceeds_corpus():
    r = HybridRetriever(CORPUS, encoder=None, candidate_depth=50)
    assert r.candidate_depth == len(CORPUS)
