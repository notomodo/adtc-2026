# STATUS — adtc-2026

**Single source of truth. Overwritten each session.**
Last updated: 2026-08-14 · Branch: `main`

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

**Full test suite: 92 passed, 2 skipped** (re-verified 2026-08-14 takeover: 9.76 s) under
the runtime+test stack (numpy, pdfplumber, tokenizers, pytest — no torch/onnxruntime/Ollama).
The 2 skips: the torch-dependent ONNX parity/export module, and the opt-in `ingest→ask` e2e
(needs the `.onnx` model + a live Ollama; Ollama is currently NOT running on this box —
`sudo systemctl start ollama` to enable). New this session: `test_answer_surfaces_ollama_generation_stats`
locks the `AnswerResult.gen_stats` contract the benchmark harness depends on.

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
CPU. **Model decision made 2026-08-14 (human + primary rules read): Qwen2.5-3B is the chosen
submission model** — top performer on the evidence AND not license-disqualified under the
published rules (see "Next action" below). **✅ Layer-B faithfulness grade DONE (2026-08-14):
3B remains the right choice** — Qwen3-4B is at parity on faithfulness-when-given-the-chunk
(28/28 vs 27/28) but fails one probe and near-saturates 8 GB; the 1.5B is clearly weakest
(`docs/LAYER_B_GRADE_2026-08-14.md`). Still pending: matched-idle perf for the 1.5B/3B, and
the reference-machine run (R1).

## Next action

**License: RESOLVED (2026-08-14).** Primary rules read directly — official Devpost rules
(`adtc-2026.devpost.com/rules`) + the Challenge Participation Agreement: **no model-license
eligibility constraint**. The open-source requirement applies to the submission's own GitHub
repo (public, MIT — ✓) and tools must be cited clearly. The 3B's Qwen **Research**
(non-commercial) license is **not disqualifying** under the published rules. Judging
(published): 50% accuracy/quality, 30% throughput, 20% RAM efficiency, +10 African-use-case,
−10 thermal, **OOM/sandbox crash = disqualification**. Gate 1 deadline: **2026-08-25**.

1. **Reference-machine benchmark (R1) — now deadline-critical.** Run `run_benchmark.sh` on
   the actual 8 GB ADTC Standard Laptop (i5 10th–12th gen / Ryzen 5, Ubuntu 22.04). The floor
   numbers come from an older 2-core Haswell box; co-resident fit on the real target is still
   unmeasured, and OOM is a disqualifier.
2. **✅ Layer-B / human grade — DONE (2026-08-14).** LLM-judge faithfulness grade of all 41
   questions × 3 models from `docs/grading_pack.md` (verdicts appended there + full report
   `docs/LAYER_B_GRADE_2026-08-14.md`). Faithfulness 3B 29/35, Qwen3-4B 30/35, 1.5B 28/35;
   gold-hit faithfulness 27/28, 28/28, 26/28; substantive unique hallucinations 0, 2, 2;
   probes 6/6, 5/6, 6/6. **The 3B's Layer-A lead is largely length-bias artifact; its real
   edge is safety + efficiency. Choice unchanged: 3B.** Human spot-check of the shaded rows
   recommended before quoting externally.
3. **🟡 Gate-1 submission pack — DRAFTED + WEIGHTS TESTED (2026-08-14).** Official template
   followed (`Africa-Deep-Tech-Foundation/adtc-2026-submission-template`): `metadata.json`
   (domain `corporate_enterprise`, 2 test prompts, model Qwen2.5-3B-Instruct-Q4_K_M,
   llama.cpp/GGUF — **schema-validated** against the official profiler schema),
   `download_model.sh` (**tested end-to-end**: 2.0 GB GGUF downloaded from the official
   Qwen HF repo, sha256 `626b4a66…5c62d` verified, valid GGUF header), `REPORT.md`
   (technical writeup incl. the official scoring formula
   S_total = 0.50·S_acc + 0.30·S_perf + 0.20·S_eff − P_thermal), `.gitignore`,
   `docs/GATE1_SUBMISSION.md` (checklist + video script), `docs/GATE1_RUNBOOK.md`,
   `docs/screenshots/` (real ingest capture: 5 docs → 47 chunks, 40 s). **✅ Profiler
   participant run DONE (dev floor): S_acc 0.80 arc_easy (n=50), 4.32 tok/s, peak RSS
   3456 MB (S_eff 50.6), **thermal throttled at 94 °C (10-pt penalty on this old dev
   CPU — R1 must check the reference machine)**; score preview ≈48.8 on the floor box
   (`results/profiler_participant_20260814.md`).** Remaining: confirm 3 metadata fields
   (team_id, submitter email/name, african_alpha_claim) + test-prompt wording; record the
   ≤2-min video; capture the ask-demo with Ollama up; R1 reference-machine run.
   Submission framing: the scored artifact is the GGUF model via llama.cpp (profiler),
   the RAG system is the showcased product layer. Gate 1: **2026-08-25**.
4. **Optional: matched-idle perf** for the 1.5B (and a fresh 3B) so the perf table's 1.5B row
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

## Takeover verification (2026-08-14)

