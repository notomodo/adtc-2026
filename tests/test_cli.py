"""Application-layer tests: the ingest/ask pipeline and the adtc-rag CLI.

Everything here runs OFFLINE. The heavy real path (a live OnnxEncoder + Ollama)
is a single opt-in test that skips cleanly when the .onnx model or the Ollama
socket are absent — mirroring the parity/offline tests' skip guards. Every other
test drives the exact same code paths with a deterministic FakeEncoder and
hand-built ExtractedDocs (the ExtractedDoc-path escape the task permits), so
idempotency, the empty-index guard, and the encoder-mismatch guard are all
exercised with no PDF, no onnxruntime, and no model server.

Several tests are known-BAD controls, not happy paths:
  * the empty-index guard MUST exit non-zero with actionable guidance;
  * asking against an index built by a DIFFERENT embedder MUST raise — the same
    embedding-space-mixing failure the pooling bug was, wearing a CLI hat.

Run:  pytest -v
"""

from __future__ import annotations

import hashlib
import socket
import sys
import urllib.parse
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app import cli  # noqa: E402
from app.pipeline import (  # noqa: E402
    DEFAULT_ONNX_PATH,
    AnswerResult,
    EmptyIndexError,
    Pipeline,
)
from core.index import ExtractedChunk, ExtractedDoc, Hit, Index  # noqa: E402


# ---------------------------------------------------------------------------
# offline fixtures — deterministic encoder + hand-built docs (mirrors test_index)
# ---------------------------------------------------------------------------


class FakeEncoder:
    """Deterministic 384-dim encoder seeded by text content — real cosine
    geometry, no model, no network, no torch. Identity strings let the manifest's
    embedder/tokenizer-mismatch guard be exercised."""

    def __init__(self, embedder_id: str = "fake-v1", tokenizer_sha256: str = "fakehash"):
        self.embedder_id = embedder_id
        self.tokenizer_sha256 = tokenizer_sha256

    def encode(self, texts, is_query: bool = False) -> np.ndarray:
        vecs = np.zeros((len(texts), 384), dtype=np.float32)
        for i, t in enumerate(texts):
            seed = int.from_bytes(hashlib.sha256(t.encode()).digest()[:8], "little")
            vecs[i] = np.random.default_rng(seed).normal(size=384)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return (vecs / np.clip(norms, 1e-9, None)).astype(np.float32)


def _make_pdf(path: Path, sentinel: bytes = b"%PDF-1.4 fake bytes") -> str:
    """Write a stand-in file and return its sha256. Not a real PDF: extraction is
    monkeypatched, so only the bytes (→ the doc's identity/idempotency key) matter."""
    path.write_bytes(sentinel + path.name.encode())
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _doc_for(path: Path, texts: list[str], pages: int = 2) -> ExtractedDoc:
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    chunks = [
        ExtractedChunk(page=1, char_start=i * 50, char_end=i * 50 + len(t), text=t,
                       n_tokens=len(t.split()))
        for i, t in enumerate(texts)
    ]
    return ExtractedDoc(sha256=sha, filename=path.name, pages=pages, chunks=chunks)


def _ingest_fake(pipe: Pipeline, monkeypatch, path: Path, texts: list[str], on_event=None):
    """Drive the real ingest_path — including the pre-extraction sha skip and the
    progress events — with extraction stubbed to a hand-built ExtractedDoc."""
    doc = _doc_for(path, texts)
    monkeypatch.setattr(Pipeline, "_extract", lambda self, p: doc)
    return pipe.ingest_path([str(path)], on_event=on_event)


# ---------------------------------------------------------------------------
# ingest: append, progress events, index stats
# ---------------------------------------------------------------------------


def test_ingest_appends_and_reports_progress(tmp_path, monkeypatch):
    pdf = tmp_path / "kibuga_terms.pdf"
    _make_pdf(pdf)
    pipe = Pipeline(index_dir=tmp_path / "idx", encoder=FakeEncoder())

    events: list[tuple] = []
    summary = _ingest_fake(pipe, monkeypatch, pdf,
                           ["Sellers must register an account.", "Returns within two days."],
                           on_event=events.append)

    assert summary.n_newly_indexed == 1
    assert summary.docs[0].n_chunks == 2
    assert summary.stats.n_documents == 1
    assert summary.stats.n_chunks == 2
    assert summary.stats.bytes_on_disk["chunks.jsonl"] > 0

    kinds = [e[0] for e in events]
    assert "extracting" in kinds  # per-document progress, not a silent hang
    assert "embedding" in kinds
    assert "appended" in kinds


