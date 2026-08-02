# Model comparison — Qwen2.5-3B vs 1.5B vs Qwen3-4B on the adtc-rag pipeline

**Updated:** 2026-08-02 · **Branch:** `main` · **Commit:** `104c58c`
**Purpose:** a *controlled* end-to-end comparison of candidate generation models on
the **same** RAG pipeline, to inform (not decide) which model to submit.

| | 3B baseline | 1.5B candidate | Qwen3-4B candidate |
|---|---|---|---|
| Ollama model | `qwen2.5:3b-instruct` | `qwen2.5:1.5b-instruct-q4_K_M` | `qwen3:4b-q4_K_M` |
| Params / quant | 3.1B · Q4_K_M | 1.5B · Q4_K_M | 4.0B (dense) · Q4_K_M |
| Thinking | n/a | n/a | **disabled** (`--think false`) |
| Run artifacts | `results/…065644Z_*` | `results/…090940Z_1p5b_*` | `results/…095051Z_qwen3-4b_*` |
| License | Qwen **Research** (non-commercial) | **Apache-2.0** | **Apache-2.0** |
| Machine state during run | floor (~idle) | **contended** | **idle** |

All runs: retrieval k=3, the v3 grounding prompt, temp 0 / seed 42 / num_ctx 4096,
the same 5-PDF / 47-chunk corpus, the same 41 questions (35 answerable + 6
unanswerable probes), graded by the same `gen_judge.layer_a`. **The only variable
is the generation model** (Qwen3 additionally needs thinking disabled to sit in the
same non-thinking regime; that knob leaves the 2.5 runs byte-identical).

> **Note on Qwen3-4B:** it is a **dense** model, not MoE — there is no sparse-MoE
> Qwen3 at 4B (the smallest Qwen3 MoE is 30B-A3B, ~18 GB @ Q4, which does not fit
> this 7.7 GB box). Thinking was disabled for an apples-to-apples comparison with
> the non-thinking Qwen2.5 instruct models; verified no reasoning leaked into any
> answer and generation token counts stayed in the normal (non-thinking) range.

---

## 0. Controlled-comparison integrity

Retrieval, the prompt, k, chunking, the index and the grader were held fixed and
verified identical across **all three** runs:

- **`gold_chunk_hit`: 28/35, question-for-question identical in all three runs**
  (same seven misses: Q17, Q19, Q22, Q27, Q29, Q32, Q35).
- **Retrieved chunk ids and order: byte-identical for all 41 questions, all runs.**

Every accuracy difference below is attributable to generation alone.

---

## 1. RAG end-to-end accuracy (Layer-A pass rate)

> **What this number is — and its two biases.** RAG **end-to-end** accuracy
> (retrieval × grounding × synthesis), scored by the **Layer-A token-overlap
> heuristic**. Not S_acc, not DECISION-002 R@k. Two grader biases:
> 1. **Known overestimate (all models):** Layer-A has confirmed false positives
>    (R5 / Q19) — it can PASS an answer built on the wrong chunk.
> 2. **Length bias (hurts terser models):** token-overlap rewards verbatim quoting;
>    both the 1.5B and Qwen3-4B paraphrase more concisely than the 3B, so several
>    *correct* answers score WEAK/FAIL on overlap alone. **The raw gaps below
>    overstate the true faithfulness differences.**
>
> Treat the pass rate as a biased proxy, not ground truth. A Layer-B / human grade
> is required to rank faithfulness for real — it is the top follow-up.

### Overall and per stratum (PASS / total)

| stratum | 3B | 1.5B | Qwen3-4B |
|---------|----|----|----|
| exact_fact | 10/10 | 9/10 | **10/10** |
| paraphrase | 5/8 | 6/8 | 5/8 |
| near_miss | 3/4 | 2/4 | 2/4 |
| multi_chunk | 3/5 | 3/5 | **4/5** |
| prose | 5/8 | 2/8 | 2/8 |
| **overall** | **26/35 (74.3%)** | **22/35 (62.9%)** | **23/35 (65.7%)** |

