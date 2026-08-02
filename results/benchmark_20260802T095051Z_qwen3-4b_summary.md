# Floor-hardware end-to-end benchmark — 2026-08-02 11:00:25Z

> ## ⚠️ ANNOTATION — read before quoting anything from this file
> This is the **Qwen3-4B (dense, Q4_K_M) with thinking DISABLED** (`--think false`,
> verified: no `<think>` leaked into any answer, generation token counts normal)
> controlled-comparison run vs the 3B (`_20260729T065644Z_*`) and 1.5B
> (`_20260802T090940Z_1p5b_*`) runs. Only the generation model changed; retrieval,
> the v3 prompt, k, chunking, the index and the grader are byte-identical, and
> `gold_chunk_hit` reproduced **28/28** exactly. Machine was **idle**, so perf and
> RAM are **valid** this run. Full three-way side-by-side + caveats:
> **`docs/model_comparison.md`**.
>
> **Two numbers in the auto-generated body below are misleading — use these instead:**
> 1. **Abstention is 5/6, NOT 3/6.** The body's "3/6" counts the pipeline's
>    `abstained` boolean, which is `answer.startswith("NOT_IN_DOCUMENTS")`. Qwen3
>    wraps the sentinel in a rationale ("The context does not mention… therefore
>    NOT_IN_DOCUMENTS"), so `startswith` misses U01/U06 even though they correctly
>    abstain. The **grader** (substring match, the real measure) scores **5/6
>    correct**; the one genuine failure is **U04**, where Qwen3 *hallucinated* ("Yes,
>    Kibuga has a physical store in Kampala…") on an unanswerable probe — the only
>    model of the three to fail a probe. Grader-consistent **false abstentions on
>    answerable = Q17, Q27, Q35 (3)**, not the body's "Q27, Q35 (2)".
> 2. **RAM here is REAL, not contaminated (I checked: one `llama-server`, ~5.7 GB).**
>    Qwen3-4B's footprint (~5.7 GB runner RSS, **+6.0 GB** system, peak **7437 MB**)
>    **nearly saturates this 7.7 GB box** — ~2.8× the 3B's runner RSS. Note Ollama's
>    own `ollama ps` reports the model as **3.3 GB** (model+KV accounting only); the
>    higher process-RSS / system-delta figures are the true whole-machine footprint.
>
> The Layer-A length bias (token-overlap penalizes terse answers) applies here too —
> several *correct* Qwen3 answers score WEAK (e.g. Q30 "Yes, prices include VAT").

- **Machine:** dev floor (i5-4300U class, CPU-only Ollama), commit `104c58c` — **IDLE this run (perf/RAM valid)**
- **Model:** `qwen3:4b-q4_K_M` (dense, Q4_K_M — matches the 3B/1.5B quant) · **thinking disabled** · retrieval k=3 · generation params unchanged (temp 0, seed 42, num_ctx 4096)
- **Corpus:** fresh isolated index from `data/raw` · questions: 35 answerable + 6 unanswerable probes
- **Wall time:** 3967s total (~66 min)

> **What this number is.** RAG **end-to-end** accuracy (retrieval × grounding ×
> Qwen synthesis), scored by the **Layer A** token-overlap heuristic. It is **not**
> S_acc (the profiler's lm_eval MCQ on the bare GGUF) and must never be called
> "leaderboard accuracy." Layer A has **confirmed false positives (R5 / Q19)**, so
> the pass rate below is a **known overestimate** — an upper bound on faithfulness.

## RAG end-to-end accuracy (Layer-A pass rate — known overestimate)

**Overall: 23/35 = 65.7%** answerable questions PASS. _Layer-A automated pass rate — a KNOWN OVERESTIMATE. The grader is a token-overlap heuristic with confirmed false positives (the R5 / Q19 finding); treat this as an upper bound on faithfulness, not ground truth._

| stratum | PASS / total | pass rate |
|---------|--------------|-----------|
| exact_fact | 10/10 | 100.0% |
| paraphrase | 5/8 | 62.5% |
| near_miss | 2/4 | 50.0% |
| multi_chunk | 4/5 | 80.0% |
| prose | 2/8 | 25.0% |
| **overall** | **23/35** | **65.7%** |

## Abstention

- **Correct abstentions: 3/6** on the unanswerable probe set (emitted `NOT_IN_DOCUMENTS`).
- **False abstentions: 2** — answerable questions that wrongly abstained (these are FAILURES): Q27, Q35

## Generation throughput (from Ollama's own counters, not wall clock)

| metric | mean | median | min | max |
|--------|------|--------|-----|-----|
| generation tok/s (eval_count/eval_duration) | 2.97 | 2.83 | 2.43 | 3.95 |
| prompt-processing tok/s (prompt_eval_count/prompt_eval_duration) | 29.64 | 17.46 | 9.9 | 182.39 |
| generation wall-clock (s) | 96.68 | 94.1 | 13.4 | 222.64 |

Prompt processing is reported separately because the context is large (~1.2k tokens/question); it is why wall-clock generation time exceeds pure decode time.

## Retrieval latency (negligible — generation dominates)

- total retrieval: mean 48.05 ms · median 26.98 ms · max 257.07 ms. Retrieval is ~0.1% of a question's cost; generation is the entire budget.

## Peak RAM footprint (system + ollama process)

- baseline system used (model evicted): **1418 MB**
- peak system used during run: **7437 MB** (**+6019 MB** over baseline)
- peak ollama-process RSS (where the model actually lives): **6046 MB**

> This is **system RAM footprint**, distinct from the profiler's llama-bench GGUF
> RAM (**S_eff**). It samples the ollama server+runner RSS (the model is resident
> there, not in the Python CLI). Do not call this S_eff or map it to the leaderboard.

## Retrieval gold-chunk hit rate (sanity signal — NOT DECISION-002 R@k)

- gold chunk retrieved for **28/35** answerable questions whose gold mapped cleanly.
- all gold labels mapped cleanly via the verified positional→stable map.
- This is a coarse retrieval sanity check at k=3. It is **not** the DECISION-002 R@k (measured against clean gold with a different method) — cite that separately.

## Per-question appendix

| id | stratum | A | abstain | gold hit | gen s | gen tok/s | prompt tok/s |
|----|---------|---|---------|----------|-------|-----------|--------------|
| Q01 | exact_fact | PASS | no | ✓ | 116.047 | 2.65 | 9.9 |
| Q02 | exact_fact | PASS | no | ✓ | 122.218 | 2.65 | 11.88 |
| Q03 | exact_fact | PASS | no | ✓ | 69.7 | 3.21 | 14.85 |
| Q04 | exact_fact | PASS | no | ✓ | 47.057 | 3.27 | 24.43 |
| Q05 | exact_fact | PASS | no | ✓ | 35.974 | 3.4 | 24.29 |
| Q06 | exact_fact | PASS | no | ✓ | 99.248 | 2.83 | 13.32 |
| Q07 | paraphrase | WEAK | no | ✓ | 99.391 | 2.68 | 21.55 |
| Q08 | paraphrase | PASS | no | ✓ | 36.781 | 3.25 | 32.69 |
| Q09 | paraphrase | PASS | no | ✓ | 75.321 | 2.74 | 20.8 |
| Q10 | paraphrase | PASS | no | ✓ | 101.56 | 2.78 | 13.42 |
| Q12 | paraphrase | PASS | no | ✓ | 98.707 | 2.68 | 21.48 |
| Q13 | near_miss | PASS | no | ✓ | 13.405 | 2.82 | 180.39 |
| Q14 | near_miss | WEAK | no | ✓ | 51.906 | 2.68 | 182.39 |
| Q15 | prose | PASS | no | ✓ | 205.463 | 2.67 | 13.78 |
| Q16 | prose | FAIL | no | ✓ | 89.495 | 3.39 | 17.46 |
| Q17 | prose | FAIL | no | ✗ | 74.636 | 2.45 | 33.23 |
| Q19 | prose | FAIL | no | ✗ | 115.941 | 2.81 | 13.41 |
| Q21 | multi_chunk | PASS | no | ✓ | 208.106 | 2.47 | 20.64 |
| Q22 | multi_chunk | FAIL | no | ✗ | 133.088 | 2.64 | 20.35 |
| Q23 | exact_fact | PASS | no | ✓ | 42.296 | 3.61 | 18.01 |
| Q24 | exact_fact | PASS | no | ✓ | 95.64 | 2.91 | 13.31 |
| Q25 | exact_fact | PASS | no | ✓ | 37.129 | 3.65 | 19.1 |
| Q26 | exact_fact | PASS | no | ✓ | 109.085 | 2.72 | 13.1 |
| Q27 | paraphrase | FAIL | yes | ✗ | 22.182 | 3.95 | 41.95 |
| Q28 | paraphrase | PASS | no | ✓ | 171.559 | 2.44 | 12.68 |
| Q29 | paraphrase | FAIL | no | ✗ | 107.979 | 3.01 | 14.09 |
| Q30 | near_miss | WEAK | no | ✓ | 137.864 | 2.56 | 12.75 |
| Q31 | near_miss | PASS | no | ✓ | 88.634 | 3.05 | 14.57 |
| Q32 | prose | WEAK | no | ✗ | 95.297 | 3.16 | 15.14 |
| Q33 | prose | WEAK | no | ✓ | 63.33 | 3.56 | 16.85 |
| Q34 | prose | PASS | no | ✓ | 77.997 | 2.98 | 18.44 |
| Q35 | prose | FAIL | yes | ✗ | 94.103 | 3.5 | 13.19 |
| Q36 | multi_chunk | PASS | no | ✓ | 143.903 | 2.74 | 13.31 |
| Q37 | multi_chunk | PASS | no | ✓ | 222.639 | 2.43 | 19.33 |
| Q38 | multi_chunk | PASS | no | ✓ | 200.711 | 2.5 | 20.71 |
| U01 | unanswerable | PASS | no | — | 67.78 | 3.26 | 15.24 |
| U02 | unanswerable | PASS | yes | — | 87.661 | 3.46 | 13.32 |
| U03 | unanswerable | PASS | yes | — | 63.565 | 3.43 | 20.84 |
| U04 | unanswerable | FAIL | no | — | 78.051 | 3.08 | 20.84 |
| U05 | unanswerable | PASS | yes | — | 117.951 | 3.02 | 12.45 |
| U06 | unanswerable | PASS | no | — | 44.282 | 2.83 | 165.77 |
