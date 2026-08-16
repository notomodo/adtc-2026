# Gate 1 Submission Pack — ADTC 2026 (2026-08-14)

Everything needed to submit at **Gate 1 (deadline 2026-08-25)** for the Africa Deep
Tech Challenge 2026, mapped against the official requirements
([rules](https://adtc-2026.devpost.com/rules),
[submission template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template)).
This file is the working checklist; `REPORT.md`, `metadata.json`, `download_model.sh`
at the repo root are the actual submission artifacts.

---

## 1. What the submission IS (important framing)

The scored artifact is the **model** (a GGUF weight file run through llama.cpp) plus
the **repo + report + video**. The ADTC profiler measures the bare model on the
standard 8 GB laptop: MCQ accuracy (S_acc), throughput (tok/s), RAM efficiency,
thermal, plus our 2 test prompts + 2 hidden prompts. **The RAG pipeline is the
product layer we showcase** (report, video, repo); the model itself is what gets
profiled. The `metadata.json` runtime field must be `llama.cpp` — GGUF only.

## 2. Checklist — status

| # | Requirement (from the official template) | Status |
|---|---|---|
| 1 | Repo public on GitHub | ✅ `notomodo/adtc-2026` (public, MIT) |
| 2 | `metadata.json` fully filled | ✅ schema-validated against the official profiler schema; **3 fields need your confirmation** (see §3) |
| 3 | `metadata.json` has exactly **2 test prompts** | ✅ tp_001/tp_002 written (confirm wording, §3) |
| 4 | `download_model.sh` downloads to `model/` | ✅ **tested end-to-end 2026-08-14**: 2.0 GB downloaded, sha256 `626b4a66…5c62d` verified |
| 5 | Downloaded file is valid GGUF `.gguf` | ✅ magic `GGUF` + exact size verified |
| 6 | `model/*.gguf` in `.gitignore` | ✅ (added `model/` + `*.gguf`) |
| 7 | `REPORT.md` technical writeup | ✅ drafted (1–3 pages, factual; §5 for polish items) |
| 8 | `bash download_model.sh` completes without errors | ✅ (full run, idempotency re-check pending) |
| 9 | Model runs 100% offline | ✅ by design (local llama.cpp/Ollama, vendored tokenizer, pinned deps; CI enforces) |
| 10 | **Local profiler run** (participant mode) | ✅ **DONE 2026-08-14**: S_acc 0.80 (arc_easy n=50), 4.32 tok/s, peak RSS 3456 MB, thermal throttled on the old dev CPU — full report `results/profiler_participant_20260814.md`; re-run after `team_id` is filled + on the reference machine |
| 11 | Screenshots / short video of the build | 🟡 CLI captures done (`docs/screenshots/`); ask-demo capture pending Ollama |
| 12 | Video (max 2 min) | ⬜ script drafted in §6; needs recording |
| 13 | Reference-machine benchmark (R1) | ⬜ pending access to the standard laptop |
| 14 | Comprehensive project report (rules also require it) | ✅ covered by this repo's docs (`DECISIONS.md`, `STATUS.md`, `docs/model_comparison.md`, `benchmarks/`, `results/`) |

## 3. Fields you must confirm / fill (no code — just values)

1. **`team_id`** — currently `"TBD-ADTF-PORTAL-ID"`. Fill with the team ID you
   registered on the ADTF portal.
2. **`submitter.email` / `submitter.name`** — filled with `andrewomodo@proton.me` /
   "Andrew Omodo" from git metadata; confirm these are the registration details.
3. **`african_alpha_claim: true`** — this claims the **African Use Case Bonus**
   (the template README defines the field that way). Our use case (offline document
   Q&A for a Ugandan SME) qualifies, but confirm you want to claim it.
4. **`test_prompts`** — 2 in-domain prompts the bare model must answer (they are
   scored alongside 2 hidden prompts). Confirm the wording; the current ones are a
   contract-termination reasoning prompt and a returns-policy drafting prompt.
5. **`cross_disciplinary_pairing.discipline`** — set to `enterprise`; adjust if the
   portal expects a different label.

## 4. Local profiler run (recommended before Gate 1)

The rules and the template both expect participants to test locally with the
official profiler (it also gives us the **S_acc number we are currently
missing** — the one accuracy number the judges actually score). The profiler
README publishes the scoring formula:

**S_total = 0.50·S_acc + 0.30·S_perf + 0.20·S_eff − P_thermal**, with
- **S_acc** = accuracy on our 2 submitted prompts + domain prompts + 2 hidden
  judges' prompts (prompt-response based; the default install also runs
  lm-eval — this corrects the older "S_acc = lm_eval MCQ" framing in our docs)
