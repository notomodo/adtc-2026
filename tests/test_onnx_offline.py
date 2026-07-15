"""The SHIPPING encoder must never fetch the tokenizer from the network.

Regression for an offline-guarantee violation: `OnnxEncoder.__init__` called
`Tokenizer.from_pretrained()`, which reaches the Hugging Face Hub on first run.
The README's headline guarantee is "no API calls, no network at runtime", and
`OnnxEncoder` is the shipping encoder — so it must honour it.

These tests would have FIRED on the pre-fix code: `test_onnx_encoder_*` construct
the real encoder with `from_pretrained` monkeypatched to explode, so the old
constructor (which called it) fails while the fixed one (which loads the vendored
`tokenizer.json`) passes.

onnxruntime is not a test dependency, so a minimal fake `InferenceSession` is
injected via sys.modules; only the tokenizer-loading path is under test.

Run:  pytest -v
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# OnnxEncoder exists in both pre-fix and post-fix code, so importing it at module
# top lets this file COLLECT against the old constructor and fail for the right
# reason. The new helper is imported inside the tests that need it.
from retriever import OnnxEncoder  # noqa: E402

VENDORED = Path(__file__).resolve().parents[1] / "src" / "tokenizer.json"


@pytest.fixture
def fake_onnxruntime(monkeypatch):
    """Stub onnxruntime so OnnxEncoder can construct without a real .onnx model
    or the onnxruntime package (which is not a CI/test dependency)."""
    mod = types.ModuleType("onnxruntime")

    class _Input:
        def __init__(self, name: str) -> None:
            self.name = name

    class _Session:
        def __init__(self, *a, **k) -> None:  # accepts (path, providers=...)
            pass

        def get_inputs(self):
            return [_Input("input_ids"), _Input("attention_mask")]

    mod.InferenceSession = _Session
    monkeypatch.setitem(sys.modules, "onnxruntime", mod)
    return mod


@pytest.fixture
def forbid_hub(monkeypatch):
    """Turn any Hub fetch into an immediate, identifiable failure."""
    from tokenizers import Tokenizer

    def _boom(*a, **k):
        raise AssertionError(
            "from_pretrained() called — the shipping path tried to hit the network"
        )

    monkeypatch.setattr(Tokenizer, "from_pretrained", staticmethod(_boom))


# --- known-GOOD: constructs offline from the committed tokenizer.json ---------

def test_onnx_encoder_constructs_without_touching_the_hub(fake_onnxruntime, forbid_hub):
    """The property that would have caught the bug: constructing the shipping
    encoder must not call from_pretrained. Pre-fix this raised (network fetch);
    post-fix it loads src/tokenizer.json."""
    enc = OnnxEncoder(onnx_path="unused-by-stub", tokenizer_name="BAAI/bge-small-en-v1.5")
    assert enc.tok.encode("returns policy").ids          # a working tokenizer
    assert enc.q_prefix.startswith("Represent this sentence")  # prefixes preserved


def test_load_vendored_tokenizer_is_offline(forbid_hub):
    """The factored loader loads from the vendored file, never the Hub."""
    from retriever import _load_vendored_tokenizer

    tok = _load_vendored_tokenizer()
    assert tok.encode("service revenue").ids


# --- known-BAD: a missing vendored file fails HARD, never falls back to Hub ---

def test_missing_vendored_tokenizer_raises_not_fetches(forbid_hub, tmp_path):
    """No silent Hub fallback (unlike ingest_sme.py). A missing file must raise
    FileNotFoundError — NOT reach the network (which would raise AssertionError
    from the forbid_hub fixture instead)."""
    from retriever import _load_vendored_tokenizer

    with pytest.raises(FileNotFoundError):
        _load_vendored_tokenizer(tmp_path / "does_not_exist.json")


def test_onnx_encoder_missing_tokenizer_raises(fake_onnxruntime, forbid_hub, tmp_path):
    """Same, through the real constructor: a bad tokenizer_path fails hard."""
    with pytest.raises(FileNotFoundError):
        OnnxEncoder(
            onnx_path="unused-by-stub",
            tokenizer_name="BAAI/bge-small-en-v1.5",
            tokenizer_path=tmp_path / "does_not_exist.json",
        )


def test_vendored_tokenizer_is_committed():
    """The offline guarantee depends on this file being in the repo."""
    assert VENDORED.exists() and VENDORED.stat().st_size > 100_000