Independently verified against the working tree + a fresh `git fetch origin` (plain fetch
fails here: the system `/etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf` has bad owner/
permissions; `GIT_SSH_COMMAND='ssh -F /dev/null'` works). **No drift: 0 ahead / 0 behind
`origin/main`; single branch `main`, no tags/stashes/worktrees.**

**Matches the handoff doc (verified by running/reading, not assumed):**
- Architecture: `app/pipeline.py` glue (one encoder identity), `app/cli.py` `adtc-rag`
  console script (smoke-tested `--help`), `core/index.py` append-only + crash-recovery
  tests, `retriever.py` BM25+RRF (NOT the empty `src/retrieval/` stub), `gen_answer.py`
  v3 prompt (temp 0 / seed 42 / num_ctx 4096 payload confirmed in `_build_payload`).
- Pinned torch-free runtime deps (numpy 2.2.1 / pdfplumber 0.11.9 / tokenizers 0.21.0 /
  onnxruntime) agree across `pyproject.toml` + `requirements.txt`.
- Corpus: 5 PDFs → 47 chunks; fingerprint `c7f23f29b738b08d` gate PASSES
  (`scripts/verify_reproducibility.py` → OK) and is CI-enforced (ci.yml asserts 47 chunks).
- **Tests: 92 passed, 2 skipped** (torch absent; Ollama e2e gate). Earlier "88" in this
  file was stale.
- Retrieval n=35: R@1 60 / R@5 83 / MRR 0.704 / prose R@5 62% (retrieval_n35/README).
- Reranker: n=19 rejected (D003), n=35 decided not shipped (D005, Q31+Q27 regressions);
  `src/eval_reranker.py` standalone.
- Floor benchmark: 74.3% (26/35) Layer-A, 6/6 abstention, ~5 tok/s, peak 4584 MB —
  committed summary + R5 record (9/10 PASSes correct, Q19 UNGROUNDED — proxy, never
  accuracy).
- Three-way comparison: 3B 74.3% > Qwen3-4B 65.7% (23/35) > 1.5B 62.9% (22/35),
  retrieval byte-identical (28/28), Qwen3-4B slowest/heaviest (2.83 tok/s, peak 7437 MB,
  runner RSS 6046 MB), licenses Qwen Research (non-commercial) vs Apache-2.0, **no
  recommendation made**.
- DECISIONS.md D4 is stale relative to the 2 Aug comparison (still "Locked 7 July") —
  flagged, deliberately NOT edited (human call). `grade_v3.py` stale `chunks_sme.fp.txt`
  (line 9, file absent). Dead stubs `src/retrieval/` + `src/llm/` (empty `__init__.py`).
  `eval_retriever.py` lacks `--onnx-path`. int8 deferred. `gen_answer.v_prev.py` kept.

**Discrepancies / nuances found:**
- "Repo clean" was imprecise: 4 untracked items — `adtc_pipeline_walkthrough.ipynb`
  (17-cell demo notebook **exists locally but is NOT committed** — commit decision
  pending), `Untitled.ipynb` (empty), `.ipynb_checkpoints/`, `test-run.log`.
- DECISION-002's "only configuration non-negative on every metric" is imprecise:
  gte-small is also non-negative vs BM25 on R@1/R@3/R@5/R@10/MRR; bge strictly dominates
  it (R@3 +5pp, MRR 0.703 vs 0.687) so the selection stands — documentation wording only.
- STATUS previously listed three docs session reports as untracked; they are now committed
  (2fc1cbe). Qwen3-4B runner RSS: 6046 MB vs "~5.7 GB" in STATUS/HANDOFF — rounding only.

**Could not verify here (external):** 8 GB reference machine results (R1 — zero data in
repo, highest-severity open risk); license eligibility vs ADTC 2026 rules (rules doc not
in repo); Layer-B/human grade (grading_pack.md is the ready substrate); ONNX parity to
1e-7 not re-run (torch not installed; committed DECISION-002 §10 + gated test stand).

## Repo state

- **This session (floor benchmark):** three prior-session e2e fixes (`fix(app)` /
  `test(app)` / `fix(dev)`, pushed) → `feat(app)` surface Ollama gen stats →
  `feat(bench)` harness + runbook → `fix(bench)` RAM sampler catches `llama-server` →
  `docs(bench)` results + this STATUS. Built on `01b13c3`.
- **Now tracked:** `benchmarks/chunk_id_migration_map.json` (+ its
  `CHUNK_ID_MIGRATION_REPORT.md`) — the verified positional→stable map is a live
  dependency of the benchmark harness (`gold_chunk_hit`), so it belongs in the repo.
- **Untracked as of 2026-08-14:** `adtc_pipeline_walkthrough.ipynb` (demo notebook —
  exists locally, NOT committed; decide whether to add), `Untitled.ipynb` (empty),
  `.ipynb_checkpoints/`, `test-run.log`. The three docs session reports previously listed
  here are now committed (2fc1cbe).
- **`models/bge-small-en-v1.5.onnx`** is gitignored; `scripts/export_onnx.py` is the source.

---

## Build vs runtime deps (do not confuse)

- **Runtime (shipped):** numpy, tokenizers, pdfplumber, onnxruntime. No torch, ever.
- **Build/test only:** torch, transformers, sentence-transformers, onnx
  (`requirements-bench.txt`) + pytest.