All three carry the R5/Q19 known-overestimate caveat. On the raw proxy Qwen3-4B
lands **between** the 1.5B and the 3B — recovering the 1.5B's lost exact_fact
(10/10) and posting the best multi_chunk (4/5), but sharing the 1.5B's prose drop
(2/8), most of which is the length bias (see §3), not faithfulness.

---

## 2. Abstention

| | 3B | 1.5B | Qwen3-4B |
|---|---|---|---|
| Correct abstentions (of 6 probes) | **6/6** | **6/6** | **5/6** — U04 failed |
| Unanswerable probe FAILURE | none | none | **U04** (hallucinated a physical store) |
| False abstentions (answerable, wrongly abstained) | 5 (Q08, Q17, Q27, Q29, Q35) | 3 (Q17, Q29, Q35) | 3 (Q17, Q27, Q35) |

> **Measurement note for Qwen3-4B.** Its auto-generated summary shows "3/6" correct
> abstentions and "2" false — those count the pipeline's `abstained` boolean
> (`answer.startswith("NOT_IN_DOCUMENTS")`). Qwen3 wraps the sentinel in a rationale,
> so `startswith` misses it; the **grader** (substring match, the real measure) gives
> the **5/6 / 3** numbers above. The one genuine probe failure, **U04**, is real: Qwen3
> answered "Yes, Kibuga has a physical store in Kampala…" on an unanswerable question.

The 3B is the most conservative (abstains on every probe, but also over-abstains on 5
answerable). The 1.5B and Qwen3-4B abstain less — better coverage on answerable
questions, but each has **one confident hallucination** the 3B avoided: the 1.5B on
**Q27** (answered from the wrong chunk), Qwen3-4B on **U04** (answered an unanswerable
probe outright). This is the recurring trade-off: **more coverage ↔ more hallucination
risk**, and the 3B sits at the conservative end.

---

## 3. Per-question verdict changes, 3B → Qwen3-4B (8 of 41)

