# Model comparison — Qwen2.5-3B vs Qwen2.5-1.5B on the adtc-rag pipeline

**Date:** 2026-08-02 · **Branch:** `main` · **Commit:** `2fc1cbe`
**Purpose:** a *controlled* end-to-end comparison of two candidate generation
models on the **same** RAG pipeline, to inform (not decide) a possible switch
from the 3B to the 1.5B.

| | 3B baseline | 1.5B candidate |
|---|---|---|
| Ollama model | `qwen2.5:3b-instruct` | `qwen2.5:1.5b-instruct-q4_K_M` |
| Params / quant | 3.1B · **Q4_K_M** | 1.5B · **Q4_K_M** |
| Run artifacts | `results/benchmark_20260729T065644Z_*` | `results/benchmark_20260802T090940Z_1p5b_*` |
| License | Qwen **RESEARCH** (non-commercial) | **Apache-2.0** |

Both runs: retrieval k=3, the v3 grounding prompt, temp 0 / seed 42 / num_ctx
4096, the same 5-PDF / 47-chunk corpus, the same 41 questions (35 answerable +
6 unanswerable probes), graded by the same `gen_judge.layer_a`. **The only
variable is the generation model.**

---

## 0. Controlled-comparison integrity (this is what makes the numbers mean anything)

Retrieval, the prompt, k, chunking, the index and the grader were held fixed and
verified identical between runs:

- **`gold_chunk_hit`: 28/35 in BOTH runs, question-for-question identical** (the
  seven misses — Q17, Q19, Q22, Q27, Q29, Q32, Q35 — are the same in both).
- **Retrieved chunk ids and their order: byte-identical for all 41 questions.**

If retrieval had drifted, the comparison would be worthless; it did not. Every
accuracy difference below is attributable to generation alone.

---

## 1. RAG end-to-end accuracy (Layer-A pass rate)

