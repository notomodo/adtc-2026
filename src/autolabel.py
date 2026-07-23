#!/usr/bin/env python3
"""Auto-labeller that ABSTAINS. It labels only what it can prove, and refuses
to guess at the rest.

THE TRAP THIS AVOIDS
====================
The previous auto-relabeller marked 26-28 of 37 chunks as gold on four
questions. Well-formed JSON, passed every structural check, and it invalidated
an entire bake-off.

The failure was not a weak matcher. It was CIRCULAR: a labeller and a retriever
are the same class of algorithm. Both rank chunks by relevance to a query. If a
script could reliably identify the answer chunk, you would ship it INSTEAD of a
retriever. So generating ground truth with algorithm A and using it to grade
algorithm B measures how similar B is to A -- not how good B is. A lexical
labeller makes BM25 look excellent. An embedding labeller makes embeddings look
excellent. The benchmark becomes a mirror.

WHY THIS ONE IS DIFFERENT
-------------------------
It never matches on the QUESTION. It matches on the ANSWER -- and only when the
answer contains an ANCHOR: a string so specific that its presence in a chunk is
not a relevance judgment but a verifiable fact.

    "support@kibuga.com"           -> anchor. Appears in exactly one chunk.
    "Two (2) days free returns"    -> anchor. Verbatim span.
    "+256200959991"                -> anchor.
    "at our discretion"            -> NOT an anchor. Appears everywhere.

Finding a literal email address in a chunk is not the same operation as deciding
a chunk is "relevant". The first is checkable by grep; the second is the
retrieval problem itself. This tool only does the first.

THE ABSTENTION RULE
-------------------
When no anchor exists, or an anchor matches too many chunks to be discriminative,
the tool WRITES NO LABEL and marks the question for human review. It would
rather hand you 12 proven labels and 10 open questions than 22 plausible guesses.

This is the whole design. An abstaining labeller is honest; a confident one is
the bug we already shipped once.

TIERS
-----
  VERBATIM  -- a >=4-word span of the answer appears literally in the chunk.
               Strongest evidence. Auto-accepted.
  ANCHOR    -- a rare token (email, phone, figure, quoted number) from the answer
               appears, and matches <= MAX_HITS chunks. Auto-accepted.
  ABSTAIN   -- everything else. Sent to human review. NOT labelled.

USAGE
    python autolabel.py --dump chunks_sme.txt --draft questions_sme_draft.json \\
        --out questions_sme_auto.json --review review.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^\[(\d+)\] source=(\S+) type=(\S+) page=(\d+)")
FINGERPRINT_RE = re.compile(r"^# corpus_fingerprint:\s*(\S+)")


def read_fingerprint(path: str) -> str:
    """The hash of the corpus these labels were made against.

    Gold labels are (question -> chunk_id) pairs. A chunk_id is only meaningful
    relative to a specific corpus. If the corpus is re-ingested and the chunking
    shifts by even one chunk, every label silently points at the wrong text --
    which is exactly what happened when a tokenizer fallback produced 57 chunks
    on one machine and 47 on another. Binding labels to a fingerprint makes that
    detectable instead of silent."""
    for line in open(path, encoding="utf-8"):
        m = FINGERPRINT_RE.match(line)
        if m:
            return m.group(1)
        if not line.startswith("#"):
            break
    return ""

# An anchor must be RARE. If a token appears in more than this fraction of the
# corpus it carries no discriminative power and using it as evidence is exactly
# the smearing failure. 0.15 is deliberately tight.
MAX_DF_FRACTION = 0.15
# Even a rare anchor should not point at many chunks. If it does, the answer is
# probably a generic phrase and we abstain.
MAX_HITS = 3
# A verbatim span must be long enough that coincidence is implausible.
MIN_SPAN_WORDS = 4

STOP = {
    "the", "a", "an", "of", "to", "in", "is", "are", "for", "and", "or", "you",
    "we", "on", "at", "by", "be", "it", "as", "our", "your", "with", "that",
    "this", "from", "may", "will", "can", "any", "all", "not", "no", "if",
}


def load_chunks(path: str) -> tuple[list[int], list[str], list[dict]]:
    ids, texts, metas = [], [], []
    cur, meta, buf, in_body = None, {}, [], False

    def body_of(lines: list[str]) -> str:
        # Byte-faithful: drop only the writer's single trailing blank spacer
        # line; never .strip() (deletes the real trailing space on chunks 0, 22).
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
    return ids, texts, metas


def norm(s: str) -> str:
    """Collapse whitespace and punctuation noise so 'Two (2) days' matches."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9@.+]+", " ", s.lower())).strip()


def verbatim_hits(answer: str, texts: list[str], ids: list[int]) -> tuple[list[int], str]:
    """Find chunks containing a >=MIN_SPAN_WORDS literal span of the answer.

    Slides a window over the answer, longest first. The first span that hits any
    chunk wins -- longest match is strongest evidence.
    """
    a_words = norm(answer).split()
    n_texts = [norm(t) for t in texts]
    for size in range(len(a_words), MIN_SPAN_WORDS - 1, -1):
        for start in range(0, len(a_words) - size + 1):
            span = " ".join(a_words[start : start + size])
            hits = [cid for cid, t in zip(ids, n_texts) if span in t]
            if hits and len(hits) <= MAX_HITS:
                return hits, span
    return [], ""


