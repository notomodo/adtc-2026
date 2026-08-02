# STATUS — adtc-2026

**Single source of truth. Overwritten each session.**
Last updated: 2026-07-29 · Branch: `main`

---

## Where we are on the critical path

RAG for the Kibuga SME corpus. Retrieval is **locked + shipped-real**; the
**application layer now exists** and runs the whole pipeline end to end:

```
adtc-rag ingest <pdf…>  → extract + chunk + embed (ONNX bge, CLS) + persist (append-only index)
adtc-rag ask "<q>"      → hybrid retrieve (BM25 + dense, RRF) → v3 grounding prompt
                          → streamed Qwen2.5-3B answer + citations / abstention-with-near-misses
```

- ✅ **Application layer landed** (this session). Two commands over the existing core,
  no core changes:
  - `src/app/pipeline.py` — UI-agnostic glue. Owns one shared encoder identity for
    ingest+ask, reuses `scripts/migrate_chunk_ids._extract_doc` (faithful char offsets,
    aborts rather than guessing), reuses `gen_answer`'s v3 prompt verbatim, adds a
    **streaming** Ollama variant (same options: temp 0, seed 42, num_ctx 4096).
  - `src/app/cli.py` — argparse `adtc-rag`; all presentation + exit codes here.
    Per-doc progress, sha256 idempotency ("already indexed"), empty-index guard
    (exit 3 with guidance), citations `[file, p.N]`, abstention prints
    `SearchResult.considered` near-misses, `--verbose` dumps ranks/rrf/timings, and
    per-run wall-clock (encoder init / retrieval / generation).
  - `pyproject.toml` — console entry `adtc-rag = app.cli:main` (editable install:
    the bridge lives in `scripts/`, the gitignored `.onnx` in `models/`).
- ✅ **ONNX encoder shipped and verified.** bge exported (fp32, `scripts/export_onnx.py`),
  `OnnxEncoder` pools CLS (was silently mean-pooling), parity with the
  sentence-transformers bake-off proven to 1e-7 across lengths + padding. Corrected
  encoder reproduces DECISION-002's n=19 numbers exactly (dense 47/74/89/95 MRR 0.636;
  hybrid 58/84/89/95 MRR 0.703). See DECISION-002 §10.
- ✅ **Chunk-dump parser** byte-faithful + fatal fidelity gate (prior session).
- ✅ **Tooling + app hardened** — all `scripts/` and `src/app/` modules import cleanly,
  every CLI answers `--help` (locked by `tests/test_scripts_importable.py`); the app
  logic (idempotency, empty-index/mismatch guards, citations/abstention formatting) is
  covered offline by `tests/test_cli.py` with a `FakeEncoder`.

**Full test suite: 88 passed, 2 skipped** under the runtime+test stack (numpy, pdfplumber,
tokenizers, pytest — no torch/onnxruntime/Ollama). The 2 skips: the torch-dependent ONNX
parity/export module, and the opt-in `ingest→ask` e2e (needs the `.onnx` model + a live
Ollama). New this session: `test_answer_surfaces_ollama_generation_stats` locks the
`AnswerResult.gen_stats` contract the benchmark harness depends on.

---

## Floor-hardware benchmark — DONE (2026-07-29)

Full 41-question end-to-end sweep on the dev **floor** box (4-core i5-4300U-class,
7.7 GB, CPU-only Ollama), harness `scripts/run_benchmark.py` + `run_benchmark.sh`,
committed under `results/benchmark_20260729T065644Z.*`. 0 failures, ~39 min.

- **RAG end-to-end accuracy: 26/35 = 74.3%** (Layer-A pass rate — a **known
  overestimate**; token-overlap grader with confirmed false positives R5/Q19).
  This is NOT S_acc and NOT DECISION-002 R@k.
- **Abstention: 6/6 correct** on unanswerable probes; **5 false abstentions** on
  answerable (Q08/Q17/Q27/Q29/Q35) — the top accuracy lever.
- **Generation: ~5 tok/s** (median 4.98; CPU-only 3B), ~55 s/question median.
  Retrieval ~25 ms — generation is the entire cost.
- **Peak RAM: 4584 MB (+3166 over a 1418 MB idle baseline)**; model runner
  (`llama-server`) resident ~2054 MB. System-footprint RAM, distinct from S_eff.
- Report: `docs/SESSION_REPORT_2026-07-29_floor-benchmark.md`.

## Model comparison: 3B vs 1.5B vs Qwen3-4B (2026-08-02)

Controlled reruns of the **same** harness with **only the generation model changed**,
evaluating two alternatives to the 3B. Both alternatives are **Apache-2.0** vs the 3B's
Qwen **Research** (non-commercial) license. Full three-way side-by-side:
`docs/model_comparison.md`. Artifacts: `results/benchmark_20260802T090940Z_1p5b.*`
(1.5B) and `results/benchmark_20260802T095051Z_qwen3-4b.*` (Qwen3-4B). Harness gained a
parameterized `--think` knob (`feat(app)` 104c58c) so Qwen3 runs with thinking disabled
while the 2.5 runs stay byte-identical.

