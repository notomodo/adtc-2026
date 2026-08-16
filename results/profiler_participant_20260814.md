# ADTC profiler — participant-mode run (2026-08-14)

Official `adtc-profiler` (v0.1.0, schema 1.1.0) run on the **dev floor machine**
(i5-4300U, 7.7 GB, CPU-only, Debian 13). Command:

```
PATH=/home/omodo/tools/llama.cpp/build/bin:$PATH \
  .venv-profiler/bin/adtc-profiler run --submission . --mode participant --output submission.json
```

Full machine-readable report: `submission.json` (gitignored — this markdown is the
in-repo record). `reproducibility.git_commit_sha` will update when the pack is committed.

## Results

| Block | Value |
|---|---|
| **Accuracy (arc_easy, n=50, acc_norm)** | **0.80** — the S_acc figure the profiler measures |
| Generation speed (llama-bench, 512 ctx) | **4.32 tok/s** |
| First-token latency (512-token prompt) | **46.4 s** |
| Peak RSS | **3456 MB** (steady-state 3350 MB) |
| CPU util p99 | 99.0% |
| **Core temp peak / throttled** | **94.0 °C / True** ⚠ |
| model_info | 3.397B params, qwen2, ctx 32768, params_match ✓ |

## Score preview (official formula, dev machine)

S_total = 0.50·S_acc + 0.30·S_perf + 0.20·S_eff − P_thermal
= 0.50·80 + 0.30·min(4.32/15,1)·100 + 0.20·(7.0−3.456)/7.0·100 − 10
= **40 + 8.6 + 10.1 − 10 = 48.8** (dev floor, thermal-penalised)

Breakdown: S_acc 80, S_perf 28.8 (4.32 tok/s vs 15 reference), S_eff 50.6
(3.46 GB peak vs 7.0 GB limit), P_thermal 10.

## Interpretation and caveats

- **S_acc 0.80 on arc_easy is the first official-accuracy number this project has
  produced** (the earlier "S_acc unmeasured" gap is now closed for the dev box). It is
  a strong MCQ result for a 3B Q4_K_M on an old CPU.
- **Thermal is the dev box's weak point, not the model's**: the aging i5-4300U hit 94 °C
  and throttled (the 10-point penalty). The standard laptop (i5 10th–12th gen, better
  cooling) is expected to stay under 85 °C, but **R1 must measure this** — thermal
  penalties and OOM are the two automatic-deduction risks in the rules.
- **S_perf 28.8 is floor-limited.** 4.32 tok/s on a 4th-gen i5; expect materially higher
  on the standard laptop (the reference machine run is the definitive number).
- **S_eff 50.6**: peak RSS 3.46 GB of the 7 GB evaluation limit leaves ~3.5 GB headroom
  — comfortably inside the budget (Qwen3-4B would have been ~6 GB peak ≈ S_eff 14, a
  near-OOM disqualification risk; this run validates the 3B choice on the efficiency
  axis with an official tool).
- First-token latency 46 s reflects 512-token prompt processing on the old CPU — the
  RAG app's real prompts are ~1.2k tokens, and prompt processing dominates wall-clock
  (matches the floor benchmark's ~55 s/question).
- **Action before submission:** replace `TBD-ADTF-PORTAL-ID` in `metadata.json`, then
  re-run this command so `submission.json` carries the real team ID; re-run on the
  reference machine for the shipped report.
