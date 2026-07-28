# STATUS — adtc-2026

**Single source of truth. Overwritten each session.**
Last updated: 2026-07-28 · Branch: `main`

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

**Full test suite: 87 passed, 2 skipped** under the runtime+test stack (numpy, pdfplumber,
tokenizers, pytest — no torch/onnxruntime/Ollama). The 2 skips: the torch-dependent ONNX
parity/export module, and the opt-in `ingest→ask` e2e (needs the `.onnx` model + a live
Ollama). Under the full benchmark stack the parity tests run and pass (was 90 passed).

---

## Next action

**Reference-machine performance run.** The app surfaces real per-run wall-clock
(encoder init / retrieval / generation) but has not been measured on the target
HDD laptop against the live model. Do a formal `ingest`+`ask` timing pass there
(minutes-long embed on HDD; 65–105 s/question generation expected). Not a code
task — a machine-time measurement session.

---

## Blocked / open items (none blocking the above)

- **`onnxruntime` is now declared in `pyproject.toml` runtime deps** (the app needs it),
  but **still absent from `requirements.txt`** — reconcile the two dependency manifests
  in a follow-up so the pip-install path matches the packaged one.
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

- **This session (application layer):** `feat(app)` pipeline glue → `feat(app)` adtc-rag
  CLI + pyproject → `test(app)` CLI/guards + extend import smoke to `src/app/` → this
  STATUS. Built on `2e8766c` (prior session tip).
- **Uncommitted (by design):** earlier-session leftovers
  (`benchmarks/CHUNK_ID_MIGRATION_REPORT.md`, `benchmarks/chunk_id_migration_map.json`,
  `docs/SESSION_REPORT_2026-07-23.md`).
- **`models/bge-small-en-v1.5.onnx`** is gitignored; `scripts/export_onnx.py` is the source.

---

## Build vs runtime deps (do not confuse)

- **Runtime (shipped):** numpy, tokenizers, pdfplumber, onnxruntime. No torch, ever.
- **Build/test only:** torch, transformers, sentence-transformers, onnx
  (`requirements-bench.txt`) + pytest.