- **S_perf** = `min(tok/s ÷ 15.0, 1.0) × 100` (reference 15 tok/s)
- **S_eff** = `max(0, (7.0 − peak_RSS_GB) ÷ 7.0) × 100` (8 GB profile, 7.0 GB
  limit used in the formula)
- **P_thermal** = 10 if CPU throttles or core temp exceeds 85 °C

Our floor numbers give a useful preview: 3B S_perf ≈ 33 (4.98 tok/s), S_eff ≈
71 (runner ~2.05 GB) — vs Qwen3-4B ≈ 19 and ≈ 14. The 1.5B would score ~62 on
S_perf but materially worse on S_acc. The 3B's accuracy advantage and RAM
efficiency more than offset its mid-table throughput.

```bash
pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
bash download_model.sh          # 2 GB → model/qwen2.5-3b-instruct-q4_k_m.gguf
adtc-profiler run --submission . --mode participant --output submission.json
cat submission.json             # expect "measured_on": "participant_laptop"
```

`--skip-accuracy` first for a fast smoke-test loop, then a full run for the
final report. The default accuracy stage is **lm-eval `arc_easy` (limit 50)**
on the quantized GGUF via llama-cpp-python. Requires `llama-bench`/`llama-cli`
on PATH (already built at `/home/omodo/tools/llama.cpp/build/bin/`). Output
file is gitignored (`submission.json` — added to our `.gitignore`).

## 5. REPORT.md polish items (before submitting)

- [ ] Append the reference-machine benchmark table when R1 is done.
- [ ] Optionally add the profiler MCQ result when the local run completes.
- [ ] Add a one-line "how to reproduce" pointer if desired (the repo README already
      covers `make setup / make all`).

## 6. Video script (max 2 minutes) — record on the floor box with Ollama up

> **0:00–0:20 — Problem.** Ugandan SMEs hold their rules in PDFs; connectivity is
> unreliable. Cloud assistants fail exactly when needed. Show the 5 Kibuga PDFs.
>
> **0:20–0:50 — Build (screenshots over narration).** Offline RAG pipeline:
> `adtc-rag ingest data/raw/*.pdf` → 47 chunks → hybrid retrieval (BM25 +
> bge-small ONNX, RRF) → Qwen2.5-3B locally via Ollama → grounded answer with
> citations. Show `adtc-rag ask "What is Kibuga's returns window?"` answering
> "2 days from the delivery date" with `[Return_Policy.pdf p.1]`.
>
> **0:50–1:20 — Safety.** Ask the unanswerable probe ("What was MTN Uganda's H1
> 2024 revenue?") → the system prints `NOT_IN_DOCUMENTS` plus the nearest
> passages it considered, instead of hallucinating. This is the abstention
> behaviour that a faithfulness grade verified (6/6 probes).
>
> **1:20–1:50 — Numbers (honest).** On an older-than-standard laptop: ~5 tok/s
> generation, 4.6 GB peak RAM of 8 GB, fully offline; reproducibility gate in CI
> (47-chunk fingerprint) so results are trustworthy.
>
> **1:50–2:00 — Close.** Open-source (MIT), built for the Africa Deep Tech
> Challenge, and deployed on the hardware Africa actually has.

## 7. Files in this pack

| File | Purpose |
|---|---|
| `metadata.json` | Submission metadata + 2 test prompts (root) |
| `download_model.sh` | Idempotent, sha256-verified GGUF download (root) |
| `REPORT.md` | Technical writeup per template (root) |
| `.gitignore` | `model/` + `*.gguf` excluded |
| `docs/LAYER_B_GRADE_2026-08-14.md` | The faithfulness evidence REPORT.md cites |
| `docs/screenshots/` | CLI "build in action" captures (help + real ingest run) |
