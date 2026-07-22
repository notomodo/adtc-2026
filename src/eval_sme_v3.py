#!/usr/bin/env python3
"""Run the LOCKED retriever (BM25 + bge-small-en-v1.5 fused by RRF k=60) over the
expanded 35-question set (questions_sme_v3.json).

Reuses the COMMITTED pipeline — it does NOT reimplement it:
    * retriever.HybridRetriever + retriever.SentenceTransformerEncoder  (locked config)
    * eval_retriever.load_chunks                                        (canonical dump parser)

Produces the full Recall@k curve, per-stratum R@3/R@5, a full 35-question rank
vector, and the k=3-vs-k=5 stress test. Output format mirrors eval_sme_output.log
so the numbers are directly comparable, but for the LOCKED config only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone

# --- REUSE THE REAL, COMMITTED CODE (import, do not reimplement) -------------
from retriever import HybridRetriever, SentenceTransformerEncoder
from eval_retriever import load_chunks

MODEL = "BAAI/bge-small-en-v1.5"
RRF_K = 60.0
RULE = "-" * 78

_NORM_RE = re.compile(r"[^a-z0-9]+")
_WORD_RE = re.compile(r"[a-z0-9]+")


def norm(s: str) -> str:
    return _NORM_RE.sub(" ", s.lower()).strip()


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def content_fingerprint(ids: list[int], texts: list[str]) -> str:
    """The canonical fingerprint ingest_sme.py defines: sha256 over (pos, text)
    pairs, first 16 hex. Reconstructed from the PARSED dump so it is stable for
    anyone re-parsing this dump the same way."""
    joined = "\n".join(f"{i}\x00{t}" for i, t in enumerate(texts))
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


def embedded_fingerprint(dump_path: str) -> str:
    for line in open(dump_path, encoding="utf-8"):
        if line.startswith("# corpus_fingerprint:"):
            return line.split(":", 1)[1].strip()
        if not line.startswith("#"):
            break
    return ""


def label_review(questions: list[dict], texts: list[str], ids: list[int]) -> list[str]:
    """Surface — not fix — gold labels that look wrong against the chunk dump.
    Two concrete, conservative checks. Everything flagged is for HUMAN adjudication."""
    id2pos = {cid: i for i, cid in enumerate(ids)}
    norm_chunks = [norm(t) for t in texts]
    tok_chunks = [set(_WORD_RE.findall(nc)) for nc in norm_chunks]

    # document frequency, to find "distinctive" (rare) answer tokens
    df: Counter[str] = Counter()
    for tc in tok_chunks:
        df.update(tc)
    n_chunks = len(texts)

    out: list[str] = []
    for q in questions:
        gold = q["gold_chunks"]
        gold_pos = [id2pos[g] for g in gold if g in id2pos]
        gold_norm = " ".join(norm_chunks[p] for p in gold_pos)
        gold_tok = set().union(*[tok_chunks[p] for p in gold_pos]) if gold_pos else set()

        ev = q.get("_evidence", {})
        matched = ev.get("matched", "")
        if matched:
            # auto_v2 claims a VERBATIM/ANCHOR span. It MUST appear in the gold chunk.
            if norm(matched) not in gold_norm:
                out.append(
                    f"  {q['id']} [{q['stratum']:<11}] origin={q.get('origin','')}: "
                    f"claimed {ev.get('tier','?')} span not found in gold chunk(s) {gold} — "
                    f"\"{matched[:48]}\"")
            continue

        # claude_v3 (unverified): check the gold chunk carries the answer's
        # distinctive terms. Distinctive = length>=4 and in <=30% of chunks.
        ans_tok = [
            w for w in _WORD_RE.findall(norm(q.get("answer", "")))
            if len(w) >= 4 and df.get(w, 0) <= max(3, int(0.30 * n_chunks))
        ]
        if not ans_tok:
            continue
        gold_hits = sum(1 for w in set(ans_tok) if w in gold_tok)
        best_other = max(
            (sum(1 for w in set(ans_tok) if w in tok_chunks[p]), ids[p])
            for p in range(n_chunks) if p not in gold_pos
        )
        # Flag only when gold carries NONE of the distinctive answer terms yet
        # some other chunk carries >=2 of them: a concrete "points at wrong chunk" signal.
        if gold_hits == 0 and best_other[0] >= 2:
            out.append(
                f"  {q['id']} [{q['stratum']:<11}] origin={q.get('origin','')}: "
                f"gold {gold} carries 0/{len(set(ans_tok))} distinctive answer terms; "
                f"chunk [{best_other[1]}] carries {best_other[0]} — verify label")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--reference-dump", default=None,
                    help="source-of-truth dump for the byte-identity fallback gate "
                         "(only needed when no fingerprint is stored in dump/questions)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # ---- parse corpus (canonical parser, no source filter -> all chunks) ----
    ids, texts, metas = load_chunks(args.dump, source=None)
    n_chunks = len(texts)
    if not texts:
        print(f"FATAL: no chunks parsed from {args.dump}", file=sys.stderr)
        return 1

    qdata = json.load(open(args.questions))
    questions = qdata["questions"]
    n = len(questions)

    # ---- FINGERPRINT / CORPUS-DRIFT GATE (FATAL on mismatch) ----------------
    # Two modes, auto-selected:
    #   (A) fingerprint  — the shipped gate. Used when the dump carries an embedded
    #       '# corpus_fingerprint:' line and/or the question set carries
    #       _meta.corpus_fingerprint. Verifies dump<->labels<->recomputed all agree.
    #   (B) byte-identity — fallback when NO fingerprint is stored anywhere (the
    #       legacy artifacts). Requires --reference-dump and enforces the dump is
    #       byte-for-byte the source-of-truth the gold labels were built against.
    work_sha = file_sha256(args.dump)
    content_fp = content_fingerprint(ids, texts)         # canonical, over parsed (id,text)
    emb_fp = embedded_fingerprint(args.dump)             # from '# corpus_fingerprint:' line
    want_fp = qdata.get("_meta", {}).get("corpus_fingerprint", "")

    if emb_fp or want_fp:
        gate_mode = "fingerprint"
        if emb_fp and emb_fp != content_fp:
            print(f"FATAL: embedded corpus_fingerprint {emb_fp} != recomputed {content_fp}. "
                  "Dump was tampered post-ingest. Aborting.", file=sys.stderr)
            return 1
        if want_fp and want_fp != content_fp:
            print("FATAL: corpus fingerprint mismatch — the gold labels were built "
                  "against a DIFFERENT corpus than this dump.\n"
                  f"       labels expect : {want_fp}\n"
                  f"       this dump is  : {content_fp}\n"
                  "       Chunk IDs have shifted; every gold label points at the WRONG\n"
                  "       chunk and every number below would be fiction. Aborting.",
                  file=sys.stderr)
            return 1
        gate_desc = (f"fingerprint gate PASSED — labels {want_fp or '(none)'} == "
                     f"dump-embedded {emb_fp or '(none)'} == recomputed {content_fp}")
    else:
        gate_mode = "byte-identity"
        if not args.reference_dump:
            print("FATAL: no fingerprint stored in dump or question set, and no "
                  "--reference-dump given. Cannot verify the corpus has not drifted. "
                  "Aborting.", file=sys.stderr)
            return 1
        ref_sha = file_sha256(args.reference_dump)
        if work_sha != ref_sha:
            print("FATAL: corpus drift — working chunk dump does NOT match the "
                  "source-of-truth dump the gold labels were built against.\n"
                  f"       working    : {work_sha}\n"
                  f"       reference  : {ref_sha}\n"
                  "       Chunk IDs are positional; every gold label would point at the\n"
                  "       WRONG chunk and every number below would be fiction. Aborting.",
                  file=sys.stderr)
            return 1
        gate_desc = (f"byte-identity gate PASSED — dump sha256 == source-of-truth dump "
                     f"({work_sha[:16]}…); no embedded fingerprint present")

    # gold ids must exist in the index
    idset = set(ids)
    bad = [q["id"] for q in questions if not set(q["gold_chunks"]) & idset]
    if bad:
        print(f"FATAL: gold chunk ids absent from index for {bad}", file=sys.stderr)
        return 1

    pos2id = {i: cid for i, cid in enumerate(ids)}

    # ---- build the LOCKED retriever (encodes docs once) --------------------
    enc = SentenceTransformerEncoder(MODEL)
    retr = HybridRetriever(texts, encoder=enc, metas=metas, rrf_k=RRF_K)

    # ---- rank every question over the FULL corpus --------------------------
    ks = (1, 3, 5, 10)
    recall = {k: 0 for k in ks}
    rr_total = 0.0
    rows = []                       # (id, stratum, rank_or_None, origin, question, gold_in_top5, n_gold)
    per_stratum: dict[str, list[int]] = {}      # hit@3
    per_stratum5: dict[str, list[int]] = {}     # hit@5

    t0 = time.perf_counter()
    for q in questions:
        gold = set(q["gold_chunks"])
        hits = retr.search(q["question"], top_k=n_chunks)        # FULL ranking
        ranked_ids = [pos2id[h.chunk_id] for h in hits]
        rank = next((i for i, d in enumerate(ranked_ids, 1) if d in gold), None)
        gold_in_top5 = sum(1 for d in ranked_ids[:5] if d in gold)
        rows.append((q["id"], q.get("stratum", "?"), rank, q.get("origin", ""),
                     q["question"], gold_in_top5, len(gold)))
    elapsed_ms = (time.perf_counter() - t0) / n * 1000.0

    for (_id, stratum, rank, *_), q in zip(rows, questions):
        rr_total += (1.0 / rank) if rank else 0.0
        for k in ks:
            if rank and rank <= k:
                recall[k] += 1
        per_stratum.setdefault(stratum, []).append(int(bool(rank and rank <= 3)))
        per_stratum5.setdefault(stratum, []).append(int(bool(rank and rank <= 5)))

    mrr = rr_total / n
    strata = sorted(per_stratum)

    # k=3 stress test
    lost_by_k3 = [(r[0], r[1], r[2], r[3]) for r in rows if r[2] in (4, 5)]
    miss_at_5 = [(r[0], r[1], r[3]) for r in rows if (r[2] is None or r[2] > 5)]

    reviews = label_review(questions, texts, ids)

    # ---- write the log -----------------------------------------------------
    L: list[str] = []
    def p(s: str = "") -> None:
        L.append(s)

    p("=" * 78)
    p("LOCKED RETRIEVER — BM25 + bge-small-en-v1.5 fused by RRF (k=60)")
    p("expanded SME question set v3 (19 auto_v2 + 16 claude_v3, hand-grounded)")
    p(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC | python {platform.python_version()} "
      f"| {platform.system()} {platform.machine()}")
    p(f"corpus: {n_chunks} chunks | questions: {n} | RRF k={RRF_K}")
    p(f"corpus fingerprint (sha256, full file) : {work_sha}")
    p(f"corpus fingerprint (canonical, id+text): {content_fp}")
    p(f"drift gate [{gate_mode}]: {gate_desc}")
    import sentence_transformers as _st
    import torch as _torch
    p(f"config stamp: sentence-transformers {_st.__version__} | torch {_torch.__version__} "
      f"| device cpu | HF_HUB_OFFLINE")
    p("=" * 78)
    p()

    # Recall table (locked config only)
    p(f"{'RETRIEVER':<38}{'R@1':>6}{'R@3':>6}{'R@5':>6}{'R@10':>6}{'MRR':>8}{'ms/q':>8}")
    p(RULE)
    p(f"{'HYBRID: BM25+bge-small-en-v1.5':<38}"
      f"{recall[1]/n:>5.0%}{recall[3]/n:>6.0%}{recall[5]/n:>6.0%}{recall[10]/n:>6.0%}"
      f"{mrr:>8.3f}{elapsed_ms:>8.1f}")
    p()

    # Per-stratum R@3 and R@5
    p(f"{'PER-STRATUM RECALL@3':<38}" + "".join(f"{s[:9]:>11}" for s in strata))
    p(RULE)
    row3 = "".join(f"{sum(per_stratum[s])/len(per_stratum[s]):>10.0%} " for s in strata)
    p(f"{'HYBRID: BM25+bge-small-en-v1.5':<38}{row3}")
    p()
    p(f"{'PER-STRATUM RECALL@5':<38}" + "".join(f"{s[:9]:>11}" for s in strata))
    p(RULE)
    row5 = "".join(f"{sum(per_stratum5[s])/len(per_stratum5[s]):>10.0%} " for s in strata)
    p(f"{'HYBRID: BM25+bge-small-en-v1.5':<38}{row5}")
    p()
    p("  (per-stratum n: " + ", ".join(f"{s}={len(per_stratum[s])}" for s in strata) + ")")
    p()

    # Full rank vector — ALL 35
    p("FULL RANK VECTOR  (rank = 1-based position of FIRST gold chunk in the full ranking)")
    p(f"{'id':>4} [{'stratum':<11}] {'rank':>5} {'origin':<10} {'g@5':>4}  question")
    p(RULE)
    for _id, stratum, rank, origin, qt, g5, ng in rows:
        rr = "MISS" if rank is None else str(rank)
        g5col = f"{g5}/{ng}" if ng > 1 else "-"
        p(f"{_id:>4} [{stratum:<11}] {rr:>5} {origin:<10} {g5col:>4}  {qt[:52]}")
    p()

    # k=3 stress test
    p("=" * 78)
    p(f"k=3 STRESS TEST — questions PRESENT at k=5 but LOST at k=3 (rank 4 or 5): {len(lost_by_k3)}")
    p("  (this is the exact recall cost of choosing k=3 over k=5)")
    p(RULE)
    if lost_by_k3:
        for _id, stratum, rank, origin in lost_by_k3:
            p(f"  {_id} [{stratum:<11}] rank {rank}  origin={origin}")
    else:
        p("  (none — no gold chunk sits at rank 4 or 5)")
    p()
    p(f"already MISS at k=5 (k=3 costs nothing extra on these): {len(miss_at_5)}")
    for _id, stratum, origin in miss_at_5:
        p(f"  {_id} [{stratum:<11}] origin={origin}")
    p()

    # LABEL REVIEW
    p("=" * 78)
    p("LABEL_REVIEW — gold labels to hand-adjudicate (NOT auto-corrected)")
    p("  claude_v3 labels are flagged single_annotator_unverified by design.")
    p(RULE)
    if reviews:
        for r in reviews:
            p(r)
    else:
        p("  (no gold label is provably wrong against chunks_sme.txt by the checks run:")
        p("   auto_v2 evidence-span presence + claude_v3 distinctive-term presence)")
    p()
    p("=" * 78)

    text = "\n".join(L) + "\n"
    open(args.out, "w", encoding="utf-8").write(text)

    # ---- console summary ---------------------------------------------------
    new_lost = [x for x in lost_by_k3 if x[3] == "claude_v3"]
    print(f"n={n}  |  R@1={recall[1]/n:.0%}  R@3={recall[3]/n:.0%}  R@5={recall[5]/n:.0%}  "
          f"R@10={recall[10]/n:.0%}  |  MRR={mrr:.3f}  |  {elapsed_ms:.1f} ms/q")
    print(f"k=3 vs k=5: {len(lost_by_k3)} question(s) lost by choosing k=3 "
          f"({len(new_lost)} of them origin=claude_v3)")
    if lost_by_k3:
        print("   lost: " + ", ".join(f"{i}(r{r})" for i, _s, r, _o in lost_by_k3))
    print(f"MISS at k=5: {len(miss_at_5)}  ->  " +
          (", ".join(i for i, _s, _o in miss_at_5) or "none"))
    print(f"LABEL_REVIEW flags: {len(reviews)}")
    print(f"log written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