# ---------------------------------------------------------------------------
# ingest: idempotency (re-ingest same file is a no-op that says so)
# ---------------------------------------------------------------------------


def test_reingest_same_file_is_idempotent(tmp_path, monkeypatch):
    pdf = tmp_path / "policy.pdf"
    _make_pdf(pdf)
    pipe = Pipeline(index_dir=tmp_path / "idx", encoder=FakeEncoder())
    texts = ["Buyers may cancel before dispatch.", "Refunds are at our discretion."]

    first = _ingest_fake(pipe, monkeypatch, pdf, texts)
    assert first.n_newly_indexed == 1
    n_chunks_after_first = first.stats.n_chunks

    # Second pass: the pre-extraction sha check must short-circuit — assert
    # extraction is NEVER called the second time.
    def _boom_extract(self, p):
        raise AssertionError("extraction must be skipped for an already-indexed file")

    monkeypatch.setattr(Pipeline, "_extract", _boom_extract)
    events: list[tuple] = []
    second = pipe.ingest_path([str(pdf)], on_event=events.append)

    assert second.n_newly_indexed == 0
    assert second.docs[0].already_indexed is True
    assert second.stats.n_chunks == n_chunks_after_first  # unchanged
    assert any(e[0] == "already_indexed" for e in events)


# ---------------------------------------------------------------------------
# ask: empty-index guard (pre-generation — testable without Ollama)
# ---------------------------------------------------------------------------


def test_answer_on_empty_index_raises_before_touching_encoder(tmp_path):
    # No encoder injected: if the guard did NOT fire first, _get_encoder would
    # raise ModelNotFoundError instead — so EmptyIndexError proves the ordering.
    pipe = Pipeline(index_dir=tmp_path / "idx")
    with pytest.raises(EmptyIndexError):
        pipe.answer("anything at all")


def test_cli_ask_empty_index_exits_nonzero_with_guidance(tmp_path, capsys):
    rc = cli.main(["--index-dir", str(tmp_path / "idx"), "ask", "what is the return window?"])
    assert rc == 3
    err = capsys.readouterr().err
    assert "No documents indexed" in err
    assert "adtc-rag ingest" in err


# ---------------------------------------------------------------------------
# ask: encoder-identity mismatch is FATAL (known-bad control)
# ---------------------------------------------------------------------------


def test_ask_with_mismatched_embedder_raises(tmp_path, monkeypatch):
    idx_dir = tmp_path / "idx"
    pdf = tmp_path / "doc.pdf"
    _make_pdf(pdf)

    pipe_a = Pipeline(index_dir=idx_dir, encoder=FakeEncoder("model-a", "hash-a"))
    _ingest_fake(pipe_a, monkeypatch, pdf, ["some indexed passage about sellers"])

    # A different embedder identity against the same index must raise at search,
    # before any generation — mixing embedding spaces is fatal by design.
    pipe_b = Pipeline(index_dir=idx_dir, encoder=FakeEncoder("model-b", "hash-a"))
    with pytest.raises(AssertionError):
        pipe_b.answer("some indexed passage")


# ---------------------------------------------------------------------------
# presentation: citations vs abstention-shows-its-work (offline, no Ollama)
# ---------------------------------------------------------------------------


def _hit(fname: str, page: int, rrf: float, cid: str = "aaaa:0") -> Hit:
    return Hit(id=cid, text="passage text here", filename=fname, page=page,
               char_start=0, char_end=10, rrf_score=rrf, bm25_rank=1, dense_rank=2)


