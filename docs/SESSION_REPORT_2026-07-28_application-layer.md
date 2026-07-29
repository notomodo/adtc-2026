# Session report — application layer (`adtc-rag ingest` / `ask`)

**Date:** 2026-07-28 · **Branch:** `main` · **HEAD:** `fe1f504` · **Pushed:** yes (`2e8766c..fe1f504`)
**Suite:** 87 passed, 2 skipped (runtime+test stack — see "What is / isn't verified")

This session built the first real application layer: two CLI commands over the
existing, locked core. It is the first time the whole pipeline
(extract → chunk → embed → persist → retrieve → generate) exists end to end
rather than in eval harnesses and stubs.

---

## 1. What landed (4 commits, in order)

| commit | what |
|---|---|
| `7faaf67` `feat(app)` | `src/app/pipeline.py` — UI-agnostic glue |
| `e98aec2` `feat(app)` | `src/app/cli.py` + `pyproject.toml` — the `adtc-rag` CLI + console entry |
| `ca62147` `test(app)` | `tests/test_cli.py` + extended `tests/test_scripts_importable.py` |
| `fe1f504` `docs`      | `STATUS.md` — application layer landed |

Core (`src/core/index.py`, `src/retriever.py`, `src/gen_answer.py`,
`src/ingest_sme.py`) was **not touched**. The app imports core; core never
imports the app.

---

## 2. Architecture

```
adtc-rag ingest <pdf|dir>…   src/app/cli.py  ── presentation + exit codes only
adtc-rag ask "<question>"           │
                                    ▼
                         src/app/pipeline.py  ── UI-agnostic glue, structured results
                                    │
      ┌─────────────────────────────┼──────────────────────────────┐
      ▼                             ▼                               ▼
 scripts/migrate_chunk_ids    core.index.Index              gen_answer (prompt)
 ._extract_doc (faithful      (append-only, mmap dense,       + streaming Ollama
  char offsets, abort-not-    BM25+RRF hybrid, manifest        variant (new here)
  guess)                       identity guard)
```

**Key decisions**

- **One shared encoder identity for ingest + ask.** `core.index` fatally rejects a
  search whose `embedder_id`/`tokenizer_sha256` differ from what the index was built
  with (mixing embedding spaces makes every dense score meaningless). The pipeline owns
  a single `EncoderHandle` — `embedder_id="BAAI/bge-small-en-v1.5"`,
  `tokenizer_sha256 = sha256(src/tokenizer.json)` — identical to what
  `scripts/migrate_chunk_ids.py` produces, so an index built by either path is
  interchangeable.
- **Char offsets are faithful or ingestion aborts.** Reused `_extract_doc` locates each
  chunk body in the per-document text stream and **raises** if it can't — it never
  writes a guessed or zero span. (Stronger than the zero-span fallback the task allowed.)
- **Streaming generation is the one new thing.** `gen_answer.call_ollama` hard-codes
  `stream:false`; at 65–105 s/question that is indistinguishable from a hang. Added a
  streaming variant with **byte-identical** options (`temperature 0, seed 42,
  num_ctx 4096`) over stdlib `urllib` — no new dependency, same determinism as the
  benchmarked generation. The v3 grounding prompt (`SYSTEM_PROMPT`/`USER_TEMPLATE`) is
  imported **verbatim**, not rewritten.
- **The encoder is injectable and lazily built.** Tests pass a deterministic
  `FakeEncoder` and exercise every offline path (idempotency, empty-index guard,
  mismatch guard) with no onnxruntime, no `.onnx` file, and no Ollama. The real ONNX
  build only happens on first ingest/ask.

**CLI behaviour**

- `ingest`: recurses directories for `*.pdf`; per-document progress
  (extracting / embedding N / appended); **idempotent by sha256** — a re-ingested file
  is skipped *before* extraction and reported "already indexed"; prints index stats
  (docs, chunks, bytes) at the end.
- `ask`: `retrieving…`/`generating…` banner before the first token; **streams** the
  answer; prints **citations** `[file, p.N]` from the hits actually used; on
  **abstention** (`NOT_IN_DOCUMENTS`) prints the `SearchResult.considered` near-misses
  with `rrf_score` so the abstention is verifiable; `--verbose` dumps chunk ids,
  bm25/dense ranks, rrf scores and retrieval timings; every run surfaces
  encoder-init / retrieval / generation wall-clock.
- Empty index → exit **3** with `No documents indexed. Run: adtc-rag ingest <path>`
  (a pre-generation guard; no crash).

---

## 3. How to run and test it

### 3.1 Prerequisites (target machine)

