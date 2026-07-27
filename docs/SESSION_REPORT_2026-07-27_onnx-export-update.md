# Session report — shipping ONNX encoder + a silent pooling bug

**Date:** 2026-07-27
**Branch:** `main` — **pushed** (`04c9040..74bf85a`, 11 commits)
**Scope:** DECISION-002 §9.4 — produce the shipping ONNX encoder for bge-small-en-v1.5
(+ two follow-up rounds: pre-push reproducibility hardening, and tooling-import fixes).
No change to the index, ingestion, or any published §1 number.
**Status:** complete and pushed. Full suite **90 passed**. The corrected ONNX encoder
reproduces DECISION-002's bge numbers **exactly**. Authoritative live state lives in
repo-root `STATUS.md`; this report is the detailed narrative.

This report is self-contained and can be handed to Claude chat without repo access.

> **Pre-push hardening (2026-07-27, after a local Debian run):** three refinements
> before pushing — see §10.
> 1. **Reproducibility gap fixed.** `onnx` (the serialization backend) was in no
>    requirements file, so a clean clone's export died at write time with "Module
>    onnx is not installed!". Now declared: `requirements-bench.txt` pins
>    `onnx==1.22.0`. Export confirmed to run from declared requirements alone.
> 2. **Canonical sha changed to `b7513a6a…c781f67`** (was `1a6ff430…`). The blob's
>    sha is a function of the exporting `transformers` version; the declared stack
>    installs 4.55.4 (ST 3.3.1 caps `<5`), last session used off-spec 5.14.1. Same
>    weights, numerically-identical graph, different serialized bytes. The parity
>    gate — not the sha — is the reproducibility contract. Details §10.
> 3. **Parity widened** across sequence lengths + padding (single-token, 394-token
>    full budget, real chunks, a 6-token string padded ~65× in a batch): worst case
>    min cosine 1.000000, max abs 1.9e-07. Tracer warnings empirically defused.

---

## 1. One-paragraph summary

The shipping dense encoder (`retriever.OnnxEncoder`) never had an actual `.onnx`
file — every dense number in DECISION-002 was measured with
`SentenceTransformerEncoder`, and everything downstream ran on a stub. Producing
the real export surfaced a **silent pooling bug**: `OnnxEncoder` **mean-pooled**
the transformer's last hidden state, but `bge-small-en-v1.5` uses **CLS pooling**
(its `1_Pooling/config.json` says so, and that is what sentence-transformers
applied during the bake-off). Shipping mean-pooled vectors would have diverged
from the benchmarked ones at **cosine ~0.93** — a silent retrieval-quality
regression, the project's highest-risk defect class. Fixed pooling mean→CLS,
wrote a reproducible exporter (`scripts/export_onnx.py`), added a parity gate
(`tests/test_onnx_parity.py`) with a load-bearing known-BAD control, and confirmed
the corrected encoder reproduces DECISION-002's bge metrics to the third decimal
(dense top-10 rankings differ on **0/19** questions). Recorded alongside the
bake-off in DECISION-002 §10 without touching §1.

---

## 2. Step 1 — ground truth, confirmed BEFORE any commit (task gate)

The task required determining bge's pooling empirically and reporting before
writing an exporter. Two independent confirmations:

**(a) The model's own files** (`~/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5`,
no deps needed):
```
1_Pooling/config.json:  pooling_mode_cls_token: true
                        pooling_mode_mean_tokens: false
modules.json:           Transformer → Pooling → Normalize
```
Plainly **CLS**, not mean.

**(b) Empirical**, on a 12-probe set (varied lengths; both `q_prefix` and
`p_prefix` paths). ST vectors = ground truth; the exported ONNX raw
`last_hidden_state` pooled each way:

| path | pooling | min cosine vs ST | max abs diff |
|---|---|---|---|
| q_prefix | **CLS** | **1.000000** | 2.5e-07 |
| q_prefix | mean (current code) | 0.927399 | 2.6e-01 |
| p_prefix | **CLS** | **1.000000** | 1.8e-07 |
| p_prefix | mean (current code) | 0.937983 | 2.4e-01 |

CLS reproduces ground truth to 2.5e-7 — well inside DECISION-002 §9.4's ~1e-5
target. Mean diverges to cosine 0.927.

**(c) Current path:** no `.onnx` existed in the repo, so `OnnxEncoder` could not
run before this task. Once exported, its mean-pool code is the MEAN row above — it
does **not** match ground truth. Bug confirmed; the docstring's "that is what
sentence-transformers does for every model in the shortlist" is false for bge.

