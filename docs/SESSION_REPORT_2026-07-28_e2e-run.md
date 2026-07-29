# Session report — first real end-to-end run (`adtc-rag`)

**Date:** 2026-07-28 · **Branch:** `main` · **Base commit:** `01b13c3` (+3 uncommitted fixes)
**Result:** ✅ **SUCCESS — the pipeline runs start to finish on real components.**

This documents the two-run debugging cycle that took the application layer from
"offline-green but unproven" to **demonstrated end to end**: extract → chunk →
embed (real ONNX bge) → persist → retrieve → generate (live Qwen2.5-3B), with
grounded answers, citations, idempotency, and verifiable abstention.

Evidence: `e2e_run.log` (driven by `run_e2e.sh`, on a 4-core / 7.7 GB Debian box,
CPU-only Ollama).

---

## 1. Two-run story

The app passed 87/88 offline tests but had **never run its live path** (this dev
box has no onnxruntime/Ollama). `run_e2e.sh` exists to run it for real on the
target machine and hand back a log. It took two runs:

- **Run 1** caught a shipping bug the offline suite could not see, and a
  test-guard gap. Nothing generated.
- **Run 2**, after three fixes + pulling the model, succeeded completely.

---

## 2. Issues found in run 1, and the fixes

| # | Issue (run 1) | Root cause | Fix |
|---|---|---|---|
| 1 | **Every `ingest`/`ask` died with `unrecognized arguments: --index-dir`** — nothing ran. | `--index-dir` was a top-level-only option; the runbook (and any user) puts it *after* the subcommand, which argparse rejects. The offline tests only used the *before* form, so it passed CI. | `src/app/cli.py`: `--index-dir` moved to a shared parent parser added to the top level **and** both subparsers → works in either position. New regression test asserts the after-subcommand form. |
| 2 | **The e2e test FAILED (HTTP 404) instead of skipping.** | Ollama was up but had **no models pulled** (`models: []`); the skip guard checked only socket reachability, so the test ran and 404'd at `/api/chat`. | `tests/test_cli.py`: guard now queries `/api/tags` and skips unless the model is actually pulled. `src/app/cli.py`: a 404 from Ollama now prints `Ollama has no model '<m>'. Pull it: ollama pull <m>` instead of a misleading "cannot reach Ollama". |
| 3 | **RAM/disk banner lines errored** (`awk: backslash not last character`). | Escaping artifact — `\"` inside the single-quoted awk program in `run_e2e.sh`. | Removed the stray backslashes; banner now prints `RAM: 7.7Gi total…`. |

All three verified locally before run 2: full suite **88 passed, 2 skipped**, and
`--index-dir` confirmed working before *and* after the subcommand.

Operational fix outside the code: **`ollama pull qwen2.5:3b-instruct`** (run 1's
Ollama had zero models).

---

## 3. Run 2 — what actually happened

### 3.1 Runtime/build separation — proven
The clean `.venv-runtime` installed **only** `numpy, onnxruntime 1.28.0,
pdfplumber, tokenizers` (+ transitive) — **no torch, no transformers**. The
"runtime deps only" claim a judge checks is now demonstrated, not just asserted.

### 3.2 Test suite (inside the runtime venv)
**89 passed, 1 skipped** in 2m26s. The one skip is the torch-dependent ONNX
parity module (correct — no torch here). Critically, the **live e2e test now ran
and passed** (real OnnxEncoder + Ollama), where run 1 had it failing.

### 3.3 Ingest — the whole corpus, first time for real
```
5 documents, 47 chunks, 222.1 KB on disk — encoder init 1.8s · total 29.1s
  General_Terms…            22 chunks / 11 pages
  Privacy_Policy             14 chunks / 3 pages
  Return_Policy               3 chunks / 2 pages
  Seek_Support                1 chunk  / 1 page
  Sellers_Terms…              7 chunks / 5 pages
```
**47 chunks = the exact corpus DECISION-002 benchmarked** (22+14+3+1+7). The
shipped app ingests the same corpus the retrieval numbers describe. Per-document
progress printed throughout (no silent hang). ~29 s total — faster than the
"minutes on HDD" worst case this box didn't hit.