def anchor_hits(answer: str, texts: list[str], ids: list[int]) -> tuple[list[int], str]:
    """Find chunks containing a STRUCTURALLY DISTINCTIVE token from the answer.

    "Rare" is not enough. On a 57-chunk corpus, an ordinary English word like
    'jurisdiction' or 'investment' can appear in only 2-3 chunks and pass a
    naive rareness test -- while carrying no proof at all. Measured: 'jurisdiction'
    matched three chunks, of which only one answered the question; the other two
    merely CONTAINED THE WORD. That is a relevance judgment masquerading as
    evidence, and it is precisely the failure that smeared the last question set.

    So an anchor must be structurally distinctive: an email, a phone number, a
    figure, a monetary amount, an identifier. Something whose presence in a chunk
    is a verifiable fact rather than an interpretation. An ordinary word -- however
    infrequent -- is never an anchor. If the answer has no such token, we ABSTAIN.
    """
    n_texts = [norm(t) for t in texts]
    toks = [t for t in norm(answer).split() if t not in STOP and len(t) > 2]

    def is_structured(t: str) -> bool:
        # Email, phone/number, or an alphanumeric identifier. NOT a plain word.
        return bool(re.search(r"@", t)) or bool(re.search(r"\d", t))

    structured = [t for t in toks if is_structured(t)]
    if not structured:
        return [], ""  # abstain -- no provable anchor

    ceiling = max(1, int(len(ids) * MAX_DF_FRACTION))
    for tok in sorted(set(structured), key=lambda t: -len(t)):
        hits = [cid for cid, t in zip(ids, n_texts) if tok in t.split()]
        if 0 < len(hits) <= min(ceiling, MAX_HITS):
            return hits, tok
    return [], ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--draft", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--review", default="review.txt")
    args = ap.parse_args()

    ids, texts, metas = load_chunks(args.dump)
    by_id = {c: (t, m) for c, t, m in zip(ids, texts, metas)}
    draft = json.load(open(args.draft))

    labelled, abstained = [], []
    print(f"{len(ids)} chunks | {len(draft['questions'])} questions\n")
    print(f"{'QID':<5}{'TIER':<10}{'GOLD':<12}EVIDENCE")
    print("-" * 74)

    for q in draft["questions"]:
        hits, span = verbatim_hits(q["answer"], texts, ids)
        tier = "VERBATIM"
        if not hits:
            hits, span = anchor_hits(q["answer"], texts, ids)
            tier = "ANCHOR"
        if not hits:
            tier = "ABSTAIN"

        if tier == "ABSTAIN":
            abstained.append(q)
            print(f"{q['id']:<5}{'ABSTAIN':<10}{'—':<12}no provable anchor — HUMAN REVIEW")
            continue

        q["gold_chunks"] = sorted(hits)
        q["_evidence"] = {"tier": tier, "matched": span}
        labelled.append(q)
        print(f"{q['id']:<5}{tier:<10}{str(sorted(hits)):<12}{span[:38]!r}")

    # Write the proven labels.
    draft["questions"] = labelled
    draft["_meta"]["labelled"] = (
        "AUTO-LABELLED BY PROOF (verbatim span or rare anchor). "
        "Questions with no provable anchor were ABSTAINED, not guessed."
    )
    draft["_meta"]["n_chunks_in_corpus"] = len(ids)
    draft["_meta"]["n_abstained"] = len(abstained)
    draft["_meta"]["corpus_fingerprint"] = read_fingerprint(args.dump)
    Path(args.out).write_text(json.dumps(draft, indent=2), encoding="utf-8")

    # Write the review file: the questions a human must still decide.
    if abstained:
        lines = [
            "QUESTIONS THE AUTO-LABELLER REFUSED TO GUESS",
            "=" * 74,
            "No verbatim span and no rare anchor. These need a human.",
            "Read the chunk, decide, then add gold_chunks to the JSON by hand.",
            "",
        ]
        for q in abstained:
            lines += [
                "=" * 74,
                f"{q['id']}  [{q['stratum']}]  {q['question']}",
                f"  expected answer: {q['answer']}",
                "-" * 74,
            ]
            # Show weak candidates purely as a reading aid. NOT a recommendation.
            want = set(norm(q["answer"]).split()) - STOP
            scored = sorted(
                ((len(want & set(norm(t).split())), cid) for cid, t in zip(ids, texts)),
                reverse=True,
            )[:5]
            for _, cid in scored:
                t, m = by_id[cid]
                head = t.split("\n", 1)[0]
                body = t.split("\n", 1)[1] if "\n" in t else ""
                lines += [
                    f"  [{cid}] {m['source'][:30]} p{m['page']} / {head[:36]}",
                    f"        {body[:170]}",
                ]
            lines += ["", "  gold_chunks: ______", ""]
        Path(args.review).write_text("\n".join(lines), encoding="utf-8")

    n = len(draft["questions"]) + len(abstained)
    print("-" * 74)
    print(f"\nPROVEN   : {len(labelled)}/{n} -> {args.out}")
    print(f"ABSTAINED: {len(abstained)}/{n} -> {args.review}  (human required)")
    if len(labelled) < 12:
        print(f"\n!! Only {len(labelled)} proven labels. That is too thin to rank "
              f"retrievers on.\n   Work through {args.review} before benchmarking.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