The user's CLS hypothesis was **correct**. (Task explicitly said: trust the
measurement over the claim if they disagreed — they agreed.)

---

## 3. What shipped — 4 commits (on `main`, NOT pushed)

Order and messages follow the task's Step 7 spec.

### `8df8f6a` fix(retrieval): correct OnnxEncoder pooling to match bge CLS
`OnnxEncoder.encode` now `pooled = hidden[:, 0]` (CLS) then L2-norm, replacing the
mask-weighted mean. Docstring rewritten: pooling is **per-model** —
bge→CLS; e5-small-v2 / gte-small / all-MiniLM-L6-v2 → mean — not uniform across
the shortlist. The attention mask is still built for the model input but no longer
participates in pooling.

### `9bfcdc3` feat(retrieval): reproducible ONNX export for bge-small-en-v1.5
`scripts/export_onnx.py`. Exports the **raw transformer** (`last_hidden_state`
only) — pooling/normalization deliberately stay in Python so the artifact is a
faithful image the parity test compares against, and the CLS choice lives in one
auditable place, not frozen in a blob. Inputs: `input_ids`, `attention_mask`,
`token_type_ids` (bge/BERT takes it; `OnnxEncoder` already feeds zeros). Dynamic
batch+sequence axes; **opset 17 pinned**. Uses `torch.onnx.export` with a thin
`RawTransformer` wrapper module and `dynamo=False` (legacy TorchScript path) for
exact I/O control and to avoid the `onnxscript` build dep the torch-2.13 default
exporter pulls. torch/transformers are **build-time only**; the shipping runtime
stays onnxruntime + tokenizers. Offline by contract (`HF_HUB_OFFLINE=1`): reads
the local cache, fails loudly if the model isn't cached rather than reaching the
Hub. **Blob gitignored** (`models/*.onnx`); the script is the source.
- Artifact: `models/bge-small-en-v1.5.onnx`, **126.9 MB (133,048,336 bytes)**,
  sha256 `b7513a6a171d6694895fd9c4da6a169d13f13bc8656069be7c9213e86c781f67`
  (declared stack; see §10 for why this superseded `1a6ff430…`).
  `onnx.checker` clean; graph inputs `[input_ids, attention_mask, token_type_ids]`,
  output `[last_hidden_state]`.

### `77ca2fe` test(retrieval): ONNX↔SentenceTransformer parity + offline controls
`tests/test_onnx_parity.py`, 5 tests:
- **known-GOOD** (both prefix paths): OnnxEncoder(CLS) vs ST ground truth — min
  cosine ≥ 0.9999, max abs diff < 1e-5 (measured ~2.5e-7).
- **known-BAD** (both paths, load-bearing): a `_MeanPoolEncoder` subclass MUST
  fail the same gate (asserts min cosine < 0.9999 **and** < 0.99, max abs diff ≥
  1e-5). A parity test that cannot fail proves nothing.
- guard: both prefixes are exercised and actually differ (bge is asymmetric).
Skips cleanly if torch / sentence-transformers / onnxruntime / the model are
absent (mirrors `test_onnx_offline.py`); **builds the model via `export_onnx.py`
if missing** so a full build env runs it end-to-end.

### `9aa94b1` docs: record real ONNX dense metrics alongside bake-off in DECISION-002
New **§10** (see §5 below). §1's numbers are **unchanged**; §10 adds the
ONNX-measured column beside them. Marks next-action §9.4 done.

---

## 4. Step 5 — offline verification

No new test needed. `tests/test_onnx_offline.py::test_onnx_encoder_constructs_without_touching_the_hub`
monkeypatches `Tokenizer.from_pretrained` to raise, so it **fails the instant**
`OnnxEncoder` reintroduces a Hub call; `OnnxEncoder` loads the vendored
`src/tokenizer.json` only. The parity run additionally loaded the real `.onnx` +
vendored tokenizer fully offline (`HF_HUB_OFFLINE=1`), zero network.

---

## 5. Step 6 — the corrected encoder reproduces DECISION-002 exactly

Same dump (`benchmarks/chunks_sme.txt`), same n=19 set
(`data/questions/questions_sme_auto.json`, fp `c7f23f29b738b08d`), same `grade()`:

