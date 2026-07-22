# ADTC 2026 — Cross-Encoder Reranker on the v3 (35-question) SME Set

**Date:** 2026-07-16
**Author:** Claude Code (automated run)
**Status:** complete — ranks reproduced identically across 4 runs; fingerprint gate passed.
**Decision made here:** NONE. This reopens DECISION-003 with evidence only; the ship/no-ship
call is left to a human.

Hand-off reference. States exactly what was run, the assumptions, packages+versions,
results, and observations. Safe to pass to Claude chat. Reads alongside the baseline
report `REPORT.md` (the v3 locked-retriever eval).

---

## 1. One-paragraph summary

A cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L6-v2`) was added as a **new stage
after** the LOCKED hybrid retriever (BM25 + bge-small-en-v1.5 + RRF k=60) — the hybrid was
not modified. For each question the hybrid's top-N candidates are re-scored pairwise by the
cross-encoder and re-sorted; N was swept over {10, 15, 20}. **Best config is N=10:** it lifts
**R@5 83%→89%, R@3 80%→86%, MRR 0.704→0.783**, and specifically **prose R@5 62%→75%** and
**multi_chunk R@5 80%→100%**. The cost: **~1.3–2.7 seconds of added CPU latency per query**
(vs ~86 ms for retrieval), and it **demotes two previously-correct hits** (Q31 near_miss
1→4, Q27 paraphrase 8→10). Enlarging N to 15/20 buys **zero** extra recall while adding more
latency and more regressions. The tradeoff — a real prose/recall gain against a 25–50×
latency hit and two regressions — is the decision to be weighed; this report does not weigh it.

---

## 2. Hypothesis under test (falsifiable) and verdict

The task posed a falsifiable prediction about the six baseline misses (ranks 8,8,10,12,13,20):
a reranker can only reorder what N retrieves, so its reach is bounded by N — **"N=10 reaches
2 misses, N=15 reaches 4, N=20 reaches all 6, but reaching ≠ lifting."**

**Verdict: confirmed, and the "reaching ≠ lifting" half is the important result.**
- N=10 (reaches the two rank-≤10 misses Q22@10, Q32@8): **both rescued** → 2/2 lifted.
- N=15/20 additionally *reach* the deep prose misses Q19@12, Q35@13, Q29@20 — but the
  cross-encoder scores those gold chunks **lower, not higher**: Q19 12→14→19, Q35 13→14→17,
  Q29 stays 20. **Reached but not lifted — in fact pushed further down.**
- Net: expanding the window past 10 recovers **nothing** and regresses several items. The
  reranker's usefulness here is entirely within the top-10.

Practical implication: the deep prose misses are not a "reranker can fix if we widen N"
problem. The cross-encoder actively disagrees with those gold chunks (see §7).

---

## 3. What was tested (scope) and NOT tested

**Tested:** the LOCKED hybrid (unchanged) + a rerank stage, N ∈ {10,15,20}, all 35 v3
questions, offline, CPU. Baseline (no rerank) is included in every table as the comparison.

**Method (exactly):** for each question, take the hybrid's **full** 47-chunk ranking, slice
the top-N, score each `(query, chunk_text)` pair with the cross-encoder, re-sort those N by
score (stable sort — ties keep hybrid order). Candidates beyond N keep their hybrid order and
are appended, so *rank is defined over all 47 chunks*. `rank` = 1-based position of the first
gold chunk in the final reordered list. Metric definitions (R@1/3/5/10, MRR, per-stratum
R@3/R@5) are **identical to `eval_sme_v3.py`**, so numbers are directly comparable to the
baseline report.

**NOT done (guard-rails honored):** did not tune the cross-encoder, change chunking, or alter
the hybrid; did not modify the question set or gold labels; did not touch DECISION-003; did
not make the ship decision; did not commit anything. The reranker is strictly additive.

---

## 4. Results

### 4.1 Comparison table (n=35)

| CONFIG | R@1 | R@3 | R@5 | R@10 | MRR | retr_ms | rerank_ms | total_ms |
|---|---|---|---|---|---|---|---|---|
| baseline (hybrid, no rerank) | 60% | 80% | 83% | 91% | 0.704 | ~86 | 0 | ~86 |
| **+ rerank top-10** ◀ best | **69%** | **86%** | **89%** | 91% | **0.783** | ~86 | ~1300–2700 | ~1.4–2.8 s |
| + rerank top-15 | 69% | 86% | 89% | 89% | 0.781 | ~86 | higher | higher |
| + rerank top-20 | 69% | 86% | 89% | 89% | 0.780 | ~86 | highest | highest |

Baseline row reproduces the v3 eval exactly (R@1 60 / R@3 80 / R@5 83 / R@10 91 / MRR 0.704) —
confirming the hybrid is untouched and this is a pure add-on measurement.

Note R@10 **drops** 91%→89% at N=15 and N=20: reranking pushes a gold chunk from rank 10 to
below 10 (Q19 12→14→19 etc.), i.e. widening N can *hurt* R@10. Another reason N=10 is best.

### 4.2 Per-stratum (baseline → best N=10)

| Stratum (n) | R@3 base → best | R@5 base → best |
|---|---|---|
| exact_fact (10) | 100% → 100% | 100% → 100% |
| multi_chunk (5) | 80% → **100%** | 80% → **100%** |
| near_miss (4)   | **100% → 75%** ⚠ | 100% → 100% |
| paraphrase (8)  | 75% → 75% | 75% → 75% |
| prose (8)       | 50% → **75%** | 62% → **75%** |

The headline **prose gain is real** (R@3 +25 pts, R@5 +13 pts) and multi_chunk jumps to 100%.
But **near_miss R@3 regresses** 100%→75% — the reranker demoted a clean near_miss hit (Q31)
below rank 3. This is the "fixes prose but breaks something else" risk the audit was built to
expose.

### 4.3 Regression / rescue audit

At **N=10**: improved 7, worsened 2, rescued (>5→≤5) 2. **Net +5.**

| | Question | stratum | baseline → reranked | origin |
|---|---|---|---|---|
| RESCUED | Q22 | multi_chunk | 10 → 2 (≤3) | auto_v2 |
| RESCUED | Q32 | prose | 8 → 1 (≤3) | claude_v3 |
| WORSENED | Q31 | near_miss | **1 → 4** | claude_v3 |
| WORSENED | Q27 | paraphrase | 8 → 10 | claude_v3 |

Other improvements (already ≤5, moved up): Q10 3→2, Q17 4→1, Q21 3→2, Q28 3→1, Q36 2→1.

At **N=15 / N=20**: still only 2 rescued (same Q22, Q32), but **4 worsened** (adds Q19 and
Q35, pushed deeper). Larger N = strictly worse here.

### 4.4 Full 35-question rank vector

In the log (`FULL RANK VECTOR`, best N=10) as `id [stratum] base → rr [+/-/=] origin question`.
23 unchanged, 7 improved, 2 worsened, 3 still MISS-region (Q19, Q29, Q35 unmoved at N=10).

---

## 5. Latency — the cost to weigh

- **Retrieval:** ~86 ms/query (the locked hybrid; unchanged).
- **Rerank stage:** **~1.3–2.7 s/query at N=10** on this CPU. It is **noisy** — across 4 runs
  the N=10 figure landed at 1494 / 1351 / 2300 / 2681 ms/q (system-load dependent; concurrent
  runs inflate it). Per (query,chunk) pair ≈ 150–270 ms.
- **Scales ~linearly with N** (N is the dominant latency knob): the cross-encoder runs one
  forward pass per pair, so N=10 does 350 passes across the set, N=20 does 700.
- **Order of magnitude is the robust finding:** the rerank stage costs **seconds per query**,
  ~25–50× the retrieval time, on the offline CPU deployment floor. Absolute ms is noisy;
  the ratio is not.

This is inherent to cross-encoders (vs the bi-encoder bge, which embeds each chunk once). A
GPU or ONNX-quantized cross-encoder would change the absolute numbers but was out of scope
(the constraint is CPU, offline, unmodified).

---

## 6. Environment, packages, model (offline)

Run with `/home/omodo/ml/.venv` — the same env as the v3 eval.

| Component | Value |
|---|---|
| python | 3.13.5 |
| numpy | 2.5.1 |
| sentence-transformers | 5.6.0 |
| torch | 2.13.0+cu130 (CPU forced via `CUDA_VISIBLE_DEVICES=""`; CUDA unavailable) |
| transformers | 5.13.1 |
| **reranker model** | `cross-encoder/ms-marco-MiniLM-L6-v2`, cache commit `c5ee24cb16019beea0893ab7796b1df96625c6b8`, `max_seq_length=512` |
| retriever model | `BAAI/bge-small-en-v1.5` (locked) |

- **Offline:** run with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`. The reranker weights were
  **fetched once (user-authorized) into the local HF cache**, then all measurement runs were
  strictly offline — verified the model loads with the Hub disabled. No network during scoring.
