# Session report — floor-hardware end-to-end benchmark (perf + accuracy)

**Date:** 2026-07-29 · **Branch:** `main` · **Benchmark commit:** `d1b1322`
**Result:** ✅ full 41-question sweep completed unattended, **0 failures**, results committed.

This session built and ran the first **full-corpus** end-to-end benchmark of the
`adtc-rag` pipeline — every question, real ONNX retrieval, live Qwen2.5-3B
generation — capturing latency, tokens/sec, peak RAM, and a RAG end-to-end
accuracy number. Evidence: `results/benchmark_20260729T065644Z.{jsonl,_summary.md,log}`.

---

## 0. Read this first — what the accuracy number is (and isn't)

The headline accuracy here is **RAG end-to-end, Layer-A automated pass rate**:
retrieval × grounding × Qwen synthesis, graded by the existing token-overlap
heuristic (`gen_judge.layer_a`, reused verbatim — no new grader). Three separate
"accuracy" figures must not be conflated:

- **This number ≠ S_acc.** S_acc is the profiler's lm_eval MCQ on the bare GGUF.
  This folds in retrieval and grounding and can never be called "leaderboard accuracy."
- **Known overestimate.** Layer A has **confirmed false positives (R5 / Q19)** — it
  passes an answer on token overlap even when the retrieved chunk was wrong. So the
  pass rate is an **upper bound** on faithfulness, stated inline everywhere it appears.
- **gold_chunk_hit ≠ DECISION-002 R@k.** The hit rate below is a coarse retrieval
  sanity signal at k=3, not the DECISION-002 R@k (clean gold, different method).

