"""Parity gate: the SHIPPING ONNX encoder must reproduce the BENCHMARKED encoder.

DECISION-002 §9.4: "Export bge-small to ONNX ... verify vectors match
sentence-transformers to ~1e-5. Benchmark numbers must describe the *shipped*
system." Every dense metric in DECISION-002 was measured with
`SentenceTransformerEncoder`. `OnnxEncoder` is what ships. If they disagree, the
recorded numbers describe a system nobody runs.

This is the control that catches the exact defect found this session: `OnnxEncoder`
MEAN-pooled, but bge uses CLS pooling, so the shipping vectors silently diverged
(cosine ~0.93) from the benchmarked ones.

  known-GOOD:  OnnxEncoder (CLS) matches ST ground truth — cosine >= 0.9999,
               max abs elementwise diff < TOL — on BOTH q_prefix and p_prefix paths.
  known-BAD :  a deliberately MEAN-pooled encoder MUST fail that same gate. A
               parity test that cannot fail proves nothing.

Requires torch + sentence-transformers (benchmark stack) + onnxruntime + the
exported model. Skips cleanly if any are absent (mirroring test_onnx_offline.py),
but MUST run and pass where they are present.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Force offline: ST/transformers must load bge from the local cache, never the Hub.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

np = pytest.importorskip("numpy")
pytest.importorskip("onnxruntime")
pytest.importorskip("torch")
pytest.importorskip("sentence_transformers")

from retriever import OnnxEncoder, SentenceTransformerEncoder  # noqa: E402

MODEL = "BAAI/bge-small-en-v1.5"
ONNX_PATH = ROOT / "models" / "bge-small-en-v1.5.onnx"

# ~1e-5 is DECISION-002's target; the measured max abs diff is ~2.5e-7, so this
# tolerance is generous by ~40x and still an order below the target.
TOL_MAX_ABS = 1e-5
MIN_COSINE = 0.9999

# Varied lengths + both a query-style and passage-style register; two are the real
# corpus's document-title chunks (General Terms, Privacy Policy) and the multi-refund
# paraphrase from DECISION-002 §3.
PROBES = [
    "returns",
    "What is Kibuga's returns policy?",
    "How do I get a refund to mobile money?",
    "Two (2) days free returns policy",
    "store credits, wallet refunds, vouchers, mobile money transfer",
    "Can Kibuga suspend my account without notice?",
    "at any time in our sole discretion and without notice or explanation",
    "How is my personal data collected and protected?",
    "General Terms and Conditions",
    "Privacy Policy for the Kibuga marketplace platform",
    "seller obligations warranties and dispute resolution",
    "How do I contact Kibuga customer support by email?",
]


@pytest.fixture(scope="module")
def onnx_path() -> Path:
    """Ensure the exported model exists; build it from the local cache if not.

    The .onnx blob is gitignored (126 MB), so a fresh checkout won't have it.
    export_onnx.py is the reproducible source — call it. If the model isn't
    cached (offline miss) or export fails, skip rather than fail: this gate is
    about parity, not about the build env's completeness."""
    if ONNX_PATH.exists():
        return ONNX_PATH
    try:
        import export_onnx

        export_onnx.export(ONNX_PATH, export_onnx.DEFAULT_OPSET)
    except Exception as e:  # pragma: no cover - env-dependent
        pytest.skip(f"exported ONNX unavailable and export failed: {e}")
    return ONNX_PATH


@pytest.fixture(scope="module")
def ground_truth() -> dict:
    """SentenceTransformerEncoder vectors = the benchmarked ground truth."""
    try:
        st = SentenceTransformerEncoder(MODEL)
    except Exception as e:  # pragma: no cover - offline cache miss
        pytest.skip(f"sentence-transformers/bge unavailable offline: {e}")
    return {
        True: st.encode(PROBES, is_query=True),
        False: st.encode(PROBES, is_query=False),
    }


def _parity(vectors, gt) -> tuple[float, float]:
    """Return (min cosine, max abs elementwise diff) between two L2-normalised sets."""
    cos = (vectors * gt).sum(axis=1)  # both already L2-normalised => cosine
    return float(cos.min()), float(np.abs(vectors - gt).max())


class _MeanPoolEncoder(OnnxEncoder):
    """KNOWN-BAD control: the pre-fix behaviour — mean-pool instead of CLS."""

    def encode(self, texts, is_query: bool = False):
        prefix = self.q_prefix if is_query else self.p_prefix
        encs = self.tok.encode_batch([prefix + t for t in texts])
        maxlen = max(len(e.ids) for e in encs)
        ids = np.zeros((len(encs), maxlen), dtype=np.int64)
        mask = np.zeros((len(encs), maxlen), dtype=np.int64)
        for i, e in enumerate(encs):
            ids[i, : len(e.ids)] = e.ids
            mask[i, : len(e.attention_mask)] = e.attention_mask
        feed = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in self._inputs:
            feed["token_type_ids"] = np.zeros_like(ids)
        hidden = self.session.run(None, feed)[0]
        m = mask[..., None].astype(np.float32)
        pooled = (hidden * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        return (pooled / np.clip(norms, 1e-9, None)).astype(np.float32)


# --- known-GOOD: CLS OnnxEncoder reproduces the benchmarked vectors -------------

@pytest.mark.parametrize("is_query", [True, False], ids=["q_prefix", "p_prefix"])
def test_onnx_matches_sentence_transformer(onnx_path, ground_truth, is_query):
    enc = OnnxEncoder(onnx_path=str(onnx_path), tokenizer_name=MODEL, model_name=MODEL)
    vecs = enc.encode(PROBES, is_query=is_query)
    min_cos, max_abs = _parity(vecs, ground_truth[is_query])
    assert min_cos >= MIN_COSINE, f"min cosine {min_cos:.6f} < {MIN_COSINE}"
    assert max_abs < TOL_MAX_ABS, f"max abs diff {max_abs:.2e} >= {TOL_MAX_ABS:.0e}"


# --- known-BAD: mean pooling MUST fail the very same gate -----------------------

@pytest.mark.parametrize("is_query", [True, False], ids=["q_prefix", "p_prefix"])
def test_mean_pooling_is_rejected_by_the_gate(onnx_path, ground_truth, is_query):
    """The load-bearing control. If mean pooling ALSO passed, the gate would be a
    placebo. It must diverge well below the parity bar."""
    bad = _MeanPoolEncoder(onnx_path=str(onnx_path), tokenizer_name=MODEL, model_name=MODEL)
    vecs = bad.encode(PROBES, is_query=is_query)
    min_cos, max_abs = _parity(vecs, ground_truth[is_query])
    # The gate would reject it:
    assert min_cos < MIN_COSINE
    assert max_abs >= TOL_MAX_ABS
    # And concretely it is the ~0.93 divergence measured this session, not a hair.
    assert min_cos < 0.99


def test_parity_covers_both_prefix_paths():
    """Guard: the parity tests above must exercise BOTH q_prefix and p_prefix, and
    the two prefixes must actually differ for bge (asymmetric model)."""
    from retriever import _prefix_for

    q_prefix, p_prefix = _prefix_for(MODEL)
    assert q_prefix and q_prefix != p_prefix, "bge is asymmetric; both paths must be tested"
