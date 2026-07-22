#!/usr/bin/env python3
"""Tabulate the completed R5 hand-validation review packet (risk R5, DECISIONS.md).

Reads the human-filled checkboxes in R5_review_packet.md and reports how many of
the sampled Layer A PASSes were confirmed CORRECT vs UNGROUNDED/WRONG/LABEL ISSUE,
plus the implied precision of Layer A's PASS verdict on this sample.

Does NOT run Layer A or an LLM judge itself, and does not adjudicate anything --
it only counts boxes a human has already checked. Fails loudly on any block that
is unfilled or has more than one box checked, rather than guessing.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VERDICTS = ["CORRECT", "UNGROUNDED", "WRONG", "LABEL ISSUE"]

BLOCK_RE = re.compile(r"^### (Q\d+) — (\S+)\s*$", re.M)
LAYER_A_RE = re.compile(r"\*\*Layer A verdict:\*\* (\S+)")
BOX_RE = re.compile(r"\[( |x|X)\]\s+(CORRECT|UNGROUNDED|WRONG|LABEL ISSUE)")


def parse_packet(text: str) -> list[dict]:
    headers = list(BLOCK_RE.finditer(text))
    if not headers:
        raise ValueError("no '### Qnn — stratum' blocks found -- wrong file, or packet format changed")

    items = []
    for i, m in enumerate(headers):
        qid, stratum = m.group(1), m.group(2)
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[start:end]

        a_match = LAYER_A_RE.search(block)
        if not a_match:
            raise ValueError(f"{qid}: no 'Layer A verdict:' line found in its block")
        a_verdict = a_match.group(1)

        boxes = BOX_RE.findall(block)
        if len(boxes) != 4:
            raise ValueError(
                f"{qid}: expected 4 verdict checkboxes (CORRECT/UNGROUNDED/WRONG/LABEL ISSUE), "
                f"found {len(boxes)} -- packet is malformed or a line was edited"
            )
        checked = [label for mark, label in boxes if mark.lower() == "x"]
        if len(checked) == 0:
            raise ValueError(f"{qid}: no verdict box checked -- packet is not fully filled in yet")
        if len(checked) > 1:
            raise ValueError(f"{qid}: multiple verdict boxes checked ({checked}) -- exactly one is required")

        items.append({"id": qid, "stratum": stratum, "a_verdict": a_verdict, "human_verdict": checked[0]})

    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", default="benchmarks/generation/R5_review_packet.md")
    ap.add_argument("--out", default="benchmarks/generation/R5_validation_result.md")
    args = ap.parse_args()

    text = Path(args.packet).read_text()
    items = parse_packet(text)

    pass_items = [it for it in items if it["a_verdict"] == "PASS"]
    weak_items = [it for it in items if it["a_verdict"] == "WEAK"]
    other_items = [it for it in items if it["a_verdict"] not in ("PASS", "WEAK")]

    def tally(group: list[dict]) -> dict:
        return {v: sum(1 for it in group if it["human_verdict"] == v) for v in VERDICTS}

    pass_tally = tally(pass_items)
    weak_tally = tally(weak_items)

    n_pass = len(pass_items)
    n_correct = pass_tally["CORRECT"]
    precision = (n_correct / n_pass) if n_pass else float("nan")

    lines = []
    lines.append("# R5 Validation Result\n")
    lines.append(
        "Tabulated from the human-completed `R5_review_packet.md`. This sample is "
        "deliberately adversarial (weighted toward multi_chunk and prose strata, the "
        "shapes where token overlap is least reliable), so the precision figure below "
        "is a **lower bound** on Layer A's true precision across the full 25 PASSes, "
        "not an unbiased estimate.\n"
    )

    lines.append(f"## Layer A PASS items (n={n_pass})\n")
    for v in VERDICTS:
        lines.append(f"- {v}: {pass_tally[v]}")
    lines.append("")
    lines.append(
        f"**Implied precision of Layer A's PASS verdict on this sample: "
        f"{n_correct}/{n_pass} ({100 * precision:.1f}%)** -- lower bound, adversarial sample, "
        "see caveat above."
    )
    lines.append("")

    if weak_items:
        lines.append(f"## Layer A WEAK items (n={len(weak_items)}) -- for context, excluded from the precision figure above\n")
        for v in VERDICTS:
            lines.append(f"- {v}: {weak_tally[v]}")
        lines.append("")

    if other_items:
        lines.append(f"## Other Layer A verdicts in sample (n={len(other_items)})\n")
        for it in other_items:
            lines.append(f"- {it['id']}: Layer A={it['a_verdict']}, human={it['human_verdict']}")
        lines.append("")

    lines.append("## Per-question verdicts\n")
    lines.append("| ID | Stratum | Layer A | Human |")
    lines.append("|---|---|---|---|")
    for it in items:
        lines.append(f"| {it['id']} | {it['stratum']} | {it['a_verdict']} | {it['human_verdict']} |")
    lines.append("")

    out_text = "\n".join(lines) + "\n"
    Path(args.out).write_text(out_text)
    print(out_text)
    print(f"Saved -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
