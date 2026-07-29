#!/usr/bin/env bash
# run_benchmark.sh — full-corpus end-to-end benchmark (perf + accuracy), logged.
#
# WHAT IT DOES
#   Builds a FRESH isolated index from data/raw, then runs the whole question
#   set (35 answerable + 6 unanswerable probes) through the shipping pipeline,
#   capturing per-question latency, tokens/sec (from Ollama's own counters),
#   peak RAM, and the Layer-A RAG end-to-end pass rate. Writes:
#     results/benchmark_<UTC>.jsonl          (incremental, resumable)
#     results/benchmark_<UTC>_summary.md      (aggregates + appendix)
#     results/benchmark_<UTC>.log             (this transcript)
#
#   THE ACCURACY NUMBER IS RAG END-TO-END, Layer-A pass rate — a known
#   overestimate (R5/Q19 false positives). It is NOT S_acc / leaderboard
#   accuracy. The summary states this inline; so does the harness.
#
#   ⚠️  THIS PINS THE CPU FOR ~60–100 MIN. Run it unattended. Generation on a
#       CPU-only 3B model is 60–150 s/question; 41 questions is over an hour.
#
# WHERE TO RUN: from the repo root, inside the proven torch-free .venv-runtime.

set -o pipefail
cd "$(dirname "$0")" || exit 1
if [[ ! -f pyproject.toml ]]; then
  echo "ERROR: run this from the repo root (no pyproject.toml here)."; exit 1
fi

VENV=".venv-runtime"
MODEL="qwen2.5:3b-instruct"
ONNX="models/bge-small-en-v1.5.onnx"
UTC="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p results
LOG="results/benchmark_${UTC}.log"
RESULTS="results/benchmark_${UTC}.jsonl"

exec > >(tee "$LOG") 2>&1

echo "########################################################"
echo "# adtc-rag end-to-end benchmark (perf + accuracy)"
echo "# date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# host:   $(hostname)"
echo "# commit: $(git rev-parse --short HEAD 2>/dev/null)  ($(git status --porcelain | wc -l) files dirty)"
echo "########################################################"

# --- 0. environment banner (mirror run_e2e.sh) --------------------------
echo; echo "===== 0. ENVIRONMENT ====="
python3 --version 2>/dev/null || true
echo "CPU:  $(nproc) cores"
echo "RAM:  $(free -h | awk '/Mem:/{print $2" total, "$7" available"}')"
echo "disk: $(df -h . | awk 'NR==2{print $4" free"}')"
echo
echo "⚠️  This run pins the CPU for ~60–100 min (41 questions × 60–150 s of"
echo "    CPU-only generation each). Leave it unattended."

# --- guards (mirror run_e2e.sh) -----------------------------------------
echo; echo "----- guard: runtime venv present? -----"
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "ERROR: $VENV missing. Create it first (run_e2e.sh builds it), or:"
  echo "   python3 -m venv $VENV && source $VENV/bin/activate && pip install -e ."
  exit 1
fi
echo "OK: $VENV present."

echo; echo "----- guard: Ollama up + model pulled? -----"
if ! curl -s --max-time 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "ERROR: Ollama not answering on :11434. Start it:  ollama serve &"
  exit 1
fi
if ! curl -s http://localhost:11434/api/tags | grep -q "$MODEL"; then
  echo "ERROR: model '$MODEL' not pulled. Pull it:  ollama pull $MODEL"
  exit 1
fi
echo "OK: Ollama up and '$MODEL' pulled."

echo; echo "----- guard: ONNX encoder present? -----"
if [[ ! -f "$ONNX" ]]; then
  echo "ERROR: $ONNX missing. Build it in your BUILD venv:"
  echo "   pip install -r requirements-bench.txt && python scripts/export_onnx.py"
  exit 1
fi
echo "OK: $ONNX present."

# --- 1. fresh isolated index (self-contained + reproducible) ------------
echo; echo "===== 1. FRESH INDEX (isolated) ====="
IDX="$(mktemp -d)/bench_index"
echo "index dir: $IDX  (fresh, so the run is self-contained and reproducible)"
echo "corpus:    data/raw ($(ls data/raw/*.pdf 2>/dev/null | wc -l) PDFs)"
"$VENV/bin/adtc-rag" ingest data/raw --index-dir "$IDX" || { echo "ingest FAILED"; exit 1; }

# --- 2. the benchmark sweep ---------------------------------------------
echo; echo "===== 2. BENCHMARK SWEEP (unattended; ~60–100 min) ====="
echo "results (incremental, resumable): $RESULTS"
"$VENV/bin/python" scripts/run_benchmark.py \
    --index-dir "$IDX" \
    --results "$RESULTS" \
    --model "$MODEL" || { echo "benchmark harness FAILED"; exit 1; }

# --- 3. done ------------------------------------------------------------
echo; echo "########################################################"
echo "# DONE."
echo "#   per-question: $RESULTS"
echo "#   summary:      ${RESULTS%.jsonl}_summary.md"
echo "#   log:          $LOG"
echo "# Commit results/ and hand the summary back."
echo "########################################################"
