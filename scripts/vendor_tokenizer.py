#!/usr/bin/env python3
"""Vendor the tokenizer into the repo. REQUIRED for the offline guarantee.

Tokenizer.from_pretrained() reaches out to the HuggingFace Hub. That breaks the
offline requirement outright -- a judge without a network cannot run the pipeline.
Run this ONCE, with a network, and commit the resulting tokenizer.json.
"""
import argparse
from pathlib import Path

MODEL = "BAAI/bge-small-en-v1.5"
OUT = Path(__file__).parent.parent / "src" / "tokenizer.json"


def main() -> None:
    # argparse so `--help` works and the network fetch runs only when invoked,
    # not on import. (Importing this module must have no side effects.)
    argparse.ArgumentParser(description=__doc__).parse_args()
    from tokenizers import Tokenizer  # local import: keeps module import side-effect-free

    Tokenizer.from_pretrained(MODEL).save(str(OUT))
    print(f"vendored {MODEL} -> {OUT}")
    print("COMMIT THIS FILE. Without it the pipeline is not offline-reproducible.")


if __name__ == "__main__":
    main()