| id | stratum | 3B → Qwen3-4B | gold hit | what happened |
|----|---------|---------------|----------|---------------|
| Q08 | paraphrase | FAIL → **PASS** | ✓ | **Genuine win.** 3B wrongly abstained; Qwen3 answered correctly. |
| Q21 | multi_chunk | WEAK → **PASS** | ✓ | **Genuine win.** Better multi-chunk synthesis cleared the overlap bar. |
| Q19 | prose | PASS → **FAIL** | ✗ | Q19 is *the* confirmed Layer-A false positive (3B's PASS was on the wrong chunk). Qwen3's FAIL here is arguably **more honest**, not worse. |
| U04 | unanswerable | PASS → **FAIL** | — | **Genuine loss.** Qwen3 hallucinated a physical-store answer instead of abstaining. |
| Q07 | paraphrase | PASS → WEAK | ✓ | Length bias — tighter paraphrase, less overlap. |
| Q30 | near_miss | PASS → WEAK | ✓ | Length bias — "Yes, prices include VAT" (correct, terse). |
| Q32 | prose | PASS → WEAK | ✗ | Length bias — concise paraphrase of the penalties list. |
| Q33 | prose | PASS → WEAK | ✓ | Length bias — tighter third-party list. |

**Reading it:** 2 genuine wins (Q08, Q21), 1 genuine loss (U04 hallucination), 1 case
where Qwen3 is *more* honest than the 3B's false-positive (Q19), and 4 length-bias
WEAK downgrades of answers that are correct on their face. As with the 1.5B, **the raw
−4-PASS gap vs the 3B overstates the real faithfulness difference** — on substance
Qwen3-4B is roughly 3B-class, with a different failure signature (occasional over-answering).

---

## 4. Performance & memory

Machine state differs by run — read the caveats. **Qwen3-4B ran on a clean idle box
(directly comparable to the 3B floor); the 1.5B ran contended (its speed is a lower
bound).**

| metric (from Ollama's own counters) | 3B (floor~idle) | 1.5B (contended) | **Qwen3-4B (idle)** |
|---|---|---|---|
| generation tok/s — median | 4.98 | 9.29 (≥, lower bound) | **2.83** |
| generation tok/s — range | 4.61–6.12 | 7.8–11.69 | 2.43–3.95 |
| generation wall-clock — median | 54.0 s | 25.7 s | **94.1 s** |
| prompt-processing tok/s — median | 23.5 | 49.2 | 17.5 |
| total run wall-clock (41 Q) | ~39 min | ~18 min | **~66 min** |
| retrieval — median | 25.3 ms | 25.6 ms | 27.0 ms |

### Memory footprint

| | 3B (floor) | Qwen3-4B (idle, clean measurement) |
|---|---|---|
| idle baseline (model evicted) | 1418 MB | 1418 MB (identical) |
| peak system used (Δ over baseline) | 4584 MB (+3166) | **7437 MB (+6019)** |
| model-runner (`llama-server`) RSS | ~2054 MB | **~5.7 GB** |
| `ollama ps` model-size accounting | — | 3.3 GB (lower; model+KV only) |

**The headline efficiency finding:** on CPU, Qwen3-4B is the **slowest** of the three
(2.83 tok/s median, ~1.75× slower than the 3B, ~3.3× slower than the 1.5B) and by far
the **heaviest** (~5.7 GB runner RSS, **nearly saturating the 7.7 GB machine** at a
7437 MB peak — ~2.8× the 3B's footprint). The RAM figure is a clean, verified
single-model measurement (one `llama-server` process), not contamination. Ollama's own
`ollama ps` reports 3.3 GB; the higher process-RSS / system-delta is the true
whole-machine footprint and is what determines "does it fit" — and it *barely* does.

---

## 5. What this comparison does — and does not — tell us

**It tells us (informative now):**

- **Retrieval is model-independent and stable** across all three runs — a clean
  generation-only comparison.
- **On the length-biased Layer-A proxy:** 3B 74.3% > Qwen3-4B 65.7% > 1.5B 62.9% — but
  the per-question analysis shows the gaps are **substantially answer-length artifact**;
  on substance the 3B and Qwen3-4B are close, and the 1.5B is not far behind.
- **Abstention/coverage trade-off:** the 3B is the most conservative (6/6 probes, but
  over-abstains on 5 answerable); the 1.5B and Qwen3-4B answer more but each has one
  confident hallucination (1.5B Q27, Qwen3-4B U04) the 3B avoided.
- **Efficiency (clean this run):** Qwen3-4B is the **slowest and heaviest** — ~2.8 tok/s
  and ~5.7 GB, nearly filling this 7.7 GB box. Its license advantage (Apache-2.0) comes
  with a real CPU-inference cost. The 1.5B is the fastest/lightest; the 3B sits in
  between on both.

**It does NOT tell us (decide elsewhere):**

- **True faithfulness ranking.** Layer-A is a biased proxy (overestimate for all;
  length-penalizes the terser 1.5B and Qwen3-4B). A **Layer-B / human grade** of the
  three runs is the single highest-value follow-up before any switch.
- **Clean 1.5B / 3B perf on this box.** The 1.5B row was contended (speed is a lower
  bound); a matched idle re-run would tighten the perf table. Qwen3-4B and the 3B are
  both ~idle and directly comparable.
- **License eligibility.** The 3B's Qwen **Research** (non-commercial) license vs the
  Apache-2.0 of the 1.5B and Qwen3-4B is a **rules question** — whether a non-commercial
  license disqualifies a submission depends on the competition's eligibility terms, not
  on anything this benchmark measures. Confirm against the rules doc.

**No recommendation is made here.** The choice belongs to a human weighing: (1) the true
accuracy gap from a Layer-B/human grade, (2) the efficiency numbers (where Qwen3-4B is
notably slower/heavier), and (3) the license constraint (where the 3B is the only one at
risk). This document supplies only the controlled comparison. One observation worth
surfacing for that decision: **Qwen3-4B trades the 3B's license risk for a real
performance/memory cost** — the opposite trade-off, not a strict improvement.
