#!/usr/bin/env python3
"""Assert the corpus fingerprint matches the one the gold labels were made against.

Chunk IDs are POSITIONAL. If ingestion drifts for any reason -- library version,
tokenizer, an edited PDF -- every gold label silently points at different text and
every benchmark number becomes fiction. A hard gate, not a warning.
"""
import json, sys
from pathlib import Path

root = Path(__file__).parent.parent
dump = root / "benchmarks" / "chunks_sme.txt"
qs = root / "data" / "questions" / "questions_sme_auto.json"

have = ""
for line in dump.open():
    if line.startswith("# corpus_fingerprint:"):
        have = line.split(":", 1)[1].strip()
        break
    if not line.startswith("#"):
        break

want = json.load(qs.open()).get("_meta", {}).get("corpus_fingerprint", "")

if not want or not have:
    print(f"FAIL: missing fingerprint (dump={have!r} questions={want!r})")
    sys.exit(1)
if want != have:
    print(f"FAIL: fingerprint mismatch\n"
          f"  labels made against: {want}\n"
          f"  current corpus     : {have}\n"
          f"  Chunk IDs have shifted. Re-run autolabel.py.")
    sys.exit(1)
print(f"OK: corpus fingerprint {have} matches the question set.")
