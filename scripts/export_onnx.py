#!/usr/bin/env python3
"""Reproducible ONNX export of bge-small-en-v1.5 for the SHIPPING encoder.

This is DECISION-002 §9.4: "Export bge-small to ONNX ... verify vectors match
sentence-transformers to ~1e-5. Benchmark numbers must describe the *shipped*
system." Until this script existed, no .onnx file existed and every dense number
downstream ran on a stub.

WHAT IS EXPORTED — the RAW TRANSFORMER, nothing more
====================================================
The graph emits the token-level `last_hidden_state` (B, T, H). Pooling and L2
normalisation deliberately stay in Python, in `retriever.OnnxEncoder`, exactly
as the current architecture already assumes. We do NOT bake pooling into the
graph. Two reasons:

  1. It keeps the ONNX artifact a faithful, inspectable image of the transformer
     — the same tensor sentence-transformers pools from — so the parity test
     (tests/test_onnx_parity.py) compares like with like.
  2. bge uses **CLS pooling** (1_Pooling/config.json: pooling_mode_cls_token=true),
     which is `hidden[:, 0]`. Keeping pooling in Python means the pooling choice
     lives in one auditable place next to the prefixes it belongs with, not
     frozen inside a binary blob.

INPUTS
======
`input_ids`, `attention_mask`, AND `token_type_ids`. bge is a BERT and its
forward takes token_type_ids; `OnnxEncoder` already feeds a zeros tensor when the
graph declares that input, so we export all three to keep the two consistent.
Batch and sequence are dynamic axes.

WHY torch.onnx.export, NOT optimum
==================================
optimum[exporters] is available in the build env and was the first preference per
the task, but torch.onnx.export is used here because it gives exact control over
the three named inputs, the dynamic axes, and a single-output raw-`last_hidden_state`
graph with a pinned opset — matching the "pooling stays in Python" architecture
with no wrapper. optimum's ORTModelForFeatureExtraction emits an I/O contract and
extra config files tuned for its own runtime wrapper, which we do not use.
torch / transformers are BUILD-TIME deps only; the shipping runtime stays
onnxruntime + tokenizers (see requirements.txt).

OFFLINE
=======
Reads the locally-cached model only (HF_HUB_OFFLINE=1). Fails loudly if the model
is not cached rather than reaching the Hub mid-export.

USAGE
    python scripts/export_onnx.py                 # -> models/bge-small-en-v1.5.onnx
    python scripts/export_onnx.py --out PATH --opset 17

Run in the benchmark/build env:  pip install -r requirements-bench.txt onnx
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

# Offline by contract: never reach the Hub during export. The model must already
# be cached locally (it was, for the bake-off). Set before importing transformers.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "models" / "bge-small-en-v1.5.onnx"
DEFAULT_OPSET = 17  # pinned; ships a stable graph across onnxruntime versions


def export(out_path: Path, opset: int) -> None:
    import torch
    from transformers import AutoModel, AutoTokenizer

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Raw transformer. AutoModel (not any *ForSequenceClassification head) returns
    # last_hidden_state as output[0] — the token-level tensor pooling reads from.
    model = AutoModel.from_pretrained(MODEL)
    model.eval()

    class RawTransformer(torch.nn.Module):
        """Fix the signature to exactly (input_ids, attention_mask, token_type_ids)
        and the output to the single last_hidden_state tensor. This removes the
        dict/kwargs ambiguity (transformers' forward also takes use_cache etc.) and
        guarantees the graph has three named inputs and one named output — nothing
        else, and no pooling head."""

        def __init__(self, m: torch.nn.Module) -> None:
            super().__init__()
            self.m = m

        def forward(self, input_ids, attention_mask, token_type_ids):
            return self.m(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
            ).last_hidden_state

    wrapped = RawTransformer(model).eval()

    # A real, batched dummy so both dynamic axes exercise > 1 and the trace does
    # not constant-fold a length-1 sequence. Two strings of different length.
    tok = AutoTokenizer.from_pretrained(MODEL)
    enc = tok(
        ["Represent this sentence for searching relevant passages: returns policy",
         "store credits, wallet refunds, vouchers, mobile money transfer"],
        padding=True,
        return_tensors="pt",
    )
    input_ids = enc["input_ids"]
    attention_mask = enc["attention_mask"]
    # bge/BERT accepts token_type_ids; OnnxEncoder feeds zeros — export with zeros.
    token_type_ids = enc.get("token_type_ids")
    if token_type_ids is None:
        token_type_ids = torch.zeros_like(input_ids)

    dynamic_axes = {
        "input_ids": {0: "batch", 1: "sequence"},
        "attention_mask": {0: "batch", 1: "sequence"},
        "token_type_ids": {0: "batch", 1: "sequence"},
        "last_hidden_state": {0: "batch", 1: "sequence"},
    }

    with torch.no_grad():
        torch.onnx.export(
            wrapped,
            (input_ids, attention_mask, token_type_ids),
            str(out_path),
            input_names=["input_ids", "attention_mask", "token_type_ids"],
            output_names=["last_hidden_state"],
            dynamic_axes=dynamic_axes,
            opset_version=opset,
            do_constant_folding=True,
            # Pin the legacy TorchScript exporter: it needs no onnxscript, emits a
            # single stable graph, and gives exact control over the named I/O above.
            # The dynamo exporter (torch>=2.x default) is an unnecessary build dep here.
            dynamo=False,
        )


def report(out_path: Path) -> None:
    data = out_path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    mb = len(data) / (1024 * 1024)
    print(f"wrote {out_path}")
    print(f"  size    {mb:.1f} MB ({len(data)} bytes)")
    print(f"  sha256  {sha}")
    print(f"  opset   pinned; inputs input_ids/attention_mask/token_type_ids; "
          f"output last_hidden_state (raw transformer, pooling stays in Python)")
    # Optional structural sanity check if onnx is importable.
    try:
        import onnx
        m = onnx.load(str(out_path))
        onnx.checker.check_model(m)
        ins = [i.name for i in m.graph.input]
        outs = [o.name for o in m.graph.output]
        print(f"  onnx.checker OK; graph inputs={ins} outputs={outs}")
    except Exception as e:  # pragma: no cover - onnx optional at report time
        print(f"  (onnx structural check skipped: {e})")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--opset", type=int, default=DEFAULT_OPSET)
    args = p.parse_args(argv)

    try:
        export(args.out, args.opset)
    except Exception as e:
        # An offline miss (model not cached) or a missing build dep must fail
        # loudly and say what is needed — never degrade silently.
        print(f"ERROR: export failed: {e}", file=sys.stderr)
        print(
            "This export is BUILD-TIME only. It needs torch + transformers and the "
            f"model {MODEL} cached locally (HF_HUB_OFFLINE=1). "
            "Install: pip install -r requirements-bench.txt onnx",
            file=sys.stderr,
        )
        return 1

    report(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
