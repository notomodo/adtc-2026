#!/usr/bin/env python3
"""Gold-label VERIFIER. Proposes candidates; you accept or reject each one.

WHY THIS IS NOT AN AUTO-LABELLER
================================
The previous auto-relabeller matched on substrings that recur in page footers
and marked 26-28 of 37 chunks as gold on four questions. Those labels were
well-formed JSON, passed every structural check, and were completely wrong --
they made the affected questions unmissable and silently inflated Recall@k for
every retriever in the bake-off. An entire benchmark was invalidated.

The lesson was not "write a better matcher." It was: A GOLD LABEL IS GROUND
TRUTH, AND GROUND TRUTH CANNOT BE INFERRED BY THE SAME CLASS OF ALGORITHM IT IS
MEANT TO EVALUATE. If a keyword matcher could reliably identify the answer
chunk, you would not need a retriever.

So this tool does exactly one thing: it shows you the candidate chunks and the
answer you are looking for, and makes YOU decide. It refuses to write a label
you have not seen.

USAGE
    python label_questions.py --dump chunks_sme.txt --draft questions_sme_draft.json \
        --out questions_sme.json

For each question it prints the top candidate chunks, and you type the chunk IDs
that ACTUALLY contain the answer (space-separated), or 's' to skip.

    Q03  What is the return window?
      [42] Return Policy / What are the conditions...
           Two (2) days free returns policy, subject to Terms and conditions...
      [44] Return Policy / How much time do I have...
           All items sold on Kibuga if faulty, can be returned within 2 days...
    gold> 42 44

A SANITY RULE, ENFORCED
-----------------------
A question with more than ~1/5 of the corpus as gold is almost certainly a
labelling artifact, not a genuinely multi-chunk question. The tool warns.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^\[(\d+)\] source=(\S+) type=(\S+) page=(\d+)")


def load_chunks(path: str) -> tuple[list[int], list[str], list[dict]]:
    ids, texts, metas = [], [], []
    cur, meta, buf, in_body = None, {}, [], False

    def body_of(lines: list[str]) -> str:
        # Byte-faithful: drop only the writer's single trailing blank spacer
        # line; never .strip(), which would delete the real trailing space on
        # chunks 0 and 22. See src/eval_retriever.py:load_chunks for the rationale.
        return "\n".join(lines[:-1] if lines and lines[-1] == "" else lines)

    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = HEADER_RE.match(line)
        if m:
            if cur is not None:
                ids.append(cur)
                texts.append(body_of(buf))
                metas.append(meta)
            cur = int(m.group(1))
            meta = {"source": m.group(2), "type": m.group(3), "page": int(m.group(4))}
            buf, in_body = [], False
            continue
        if cur is None:
            continue
        if line.startswith("---"):
            in_body = True
            continue
        if in_body:
            buf.append(line)
    if cur is not None:
        ids.append(cur)
        texts.append(body_of(buf))
        metas.append(meta)
    # Parser-fidelity gate (fatal): reproduce the dump's stamped fingerprint.
    from chunk_dump import verify_fidelity
    verify_fidelity(texts, path)
    return ids, texts, metas


def candidates(answer: str, texts: list[str], ids: list[int], n: int = 6) -> list[int]:
    """Rank chunks by overlap with the ANSWER text (not the question).

    Ranking on the answer rather than the question is deliberate: it surfaces the
    chunk that actually contains the fact, rather than the chunk that merely uses
    similar words to the question. It is still only a PROPOSAL.
    """
    want = set(re.findall(r"[a-z0-9]+", answer.lower())) - {
        "the", "a", "an", "of", "to", "in", "is", "are", "for", "and", "or", "you", "we",
    }
    scored = []
    for cid, t in zip(ids, texts):
        have = set(re.findall(r"[a-z0-9]+", t.lower()))
        scored.append((len(want & have), cid))
    scored.sort(reverse=True)
    return [cid for _, cid in scored[:n]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--draft", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ids, texts, metas = load_chunks(args.dump)
    by_id = {c: (t, m) for c, t, m in zip(ids, texts, metas)}
    draft = json.load(open(args.draft))
    ceiling = max(3, len(ids) // 5)

    print(f"\n{len(ids)} chunks | {len(draft['questions'])} questions")
    print("For each: type the chunk IDs that CONTAIN THE ANSWER, or 's' to skip.\n")

    out = []
    for q in draft["questions"]:
        print("=" * 74)
        print(f"{q['id']}  [{q['stratum']}]  {q['question']}")
        print(f"   expected answer: {q['answer']}")
        print("-" * 74)
        for cid in candidates(q["answer"], texts, ids):
            t, m = by_id[cid]
            head = t.split("\n", 1)[0]
            body = t.split("\n", 1)[1] if "\n" in t else ""
            print(f"  [{cid}] {m['source'][:28]} p{m['page']} / {head[:40]}")
            print(f"        {body[:150]}")
        while True:
            raw = input("  gold> ").strip()
            if raw.lower() == "s":
                gold = None
                break
            try:
                gold = [int(x) for x in raw.split()]
            except ValueError:
                print("  ! digits or 's'")
                continue
            if not gold:
                print("  ! give at least one id, or 's' to skip")
                continue
            unknown = [g for g in gold if g not in by_id]
            if unknown:
                print(f"  ! no such chunk: {unknown}")
                continue
            if len(gold) > ceiling:
                print(f"  ! {len(gold)} gold chunks (> {ceiling}). That is the "
                      f"smearing pattern that broke the last question set.")
                if input("  really? [y/N] ").strip().lower() != "y":
                    continue
            break
        if gold is None:
            print("  skipped\n")
            continue
        q["gold_chunks"] = gold
        out.append(q)
        print(f"  -> gold {gold}\n")

    draft["questions"] = out
    draft["_meta"]["labelled"] = "HAND-VERIFIED via label_questions.py"
    draft["_meta"]["n_chunks_in_corpus"] = len(ids)
    Path(args.out).write_text(json.dumps(draft, indent=2), encoding="utf-8")
    print(f"\nwrote {len(out)} hand-verified questions -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
