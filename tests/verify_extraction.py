#!/usr/bin/env python3
"""Extraction verification harness — SEMANTIC quality gates.

WHY THIS EXISTS
===============
v1's quality metrics reported all-green on a corpus that was semantically
destroyed. Every check was STRUCTURAL ("how many chunks?", "any under 80
chars?"). None asked the only question that matters:

    "Does this chunk still MEAN anything on its own?"

CHANGELOG
=========
v3 (2026-07-12) — GATE 3: GARBLED LABEL DETECTION.
    v2.1's GATE 1 checked whether label markers (':', '|') were PRESENT. It did
    not check whether the labels were MEANINGFUL. So it passed this, from the
    annual report:

        1.1 tn XGU | col1: UGX 947.5 bn UGX 811.8 bn

    "XGU" is "UGX" read backwards. "col1" means header detection failed. The
    chunk has label markers, so GATE 1 said PASS. It is garbage.

    THIRD INSTANCE of the project's recurring lesson: the gate tested STRUCTURE,
    and structure is not meaning. Recorded because it keeps recurring at every
    layer we build.

    GATE 3 keys on CORRUPTION ARTIFACTS, not on vocabulary:
      A. Placeholder headers  (`col1:`)   -> header row was never found
      B. Stranded suffixes    (`: ted`)   -> word split across a cell boundary
      C. Orphaned decimals    (`| .7 bn`) -> number split across a cell boundary

    A vocabulary-based detector (e.g. "flag unknown ALLCAPS fragments") was
    tried and REJECTED: it fired on `ASK/OOK` and `MHz` in the engineering
    report's legitimate protocol table. Domain acronyms are indistinguishable
    from garbling by that signal. Corruption artifacts are not.

v2.1 (2026-07-12) — FALSE-POSITIVE FIX.
    GATE 1 fired on the engineering report's Table of Contents / List of Figures
    / List of Tables. Root cause: the numeric regex matched a BARE DOT, so
    dot-leader lines scored 0.90 density. Fix: a numeric token must contain a
    DIGIT; dot-leaders are stripped; front matter is exempted structurally.

    LESSON: the v2.0 gate was validated ONLY against known-bad input. It was
    proven able to FAIL but never proven able to PASS. A gate needs BOTH a
    positive and a negative control. This is the SAME fixture-selection error
    that caused the original extraction defect.
"""

from __future__ import annotations

import re
import sys
import platform
from datetime import datetime, timezone
from pathlib import Path

# extract.py lives in src/ingestion/ (this file is tests/). Resolve it relative
# to this file so the harness works from any cwd and from a clean clone.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "ingestion"))
from extract import extract  # noqa: E402


# --- Tunables ----------------------------------------------------------------

#: Broken v1 table chunks score 0.73-0.78; fixed v3 rows score ~0.21-0.29.
DIGIT_DENSITY_THRESHOLD = 0.35

#: v3 table rows carry "Header: value" pairs. Presence is a cheap proxy for
#: "this row is labelled" — but see GATE 3: presence is not sufficiency.
LABEL_MARKERS = (":", "|")

#: Blocks whose tokens are largely dot-leaders are front matter, not broken data.
DOT_LEADER_RATIO = 0.30
DOT_LEADER_RE = re.compile(r"(?:\.\s*){4,}")

#: A table-of-contents line: SECTION NUMBER ... TITLE ... PAGE NUMBER.
#: "5.1 Conclusion . . . . . 28"  ->  section 5.1, page 28.
#: Neither number is a data value. A broken table row matches NEITHER end.
TOC_LINE_RE = re.compile(r"^\s*\d+(?:\.\d+)*\s+\S[^|]*?\s+\d+\s*$")

# --- GATE 3 corruption signatures --------------------------------------------

#: `col1:` — serialise_table fell back to placeholder names, i.e. the real
#: header row was never located. The row is unlabelled in substance.
GARBLE_PLACEHOLDER = re.compile(r"\bcol\d+\s*:")

#: `: ted` — a word suffix stranded after a colon, e.g. "contribu ... : ted".
#: Signature of a word split across a cell boundary by bad glyph ordering.
GARBLE_STRANDED = re.compile(r":\s*(?:ted|ing|tion|ed|ly|ment|ness)\b")

