# Floor-hardware end-to-end benchmark — 2026-07-29 07:36:02Z

- **Machine:** dev floor (i5-4300U class, CPU-only Ollama), commit `d1b1322`
- **Model:** `qwen2.5:3b-instruct` · retrieval k=3 · generation params unchanged (temp 0, seed 42, num_ctx 4096)
- **Corpus:** fresh isolated index from `data/raw` · questions: 35 answerable + 6 unanswerable probes
- **Wall time:** 2329s total

> **What this number is.** RAG **end-to-end** accuracy (retrieval × grounding ×
> Qwen synthesis), scored by the **Layer A** token-overlap heuristic. It is **not**
> S_acc (the profiler's lm_eval MCQ on the bare GGUF) and must never be called
> "leaderboard accuracy." Layer A has **confirmed false positives (R5 / Q19)**, so
> the pass rate below is a **known overestimate** — an upper bound on faithfulness.

## RAG end-to-end accuracy (Layer-A pass rate — known overestimate)

**Overall: 26/35 = 74.3%** answerable questions PASS. _Layer-A automated pass rate — a KNOWN OVERESTIMATE. The grader is a token-overlap heuristic with confirmed false positives (the R5 / Q19 finding); treat this as an upper bound on faithfulness, not ground truth._

| stratum | PASS / total | pass rate |
|---------|--------------|-----------|
| exact_fact | 10/10 | 100.0% |
| paraphrase | 5/8 | 62.5% |
| near_miss | 3/4 | 75.0% |
| multi_chunk | 3/5 | 60.0% |
| prose | 5/8 | 62.5% |
| **overall** | **26/35** | **74.3%** |

## Abstention

- **Correct abstentions: 6/6** on the unanswerable probe set (emitted `NOT_IN_DOCUMENTS`).
- **False abstentions: 5** — answerable questions that wrongly abstained (these are FAILURES): Q08, Q17, Q27, Q29, Q35

## Generation throughput (from Ollama's own counters, not wall clock)

| metric | mean | median | min | max |
|--------|------|--------|-----|-----|
| generation tok/s (eval_count/eval_duration) | 5.22 | 4.98 | 4.61 | 6.12 |
| prompt-processing tok/s (prompt_eval_count/prompt_eval_duration) | 58.7 | 23.53 | 14.64 | 496.05 |
| generation wall-clock (s) | 56.74 | 53.99 | 3.81 | 138.74 |

Prompt processing is reported separately because the context is large (~1.2k tokens/question); it is why wall-clock generation time exceeds pure decode time.

## Retrieval latency (negligible — generation dominates)

- total retrieval: mean 25.26 ms · median 25.31 ms · max 35.4 ms. Retrieval is ~0.1% of a question's cost; generation is the entire budget.

## Peak RAM footprint (system + model runner)

- baseline system used (model evicted): **1418 MB**
- peak system used during run: **4584 MB** (**+3166 MB** over baseline) ← the reliable footprint
- model-runner (`llama-server`) resident RSS: **~2054 MB** (measured directly, see note)
- ~~automated per-process RSS sample: 64 MB~~ — **UNDER-COUNT, do not use** (see note)

> **RAM-sampler correction.** The automated sampler recorded a per-process RSS of
> only 64 MB because it filtered on processes named `ollama` — but `ollama serve`
> is just the ~60 MB API broker. The model actually runs in a **separate
> `llama-server` subprocess** (launched `--no-mmap`, so the whole model sits in
> real RSS), which the filter missed. Measured directly under load,
> `llama-server` holds **~2054 MB** — consistent with the reliable whole-machine
> signal below. The harness sampler has been fixed to sum `llama-server` too
> (`fix(bench)`); this run's per-process line is corrected post-hoc from a direct
> reading. **The system used-memory delta (+3166 MB) was always correct** — it
> comes from `/proc/meminfo` `MemAvailable`, independent of process naming, and it
> captured the model load in full.
>
> This is **system RAM footprint**, distinct from the profiler's llama-bench GGUF
> RAM (**S_eff**). Do not call this S_eff or map it to the leaderboard.

## Retrieval gold-chunk hit rate (sanity signal — NOT DECISION-002 R@k)

- gold chunk retrieved for **28/35** answerable questions whose gold mapped cleanly.
- all gold labels mapped cleanly via the verified positional→stable map.
- This is a coarse retrieval sanity check at k=3. It is **not** the DECISION-002 R@k (measured against clean gold with a different method) — cite that separately.

## Per-question appendix

| id | stratum | A | abstain | gold hit | gen s | gen tok/s | prompt tok/s |
|----|---------|---|---------|----------|-------|-----------|--------------|
| Q01 | exact_fact | PASS | no | ✓ | 78.173 | 5.07 | 14.64 |
| Q02 | exact_fact | PASS | no | ✓ | 83.926 | 4.92 | 17.08 |
| Q03 | exact_fact | PASS | no | ✓ | 51.515 | 5.05 | 20.41 |
| Q04 | exact_fact | PASS | no | ✓ | 32.172 | 5.07 | 33.93 |
| Q05 | exact_fact | PASS | no | ✓ | 25.49 | 5.37 | 33.59 |
| Q06 | exact_fact | PASS | no | ✓ | 69.843 | 4.95 | 18.45 |
| Q07 | paraphrase | PASS | no | ✓ | 53.857 | 4.87 | 31.71 |
| Q08 | paraphrase | FAIL | yes | ✓ | 20.046 | 6.1 | 45.42 |
| Q09 | paraphrase | PASS | no | ✓ | 45.387 | 4.95 | 30.89 |
| Q10 | paraphrase | PASS | no | ✓ | 68.767 | 4.96 | 18.61 |
| Q12 | paraphrase | PASS | no | ✓ | 51.764 | 4.77 | 30.69 |
| Q13 | near_miss | PASS | no | ✓ | 6.375 | 4.98 | 495.42 |
| Q14 | near_miss | WEAK | no | ✓ | 28.785 | 4.79 | 496.05 |
| Q15 | prose | PASS | no | ✓ | 87.943 | 4.81 | 18.96 |
| Q16 | prose | FAIL | no | ✓ | 43.712 | 5.12 | 23.53 |
| Q17 | prose | FAIL | yes | ✗ | 31.312 | 5.84 | 48.26 |
| Q19 | prose | PASS | no | ✗ | 76.458 | 4.85 | 18.4 |
| Q21 | multi_chunk | WEAK | no | ✓ | 138.737 | 4.61 | 28.8 |
| Q22 | multi_chunk | FAIL | no | ✗ | 53.995 | 4.86 | 30.37 |
| Q23 | exact_fact | PASS | no | ✓ | 30.302 | 5.33 | 24.41 |
| Q24 | exact_fact | PASS | no | ✓ | 67.494 | 5.11 | 18.4 |
| Q25 | exact_fact | PASS | no | ✓ | 26.408 | 5.33 | 26.06 |
| Q26 | exact_fact | PASS | no | ✓ | 74.666 | 4.92 | 18.18 |
| Q27 | paraphrase | FAIL | yes | ✗ | 15.281 | 6.12 | 60.11 |
| Q28 | paraphrase | PASS | no | ✓ | 107.27 | 4.67 | 17.67 |
| Q29 | paraphrase | FAIL | yes | ✗ | 52.274 | 6.12 | 19.56 |
| Q30 | near_miss | PASS | no | ✓ | 84.143 | 4.77 | 17.59 |
| Q31 | near_miss | PASS | no | ✓ | 57.117 | 5.05 | 19.8 |
| Q32 | prose | PASS | no | ✗ | 60.752 | 4.96 | 20.67 |
| Q33 | prose | PASS | no | ✓ | 39.274 | 4.96 | 23.26 |
| Q34 | prose | PASS | no | ✓ | 54.873 | 4.81 | 27.13 |
| Q35 | prose | FAIL | yes | ✗ | 67.492 | 5.88 | 18.23 |
| Q36 | multi_chunk | PASS | no | ✓ | 84.166 | 4.81 | 18.43 |
| Q37 | multi_chunk | PASS | no | ✓ | 73.489 | 4.68 | 27.01 |
| Q38 | multi_chunk | PASS | no | ✓ | 116.325 | 4.69 | 31.05 |
| U01 | unanswerable | PASS | yes | — | 43.072 | 6.09 | 20.6 |
| U02 | unanswerable | PASS | yes | — | 62.211 | 5.97 | 18.59 |
| U03 | unanswerable | PASS | yes | — | 39.72 | 5.9 | 30.74 |
| U04 | unanswerable | PASS | yes | — | 34.186 | 5.96 | 27.42 |
| U05 | unanswerable | PASS | yes | — | 83.825 | 5.78 | 17.34 |
| U06 | unanswerable | PASS | yes | — | 3.811 | 5.98 | 449.06 |