### 3.4 Idempotency — verified
Second ingest: all 5 docs reported **`already indexed`**, chunk count unchanged
at 47, **0.5 s** (extraction skipped by the sha256 pre-check). Exactly the intended
no-op.

### 3.5 Ask — answerable, grounded, cited
- **"What is the return window?"** → *"2 days from the delivery date"* — correct;
  `Sources: [Return_Policy.pdf, p.1]`; all 3 retrieved chunks from Return_Policy;
  retrieval 30 ms, generation 110.4 s.
- **"How do I contact seller support?"** → correct email `support@kibuga.com`,
  both phone numbers, and the `@KibugaOnlineShop` handle; cited Return_Policy +
  Seek_Support; retrieval 45 ms, generation 151.9 s.

`--verbose` dumped chunk ids, bm25/dense ranks, rrf scores and per-stage timings
for both.

### 3.6 Ask — unanswerable, abstention shows its work
- **"What was MTN Uganda's H1 2024 revenue?"** (not in this corpus) → emitted the
  bare **`NOT_IN_DOCUMENTS`** sentinel, then listed **5 near-misses with rrf
  scores** so the abstention is verifiable rather than a black box. generation 62.8 s.

This is the DECISION-004 abstention behaviour working on the real stack.

---

## 4. Persisting / minor issues

1. **Generation is the dominant cost: 63–152 s/question** (Qwen2.5-3B, CPU-only,
   4 cores). Retrieval is trivial by comparison (30–68 ms). One question (152 s)
   exceeded the 65–105 s estimate. Not a bug — model/hardware — but it drives demo
   pacing. **Streaming is what makes this usable**; the `retrieving…/generating…`
   banner + token stream mean it never reads as a hang. A GPU or a smaller model
   would be the lever if faster answers are needed.
2. **`/usr/bin/time` is absent on the box** (`time` package not installed), so the
   ingest step lost its detailed resource stats — the `|| fallback` ran, ingest
   still worked and self-reported 29.1 s. Options: `sudo apt install time`, or make
   the runbook guard with `command -v /usr/bin/time` / use the bash builtin.
3. **The model leaked internal passage numbers into one answer:** *"found in both
   [1] and [3] passages"*. Cosmetic — the v3 prompt numbers context passages and the
   model referenced them by number. The answer is correct and cited; the `[1]/[3]`
   is just chatter. A future prompt tweak could suppress it, but the v3 prompt is
   locked (DECISION-004) and this is not a grounding failure.
4. **The three fixes are still uncommitted** (log stamped `01b13c3`, "7 files
   dirty"). They need committing/pushing — see §6.

None of these block anything.

---

## 5. Readiness

**The application layer is now demonstrated working end to end on the target
machine.** Real ONNX embeddings, the same 47-chunk corpus the numbers describe,
correct grounded+cited answers, working idempotency, and verifiable abstention —
all offline except the local Ollama socket, from a provably torch-free runtime
venv. This clears the "reference-machine performance run" that was STATUS.md's
next action.

---

## 6. Next steps

1. **Commit + push the three fixes** (currently uncommitted on top of `01b13c3`):
   - `fix(app): accept --index-dir after the subcommand; name the missing Ollama model`
   - `test(app): skip e2e when the Ollama model isn't pulled`
   - `fix(dev): correct awk quoting in run_e2e.sh banner`
2. **Update STATUS.md** — critical path item "reference-machine performance run"
   is done; record the real timings (ingest ~29 s; generation 63–152 s/q).
3. Optional: install `time` on the box (or make the runbook portable) to recover
   ingest resource stats on future runs.
4. Handoff docs from this session still untracked and worth committing:
   `docs/SESSION_REPORT_2026-07-28_application-layer.md` and this report.
