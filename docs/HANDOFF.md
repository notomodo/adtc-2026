# Handoff to Claude chat — adtc-rag model evaluation (2026-08-02)

**Repo:** adtc-2026 · **Commit:** `3169512` (origin/main == local). This brief is
self-contained: a Claude chat session has **no repo/filesystem access**, so everything
it needs must be in this doc or in an uploaded file (see the **Upload manifest** at the
end).

---

## 1. What this project is

A retrieval-augmented-generation (RAG) pipeline (`adtc-rag`) over a 5-PDF Kibuga SME
corpus (47 chunks): extract → chunk → embed (ONNX bge-small, CLS pooling) → hybrid
retrieve (BM25 + dense, RRF, k=3) → v3 grounding prompt → local Ollama generation with
citations / abstention. Retrieval is locked; the open question is **which generation
model to submit**.

## 2. The three-accuracy-numbers framing (do NOT conflate these)

1. **RAG end-to-end, Layer-A pass rate** — what these benchmarks measure: retrieval ×
   grounding × synthesis, graded by a **token-overlap heuristic** (`gen_judge.layer_a`).
2. **NOT `S_acc`** — that is the profiler's lm_eval MCQ on the bare GGUF. Never call
   these numbers "leaderboard accuracy."
3. **NOT DECISION-002 R@k** — the `gold_chunk_hit` figure here is a coarse k=3 retrieval
   sanity signal, not R@k.

**Layer-A has two biases, and both matter:** it **overestimates** faithfulness
(confirmed false positives — the R5/Q19 finding) AND it **length-penalizes terser
models** (a correct one-line answer can score WEAK/FAIL on overlap). So the raw pass
rates below are a **biased proxy, not a faithfulness ranking**.

## 3. What was done and found

Three controlled runs on the **same** harness — only the generation model changed
(Qwen3 additionally ran with thinking disabled to match the non-thinking Qwen2.5
regime; that knob leaves the 2.5 runs byte-identical). **Integrity verified:**
`gold_chunk_hit` **28/28 identical** and retrieved-id order byte-identical across all
three, so every accuracy delta is generation-only.

| | 3B | 1.5B | Qwen3-4B |
|---|---|---|---|
| Ollama model / quant | `qwen2.5:3b-instruct` · Q4_K_M | `qwen2.5:1.5b-instruct-q4_K_M` | `qwen3:4b-q4_K_M` (dense) |
| License | Qwen **Research** (non-commercial) | **Apache-2.0** | **Apache-2.0** |
| **Layer-A pass rate** | **26/35 = 74.3%** | **22/35 = 62.9%** | **23/35 = 65.7%** |
| Abstention (correct / 6 probes) | 6/6 | 6/6 | **5/6** (U04 hallucinated) |
| False abstentions (answerable) | 5 | 3 | 3 |
| Gen speed (tok/s median) | 4.98 (idle) | 9.29 (contended, ≥ lower bound) | **2.83 (idle)** |
| Memory (runner RSS / peak system) | ~2.05 GB / 4584 MB | — (contended) | **~5.7 GB / 7437 MB** |
| Machine state during run | floor (~idle) | contended | idle |

**Key reads:**
- On the raw proxy: **3B > Qwen3-4B > 1.5B**, but the per-question diffs show **most of
  the gaps are the length bias, not faithfulness**. On substance the 3B and Qwen3-4B are
  close; Qwen3-4B recovers exact_fact (10/10) and leads multi_chunk (4/5).
- **Coverage vs safety trade-off:** the 3B is most conservative (6/6 probes but
  over-abstains on 5 answerable). The 1.5B and Qwen3-4B answer more, but each has **one
  confident hallucination the 3B avoided** — 1.5B on **Q27** (answered from the wrong
  chunk), Qwen3-4B on **U04** (answered an unanswerable probe).
- **Efficiency (clean, idle):** **Qwen3-4B is the slowest and heaviest** — ~2.8 tok/s and
  ~5.7 GB, **nearly saturating the 7.7 GB box**. So Qwen3-4B **trades the 3B's license
  risk for a real perf/memory cost** — the opposite trade-off, not a strict improvement.
- Note on Qwen3-4B's abstention: its auto-summary shows "3/6" because the pipeline's
  `abstained` flag is `startswith("NOT_IN_DOCUMENTS")` and Qwen3 wraps the sentinel in
  prose; the grader-correct number is **5/6** (U04 the one genuine miss).

## 4. Open decisions (these are what the chat session is for)

- **A — The model choice** (a human call, NOT made by the benchmark). Weigh three axes:
  (1) true accuracy, (2) efficiency (Qwen3-4B clearly weakest), (3) license (only the 3B
  at risk). The data says Qwen3-4B is license-clean but slow/heavy; the 3B is fastest-
  accurate but non-commercial; the 1.5B is lightest but lowest-quality.
- **B — Layer-B / human faithfulness grade** (the #1 follow-up). The Layer-A numbers are
  a biased proxy; a faithfulness-aware grade is needed to know the *real* ranking. The
  **`grading_pack.md`** file is a self-contained substrate built exactly for this — do it
  in chat.
- **C — License eligibility.** Whether the 3B's non-commercial license disqualifies a
  submission is a **rules question** — it needs the competition's eligibility terms
  (upload the rules doc). The benchmark cannot settle it.

## 5. Suggested chat prompts (pick the task)

- *Layer-B grade:* "Using the uploaded grading_pack.md, grade each model's answer on
  faithfulness to the retrieved context per the rubric, then tell me where your Layer-B
  verdicts disagree with Layer-A and what the corrected three-way ranking looks like."
- *Decision write-up:* "Using HANDOFF.md and model_comparison.md, draft the model-choice
  section weighing accuracy, efficiency, and license — present the trade-off, do not pick
  for me."
- *License:* "Given this competition rules doc [upload] and the license column in
  HANDOFF.md, is the Qwen2.5-3B (Qwen Research, non-commercial) eligible?"

---

## 6. UPLOAD MANIFEST — exactly what to attach in Claude chat

All paths are in the repo at commit `3169512`. Download these and attach them.

**Always upload (core):**
- `docs/HANDOFF.md` — this brief (orientation + numbers).

**For the Layer-B faithfulness grade (task B — the top follow-up):**
- `docs/grading_pack.md` — **self-contained**; per-question retrieved context + all three
  models' answers + Layer-A verdicts + a Layer-B fill-in column. **Sufficient on its own**
  for this task (you do NOT need the raw jsonl or question sets — they are already joined
  into it).

**For the model-decision write-up (task A):**
- `docs/model_comparison.md` — the full three-way tables (accuracy, abstention,
  verdict-diff, perf, memory) with all caveats.
- *(optional, for raw appendix numbers)* the three run summaries:
  `results/benchmark_20260729T065644Z_summary.md` (3B),
  `results/benchmark_20260802T090940Z_1p5b_summary.md` (1.5B),
  `results/benchmark_20260802T095051Z_qwen3-4b_summary.md` (Qwen3-4B).

**For the license question (task C):**
- Your **competition rules / eligibility document** (not in this repo — you provide it).
- `docs/model_comparison.md` (for the license column / context).

**You do NOT need to upload** (already synthesized into the above): the raw
`results/benchmark_*.jsonl`, the question sets (`data/questions/*.json`), or the chunk
dump (`benchmarks/chunks_sme.txt`). Attach them only if the chat session needs to
recompute something from scratch.