- **Integrity proven (all 3 runs):** retrieval held fixed — `gold_chunk_hit` **28/28
  identical** and retrieved-id order byte-identical. Every accuracy delta is generation-only.
- **Layer-A pass rate: 3B 74.3% (26/35) > Qwen3-4B 65.7% (23/35) > 1.5B 62.9% (22/35).**
  BUT the per-question diffs show the gaps are **substantially the grader's answer-length
  bias, not faithfulness** — the 1.5B and Qwen3-4B paraphrase tersely and lose token-overlap
  on *correct* answers. On substance the 3B and Qwen3-4B are close; Qwen3-4B recovers
  exact_fact (10/10) and leads multi_chunk (4/5).
- **Abstention / coverage trade-off:** 3B is most conservative (6/6 probes, but over-abstains
  on 5 answerable). The 1.5B and Qwen3-4B answer more but each has **one confident
  hallucination** the 3B avoided — 1.5B on **Q27** (wrong chunk), Qwen3-4B on **U04** (answered
  an unanswerable probe; its grader-correct abstention is **5/6**, not the auto-summary's
  flag-based "3/6" — Qwen3 wraps the sentinel in prose so `startswith` undercounts).
- **Efficiency — Qwen3-4B is the SLOWEST and HEAVIEST (idle, clean measurement):** ~2.83 tok/s
  (vs 3B 4.98, 1.5B 9.29≥) and **~5.7 GB runner RSS / peak 7437 MB — nearly saturating the
  7.7 GB box** (~2.8× the 3B). The 1.5B row is a lower bound (it ran contended). So Qwen3-4B
  **trades the 3B's license risk for a real perf/memory cost** — not a strict improvement.

**Decided by these runs:** retrieval is model-independent/stable; the Layer-A gaps overstate
the true accuracy differences; Qwen3-4B is license-clean but the slowest/heaviest option on
CPU. **Pending (decided elsewhere):** true faithfulness ranking (Layer-B/human grade — top
follow-up), matched-idle perf for the 1.5B/3B, and whether the 3B's non-commercial license is
competition-eligible (a rules question). **No model recommendation is made from this data.**

## Next action

1. **Layer-B / human grade** of the three runs to pin the real faithfulness ranking under the
   length-biased Layer-A ceiling — the highest-value follow-up before any model switch.
2. **Confirm license eligibility** against the competition rules — the only axis on which the
   3B (Qwen Research, non-commercial) differs from the Apache-2.0 alternatives.
3. **Optional: matched-idle perf** for the 1.5B (and a fresh 3B) so the perf table's 1.5B row
   stops being a lower bound. Qwen3-4B and the 3B floor are already ~idle and comparable.

---

## Blocked / open items (none blocking the above)

- ✅ **`onnxruntime` manifests reconciled** — now declared in BOTH `pyproject.toml` and
  `requirements.txt` (`fix(deps)`, commit `7d0ebc5`). The runtime-deps `run_benchmark.sh`
  venv install (numpy/onnxruntime/pdfplumber/tokenizers, no torch) proves the two agree.
- **int8 quantisation deferred.** Shipped ONNX is fp32 (~127 MB) for bake-off parity;
  int8 is a future size optimisation on its own parity budget (DECISION-002 §8, §10.3).
- **`.onnx` sha is stack-dependent**, not weight-only: canonical `b7513a6a…` holds only
  for the pinned declared stack (transformers 4.55.4). The reproducibility contract is
  the parity gate, not the blob sha (DECISION-002 §10.4).
- **`grade_v3.py`** references an absent `chunks_sme.fp.txt` (stale one-off; harmless).
- **`eval_retriever.py` CLI** wires only `SentenceTransformerEncoder`; ONNX benchmarking
  was done via a scratch harness. Adding `--onnx-path` is a deliberate non-goal for now.

---

## Repo state

- **This session (floor benchmark):** three prior-session e2e fixes (`fix(app)` /
  `test(app)` / `fix(dev)`, pushed) → `feat(app)` surface Ollama gen stats →
  `feat(bench)` harness + runbook → `fix(bench)` RAM sampler catches `llama-server` →
  `docs(bench)` results + this STATUS. Built on `01b13c3`.
- **Now tracked:** `benchmarks/chunk_id_migration_map.json` (+ its
  `CHUNK_ID_MIGRATION_REPORT.md`) — the verified positional→stable map is a live
  dependency of the benchmark harness (`gold_chunk_hit`), so it belongs in the repo.
- **Still untracked (older handoffs, left for review):** `docs/SESSION_REPORT_2026-07-23.md`,
  `docs/SESSION_REPORT_2026-07-28_application-layer.md`, `docs/SESSION_REPORT_2026-07-28_e2e-run.md`.
- **`models/bge-small-en-v1.5.onnx`** is gitignored; `scripts/export_onnx.py` is the source.

---

## Build vs runtime deps (do not confuse)

- **Runtime (shipped):** numpy, tokenizers, pdfplumber, onnxruntime. No torch, ever.
- **Build/test only:** torch, transformers, sentence-transformers, onnx
  (`requirements-bench.txt`) + pytest.
