# STATUS — adtc-2026

**Single source of truth. Overwritten each session.**
Last updated: 2026-07-27 · Branch: `main`

---

## Where we are on the critical path

RAG retrieval for the Kibuga SME corpus. Retrieval is **locked and now shipped-real**:

```
ingest → chunk dump (47 chunks, fingerprint-gated) → hybrid retrieval
   BM25 (stdlib) + bge-small-en-v1.5 dense (ONNX, CLS pooling) fused by RRF
   ↳ DECISION-002: hybrid + bge. Numbers now measured on the SHIPPED encoder.
```

- ✅ **ONNX encoder shipped and verified.** bge exported (fp32, `scripts/export_onnx.py`),
  `OnnxEncoder` pools CLS (was silently mean-pooling), parity with the
  sentence-transformers bake-off proven to 1e-7 across lengths + padding. Corrected
  encoder reproduces DECISION-002's n=19 numbers exactly (dense 47/74/89/95 MRR 0.636;
  hybrid 58/84/89/95 MRR 0.703). See DECISION-002 §10.
- ✅ **Chunk-dump parser** byte-faithful + fatal fidelity gate (prior session).
- ✅ **Tooling hardened** — all `scripts/` modules import cleanly and answer `--help`
  (locked by `tests/test_scripts_importable.py`).

**Full test suite: 90 passed** (run under the benchmark stack; retrieval-only CI skips
the parity/export tests when torch/onnxruntime are absent).

---

## Next action

**Build the application layer** (DECISION-002 §9.5): retrieval is good enough; the
end-to-end system (retrieve → prompt → Qwen2.5-3B generation → grounded answer) does
not exist yet. *Not started — do not start without direction.*

---

## Blocked / open items (none blocking the above)

- **`onnxruntime` is not declared in `requirements.txt`** though it is a *runtime* dep
  (numpy, tokenizers, pdfplumber, onnxruntime). Same class of gap as the undeclared
  `onnx` build dep just fixed. Declare in a follow-up.
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

- **Latest content commit:** `7d556e2` (docs: reconcile §8). This `STATUS.md` commit sits
  on top as the session marker (branch tip).
- **This session's commits (ONNX + tooling):** pooling fix → export → parity gate →
  ONNX metrics doc → onnx build-dep → widened parity → sha/reproducibility doc →
  scripts import fix → scripts test → §8 reconcile → STATUS.
- **Uncommitted (by design):** `docs/SESSION_REPORT_2026-07-27_onnx-export.md` (detailed
  handoff, kept for review), plus earlier-session leftovers
  (`benchmarks/CHUNK_ID_MIGRATION_REPORT.md`, `benchmarks/chunk_id_migration_map.json`,
  `docs/SESSION_REPORT_2026-07-23*.md`).
- **`models/bge-small-en-v1.5.onnx`** is gitignored; `scripts/export_onnx.py` is the source.

---

## Build vs runtime deps (do not confuse)

- **Runtime (shipped):** numpy, tokenizers, pdfplumber, onnxruntime. No torch, ever.
- **Build/test only:** torch, transformers, sentence-transformers, onnx
  (`requirements-bench.txt`) + pytest.
