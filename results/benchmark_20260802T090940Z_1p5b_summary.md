# Floor-hardware end-to-end benchmark — 2026-08-02 09:28:49Z

> ## ⚠️ ANNOTATION — read before quoting anything from this file
> This is the **Qwen2.5-1.5B-Instruct (Q4_K_M)** controlled-comparison run against
> the 3B floor baseline (`results/benchmark_20260729T065644Z_*`). Only the
> generation model changed — retrieval, the v3 prompt, k, chunking, the index and
> the grader are byte-identical, and `gold_chunk_hit` reproduced **28/28** exactly.
> Full side-by-side + honesty caveats: **`docs/model_comparison_3b_vs_1p5b.md`**.
>
> **Two annotations the auto-generated body below does NOT carry:**
> 1. **Performance numbers here are DEFERRED / NON-COMPARABLE.** This run was on a
>    **contended** desktop (firefox + Xorg + okular active, load ~1.1, baseline RAM
>    2937 MB vs the 3B run's 1418 MB idle floor). Generation tok/s, wall-clock and
>    RAM below are therefore **not** a clean floor comparison to the 3B — they are a
>    lower bound on 1.5B's speed. Floor perf for 1.5B is deferred to the clean
>    **reference-machine** run. Accuracy is deterministic (temp 0, seed 42) and
>    load-insensitive, so the accuracy section IS valid.
> 2. **The 62.9% is confounded by answer length, not just faithfulness.** Layer-A
>    token-overlap rewards verbatim quoting; the 1.5B paraphrases more tersely, so
>    several *correct* 1.5B answers score WEAK/FAIL on overlap alone (e.g. Q25
>    answered `support@kibuga.com` — correct, graded FAIL). The raw 3B−1.5B gap
>    **overstates** the true faithfulness difference. See the comparison doc.

- **Machine:** dev floor (i5-4300U class, CPU-only Ollama), commit `2fc1cbe` — **NOT idle this run (see annotation)**
- **Model:** `qwen2.5:1.5b-instruct-q4_K_M` (Q4_K_M — matches the 3B quant) · retrieval k=3 · generation params unchanged (temp 0, seed 42, num_ctx 4096)
- **Corpus:** fresh isolated index from `data/raw` · questions: 35 answerable + 6 unanswerable probes
- **Wall time:** 1099s total

> **What this number is.** RAG **end-to-end** accuracy (retrieval × grounding ×
> Qwen synthesis), scored by the **Layer A** token-overlap heuristic. It is **not**
> S_acc (the profiler's lm_eval MCQ on the bare GGUF) and must never be called
> "leaderboard accuracy." Layer A has **confirmed false positives (R5 / Q19)**, so
> the pass rate below is a **known overestimate** — an upper bound on faithfulness.

## RAG end-to-end accuracy (Layer-A pass rate — known overestimate)

**Overall: 22/35 = 62.9%** answerable questions PASS. _Layer-A automated pass rate — a KNOWN OVERESTIMATE. The grader is a token-overlap heuristic with confirmed false positives (the R5 / Q19 finding); treat this as an upper bound on faithfulness, not ground truth._

| stratum | PASS / total | pass rate |
|---------|--------------|-----------|
| exact_fact | 9/10 | 90.0% |
| paraphrase | 6/8 | 75.0% |
| near_miss | 2/4 | 50.0% |
| multi_chunk | 3/5 | 60.0% |
| prose | 2/8 | 25.0% |
| **overall** | **22/35** | **62.9%** |

## Abstention

- **Correct abstentions: 6/6** on the unanswerable probe set (emitted `NOT_IN_DOCUMENTS`).
- **False abstentions: 3** — answerable questions that wrongly abstained (these are FAILURES): Q17, Q29, Q35

## Generation throughput (from Ollama's own counters, not wall clock)

| metric | mean | median | min | max |
|--------|------|--------|-----|-----|
| generation tok/s (eval_count/eval_duration) | 9.61 | 9.29 | 7.8 | 11.69 |
| prompt-processing tok/s (prompt_eval_count/prompt_eval_duration) | 120.84 | 49.18 | 31.6 | 1034.71 |
| generation wall-clock (s) | 26.75 | 25.73 | 2.07 | 54.29 |

Prompt processing is reported separately because the context is large (~1.2k tokens/question); it is why wall-clock generation time exceeds pure decode time.

## Retrieval latency (negligible — generation dominates)

- total retrieval: mean 26.05 ms · median 25.57 ms · max 47.62 ms. Retrieval is ~0.1% of a question's cost; generation is the entire budget.

## Peak RAM footprint (system + ollama process)

- baseline system used (model evicted): **2937 MB**
- peak system used during run: **4248 MB** (**+1311 MB** over baseline)
- peak ollama-process RSS (where the model actually lives): **1896 MB**

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
| Q01 | exact_fact | PASS | no | ✓ | 48.718 | 9.13 | 31.6 |
| Q02 | exact_fact | PASS | no | ✓ | 44.109 | 7.8 | 32.64 |
| Q03 | exact_fact | PASS | no | ✓ | 25.734 | 8.43 | 37.6 |
| Q04 | exact_fact | PASS | no | ✓ | 16.456 | 9.31 | 64.78 |
| Q05 | exact_fact | PASS | no | ✓ | 11.78 | 11.11 | 69.8 |
| Q06 | exact_fact | PASS | no | ✓ | 34.983 | 9.19 | 37.27 |
| Q07 | paraphrase | PASS | no | ✓ | 21.464 | 9.17 | 63.93 |
| Q08 | paraphrase | PASS | no | ✓ | 12.131 | 9.29 | 89.9 |
| Q09 | paraphrase | PASS | no | ✓ | 21.324 | 9.02 | 62.4 |
| Q10 | paraphrase | PASS | no | ✓ | 36.289 | 8.92 | 36.9 |
| Q12 | paraphrase | PASS | no | ✓ | 23.867 | 9.08 | 63.78 |
| Q13 | near_miss | PASS | no | ✓ | 3.383 | 9.44 | 1034.71 |
| Q14 | near_miss | WEAK | no | ✓ | 15.679 | 8.85 | 1028.48 |
| Q15 | prose | PASS | no | ✓ | 37.525 | 8.96 | 39.54 |
| Q16 | prose | FAIL | no | ✓ | 28.145 | 9.37 | 49.18 |
| Q17 | prose | FAIL | yes | ✗ | 15.527 | 10.66 | 98.74 |
| Q19 | prose | WEAK | no | ✗ | 33.045 | 9.48 | 38.18 |
| Q21 | multi_chunk | WEAK | no | ✓ | 54.294 | 8.53 | 57.57 |
| Q22 | multi_chunk | FAIL | no | ✗ | 22.413 | 9.08 | 63.98 |
| Q23 | exact_fact | PASS | no | ✓ | 14.319 | 10.07 | 49.57 |
| Q24 | exact_fact | PASS | no | ✓ | 33.652 | 9.46 | 37.61 |
| Q25 | exact_fact | FAIL | no | ✓ | 11.46 | 11.21 | 54.46 |
| Q26 | exact_fact | PASS | no | ✓ | 36.673 | 9.15 | 37.72 |
| Q27 | paraphrase | FAIL | no | ✗ | 12.237 | 9.34 | 123.22 |
| Q28 | paraphrase | PASS | no | ✓ | 46.374 | 8.58 | 36.59 |
| Q29 | paraphrase | FAIL | yes | ✗ | 25.213 | 11.49 | 40.89 |
| Q30 | near_miss | WEAK | no | ✓ | 38.966 | 9.07 | 36.54 |
| Q31 | near_miss | PASS | no | ✓ | 28.689 | 9.28 | 41.19 |
| Q32 | prose | WEAK | no | ✗ | 24.062 | 9.38 | 43.26 |
| Q33 | prose | WEAK | no | ✓ | 20.731 | 9.54 | 47.45 |
| Q34 | prose | PASS | no | ✓ | 26.097 | 8.83 | 56.29 |
| Q35 | prose | FAIL | yes | ✗ | 32.75 | 11.26 | 37.79 |
| Q36 | multi_chunk | PASS | no | ✓ | 36.392 | 8.98 | 38.21 |
| Q37 | multi_chunk | PASS | no | ✓ | 33.042 | 8.67 | 55.76 |
| Q38 | multi_chunk | PASS | no | ✓ | 38.494 | 8.41 | 64.33 |
| U01 | unanswerable | PASS | yes | — | 21.409 | 10.14 | 41.91 |
| U02 | unanswerable | PASS | yes | — | 30.735 | 11.39 | 37.84 |
| U03 | unanswerable | PASS | yes | — | 19.236 | 11.24 | 64.1 |
| U04 | unanswerable | PASS | yes | — | 16.43 | 11.69 | 57.67 |
| U05 | unanswerable | PASS | yes | — | 40.757 | 10.68 | 35.85 |
| U06 | unanswerable | PASS | yes | — | 2.067 | 11.24 | 915.29 |