```bash
# runtime deps + the console entry point (editable install is intended:
# the extraction bridge lives in scripts/ and the .onnx model in models/)
pip install -e .                      # numpy, pdfplumber, tokenizers, onnxruntime + adtc-rag

# the shipping encoder (gitignored, ~127 MB). Already present at
# models/bge-small-en-v1.5.onnx; rebuild reproducibly with the bench stack if absent:
#   pip install -r requirements-bench.txt && python scripts/export_onnx.py

# local generation model
ollama serve &                        # if not already running
ollama pull qwen2.5:3b-instruct
```

### 3.2 The real end-to-end run

```bash
# ingest the 5-PDF Kibuga corpus (minutes-long embed on an HDD laptop — progress prints)
adtc-rag ingest data/raw
# or explicit files:  adtc-rag ingest data/raw/*.pdf

# re-run to see idempotency: every doc reports "already indexed", chunk count unchanged
adtc-rag ingest data/raw

# ask an answerable question (streams; prints citations + timings)
adtc-rag ask "What is the return window?"
adtc-rag ask "How do I contact seller support?" --verbose

# ask an UNanswerable one to see abstention show its work (near-misses + rrf scores)
adtc-rag ask "What is MTN's H1 2024 revenue?"
```

Index lives at `~/.adtc/index` by default; add `--index-dir <path>` to isolate a run.

### 3.3 Automated tests

```bash
pip install -r requirements-dev.txt   # pytest
pytest -q                             # full suite

# app layer only:
pytest tests/test_cli.py tests/test_scripts_importable.py -v
```

- **Offline (always run):** ingest/append, progress events, sha256 idempotency, the
  empty-index guard (incl. through the real CLI → exit 3), the encoder-mismatch
  known-bad control (must raise), and citation/abstention/verbose formatting — all with
  a `FakeEncoder`, no heavy deps.
- **`tests/test_cli.py::test_ingest_then_ask_end_to_end`** is the real-path test: it
  drives the actual `OnnxEncoder` + live Ollama. It **skips** cleanly unless
  `models/bge-small-en-v1.5.onnx` exists *and* Ollama answers on `localhost:11434`.
  On the target machine with both present, it runs and asserts the streamed text equals
  the final answer.

### 3.4 What "good" looks like

- `ingest data/raw` → 5 documents, ~47 chunks, an `~/.adtc/index` with
  `chunks.jsonl` / `embeddings.npy` / `bm25.json` / `manifest.json`.
- Answerable `ask` → a grounded answer + `Sources: [Return_Policy.pdf, p.N]`.
- Unanswerable `ask` → `NOT_IN_DOCUMENTS`, then a "Nearest passages considered" list.
- `pytest -q` → green (heavy paths skip when their deps are absent).

---

## 4. What is / isn't verified

**Verified (this session, offline):**
- 87 passed / 2 skipped on the runtime+test stack (numpy, pdfplumber, tokenizers,
  pytest — no torch/onnxruntime/Ollama).
- All app logic: ingest/idempotency, guards, streaming↔final consistency (via the
  callback contract), citation/abstention/verbose rendering.
- `adtc-rag --help`, `ingest --help`, `ask --help`, the empty-index CLI path (exit 3),
  and the bad-path CLI error (exit 2) — run as the real binary.

**NOT yet verified (needs the reference machine):**
- The **live** `OnnxEncoder` + real PDFs + Ollama end-to-end. This box has no
  onnxruntime and no running Ollama, so the real encode+generate path has not executed
  in-session. The e2e test *will* cover it where those are present.
- Real wall-clock numbers (encoder init / retrieval / generation) on the HDD laptop.

---

## 5. Readiness

**Ready for a supervised reference-machine run — not yet "known-working end to end".**
The logic is complete and green offline, the real path is gated behind a clean-skipping
e2e test, and every artifact it needs (model, tokenizer, PDFs, dump) is in place. The
one thing standing between "written + offline-green" and "demonstrated" is running §3.2
on a box with onnxruntime + Ollama. Expect the first ingest to take minutes on an HDD
and generation ~65–105 s/question.

---

## 6. Open items (unchanged from STATUS.md unless noted)

- **Dependency manifests to reconcile:** `onnxruntime` is now declared in
  `pyproject.toml` runtime deps (the app needs it) but is still absent from
  `requirements.txt`. Make the pip-install path match the packaged one.
- **int8 quantisation deferred** — shipped ONNX is fp32 (~127 MB) for bake-off parity.
- **`.onnx` sha is stack-dependent**, not weight-only — the reproducibility contract is
  the parity gate, not the blob sha (DECISION-002 §10.4).
- Non-goals held this session: no web UI, no `--onnx-path` on `eval_retriever`, no core
  refactor.
