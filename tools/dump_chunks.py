#!/usr/bin/env python3
"""Produce a chunk dump from v2 extraction, for review and question-set labelling.

USAGE
-----
    python dump_chunks.py *.pdf > chunk_dump_v2.txt

Then paste/upload `chunk_dump_v2.txt` back into the chat. Plain text survives the
platform's file conversion; PDFs do not.

WHAT TO LOOK AT (do not trust the metrics — that is exactly how v1 passed)
--------------------------------------------------------------------------
For every chunk marked [table], read the actual rows and confirm each one reads
like:

    Service revenue | H1 24: 1,505,398 | H1 23: 1,250,059 | % change: 20.4%

and NOT like:

    Service revenue 1,505,398 1,250,059 20.4%

The second form is the v1 defect: numbers with no headers attached. If you see it,
the fix has not worked on that document and I need to know.

PAY SPECIAL ATTENTION TO THE ANNUAL REPORT. It is the largest document (895 v1
chunks), it has nested / multi-page tables and notes-to-accounts, and
pdfplumber's table finder is heuristic — it may behave differently there than on
the interim results. This is the file the fix has the weakest evidence for.
"""

from __future__ import annotations

import sys
import platform
from datetime import datetime, timezone
from pathlib import Path

# This file lives in tools/. extract.py is in src/ingestion/; the verification
# gates are in tests/. Resolve both relative to the repo root so the dump works
# from any cwd and from a clean clone.
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src" / "ingestion"))
sys.path.insert(0, str(_ROOT / "tests"))
from extract import extract  # noqa: E402
from verify_extraction import digit_density, is_orphan_number_block, is_garbled, has_ambiguous_headers  # noqa: E402


def dump(path: Path) -> None:
    blocks = extract(path)

    print("#" * 78)
    print(f"DOCUMENT: {path.name}")
    print("#" * 78)

    tables = [b for b in blocks if b.kind == "table"]
    orphans = [b for b in blocks if is_orphan_number_block(b.text)]

    print("QUALITY METRICS")
    print(f"  blocks           : {len(blocks)}")
    print(f"  tables           : {len(tables)} ({sum(b.n_rows for b in tables)} data rows)")
    print(f"  prose            : {len(blocks) - len(tables)}")
    print(f"  ORPHAN DIGIT-WALLS: {len(orphans)}   <-- MUST BE 0")
    if orphans:
        print("  *** GATE 1 FAILED — v1 defect still present in this document ***")
    if not tables:
        print("  *** GATE 2 WARNING — zero tables. For a financial doc this is a bug. ***")
    print()

    print("CHUNKS")
    for i, b in enumerate(blocks):
        flag = "  <<< ORPHAN — BROKEN" if is_orphan_number_block(b.text) else ("  <<< GARBLED" if is_garbled(b.text) else ("  <<< AMBIGUOUS HEADERS" if has_ambiguous_headers(b.text) else ""))
        print("-" * 78)
        print(
            f"[{i}] source={path.name} type={b.kind} page={b.page} "
            f"len={len(b.text)} rows={b.n_rows} strat={b.strategy} density={digit_density(b.text):.2f}{flag}"
        )
        print("-" * 78)
        print(b.text)
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"# chunk dump v3.1 | {stamp} | python {platform.python_version()} "
          f"| {platform.system()} {platform.machine()}")
    print()

    for p in sys.argv[1:]:
        dump(Path(p))