def test_footer_prints_citations_when_grounded(capsys):
    result = AnswerResult(
        question="q", answer="Returns must be initiated within two days.", abstained=False,
        hits=[_hit("terms.pdf", 3, 0.031), _hit("terms.pdf", 3, 0.02, "aaaa:1")],
        considered=[], timings={"bm25_ms": 1.0, "dense_ms": 2.0, "fuse_ms": 0.1, "total_ms": 3.5},
        encoder_init_s=0.4, retrieval_s=0.05, generation_s=12.0,
    )
    cli._print_answer_footer(result, verbose=False)
    out = capsys.readouterr().out
    assert "Sources:" in out
    assert "[terms.pdf, p.3]" in out
    assert out.count("[terms.pdf, p.3]") == 1  # (filename,page) deduped
    assert "generation 12.0s" in out


def test_footer_shows_near_misses_when_abstaining(capsys):
    result = AnswerResult(
        question="q", answer="NOT_IN_DOCUMENTS", abstained=True, hits=[],
        considered=[_hit("faq.pdf", 5, 0.0123), _hit("terms.pdf", 1, 0.0098, "bbbb:2")],
        timings={"bm25_ms": 1.0, "dense_ms": 2.0, "fuse_ms": 0.1, "total_ms": 3.5},
        encoder_init_s=0.4, retrieval_s=0.05, generation_s=8.0,
    )
    cli._print_answer_footer(result, verbose=False)
    out = capsys.readouterr().out
    assert "Sources:" not in out
    assert "faq.pdf p.5" in out
    assert "rrf=0.0123" in out


def test_verbose_footer_dumps_ranks_and_timings(capsys):
    result = AnswerResult(
        question="q", answer="an answer", abstained=False,
        hits=[_hit("terms.pdf", 2, 0.031, "cccc:4")], considered=[],
        timings={"bm25_ms": 1.4, "dense_ms": 2.7, "fuse_ms": 0.05, "total_ms": 4.3},
        encoder_init_s=0.4, retrieval_s=0.05, generation_s=9.0,
    )
    cli._print_answer_footer(result, verbose=True)
    out = capsys.readouterr().out
    assert "cccc:4" in out
    assert "bm25_rank=1" in out and "dense_rank=2" in out
    assert "total=4.3ms" in out


# ---------------------------------------------------------------------------
# the real end-to-end path — opt-in, skips cleanly when heavy deps are absent
# ---------------------------------------------------------------------------


def _ollama_up(host: str = "http://localhost:11434") -> bool:
    u = urllib.parse.urlparse(host)
    try:
        with socket.create_connection((u.hostname, u.port or 11434), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.mark.skipif(not DEFAULT_ONNX_PATH.exists(), reason="shipping .onnx model not built")
@pytest.mark.skipif(not _ollama_up(), reason="Ollama not reachable")
def test_ingest_then_ask_end_to_end(tmp_path, monkeypatch):
    """Full pipeline on the real OnnxEncoder + live Ollama. Uses the committed
    corpus chunks as ExtractedDocs so no PDF/pdfplumber is needed, but drives the
    real encoder, index and generation. Skips unless both heavy deps are present."""
    pytest.importorskip("onnxruntime")
    pytest.importorskip("tokenizers")

    from chunk_dump import parse_dump  # committed byte-faithful parser

    dump = ROOT / "benchmarks" / "chunks_sme.txt"
    if not dump.exists():
        pytest.skip("corpus dump absent")
    _ids, texts, _metas = parse_dump(str(dump))
    texts = texts[:6]
    fake_pdf = tmp_path / "kibuga_corpus.pdf"
    _make_pdf(fake_pdf)
    chunks = [ExtractedChunk(page=1, char_start=0, char_end=len(t), text=t, n_tokens=1)
              for t in texts]
    doc = ExtractedDoc(sha256=hashlib.sha256(fake_pdf.read_bytes()).hexdigest(),
                       filename=fake_pdf.name, pages=1, chunks=chunks)

    pipe = Pipeline(index_dir=tmp_path / "idx")  # real OnnxEncoder
    idx = Index.open(pipe.index_dir)
    pipe._ingest_docs(idx, [doc], pipe._get_encoder(), None)

    tokens: list[str] = []
    result = pipe.answer("What is the returns policy?", k=3, on_token=tokens.append)
    assert result.answer  # something came back
    assert len(result.hits) == 3
    assert result.generation_s > 0
    assert "".join(tokens) == result.answer  # streamed text == final text
