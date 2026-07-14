#!/usr/bin/env python3
"""Vendor the tokenizer into the repo. REQUIRED for the offline guarantee.

Tokenizer.from_pretrained() reaches out to the HuggingFace Hub. That breaks the
offline requirement outright -- a judge without a network cannot run the pipeline.
Run this ONCE, with a network, and commit the resulting tokenizer.json.
"""
from pathlib import Path
from tokenizers import Tokenizer

MODEL = "BAAI/bge-small-en-v1.5"
out = Path(__file__).parent.parent / "src" / "tokenizer.json"
Tokenizer.from_pretrained(MODEL).save(str(out))
print(f"vendored {MODEL} -> {out}")
print("COMMIT THIS FILE. Without it the pipeline is not offline-reproducible.")