- **Determinism (constraint #5):** cross-encoder in eval mode, no dropout, CPU. Two-run (in
  fact four-run) check: **all ranks, recall, MRR, per-stratum, audit, and the full vector are
  byte-identical** across runs. Only latency varies. Sample score reproduced exactly (8.1537).
- **Assumption/caveat:** stack is `sentence-transformers 5.6.0` / `torch 2.13`, not the repo
  pin `3.3.1`. Same weights, same math → ranks unaffected (same reasoning as REPORT §6.1).

---

## 7. Label review

`LABEL_REVIEW` in the log is **empty** — no gold label is provably wrong (reusing the v3
checks: auto_v2 evidence-span presence + claude_v3 distinctive-term presence).

**Important nuance surfaced by the reranker:** on Q19, Q29, Q35 the cross-encoder ranks the
*gold* chunk **lower** than the hybrid did. That could look like a labeling problem, but these
three gold labels were **hand-verified correct** in the v3 eval (chunk 2 = suspension clause,
chunk 33 = erasure rights, chunk 20 = jurisdiction). So this is a **retrieval-quality signal**
(the cross-encoder is weak on Ugandan legal-prose paraphrase), **not** a labeling error. The
`claude_v3` labels remain `single_annotator_unverified` by design — a human should still
spot-check, but the reranker disagreement alone is not evidence of a bad label.