#: `| .7 bn` — a value beginning with a bare decimal point: a number torn in two.
GARBLE_ORPHAN_DECIMAL = re.compile(r"\|\s*\.\d")


def _strip_dot_leaders(text: str) -> str:
    return DOT_LEADER_RE.sub(" ", text)


def _is_numeric_token(tok: str) -> bool:
    """True only for tokens containing at least one DIGIT.

    THE v2.0 BUG LIVED HERE: the old pattern matched a bare '.', so TOC dot
    leaders were counted as numbers.
    """
    if not any(c.isdigit() for c in tok):
        return False
    return bool(re.fullmatch(r"[\d,.()%\-+]+", tok))


def is_front_matter(text: str) -> bool:
    """TOC / List of Figures / List of Tables, detected structurally.

    TWO SIGNALS, either sufficient:

      A. Dot-leader density (works on multi-line TOC blocks).
      B. TOC LINE SHAPE: section number ... title ... page number, with dot
         leaders between. A single TOC line ("5.1 Conclusion . . . 28") has too
         few tokens for signal A to fire -- after stripping leaders only three
         remain, two of them numeric -> density 0.67. Signal B catches it.

    Signal B is the load-bearing one: a broken table row
    ("Total revenue 1,522,676 1,267,089 ...") matches NEITHER end of the shape.
    It has no leading section number and does not terminate in a bare page
    number, so it cannot be mistaken for front matter.
    """
    toks = text.split()
    if not toks:
        return False

    dots = sum(1 for t in toks if set(t) == {"."})
    if (dots / len(toks)) >= DOT_LEADER_RATIO:
        return True

    leader_lines = [l for l in text.split("\n") if DOT_LEADER_RE.search(l)]
    if not leader_lines:
        return False
    stripped = [DOT_LEADER_RE.sub(" ", l).strip() for l in leader_lines]
    hits = sum(bool(TOC_LINE_RE.match(s)) for s in stripped)
    return hits / len(leader_lines) >= 0.5


def digit_density(text: str) -> float:
    """Fraction of tokens that are genuine numeric literals.

    Front matter is excluded outright: a TOC line's numbers are a section number
    and a page number, not data values, so scoring their density is meaningless.
    (A bare "5.1 Conclusion . . . 28" strips to three tokens, two numeric ->
    0.67, which would trip the gate on correctly-extracted content.)
    """
    if is_front_matter(text):
        return 0.0
    toks = _strip_dot_leaders(text).split()
    if not toks:
        return 0.0
    return sum(_is_numeric_token(t) for t in toks) / len(toks)



def is_orphan_number_block(text: str) -> bool:
    """GATE 1 — an UNLABELLED digit-wall. The original v1 defect."""
    if is_front_matter(text):
        return False
    if digit_density(text) < DIGIT_DENSITY_THRESHOLD:
        return False
    return not any(m in text for m in LABEL_MARKERS)


def is_garbled(text: str) -> bool:
    """GATE 3 — labels are PRESENT but MEANINGLESS.

    Keys on corruption artifacts, never on vocabulary. A vocabulary-based
    detector was tried and rejected: it flagged `ASK/OOK` and `MHz` in a
    legitimate protocol-comparison table.
    """
    return bool(
        GARBLE_PLACEHOLDER.search(text)
        or GARBLE_STRANDED.search(text)
        or GARBLE_ORPHAN_DECIMAL.search(text)
    )


def has_ambiguous_headers(text: str) -> bool:
    """GATE 4 — a row's headers are DUPLICATED, so its values are unresolvable.

    WHY (v3.1): statutory statements stack headers three deep (period / audit
    status / units). A single-row header picker took the UNITS row, yielding:

        Property, plant and equipment | Shs '000: 1,200,858,421 | Shs '000: 1,031,959,769

    Three columns, three IDENTICAL headers. Every value is labelled, so GATE 1
    and GATE 3 both PASS — and the chunk is still unanswerable, because nothing
    says which column is June 2024.

    FOURTH instance of the project's recurring lesson: the value carried *a*
    label, but not the *disambiguating* one. GATE 4 checks that a row's headers
    are DISTINCT, which is the property that actually makes a value resolvable.
    """
    for line in text.split("\n"):
        if "|" not in line:
            continue
        headers = [
            seg.split(":", 1)[0].strip()
            for seg in line.split("|")[1:]
            if ":" in seg
        ]
        if len(headers) >= 2 and len(set(headers)) < len(headers):
            return True
    return False