| bge, n=19 | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---|---|---|---|---|
| dense — ST bake-off (§1) | 47% | 74% | 89% | 95% | 0.636 |
| dense — **ONNX CLS (shipped)** | 47% | 74% | 89% | 95% | **0.636** |
| hybrid — ST bake-off (§1) | 58% | 84% | 89% | 95% | 0.703 |
| hybrid — **ONNX CLS (shipped)** | 58% | 84% | 89% | 95% | **0.703** |

Identical to the third decimal; **dense top-10 rankings differ on 0/19 questions.**
The shipped system now provably *is* the benchmarked system. No published number
moved, so none was overwritten.

**The bug, for contrast** — mean pooling would have shipped a *different,
plausible-but-wrong* table: dense R@10 95%→89%, hybrid R@5 89%→84%, dense R@1 *up*
to 53% (a different model, not a better one). Exactly the trap a parity gate
exists to catch.

---

## 6. Environment used (build/test only — not shipped)

System has no build deps and is PEP-668 externally-managed; `python` is 2.7,
`python3` is 3.13.5, network to PyPI works, bge is already cached. Built a venv at
`…/scratchpad/venv`: torch 2.13.0+cpu, sentence-transformers 5.6.1, onnx 1.22.0,
onnxruntime 1.28.0, transformers (5.x), pytest 8.3.5. `optimum` 2.2.0 installed but
its `exporters` extra doesn't exist in that version — irrelevant, we used
`torch.onnx.export` by design. To reproduce: `pip install -r requirements-bench.txt
onnx onnxruntime` then `python scripts/export_onnx.py`.

---

## 7. Current repo state

- **`main`: pushed at `74bf85a`** (`04c9040..74bf85a`). **11 commits** this session:
  - ONNX (7): `8df8f6a` fix pooling · `9bfcdc3` feat export · `77ca2fe` test parity ·
    `9aa94b1` docs metrics · `e39642d` build onnx-dep · `ee63b53` test widen-parity ·
    `b259aac` docs sha/reproducibility.
  - Tooling (2): `88c3b5b` fix(tools) migrate import + scripts importable ·
    `7504684` test(tools) scripts import/--help.
  - Docs (2): `7d556e2` docs §8 reconcile · `74bf85a` docs STATUS.md.
- **Full suite: 90 passed** (67 prior + 15 parity + 8 scripts-importable). CI
  (`pytest -q`) picks these up; parity/export tests skip where torch/ST/onnxruntime/
  model are absent, so a runtime-only CI stays green and a build-env CI runs them.
- **New/changed files:** `scripts/export_onnx.py` (new), `src/retriever.py` (pooling +
  docstring), `src/chunk_dump.py` (public `HEADER_RE`), `scripts/migrate_chunk_ids.py`
  (import fix), `scripts/vendor_tokenizer.py` + `scripts/verify_reproducibility.py`
  (import-safe guards), `tests/test_onnx_parity.py` (new, 15), `tests/test_scripts_importable.py`
  (new, 8), `.gitignore` (+`models/*.onnx`), `requirements-bench.txt` (+`onnx==1.22.0`),
  `docs/DECISION-002-retrieval-architecture.md` (+§10, §8 reconciled, §9.4 done),
  `STATUS.md` (new).
- **Untracked, untouched by design:** `benchmarks/CHUNK_ID_MIGRATION_REPORT.md`,
  `benchmarks/chunk_id_migration_map.json`, `docs/SESSION_REPORT_2026-07-23.md`
  (leftovers from earlier sessions).
- **`models/bge-small-en-v1.5.onnx`** exists locally, gitignored.

---

## 8. Open items / decisions pending

1. ✅ **PUSH — done** (`04c9040..74bf85a`); `origin/main == local main`.
2. ✅ **migrate_chunk_ids `HEADER_RE` regression — fixed** (`88c3b5b`). Now imports the
   public `chunk_dump.HEADER_RE`; `vendor_tokenizer.py`/`verify_reproducibility.py` also
   made import-safe, and `tests/test_scripts_importable.py` (`7504684`) locks the whole
   class shut (every `scripts/*.py` imports + `--help` exits 0).
3. **int8 — deferred (open).** §8/§9.4 of DECISION-002 said "ONNX int8"; the export is
   **fp32** (int8 cannot hold 0.9999 cosine parity, ~1e-2 error). §8 reconciled
   (`7d556e2`) to state fp32 ~127 MB as a deliberate parity-first tradeoff; int8 remains
   a future size optimisation on its own parity budget.
