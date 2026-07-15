#!/usr/bin/env python3
"""Grade the hybrid retriever against BM25-only and dense-only.

The question this answers, and the ONLY question it answers:

    Does fusing BM25 with a dense retriever beat BM25 alone?

The metric that DECIDES is RECALL@1: a higher top-1 hit rate means fewer chunks
passed to the CPU-only LLM, which is a direct latency and RAM saving. R@5 is
often a TIE on a small corpus, so gating on it alone is misleading -- an earlier
verdict did exactly that and printed "hybrid does NOT beat BM25" while every
hybrid beat BM25 on R@1 and MRR, contradicting its own table (DECISION-002 §2,
§5.3). A negative result here is a real result — say so and move on.

USAGE
    python eval_retriever.py --dump chunks_v2.txt \
        --questions questions_interim_v2.json \
        --source MTN-Uganda-H1-24-Interim-results.pdf \
        --models intfloat/e5-small-v2 BAAI/bge-small-en-v1.5
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import time
from datetime import datetime, timezone

import numpy as np

from retriever import BM25, HybridRetriever, SentenceTransformerEncoder, rrf_fuse

HEADER_RE = re.compile(
    r"^\[(\d+)\] source=(\S+) type=(\S+) page=(\d+) len=(\d+) tokens=(\d+)"
)
RULE = "-" * 78


def load_chunks(path: str, source: str | None) -> tuple[list[int], list[str], list[dict]]:
    """Parse the chunk dump. Returns (ids, texts, metas) in dump order."""
    ids: list[int] = []
    texts: list[str] = []
    metas: list[dict] = []

    cur_id: int | None = None
    cur_meta: dict = {}
    buf: list[str] = []
    in_body = False

    def flush() -> None:
        nonlocal cur_id, buf
        if cur_id is not None:
            ids.append(cur_id)
            texts.append("\n".join(buf).strip())
            metas.append(dict(cur_meta))
        cur_id, buf = None, []

    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = HEADER_RE.match(line)
        if m:
            flush()
            src = m.group(2)
            if source and src != source:
                cur_id = None
                in_body = False
                continue
            cur_id = int(m.group(1))
            cur_meta = {
                "source": src,
                "type": m.group(3),
                "page": int(m.group(4)),
                "tokens": int(m.group(6)),
            }
            in_body = False
            continue
        if cur_id is None:
            continue
        if line.startswith("---"):
            in_body = True
            continue
        if in_body:
            buf.append(line)

    flush()
    return ids, texts, metas


def grade(rankings: dict[str, list[int]], questions: list[dict], ks=(1, 3, 5, 10)) -> dict:
    """rankings: qid -> ranked list of ORIGINAL chunk ids."""
    recall = {k: 0 for k in ks}
    rr_total = 0.0
    per_stratum: dict[str, list[int]] = {}
    failures: list[tuple] = []

    for q in questions:
        gold = set(q["gold_chunks"])
        ranked = rankings[q["id"]]
        stratum = q.get("stratum", "?")

        rank = next((i for i, d in enumerate(ranked, 1) if d in gold), None)
        rr_total += (1.0 / rank) if rank else 0.0

        for k in ks:
            if rank and rank <= k:
                recall[k] += 1

        hit5 = bool(rank and rank <= 5)
        per_stratum.setdefault(stratum, []).append(int(hit5))
        if not hit5:
            failures.append((q["id"], stratum, rank or "miss", q["question"]))

    n = len(questions)
    return {
        "recall": {k: v / n for k, v in recall.items()},
        "mrr": rr_total / n,
        "strata": {s: sum(v) / len(v) for s, v in per_stratum.items()},
        "failures": failures,
    }


def _non_negative_everywhere(r: dict, bm: dict) -> bool:
    """True if a hybrid beats OR TIES BM25 on every metric (no regression)."""
    return all(r["recall"][k] >= bm["recall"][k] for k in bm["recall"]) and \
        r["mrr"] >= bm["mrr"]


def verdict_lines(results: dict) -> list[str]:
    """Render the verdict. SELECT the best hybrid by non-regression, then rank.

    SELECTION CRITERION (DECISION-002 §1, §2)
    -----------------------------------------
    A hybrid earns its RAM only if it does not make retrieval WORSE on any axis.
    So the candidate set is the hybrids that beat-or-tie BM25 on EVERY metric
    (R@1, R@3, R@5, R@10, MRR). Among those we take the best by Recall@1, then
    MRR — R@1 is the deploy-relevant metric (a higher top-1 hit rate means fewer
    chunks fed to the CPU-only LLM, i.e. less prefill latency and RAM).

    WHY NOT GATE ON R@5 (the defect this replaced)
    ----------------------------------------------
    An earlier verdict selected by R@5 and gated on it. On this corpus R@5 is a
    TIE at 89%, so the delta was 0 and it printed "Hybrid does NOT beat BM25" --
    while every hybrid beat BM25 on Recall@1 and MRR. The verdict contradicted
    its own table. (DECISION-002 §5.3.)

    If NO hybrid is non-negative everywhere, we fall back to the best by R@1 and
    say so plainly, so a real regression is never hidden.
    """
    out = ["=" * 78]
    bm = results["BM25 only"]
    hybrids = [(n, r) for n, r in results.items() if n.startswith("HYBRID")]
    if not hybrids:
        out.append("VERDICT: no dense model ran — BM25-only numbers above are the baseline.")
        out.append("=" * 78)
        return out

    clean = [(n, r) for n, r in hybrids if _non_negative_everywhere(r, bm)]
    pool = clean or hybrids
    name, r = max(pool, key=lambda kv: (kv[1]["recall"][1], kv[1]["mrr"]))

    d1 = r["recall"][1] - bm["recall"][1]
    d5 = r["recall"][5] - bm["recall"][5]
    dm = r["mrr"] - bm["mrr"]
    basis = "non-negative on every metric" if clean else "best R@1 — regresses elsewhere"
    out.append(f"VERDICT  best hybrid ({basis}): {name}")
    out.append(f"         R@1  {bm['recall'][1]:.0%} -> {r['recall'][1]:.0%}  ({d1:+.0%})")
    out.append(f"         R@5  {bm['recall'][5]:.0%} -> {r['recall'][5]:.0%}  ({d5:+.0%})")
    out.append(f"         MRR  {bm['mrr']:.3f} -> {r['mrr']:.3f}  ({dm:+.3f})")
    if clean and d1 > 0:
        out.append("         Beats BM25 on Recall@1 and never regresses. It earns its RAM.")
    elif clean:
        out.append("         Ties BM25 on Recall@1 and never regresses — marginal but safe.")
    elif d1 > 0:
        out.append("         Beats BM25 on Recall@1 but regresses on another metric —")
        out.append("         weigh the trade-off before shipping.")
    else:
        out.append("         Hybrid does NOT beat BM25 on Recall@1 on this corpus.")
        out.append("         A null result here is a verdict on THIS corpus, not on")
        out.append("         hybrid retrieval — re-run on a representative question set.")
    out.append("=" * 78)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--source", default=None)
    ap.add_argument("--models", nargs="*", default=[])
    ap.add_argument("--rrf-k", type=float, default=60.0)
    ap.add_argument("--top-k", type=int, default=10)
    args = ap.parse_args()

    ids, texts, metas = load_chunks(args.dump, args.source)
    if not texts:
        print(f"ERROR: no chunks parsed from {args.dump} (source filter: {args.source})",
              file=sys.stderr)
        return 1

    qdata = json.load(open(args.questions))
    questions = qdata["questions"]

    # FINGERPRINT GATE. Refuse to grade against a corpus the labels were not made
    # against. Chunk IDs are positional; if ingestion drifted, every gold label
    # now points at different text and every number below would be fiction.
    want = qdata.get("_meta", {}).get("corpus_fingerprint", "")
    have = ""
    for line in open(args.dump, encoding="utf-8"):
        if line.startswith("# corpus_fingerprint:"):
            have = line.split(":", 1)[1].strip()
            break
        if not line.startswith("#"):
            break
    if want and have and want != have:
        print(f"FATAL: corpus fingerprint mismatch.\n"
              f"       question set was labelled against : {want}\n"
              f"       this chunk dump is               : {have}\n"
              f"       Chunk IDs have shifted. Every gold label now points at the\n"
              f"       WRONG chunk and every metric would be fiction.\n"
              f"       Re-run autolabel.py against this dump.", file=sys.stderr)
        return 1
    if not want:
        print("[warn] question set has no corpus_fingerprint — cannot verify it "
              "matches this dump.", file=sys.stderr)

    # Guard: gold ids must exist in the index, or Recall@k is unmeasurable.
    idset = set(ids)
    bad = [q["id"] for q in questions if not set(q["gold_chunks"]) & idset]
    if bad:
        print(f"ERROR: gold chunk ids not present in index for: {bad}", file=sys.stderr)
        print("       Re-label the question set against this dump.", file=sys.stderr)
        return 1

    # GOLD-LABEL SANITY GATE.
    # The auto-relabeller matched on substrings that recur in page footers
    # (dates, "MTN Uganda"), marking 26-28 of 37 chunks as gold on four
    # questions. A question whose gold set is most of the corpus is
    # unmissable, silently inflating Recall@k for every retriever. Structural
    # checks cannot catch this -- the JSON is perfectly well-formed. Only a
    # semantic check on gold CARDINALITY can.
    ceiling = max(3, len(ids) // 5)
    smeared = [
        (q["id"], len(q["gold_chunks"]))
        for q in questions
        if len(q["gold_chunks"]) > ceiling
    ]
    if smeared:
        print(f"!! GOLD-LABEL WARNING: {len(smeared)} question(s) have > {ceiling} "
              f"gold chunks out of {len(ids)}.", file=sys.stderr)
        for qid, n_gold in smeared:
            print(f"     {qid}: {n_gold} gold chunks — near-unmissable, "
                  f"inflates Recall@k", file=sys.stderr)
        print("   These labels are almost certainly auto-relabeller artifacts. "
              "HAND-VERIFY before trusting any number below.\n", file=sys.stderr)

    pos2id = {i: cid for i, cid in enumerate(ids)}

    print("=" * 78)
    print("HYBRID RETRIEVER — does BM25 + dense beat BM25 alone?")
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC | python "
          f"{platform.python_version()} | {platform.system()} {platform.machine()}")
    print(f"corpus: {len(texts)} chunks | questions: {len(questions)} | RRF k={args.rrf_k}")
    print("=" * 78)
    print()

    results: dict[str, dict] = {}
    latency: dict[str, float] = {}

    # --- BM25 alone (the incumbent, and the bar to beat) ---
    r_bm = HybridRetriever(texts, encoder=None)
    t0 = time.perf_counter()
    rk = {q["id"]: [pos2id[h.chunk_id] for h in r_bm.search(q["question"], args.top_k)]
          for q in questions}
    latency["BM25 only"] = (time.perf_counter() - t0) / len(questions) * 1000
    results["BM25 only"] = grade(rk, questions)

    for model in args.models:
        try:
            enc = SentenceTransformerEncoder(model)
        except Exception as e:  # noqa: BLE001
            print(f"  [skip] {model}: {e}", file=sys.stderr)
            continue

        short = model.split("/")[-1]

        # --- dense alone ---
        r_dn = HybridRetriever(texts, encoder=enc)
        dense_only: dict[str, list[int]] = {}
        hybrid: dict[str, list[int]] = {}

        t0 = time.perf_counter()
        for q in questions:
            dn = r_dn._dense_ranking(q["question"], r_dn.candidate_depth)
            dense_only[q["id"]] = [pos2id[d] for d in dn[: args.top_k]]
        latency[f"dense: {short}"] = (time.perf_counter() - t0) / len(questions) * 1000
        results[f"dense: {short}"] = grade(dense_only, questions)

        # --- hybrid ---
        t0 = time.perf_counter()
        for q in questions:
            hits = r_dn.search(q["question"], args.top_k)
            hybrid[q["id"]] = [pos2id[h.chunk_id] for h in hits]
        latency[f"HYBRID: BM25+{short}"] = (time.perf_counter() - t0) / len(questions) * 1000
        results[f"HYBRID: BM25+{short}"] = grade(hybrid, questions)

    # --- report ---
    print(f"{'RETRIEVER':<38}{'R@1':>6}{'R@3':>6}{'R@5':>6}{'R@10':>6}{'MRR':>8}{'ms/q':>8}")
    print(RULE)
    for name, r in results.items():
        rc = r["recall"]
        print(f"{name:<38}{rc[1]:>5.0%}{rc[3]:>6.0%}{rc[5]:>6.0%}{rc[10]:>6.0%}"
              f"{r['mrr']:>8.3f}{latency[name]:>8.1f}")

    strata = sorted({s for r in results.values() for s in r["strata"]})
    print()
    print(f"{'PER-STRATUM RECALL@5':<38}" + "".join(f"{s[:9]:>11}" for s in strata))
    print(RULE)
    for name, r in results.items():
        row = "".join(f"{r['strata'].get(s, float('nan')):>10.0%} " for s in strata)
        print(f"{name:<38}{row}")

    print()
    print("FAILURES (gold chunk NOT in top-5)")
    print(RULE)
    for name, r in results.items():
        if not r["failures"]:
            print(f"\n  {name}\n    (none)")
            continue
        print(f"\n  {name}")
        for qid, stratum, rank, qt in r["failures"]:
            print(f"    {qid} [{stratum:<11}] rank {str(rank):<6} {qt[:44]}")

    # --- the verdict, stated so it can be negative ---
    print()
    for line in verdict_lines(results):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