# --- Self-test ---------------------------------------------------------------
# A gate must be proven able to BOTH fire and stay silent. v2.0 was only ever
# tested against known-bad input, which is exactly why it over-fired.

_ORPHAN_MUST_FIRE = [
    "Total revenue 1,522,676 1,267,089 20.2% 772,184 639,161 20.8%\n"
    "Service revenue 1,505,398 1,250,059 20.4% 764,029 628,948 21.5%",
]
_ORPHAN_MUST_NOT_FIRE = [
    "Total revenue | H1 2024: 1,522,676 | H1 2023: 1,267,089 | YoY: 20.2%",
    "5.1 Conclusion . . . . . . . . . . . . . . . . . 28\n"
    "5.2 Recommendations . . . . . . . . . . . . . . . 29",
    "List of Figures\n2.1 On-Off Shift Keying [6]. . . . . . . . . . 6",
    "List of Tables\n2.1 Operational Comparison of Low-Power Protocols . . . . 5",
    "Service revenue grew by 20.4% driven by resilience in connectivity.",
]
_GARBLE_MUST_FIRE = [
    # Real annual-report output.
    "1.1 tn XGU | col1: UGX 947.5 bn UGX 811.8 bn",
    "Profit after tax rose Taxes contribu 678.8 XG 1.6 XG | .7 bn: ted",
]
_GARBLE_MUST_NOT_FIRE = [
    "Service revenue | 2025: 3,566,206 | 2024: 3,143,587 | 2023: 2,629,863",
    "Total revenue | H1 2024: 1,522,676 | H1 2023: 1,267,089 | YoY: 20.2%",
    # Legitimate technical acronyms — a vocabulary detector wrongly flagged this.
    "ASK/OOK | Frequency Band: 433.92 MHz | Typical Range: 50m - 100m",
    "Investment community | h Network performance.: h Strong business results.",
]


_AMBIG_MUST_FIRE = [
    # Real v3.0 output: units row taken as header -> three identical columns.
    "Property, plant and equipment | Shs '000: 1,200,858,421 | Shs '000: 1,031,959,769 | Shs '000: 1,086,547,617",
]
_AMBIG_MUST_NOT_FIRE = [
    # v3.1 output: full header stack merged, periods distinct.
    "Property, plant and equipment | June 2024 Reviewed Shs '000: 1,200,858,421 "
    "| June 2023 Reviewed Shs '000: 1,031,959,769",
    "Total revenue | H1 2024: 1,522,676 | H1 2023: 1,267,089 | YoY: 20.2%",
    "Service revenue | 2025: 3,566,206 | 2024: 3,143,587 | 2023: 2,629,863",
]


def self_test(verbose: bool = True) -> bool:
    ok = True

    def _check(fn, samples, expect, label):
        nonlocal ok
        for t in samples:
            if fn(t) != expect:
                if verbose:
                    verb = "did NOT fire" if expect else "FIRED"
                    print(f"  [SELFTEST FAIL] {label} {verb}: {t[:52]}...")
                ok = False

    _check(is_orphan_number_block, _ORPHAN_MUST_FIRE, True, "GATE1")
    _check(is_orphan_number_block, _ORPHAN_MUST_NOT_FIRE, False, "GATE1")
    _check(is_garbled, _GARBLE_MUST_FIRE, True, "GATE3")
    _check(is_garbled, _GARBLE_MUST_NOT_FIRE, False, "GATE3")
    _check(has_ambiguous_headers, _AMBIG_MUST_FIRE, True, "GATE4")
    _check(has_ambiguous_headers, _AMBIG_MUST_NOT_FIRE, False, "GATE4")
    return ok


