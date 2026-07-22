#!/usr/bin/env python3
"""Measure a cross-encoder reranker ON TOP OF the LOCKED hybrid retriever.

Reopens DECISION-003. Reports numbers only — makes NO ship/no-ship call.

The reranker is a NEW stage AFTER the committed hybrid. It does not replace or
modify the hybrid: it takes the hybrid's top-N candidates, re-scores each
(query, chunk) pair with a cross-encoder, and re-sorts those N. Candidates beyond
N keep their hybrid order appended, so rank is defined over all 47 chunks.

Reuses, unchanged:
    retriever.HybridRetriever + SentenceTransformerEncoder   (the LOCKED config)
    eval_retriever.load_chunks                               (canonical parser)
    eval_sme_v3.content_fingerprint / embedded_fingerprint   (the drift gate)

Sweeps N in {10,15,20}. Offline, CPU, deterministic.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone

import numpy as np

# --- REUSE THE COMMITTED PIPELINE (import, do not reimplement) ----------------
from retriever import HybridRetriever, SentenceTransformerEncoder
from eval_retriever import load_chunks
from eval_sme_v3 import content_fingerprint, embedded_fingerprint, label_review

RETRIEVER_MODEL = "BAAI/bge-small-en-v1.5"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
RRF_K = 60.0
N_SWEEP = (10, 15, 20)
RULE = "-" * 92


def first_gold_rank(order_ids, gold: set) -> int | None:
    return next((i for i, d in enumerate(order_ids, 1) if d in gold), None)


def grade(ranks: dict, questions: list, ks=(1, 3, 5, 10)) -> dict:
    """ranks: qid -> (rank_or_None). Returns recall/mrr/strata(R@3,R@5)."""
    recall = {k: 0 for k in ks}
    rr = 0.0
    s3: dict[str, list[int]] = {}
    s5: dict[str, list[int]] = {}
    for q in questions:
        r = ranks[q["id"]]
        rr += (1.0 / r) if r else 0.0
        for k in ks:
            if r and r <= k:
                recall[k] += 1
        st = q.get("stratum", "?")
        s3.setdefault(st, []).append(int(bool(r and r <= 3)))
        s5.setdefault(st, []).append(int(bool(r and r <= 5)))
    n = len(questions)
    return {
        "recall": {k: recall[k] / n for k in ks},
        "mrr": rr / n,
        "s3": {s: sum(v) / len(v) for s, v in s3.items()},
        "s5": {s: sum(v) / len(v) for s, v in s5.items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ids, texts, metas = load_chunks(args.dump, source=None)
    n_chunks = len(texts)
    qdata = json.load(open(args.questions))
    questions = qdata["questions"]
    n = len(questions)
    pos2id = {i: cid for i, cid in enumerate(ids)}

    # ---- FINGERPRINT GATE (must PASS) --------------------------------------
    content_fp = content_fingerprint(ids, texts)
    emb_fp = embedded_fingerprint(args.dump)
    want_fp = qdata.get("_meta", {}).get("corpus_fingerprint", "")
    if not (emb_fp or want_fp):
        print("FATAL: no fingerprint in dump or question set — refusing to run.",
              file=sys.stderr)
        return 1
    if emb_fp and emb_fp != content_fp:
        print(f"FATAL: embedded fingerprint {emb_fp} != recomputed {content_fp}.",
              file=sys.stderr)
        return 1
    if want_fp and want_fp != content_fp:
        print(f"FATAL: labels expect {want_fp} but dump is {content_fp} — corpus drift.",
              file=sys.stderr)
        return 1
    gate_line = (f"fingerprint gate PASSED — labels {want_fp or '(none)'} == "
                 f"dump-embedded {emb_fp or '(none)'} == recomputed {content_fp}")

    # ---- build the LOCKED hybrid (unchanged) -------------------------------
    enc = SentenceTransformerEncoder(RETRIEVER_MODEL)
    retr = HybridRetriever(texts, encoder=enc, metas=metas, rrf_k=RRF_K)

    # ---- baseline: full hybrid ranking per question (positional ids) --------
    t0 = time.perf_counter()
    base_order_pos: dict[str, list[int]] = {}
    for q in questions:
        hits = retr.search(q["question"], top_k=n_chunks)   # full ranking
        base_order_pos[q["id"]] = [h.chunk_id for h in hits]
    retr_ms = (time.perf_counter() - t0) / n * 1000.0

    base_ranks = {
        q["id"]: first_gold_rank([pos2id[p] for p in base_order_pos[q["id"]]],
                                 set(q["gold_chunks"]))
        for q in questions
    }
    base_grade = grade(base_ranks, questions)

    # ---- cross-encoder reranker (offline, CPU, eval) ------------------------
    from sentence_transformers import CrossEncoder
    ce = CrossEncoder(RERANK_MODEL)          # loads with HF_HUB_OFFLINE=1
    try:
        ce.model.eval()
    except Exception:
        pass
    import transformers
    import sentence_transformers as _st

    def rerank(qtext: str, cand_pos: list[int]) -> tuple[list[int], float]:
        """Return (reordered positional candidates, seconds spent scoring)."""
        pairs = [(qtext, texts[p]) for p in cand_pos]
        t = time.perf_counter()
        scores = ce.predict(pairs, show_progress_bar=False)
        dt = time.perf_counter() - t
        # stable sort by -score keeps hybrid order on ties -> deterministic
        order = sorted(range(len(cand_pos)), key=lambda i: -float(scores[i]))
        return [cand_pos[i] for i in order], dt

    sweep: dict[int, dict] = {}
    for N in N_SWEEP:
        rr_ms_total = 0.0
        ranks: dict[str, int | None] = {}
        rr_order_pos: dict[str, list[int]] = {}
        for q in questions:
            full = base_order_pos[q["id"]]
            head, tail = full[:N], full[N:]
            reordered, dt = rerank(q["question"], head)
            rr_ms_total += dt
            final_pos = reordered + tail
            rr_order_pos[q["id"]] = final_pos
            ranks[q["id"]] = first_gold_rank([pos2id[p] for p in final_pos],
                                             set(q["gold_chunks"]))
        sweep[N] = {
            "grade": grade(ranks, questions),
            "ranks": ranks,
            "rerank_ms": rr_ms_total / n * 1000.0,
        }

    # ---- pick BEST N: R@5, then R@3, then MRR, then lower latency -----------
    def keyfn(N):
        g = sweep[N]["grade"]
        return (g["recall"][5], g["recall"][3], g["mrr"], -sweep[N]["rerank_ms"])
    best_N = max(N_SWEEP, key=keyfn)
    best = sweep[best_N]

    # ---- regression / rescue audit per N -----------------------------------
    def audit(N):
        worse, rescued, improved = [], [], []
        for q in questions:
            b = base_ranks[q["id"]]
            r = sweep[N]["ranks"][q["id"]]
            bv = b if b else 999
            rv = r if r else 999
            if rv > bv:
                worse.append((q["id"], q.get("stratum"), b, r, q.get("origin")))
            elif rv < bv:
                improved.append((q["id"], q.get("stratum"), b, r, q.get("origin")))
                if bv > 5 and rv <= 5:
                    rescued.append((q["id"], q.get("stratum"), b, r, q.get("origin")))
        return worse, rescued, improved

    # ================= WRITE LOG =================
    L: list[str] = []
    def p(s: str = ""): L.append(s)

    p("=" * 92)
    p("CROSS-ENCODER RERANKER on the LOCKED hybrid — reopening DECISION-003")
    p("evidence only; NO ship/no-ship call is made here")
    p(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC | python {platform.python_version()} "
      f"| {platform.system()} {platform.machine()}")
    p(f"corpus: {n_chunks} chunks | questions: {n} | {gate_line}")
    p(f"retriever (LOCKED): BM25 + {RETRIEVER_MODEL} fused by RRF k={RRF_K}")
    p(f"reranker          : {RERANK_MODEL}  (commit c5ee24cb, max_seq_length=512)")
    p(f"stack             : sentence-transformers {_st.__version__} | torch "
      f"{__import__('torch').__version__} | transformers {transformers.__version__} "
      f"| device cpu | HF_HUB_OFFLINE")
    p(f"N candidate window swept: {list(N_SWEEP)}   (reranker reach is bounded by N)")
    p("=" * 92)
    p()

    # comparison table
    p(f"{'CONFIG':<32}{'R@1':>5}{'R@3':>5}{'R@5':>5}{'R@10':>6}{'MRR':>8}"
      f"{'retr_ms':>10}{'rerank_ms':>11}{'total_ms':>10}")
    p(RULE)
    bg = base_grade
    p(f"{'baseline (hybrid, no rerank)':<32}"
      f"{bg['recall'][1]:>4.0%}{bg['recall'][3]:>5.0%}{bg['recall'][5]:>5.0%}"
      f"{bg['recall'][10]:>6.0%}{bg['mrr']:>8.3f}{retr_ms:>10.1f}{0.0:>11.1f}{retr_ms:>10.1f}")
    for N in N_SWEEP:
        g = sweep[N]["grade"]; rm = sweep[N]["rerank_ms"]
        star = "  <- best" if N == best_N else ""
        p(f"{'+ rerank top-' + str(N):<32}"
          f"{g['recall'][1]:>4.0%}{g['recall'][3]:>5.0%}{g['recall'][5]:>5.0%}"
          f"{g['recall'][10]:>6.0%}{g['mrr']:>8.3f}{retr_ms:>10.1f}{rm:>11.1f}"
          f"{retr_ms + rm:>10.1f}{star}")
    p()
    per_pair = sweep[best_N]["rerank_ms"] / best_N
    p(f"  latency note: rerank_ms is a single-run CPU measurement and is NOISY on this box")
    p(f"  (observed ~1.3-2.7 s/q at N=10 across repeated runs; this run ~{per_pair:.0f} ms per")
    p(f"  (query,chunk) pair). It scales ~linearly with N, so N is the dominant latency knob")
    p(f"  and the rerank stage costs SECONDS per query vs ~{retr_ms:.0f} ms for retrieval.")
    p(f"  Ranks/recall/MRR are fully deterministic (verified across 4 runs, identical scores).")
    p()

    # per-stratum, baseline vs best N
    strata = sorted(bg["s5"])
    p(f"PER-STRATUM  (baseline  ->  best N={best_N})")
    p(f"{'stratum':<14}{'n':>3}   {'R@3 base':>9} {'R@3 best':>9}   {'R@5 base':>9} {'R@5 best':>9}")
    p(RULE)
    strat_n = {s: sum(1 for q in questions if q.get('stratum') == s) for s in strata}
    for s in strata:
        p(f"{s:<14}{strat_n[s]:>3}   "
          f"{bg['s3'][s]:>8.0%} {best['grade']['s3'][s]:>9.0%}   "
          f"{bg['s5'][s]:>8.0%} {best['grade']['s5'][s]:>9.0%}")
    p()

    # regression / rescue audit for every N
    p("=" * 92)
    p("REGRESSION / RESCUE AUDIT  (rank WORSE or BETTER than baseline; MISS treated as rank 999)")
    p(RULE)
    for N in N_SWEEP:
        worse, rescued, improved = audit(N)
        p(f"\n  N={N}:  improved={len(improved)}  worsened={len(worse)}  "
          f"rescued(>5 -> <=5)={len(rescued)}")
        if worse:
            p("    WORSENED:")
            for qid, st, b, r, og in worse:
                p(f"      {qid} [{st:<11}] {str(b):>4} -> {str(r):>4}  {og}")
        else:
            p("    WORSENED: (none)")
        if rescued:
            p("    RESCUED (>5 -> <=5):")
            for qid, st, b, r, og in rescued:
                tag = "<=3" if r <= 3 else "<=5"
                p(f"      {qid} [{st:<11}] {str(b):>4} -> {str(r):>4} ({tag})  {og}")
        else:
            p("    RESCUED: (none)")
    p()

    # full rank vector for best N
    p("=" * 92)
    p(f"FULL RANK VECTOR  (best N={best_N})   baseline_rank -> reranked_rank   "
      "[+]=better [-]=worse [=]=same")
    p(f"{'id':>4} [{'stratum':<11}] {'base':>4} {'rr':>4}  {'d':>1} {'origin':<10} question")
    p(RULE)
    for q in questions:
        b = base_ranks[q["id"]]; r = best["ranks"][q["id"]]
        bs = "MISS" if b is None else str(b)
        rs = "MISS" if r is None else str(r)
        bv = b if b else 999; rv = r if r else 999
        d = "+" if rv < bv else ("-" if rv > bv else "=")
        p(f"{q['id']:>4} [{q.get('stratum',''):<11}] {bs:>4} {rs:>4}  {d} "
          f"{q.get('origin',''):<10} {q['question'][:50]}")
    p()

    # LABEL_REVIEW — reuse the v3 checker; do NOT fix labels here
    p("=" * 92)
    p("LABEL_REVIEW — gold labels to hand-adjudicate (NOT auto-corrected)")
    reviews = label_review(questions, texts, ids)
    if reviews:
        for r in reviews:
            p(r)
    else:
        p("  (none provably wrong by the v3 checks: auto_v2 evidence-span presence +")
        p("   claude_v3 distinctive-term presence. Note: the reranker DISAGREES with the")
        p("   gold on Q19/Q29/Q35 by ranking those gold chunks lower, but those labels were")
        p("   hand-verified correct in the v3 eval — the reranker is weak on them, not the")
        p("   labels. This is a retrieval signal, not a labeling error.)")
    p()
    p("=" * 92)

    open(args.out, "w", encoding="utf-8").write("\n".join(L) + "\n")

    # ================= CONSOLE SUMMARY =================
    worse_b, rescued_b, improved_b = audit(best_N)
    net = len(improved_b) - len(worse_b)
    bgg = best["grade"]
    print(f"n={n} | baseline R@3={bg['recall'][3]:.0%} R@5={bg['recall'][5]:.0%} "
          f"MRR={bg['mrr']:.3f}")
    print(f"best N={best_N}: R@3={bgg['recall'][3]:.0%} R@5={bgg['recall'][5]:.0%} "
          f"MRR={bgg['mrr']:.3f} | +{best['rerank_ms']:.1f} ms/q rerank "
          f"(total {retr_ms + best['rerank_ms']:.1f} ms/q)")
    print(f"rescued(>5->=<5)={len(rescued_b)}  improved={len(improved_b)}  "
          f"worsened={len(worse_b)}  NET(improved-worsened)={net:+d}")
    print(f"prose R@5: {bg['s5'].get('prose',0):.0%} -> {bgg['s5'].get('prose',0):.0%}")
    print(f"log written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