4. **`onnxruntime` absent from `requirements.txt` (open).** It is a *runtime* dep
   (numpy, tokenizers, pdfplumber, onnxruntime) but undeclared — same class as the
   `onnx` build-dep gap just fixed. Declare in a follow-up. (Tracked in `STATUS.md`.)
5. **CLI (open, deliberate non-goal for now).** `eval_retriever.py main()` still wires
   only `SentenceTransformerEncoder` (`--models`); ONNX benchmarking ran via a scratch
   harness reusing its `grade()`. Adding `--onnx-path` is a small separate addition.

---

## 10. Pre-push hardening (2026-07-27) — reproducibility + widened parity

Prompted by a local Debian run of `scripts/export_onnx.py` in a user venv.

### 10.1 `onnx` was undeclared — a clean clone couldn't export
The exporter needs `onnx` (the serialization backend `torch.onnx.export` writes
through). Nothing pulls it transitively, so a fresh clone hit "Module onnx is not
installed!" at write time — the script hardcoded the fix in its error string but no
requirements file declared it. **Fixed:** `requirements-bench.txt` now pins
`onnx==1.22.0`, with a comment explaining why. Verified: a venv built **strictly**
from `pip install -r requirements-bench.txt` exports clean, no manual installs.
(Also documented `dynamo=False` in the script: it pins the legacy TorchScript
exporter to avoid the `onnxscript` build dep; the DeprecationWarning is an accepted,
documented choice.)

### 10.2 The sha changed — and why it is expected to
The declared stack resolves sentence-transformers 3.3.1 → **transformers 4.55.4**
(the `<5` cap), torch 2.13.0+cpu, onnx 1.22.0. Exporting there yields
`sha256 b7513a6a171d6694895fd9c4da6a169d13f13bc8656069be7c9213e86c781f67`
(133,048,336 bytes) — **byte-identical on re-run** (determinism confirmed).

Last session's `1a6ff430…` came from an **off-spec transformers 5.14.1** that ST
3.3.1's pin cannot install. transformers 4.x and 5.x build the attention mask via
different code paths (4.x: `modeling_attn_mask_utils.py` `1.0 - expanded_mask`;
5.x: newer `masking_utils`/sdpa) — different constant nodes, same numerical graph,
different serialized bytes. **Conclusion: the .onnx sha is a function of the
exporting `transformers` version, not just the weights. The reproducibility contract
is the parity gate, not the blob sha.** `b7513a6a…` is recorded as canonical for the
*pinned declared stack* (DECISION-002 §10.4); if the transitive deps float, expect
the sha to move and parity to still hold.

### 10.3 Parity widened to defuse the tracer warnings empirically
The export emits tracer warnings on a *successful* trace (opset-11 `aten::index`
"incorrect if indices are negative"; "value baked in as a constant might not
generalise"). The 12 short synthetic probes did not prove parity across lengths and
padding — exactly what those warn about. `tests/test_onnx_parity.py` now also asserts
the same gate (cosine ≥ 0.9999, max abs < 1e-5) on:
- a **single-token** input,
- a **full-budget** input (the 394-token longest real chunk),
- **4 real chunks** sampled from `benchmarks/chunks_sme.txt`,
- a **padding-variance batch** — a ~6-token string batched with the full-budget one,
  so it is padded ~65× — plus a dedicated test that the padded short vector is
  **identical** encoded alone vs in-batch (padding must not leak into attention).

All pass, both q_prefix and p_prefix: **worst case min cosine 1.000000, max abs diff
1.9e-07** (~53× under the 1e-5 bar). The graph generalises across padding; no
divergence. Parity tests: 5 → **15**.

---

## 9. Standing lessons reinforced

- **A shipping path that is never exercised hides its own bugs.** The pooling error
  survived because no `.onnx` existed and every number came from ST or a stub. The
  fix is not just CLS — it's the parity gate that makes shipped-vs-benchmarked
  divergence impossible to reintroduce silently.
- **Pooling is per-model; do not assume uniformity.** bge is CLS; the other three
  shortlist models are mean. The old docstring's "for every model in the shortlist"
  was the exact overgeneralisation that let mean-pool look reasonable.
- **The load-bearing test is the known-BAD control.** A mean-pooled encoder MUST
  fail the parity gate, or the gate proves nothing.
- **Don't bake pooling into the graph.** Exporting the raw transformer keeps the
  artifact comparable to ST and the pooling decision auditable in Python.
- **Report the measurement, don't overwrite the record.** §1's numbers stand; §10
  adds the agreeing ONNX column beside them.