Generation metrics come from **Ollama's own response counters** (`eval_count /
eval_duration`), never wall clock. Generation params were untouched (temp 0, seed
42, num_ctx 4096) — this session added metrics only.

---

## 1. Setup

- **Machine:** dev floor box — 4-core i5-4300U-class, 7.7 GB RAM, **CPU-only** Ollama.
  (This is the *floor*, not the teammate's reference i5 — that run is still outstanding.)
- **Runtime:** the proven torch-free `.venv-runtime` (numpy, onnxruntime, pdfplumber, tokenizers).
- **Corpus:** a fresh isolated index built from `data/raw` at the start — 5 PDFs, 47 chunks.
- **Questions:** 35 answerable (`questions_sme_v3.json`) + 6 unanswerable probes
  (`questions_unanswerable.json`) = **41**.
- **Wall time:** **2329 s (~39 min)**, 0 questions failed.

---

## 2. Headline results

### RAG end-to-end accuracy — Layer-A pass rate (known overestimate)

**26 / 35 = 74.3%** answerable questions PASS. Per stratum:

| stratum | PASS / total | rate |
|---------|--------------|------|
| exact_fact | 10/10 | 100% |
| paraphrase | 5/8 | 62.5% |
| near_miss | 3/4 | 75% |
| multi_chunk | 3/5 | 60% |
| prose | 5/8 | 62.5% |
| **overall** | **26/35** | **74.3%** |

Caveat repeated: token-overlap grader, confirmed false positives (R5/Q19) — an
upper bound, not ground truth.

### Abstention

- **Correct abstentions: 6 / 6** on the unanswerable probes — every probe emitted
  `NOT_IN_DOCUMENTS`. Clean sweep; the DECISION-004 abstention policy holds end to end.
- **False abstentions: 5** on answerable questions (**Q08, Q17, Q27, Q29, Q35**) — the
  model wrongly abstained where an answer existed. These are the bulk of the 9 non-passes
  and the most actionable failure mode (see §4).

### Performance

| metric | mean | median | min | max |
|--------|------|--------|-----|-----|
| **generation** tok/s (Ollama counters) | 5.22 | 4.98 | 4.61 | 6.12 |
| **prompt** tok/s | 58.7 | 23.5 | 14.6 | 496 |
| generation wall-clock (s) | 56.7 | 54.0 | 3.8 | 138.7 |
| retrieval total (ms) | 25.3 | 25.3 | — | 35.4 |

Generation is the entire cost: **~5 tok/s** decode on a CPU-only 3B, so ~55 s/question
median. Retrieval is ~25 ms — ~0.05% of a question. Prompt-processing tok/s is reported
separately and is highly variable (14–496): the high outliers are questions whose prompt
was largely cache-served; the ~1.2k-token context is why wall-clock generation exceeds
pure decode time.

### Peak RAM footprint

- baseline (model evicted): **1418 MB**
- **peak system used: 4584 MB (+3166 MB)** ← the reliable footprint
- model runner (`llama-server`) resident: **~2054 MB** (measured directly — see §3)

This is **system RAM footprint**, distinct from the profiler's llama-bench GGUF RAM
(**S_eff**). Do not map it to the leaderboard.

### Retrieval sanity

- gold chunk retrieved for **28 / 35** answerable questions; all gold labels mapped
  cleanly through the verified positional→stable map (no unmappable labels). Coarse
  k=3 signal only — **not** DECISION-002 R@k.

---

## 3. Issue found & fixed mid-session: RAM sampler under-counted the model

The automated per-process RSS sample came back at **64 MB** — impossible for a ~2 GB
model. Root cause: the sampler filtered on processes named `ollama`, but **`ollama
serve` is only the ~60 MB API broker**. The model runs in a **separate `llama-server`
subprocess** (launched `--no-mmap`, so the whole model is in real RSS), which the filter
never matched. Measured directly under load, `llama-server` holds **~2054 MB**.

- **Fix:** `fix(bench)` — the sampler now sums `llama-server`/`llama_server` alongside
  `ollama`. Verified it reports ~2 GB during inference.
- **Why the headline RAM number still stands:** the **system used-memory delta
  (+3166 MB)** comes from `/proc/meminfo` `MemAvailable`, independent of process naming,
  and captured the model load in full. Only the per-process sub-line was wrong; it's
  corrected post-hoc in the summary from the direct reading.

Everything else (accuracy, TPS, latency) was correct as recorded.

---

## 4. Persisting issues (none block the deliverable)

1. **5 false abstentions (Q08, Q17, Q27, Q29, Q35).** Answerable questions where the 3B
   wrongly emitted `NOT_IN_DOCUMENTS`. Note Q08/Q27/Q29/Q35 map to gold-hit ✓ in several
   cases — retrieval surfaced the right chunk but the model still declined. This is a
   generation/grounding-sensitivity ceiling of the 3B under the (locked) v3 prompt, not a
   retrieval defect. The biggest lever on the pass rate.
2. **Layer-A false positives visible in the data (Q19, Q32).** Both PASS with
   gold_chunk_hit ✗ — token overlap cleared them despite retrieving the wrong chunk. This
   is exactly why 74.3% is labelled an overestimate; a Layer-B/human pass would revise it down.
3. **~5 tok/s generation** is the floor-hardware reality (CPU-only 3B). Fine for the floor
   capacity question; a GPU or smaller/quantised model is the lever if speed matters.

---

## 5. Readiness / next steps

- **Floor-hardware perf run: DONE.** Real numbers captured, committed, reproducible via
  `run_benchmark.sh`.
- **Reference-machine run still outstanding** — this was the dev i5-4300U *floor*, not the
  teammate's reference i5. Re-run `run_benchmark.sh` there for the reference row.
- Optional follow-ups: Layer-B/human grade to pin the true pass rate under the 74.3%
  ceiling; investigate the 5 false abstentions as the highest-value accuracy lever.

---

## 6. Repo state this session

- `fix(app)` ×1, `test(app)` ×1, `fix(dev)` ×1 — the three e2e fixes from the prior
  session, committed + pushed first.
- `feat(app)` — surface Ollama generation stats (`eval_count`/`eval_duration`) on `AnswerResult`.
- `feat(bench)` — `run_benchmark.py` + `run_benchmark.sh` harness.
- `fix(bench)` — RAM sampler catches the `llama-server` runner.
- `docs(bench)` — `results/` (jsonl + summary + log), this report, STATUS.md update.
