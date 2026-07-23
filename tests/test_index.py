"""Tests for the persistent chunk index (src/core/index.py).

Uses a deterministic, seeded FakeEncoder — no model, no network, no torch —
mirroring test_retriever.py's StubEncoder pattern: enough real vector
geometry to exercise dense ranking and the mmap round-trip, without needing
onnxruntime or a real .onnx model file.

Several tests here are known-BAD controls, not just happy paths: the
embedder-mismatch test and the crash-simulation test must FAIL loudly (raise,
or self-heal on reopen) precisely because a test suite that only exercises
the happy path is what let the v1 extraction defect ship (see
tests/test_extraction.py's own docstring for the same lesson).

Run:  pytest -v
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.index import ExtractedChunk, ExtractedDoc, Index  # noqa: E402


class FakeEncoder:
    """Deterministic 384-dim encoder seeded by text content: identical text
    always yields an identical vector, different text yields a different
    (but reproducible) one. Real cosine geometry, no model."""

    def __init__(self, embedder_id: str = "fake-v1", tokenizer_sha256: str = "fakehash"):
        self.embedder_id = embedder_id
        self.tokenizer_sha256 = tokenizer_sha256

    def encode(self, texts, is_query: bool = False) -> np.ndarray:
        vecs = np.zeros((len(texts), 384), dtype=np.float32)
        for i, t in enumerate(texts):
            seed = int.from_bytes(hashlib.sha256(t.encode()).digest()[:8], "little")
            rng = np.random.default_rng(seed)
            vecs[i] = rng.normal(size=384)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return (vecs / np.clip(norms, 1e-9, None)).astype(np.float32)


def _doc(sha256: str, filename: str, texts: list[str], pages: int = 1) -> ExtractedDoc:
    chunks = [
        ExtractedChunk(
            page=1, char_start=i * 100, char_end=i * 100 + len(t),
            text=t, n_tokens=len(t.split()),
        )
        for i, t in enumerate(texts)
    ]
    return ExtractedDoc(sha256=sha256, filename=filename, pages=pages, chunks=chunks)


# =============================================================================
# Stable IDs across appends
# =============================================================================


def test_append_two_docs_ids_from_first_unchanged(tmp_path):
    idx = Index.open(tmp_path)
    enc = FakeEncoder()

    doc1 = _doc("a" * 64, "doc1.pdf", ["alpha text one", "alpha text two"])
    r1 = idx.append_document(doc1, enc)
    assert r1.n_chunks_added == 2
    ids_before = [c["id"] for c in idx._read_all_chunks()]

    doc2 = _doc("b" * 64, "doc2.pdf", ["beta text one", "beta text two", "beta text three"])
    r2 = idx.append_document(doc2, enc)
    assert r2.n_chunks_added == 3

    ids_after = [c["id"] for c in idx._read_all_chunks()]
    assert ids_after[:2] == ids_before, "appending doc2 must not renumber doc1's chunks"
    assert ids_after[0] == "aaaaaaaa:0"
    assert ids_after[1] == "aaaaaaaa:1"
    assert ids_after[2] == "bbbbbbbb:0"


# =============================================================================
# Re-append is a no-op
# =============================================================================


def test_reappend_same_doc_is_noop(tmp_path):
    idx = Index.open(tmp_path)
    enc = FakeEncoder()
    doc = _doc("c" * 64, "doc.pdf", ["x chunk", "y chunk"])

    r1 = idx.append_document(doc, enc)
    assert r1.already_indexed is False
    assert r1.n_chunks_added == 2

    r2 = idx.append_document(doc, enc)
    assert r2.already_indexed is True
    assert r2.n_chunks_added == 0
    assert r2.chunk_id_range == r1.chunk_id_range

    records = idx._read_all_chunks()
    assert len(records) == 2  # not duplicated
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))


# =============================================================================
# Crash recovery — the load-bearing test
# =============================================================================


def test_crash_between_embeddings_and_manifest_write_is_recoverable(tmp_path, monkeypatch):
    import core.index as index_mod

    idx = Index.open(tmp_path)
    enc = FakeEncoder()
    idx.append_document(_doc("d" * 64, "doc1.pdf", ["first chunk text"]), enc)
    stats_before = idx.stats()

    real_write_text = index_mod._atomic_write_text

    def _boom(path, text):
        if path.name == "manifest.json":
            raise RuntimeError("simulated crash before manifest commit")
        return real_write_text(path, text)

    monkeypatch.setattr(index_mod, "_atomic_write_text", _boom)

    with pytest.raises(RuntimeError):
        idx.append_document(_doc("e" * 64, "doc2.pdf", ["second chunk text"]), enc)

    monkeypatch.undo()

    # The crashed Index instance's own in-memory manifest must not have been
    # corrupted by the failed attempt either.
    assert idx.has_document("e" * 64) is False

    # A FRESH open (simulating a process restart after the crash) must see
    # exactly the pre-crash state — chunks.jsonl/embeddings.npy/bm25.json
    # were partially advanced past the manifest and must self-heal.
    reopened = Index.open(tmp_path)
    assert reopened.has_document("d" * 64) is True
    assert reopened.has_document("e" * 64) is False
    stats_after = reopened.stats()
    assert stats_after.n_documents == stats_before.n_documents == 1
    assert stats_after.n_chunks == stats_before.n_chunks == 1

    records = reopened._read_all_chunks()
    assert len(records) == 1
    emb = np.load(reopened._embeddings_path)
    assert emb.shape[0] == 1

    # And the recovered index must still be fully searchable afterward.
    result = reopened.search("first chunk", k=1, encoder=enc)
    assert len(result.hits) == 1


# =============================================================================
# Embedder/tokenizer mismatch — known-bad control
# =============================================================================


def test_embedder_mismatch_raises(tmp_path):
    idx = Index.open(tmp_path)
    enc1 = FakeEncoder(embedder_id="model-a", tokenizer_sha256="hash-a")
    idx.append_document(_doc("f" * 64, "doc.pdf", ["some text here"]), enc1)

    enc_wrong_model = FakeEncoder(embedder_id="model-b", tokenizer_sha256="hash-a")
    with pytest.raises(AssertionError):
        idx.append_document(_doc("g" * 64, "doc2.pdf", ["other text"]), enc_wrong_model)

    enc_wrong_tokenizer = FakeEncoder(embedder_id="model-a", tokenizer_sha256="hash-b")
    with pytest.raises(AssertionError):
        idx.append_document(_doc("h" * 64, "doc3.pdf", ["other text"]), enc_wrong_tokenizer)

    with pytest.raises(AssertionError):
        idx.search("some text", k=1, encoder=enc_wrong_model)

    # the correct encoder must still work — this isn't a permanently broken index
    result = idx.search("some text", k=1, encoder=enc1)
    assert len(result.hits) == 1


# =============================================================================
# Search shape
# =============================================================================


def test_search_returns_hits_considered_and_timings(tmp_path):
    idx = Index.open(tmp_path)
    enc = FakeEncoder()
    texts = [f"chunk number {i} about topic {i % 3}" for i in range(20)]
    idx.append_document(_doc("i" * 64, "doc.pdf", texts), enc)

    result = idx.search("topic 1", k=3, encoder=enc)
    assert len(result.hits) == 3
    assert len(result.considered) > 0
    for h in result.hits + result.considered:
        assert h.id
        assert h.text
        assert h.filename == "doc.pdf"
    assert set(result.timings) == {"bm25_ms", "dense_ms", "fuse_ms", "total_ms"}
    assert all(v >= 0.0 for v in result.timings.values())


# =============================================================================
# Unit-norm invariant
# =============================================================================


def test_unit_norm_invariant_holds_after_two_appends(tmp_path):
    idx = Index.open(tmp_path)
    enc = FakeEncoder()
    idx.append_document(_doc("j" * 64, "d1.pdf", ["one chunk", "two chunk"]), enc)
    idx.append_document(_doc("k" * 64, "d2.pdf", ["three chunk", "four chunk", "five chunk"]), enc)

    emb = np.load(idx._embeddings_path)
    assert emb.shape == (5, 384)
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


# =============================================================================
# Known-good control
# =============================================================================


def test_happy_path_append_and_search_raises_nothing(tmp_path):
    idx = Index.open(tmp_path)
    enc = FakeEncoder()
    idx.append_document(_doc("l" * 64, "d.pdf", ["hello world chunk", "goodbye world chunk"]), enc)

    result = idx.search("hello", k=1, encoder=enc)
    assert len(result.hits) == 1

    stats = idx.stats()
    assert stats.n_documents == 1
    assert stats.n_chunks == 2
    assert stats.bytes_on_disk["chunks.jsonl"] > 0
    assert stats.bytes_on_disk["embeddings.npy"] > 0
    assert stats.bytes_on_disk["manifest.json"] > 0
    assert stats.bm25_load_rss_delta_bytes >= 0

    assert idx.has_document("l" * 64) is True
    assert idx.has_document("z" * 64) is False


# =============================================================================
# stats() RSS-delta regression
# =============================================================================


def test_bm25_load_rss_delta_is_actually_measured(tmp_path):
    """Regression for two real bugs found while benchmarking, in order:

    1. Measuring with resource.getrusage().ru_maxrss (a monotonic
       high-water mark) always read 0, because Index.open() itself already
       reads the full chunks.jsonl during _recover()'s consistency check --
       which peaks RSS higher than loading bm25.json ever does -- before
       stats() gets a chance to measure anything.
    2. Switching to /proc/self/status's current-usage VmRSS did not fix
       it either: Python/glibc's allocator can satisfy the bm25.json load
       entirely from memory _recover()'s own temporary chunk list *just
       freed*, so even genuine, real allocation can read as a zero (or
       negative-clamped-to-zero) delta at the OS level -- confirmed
       empirically to vary 0x-4x run to run on identical input.

    tracemalloc tracks Python-level allocations directly and sidesteps
    both: it is immune to what the process did before (unlike #1) and to
    OS-level allocator reuse (unlike #2). It is also deterministic --
    asserted here by checking two separate builds give the same nonzero
    reading, not just "nonzero once".
    """
    enc = FakeEncoder()
    texts = [f"chunk {i} about seller buyer marketplace returns policy topic {i % 7}" for i in range(3000)]

    deltas = []
    for i in range(2):
        idx = Index.open(tmp_path / f"idx{i}")
        idx.append_document(_doc("m" * 64, "big.pdf", texts), enc)
        deltas.append(idx.stats().bm25_load_rss_delta_bytes)

    for d in deltas:
        assert d > 100_000, (
            f"bm25_load_rss_delta_bytes={d} -- expected a real, measurable "
            f"delta for a ~3000-chunk bm25.json"
        )
    # Not exact-equal -- a handful of bytes of incidental allocation (e.g.
    # path strings) vary run to run -- but tight enough to catch a
    # regression back to the allocator-noise behaviour that varied 0x-4x.
    assert abs(deltas[0] - deltas[1]) < 1_000, (
        f"tracemalloc delta should be near-identical for identical input, got {deltas}"
    )