---

## 8. Observations

1. **The reranker's value is entirely within top-10.** It rescues two genuine misses (Q22,
   Q32) into the top-3 and tidies several near-hits. Beyond N=10 there is no recall to gain
   and active harm (deeper demotions, R@10 drop).
2. **It is not free of collateral damage.** Q31 (a clean near_miss, rank 1) drops to rank 4,
   and Q27 8→10. A reranker that demotes a correct top-1 hit is exactly the "bad trade" to
   weigh against the prose gains.
3. **Latency is the gating factor, not accuracy.** On the offline CPU floor, seconds/query is
   a product-level cost. If a reranker is pursued, the real engineering question is a cheaper
   cross-encoder (quantized/ONNX) or a smaller N — not whether MiniLM-L6 improves recall (it
   does, modestly).
4. **The deep prose misses (Q19, Q29, Q35) are not reranker-addressable** at any N tested.
   They need better *candidate generation* (the hybrid), not reordering.

---

## 9. Deliverables & exact reproduction

Files (in `newfiles/v3_eval/`):
- `eval_reranker_output.log` — the evidence log (this report summarizes it).
- `eval_reranker.py` — the harness (imports the locked pipeline + v3 gate; adds rerank).
- `reranker_console.txt` — console summary.
- Baseline for comparison: `eval_sme_v3_output.log` + `REPORT.md`.
- Shared, unchanged: `retriever.py`, `eval_retriever.py`, `eval_sme_v3.py`,
  `inputs/chunks_sme.fp.txt`, `inputs/questions_sme_v3.fp.json`.

```bash
cd newfiles/v3_eval
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES="" \
/home/omodo/ml/.venv/bin/python eval_reranker.py \
  --dump inputs/chunks_sme.fp.txt \
  --questions inputs/questions_sme_v3.fp.json \
  --out eval_reranker_output.log
```
Offline, CPU. Ranks are deterministic; only the latency columns vary run-to-run. Requires
`cross-encoder/ms-marco-MiniLM-L6-v2` in the local HF cache (commit `c5ee24cb`).