> **What this number is — and its two biases.** RAG **end-to-end** accuracy
> (retrieval × grounding × synthesis), scored by the **Layer-A token-overlap
> heuristic**. It is **not** S_acc (the profiler's lm_eval MCQ on the bare GGUF)
> and not DECISION-002 R@k. Two grader biases matter here:
> 1. **Known overestimate (both models):** Layer-A has confirmed false positives
>    (the R5 / Q19 finding) — it can PASS an answer built on the wrong chunk.
> 2. **Length bias (hurts the terser model):** token-overlap rewards verbatim
>    quoting. The 1.5B paraphrases more concisely, so several *correct* 1.5B
>    answers lose overlap and score WEAK/FAIL. **This makes the raw 3B−1.5B gap
>    an overstatement of the true faithfulness difference** (see §3).
>
> Treat the pass rate as a biased proxy, not ground truth. A Layer-B / human
> grade would move both numbers, and would likely *narrow* the gap.

### Overall and per stratum

| stratum | 3B PASS/total | 3B rate | 1.5B PASS/total | 1.5B rate | Δ |
|---------|---------------|---------|-----------------|-----------|---|
| exact_fact | 10/10 | 100.0% | 9/10 | 90.0% | −1 |
| paraphrase | 5/8 | 62.5% | 6/8 | 75.0% | **+1** |
| near_miss | 3/4 | 75.0% | 2/4 | 50.0% | −1 |
| multi_chunk | 3/5 | 60.0% | 3/5 | 60.0% | 0 |
| prose | 5/8 | 62.5% | 2/8 | 25.0% | −3 |
| **overall** | **26/35** | **74.3%** | **22/35** | **62.9%** | **−4 (−11.4 pts)** |

Both figures carry the R5/Q19 known-overestimate caveat. The headline gap is
**−4 PASSes**, concentrated in **prose** — but §3 shows most of that is the
grader's length bias, not a real faithfulness loss.

---

## 2. Abstention

| | 3B | 1.5B |
|---|---|---|
| Correct abstentions (of 6 unanswerable probes) | **6/6** | **6/6** |
| False abstentions (answerable, wrongly abstained) | **5** — Q08, Q17, Q27, Q29, Q35 | **3** — Q17, Q29, Q35 |

Both models abstain correctly on **every** unanswerable probe — the DECISION-004
abstention policy holds for both. The difference is that **the 1.5B abstains
less** on answerable questions (3 false abstentions vs 5). That cuts both ways —
see Q08 and Q27 in §3.

---

## 3. Per-question verdict changes (7 of 41) — and what actually drives them

| id | stratum | 3B → 1.5B | gold hit | what happened |
|----|---------|-----------|----------|---------------|
| Q08 | paraphrase | FAIL → **PASS** | ✓ | **Genuine 1.5B win.** 3B wrongly abstained; 1.5B answered correctly ("No, under 18 cannot register"). |
| Q25 | exact_fact | PASS → **FAIL** | ✓ | **Grader false negative.** 1.5B answered `support@kibuga.com` — *correct* but too terse for token-overlap ≥0.5, so graded FAIL. |
| Q19 | prose | PASS → WEAK | ✗ | Both answers ungrounded-ish (gold not retrieved; Q19 is *the* confirmed Layer-A false positive). 1.5B's terser phrasing scores WEAK instead of a false PASS. |
| Q30 | near_miss | PASS → WEAK | ✓ | **Length bias.** 1.5B: "Yes, prices are inclusive of VAT" — correct; 3B quoted the passage verbatim → more overlap → PASS. |
| Q32 | prose | PASS → WEAK | ✗ | **Length bias.** 1.5B gives a tight paraphrase of the penalties list; fewer overlapping tokens → WEAK. |
| Q33 | prose | PASS → WEAK | ✓ | **Length bias.** Same third-party list, more concisely worded → WEAK. |
| Q27 | paraphrase | FAIL → FAIL | ✗ | **Genuine 1.5B risk.** Neither retrieved the gold chunk. 3B abstained (safe); 1.5B *confidently answered from the wrong chunk* (returns-retention instead of data-retention) — a hallucination the abstention policy caught in the 3B. |

**Reading this table:**

- **1 genuine accuracy win for the 1.5B** (Q08).
- **1 genuine accuracy loss** in the sense the grader can't see: **Q27**, where the
  1.5B's lower abstention rate produced a confident wrong answer instead of a safe
  abstention. This is the real cost of the abstention difference in §2.
- **The other 5 changes (Q25, Q19, Q30, Q32, Q33) are grader artifacts of answer
  length, not faithfulness.** Four of them (Q25, Q30, Q32, Q33) are answers that
  are *correct on their face*; they lost points only because the 1.5B quotes less
  verbatim text. **This is why the raw −11.4-pt gap overstates the real
  difference.** Under a faithfulness-aware (Layer-B / human) grade, the prose
  stratum in particular would recover much of its apparent loss.

The honest summary: on *faithfulness*, the two models are much closer than
74.3% vs 62.9% suggests. The clearest real behavioral difference is the
abstention/coverage trade-off — the 1.5B answers more (helping Q08) at the cost
of occasionally answering when it should decline (hurting Q27).

---

## 4. Performance — DEFERRED (machine was not idle)

Per the evaluation plan, floor performance for the 1.5B is **deferred to the
clean reference-machine run** and is **not** presented here as a comparison. This
1.5B run executed on a **contended** desktop (firefox, Xorg, okular active; load
average ~1.1 on 4 cores; baseline RAM 2937 MB vs the 3B run's 1418 MB idle
floor). Contention only *slows* the 1.5B, so any speed advantage it shows is a
**lower bound**, not a number to bank.

Directionally (and only directionally): even contended, the 1.5B decoded roughly
**~1.9× faster** and used **less** runner RAM than the 3B floor run — the
expected shape for a smaller model. The magnitude is not trustworthy until both
models are measured on the same idle reference box. The raw per-question perf
counters are in the run's `_summary.md` and `.jsonl`, flagged there as deferred.

---

## 5. What this comparison does — and does not — tell us

**It tells us (informative now):**

- **Retrieval is model-independent and stable** — proven identical across the two
  runs, so this is a clean generation-only comparison.
- **On the length-biased Layer-A proxy, the 3B scores higher (74.3% vs 62.9%),**
  but the per-question analysis shows **most of that gap is answer-length
  artifact, not faithfulness** — the two models are closer than the headline.
- **Both models nail abstention on unanswerable probes (6/6).** The real
  behavioral difference is that **the 1.5B abstains less on answerable questions**
  — a coverage/safety trade-off (helps Q08, hurts Q27).

**It does NOT tell us (decide elsewhere):**

- **True faithfulness ranking.** Layer-A is a biased proxy (overestimate for both;
  length-penalizes the terser 1.5B). A **Layer-B / human grade** is required to
  pin the real accuracy gap — it is the single highest-value follow-up before any
  switch.
- **Floor / reference performance.** Deferred — this box was contended. The 1.5B's
  perf case (its main draw) must be measured on the **idle reference machine**
  alongside a fresh 3B row.
- **The license question.** The 1.5B being **Apache-2.0** vs the 3B's **research
  (non-commercial)** license is a separate, non-benchmark axis. It is noted here
  as context but is a decision for humans, not something this data settles.

**No recommendation is made here.** The model choice belongs to a human weighing:
(1) the true accuracy gap from a Layer-B/human grade, (2) clean reference-machine
performance, and (3) the license constraint. This document supplies only the
controlled accuracy comparison.