def verify(path: Path) -> dict:
    blocks = extract(path)
    tables = [b for b in blocks if b.kind == "table"]
    orphans = [b for b in blocks if is_orphan_number_block(b.text)]
    garbled = [b for b in blocks if is_garbled(b.text)]
    ambiguous = [b for b in blocks if has_ambiguous_headers(b.text)]
    front = [b for b in blocks if is_front_matter(b.text)]

    return {
        "path": path.name,
        "blocks": len(blocks),
        "tables": len(tables),
        "table_rows": sum(b.n_rows for b in tables),
        "by_strategy": {
            s: sum(1 for b in tables if b.strategy == s) for s in ("lines", "text")
        },
        "prose": len(blocks) - len(tables),
        "front_matter": len(front),
        "orphans": len(orphans),
        "garbled": len(garbled),
        "ambiguous": len(ambiguous),
        "ambiguous_samples": [b.text.split("\n")[0][:95] for b in ambiguous[:3]],
        "orphan_samples": [b.text[:95] for b in orphans[:3]],
        "garbled_samples": [b.text[:95] for b in garbled[:3]],
        "table_samples": [b.text.split("\n")[0][:105] for b in tables[:2]],
    }


def report(results: list[dict]) -> bool:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 78)
    print("EXTRACTION VERIFICATION v3.1 — semantic quality gates")
    print(f"{stamp} | python {platform.python_version()} | {platform.system()}")
    print("=" * 78)

    print("\nSELF-TEST (each gate must fire on known-bad AND stay silent on known-good)")
    if not self_test():
        print("  [ABORT] A gate is broken. Its verdicts cannot be trusted.")
        return False
    n_bad = len(_ORPHAN_MUST_FIRE) + len(_GARBLE_MUST_FIRE) + len(_AMBIG_MUST_FIRE)
    n_good = (len(_ORPHAN_MUST_NOT_FIRE) + len(_GARBLE_MUST_NOT_FIRE)
              + len(_AMBIG_MUST_NOT_FIRE))
    print(f"  [PASS] {n_bad} known-bad fired; {n_good} known-good silent.")

    ok = True
    for r in results:
        print(f"\n### {r['path']}")
        strat = r["by_strategy"]
        print(f"  blocks        : {r['blocks']}")
        print(f"  tables        : {r['tables']}  ({r['table_rows']} data rows) "
              f"[lines={strat['lines']} text={strat['text']}]")
        print(f"  prose         : {r['prose']}  ({r['front_matter']} front matter)")

        if r["orphans"]:
            ok = False
            print(f"\n  [FAIL] GATE 1: {r['orphans']} unlabelled digit-wall(s).")
            print("         Numbers with no header attached. Unretrievable.")
            for s in r["orphan_samples"]:
                print(f"           > {s}")
        else:
            print("  [PASS] GATE 1: no unlabelled digit-walls.")

        if r["tables"] == 0:
            ok = False
            print("  [FAIL] GATE 2: zero tables detected.")
            print("         For a document with tabular data this is a bug.")
        else:
            print("  [PASS] GATE 2: tables detected and structured.")
            for s in r["table_samples"]:
                print(f"           > {s}")

        if r["garbled"]:
            ok = False
            print(f"\n  [FAIL] GATE 3: {r['garbled']} garbled block(s).")
            print("         Labels present but MEANINGLESS (rotated/curved source")
            print("         text). Known limitation — flagged, not silently passed.")
            for s in r["garbled_samples"]:
                print(f"           > {s}")
        else:
            print("  [PASS] GATE 3: no garbled labels.")

        if r["ambiguous"]:
            ok = False
            print(f"\n  [FAIL] GATE 4: {r['ambiguous']} row(s) with DUPLICATE headers.")
            print("         Values are labelled but UNRESOLVABLE - nothing says which")
            print("         column is which period. Multi-row header stack not merged.")
            for s in r["ambiguous_samples"]:
                print(f"           > {s}")
        else:
            print("  [PASS] GATE 4: all row headers distinct.")

    print()
    print("=" * 78)
    print("RESULT:", "PASS — corpus is fit for embedding benchmarking"
          if ok else "FAIL — do NOT proceed to embedding selection")
    print("=" * 78)
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nSelf-test only:\n")
        r = self_test()
        print("  PASS" if r else "  FAIL")
        sys.exit(0 if r else 1)
    res = [verify(Path(p)) for p in sys.argv[1:]]
    sys.exit(0 if report(res) else 1)
