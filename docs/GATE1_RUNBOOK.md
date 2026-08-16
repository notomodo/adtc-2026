# Gate-1 submission runbook (2026-08-14)

Sequence to execute on submission day (or as a dry run now). Every step is
reversible; nothing below modifies the tracked code.

## 0. Confirm metadata (needs Andrew)

- [ ] `metadata.json` → `team_id` (ADTF portal ID) — currently `TBD-ADTF-PORTAL-ID`
- [ ] confirm `submitter.name` / `submitter.email` match the registration
- [ ] confirm `african_alpha_claim: true` (African Use Case Bonus claim)
- [ ] confirm the 2 `test_prompts` wording (they are scored with 2 hidden prompts)

## 1. Weights + profiler (background jobs already running 2026-08-14)

```bash
bash download_model.sh        # ~2.0 GB → model/qwen2.5-3b-instruct-q4_k_m.gguf (sha256-verified)
# profiler venv: .venv-profiler (gitignored) — pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
```

## 2. Local profiler run (participant mode)

```bash
export PATH="/home/omodo/tools/llama.cpp/build/bin:$PATH"   # llama-bench, llama-cli
.venv-profiler/bin/adtc-profiler run --submission . --mode participant --output submission.json --skip-accuracy   # fast smoke test
cat submission.json
# then the full run (adds lm-eval arc_easy, limit 50 — the S_acc number):
.venv-profiler/bin/adtc-profiler run --submission . --mode participant --output submission.json
```

Sanity checks on the report: `measured_on == "participant_laptop"`, peak RSS well
under 7 GB, tok/s present, `accuracy` block populated (arc_easy score), thermal
`throttled == false`.

Measured on this dev box 2026-08-14 (i5-4300U): S_acc 0.80 (arc_easy n=50), S_perf
28.8 (4.32 tok/s vs 15 reference), S_eff 50.6 (3.46 GB peak vs 7.0 GB limit),
thermal throttled at 94 °C (−10). Score preview ≈48.8. The reference machine
(standard laptop) should improve S_perf and hopefully clear the thermal penalty.

## 3. Push + submit

```bash
git add metadata.json download_model.sh REPORT.md .gitignore docs/GATE1_SUBMISSION.md docs/screenshots/
git commit -m "feat(submission): Gate-1 pack — metadata, GGUF downloader, REPORT.md (ADTC 2026 template)"
git push origin main
# submit the repo URL at https://adtc-2026.devpost.com (Gate 1: 2026-08-25)
```

## 4. Still open (needs Andrew / hardware)

- [ ] Record the ≤2-min video (`docs/GATE1_SUBMISSION.md` §6 has the script)
- [ ] Start Ollama (`sudo systemctl start ollama`) and capture `ask` demo
      (`docs/screenshots/ask_demo.txt`) — the one missing screenshot
- [ ] Run `run_benchmark.sh` on the 8 GB reference machine (R1) and append the
      table to `REPORT.md`
