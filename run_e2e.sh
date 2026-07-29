#!/usr/bin/env bash
# run_e2e.sh — first real end-to-end run of adtc-rag, fully logged.
#
# WHY A SEPARATE VENV: this project deliberately splits runtime deps
# (numpy/pdfplumber/tokenizers/onnxruntime) from build-time deps
# (torch/transformers/sentence-transformers, in requirements-bench.txt).
# Installing the app into a venv that already holds the build stack
# downgrades huggingface-hub/tokenizers and breaks transformers — exactly
# what happened on the first attempt. A clean runtime venv both fixes that
# AND proves the "runtime deps only" claim a judge will check.
#
# WHERE TO RUN: from the repository root (the dir containing pyproject.toml).
# WHAT YOU GET: everything printed to screen AND appended to e2e_run.log,
#               which you hand back as feedback.

set -o pipefail

# --- resolve to repo root regardless of where you invoke from ------------
cd "$(dirname "$0")" || exit 1
if [[ ! -f pyproject.toml ]]; then
  echo "ERROR: run this from the repo root (no pyproject.toml here)."; exit 1
fi

LOG="e2e_run.log"
VENV=".venv-runtime"            # deliberately NOT your build venv
MODEL="models/bge-small-en-v1.5.onnx"

# tee everything (stdout+stderr) to the log from here on
exec > >(tee "$LOG") 2>&1

echo "########################################################"
echo "# adtc-rag end-to-end run"
echo "# date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# host:   $(hostname)"
echo "# pwd:    $(pwd)"
echo "# commit: $(git rev-parse --short HEAD 2>/dev/null)  ($(git status --porcelain | wc -l) files dirty)"
echo "########################################################"

# --- 0. environment sanity ----------------------------------------------
echo; echo "===== 0. ENVIRONMENT ====="
python3 --version
echo "CPU:  $(nproc) cores"
echo "RAM:  $(free -h | awk '/Mem:/{print $2" total, "$7" available"}')"
echo "disk: $(df -h . | awk 'NR==2{print $4" free"}')"

echo; echo "----- Ollama reachable? -----"
if curl -s --max-time 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "OK: Ollama is up."
  curl -s http://localhost:11434/api/tags | python3 -c "import sys,json;print('models:',[m['name'] for m in json.load(sys.stdin).get('models',[])])" 2>/dev/null || true
else
  echo "WARN: Ollama not answering on :11434 — 'ask' will fail at generation."
  echo "      Start it with:  ollama serve &   and:  ollama pull qwen2.5:3b-instruct"
fi

echo; echo "----- ONNX model present? -----"
if [[ -f "$MODEL" ]]; then
  echo "OK: $MODEL ($(du -h "$MODEL" | cut -f1))"
else
  echo "ERROR: $MODEL missing. Rebuild in your BUILD venv:"
  echo "   pip install -r requirements-bench.txt && python scripts/export_onnx.py"
  echo "Continuing — ingest/ask will fail at encode until this exists."
fi

# --- 1. clean runtime venv ----------------------------------------------
echo; echo "===== 1. CLEAN RUNTIME VENV ($VENV) ====="
echo "(fresh venv so build-time deps can't leak in and nothing gets downgraded)"
rm -rf "$VENV"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -q --upgrade pip
echo "installing the app (runtime deps only) ..."
pip install -e . 2>&1 | tail -5
echo; echo "----- installed package set (should have NO torch/transformers) -----"
pip list 2>/dev/null | grep -iE "torch|transformers|sentence|onnxruntime|numpy|tokenizers|pdfplumber" || true
if pip list 2>/dev/null | grep -qiE "^transformers|^torch"; then
  echo "WARN: build-time deps present in the runtime venv — separation not clean."
else
  echo "OK: runtime venv is clean (no torch/transformers)."
fi

echo; echo "----- CLI is wired? -----"
adtc-rag --help  | head -20 || { echo "ERROR: adtc-rag entry point not found"; exit 1; }

# --- 2. full test suite --------------------------------------------------
echo; echo "===== 2. TEST SUITE ====="
pip install -q -r requirements-dev.txt 2>&1 | tail -2
echo "(heavy paths — real OnnxEncoder / Ollama — skip cleanly if unavailable)"
pytest -q 2>&1 | tail -25

# --- 3. ingest (timed) ---------------------------------------------------
echo; echo "===== 3. INGEST (timed, isolated index) ====="
IDX="$(mktemp -d)/index"
echo "index dir: $IDX  (isolated, so this run is reproducible)"
echo "corpus:    data/raw ($(ls data/raw/*.pdf 2>/dev/null | wc -l) PDFs)"
echo "--- first ingest: expect minutes on HDD; progress should print ---"
/usr/bin/time -v adtc-rag ingest data/raw --index-dir "$IDX" 2>&1 || \
  adtc-rag ingest data/raw --index-dir "$IDX"   # fallback if /usr/bin/time absent

echo; echo "--- second ingest: must report 'already indexed', chunk count unchanged ---"
adtc-rag ingest data/raw --index-dir "$IDX"

# --- 4. ask: answerable (timed, verbose) ---------------------------------
echo; echo "===== 4. ASK — answerable (verbose, timed) ====="
for Q in "What is the return window?" "How do I contact seller support?"; do
  echo; echo "----- Q: $Q -----"
  time adtc-rag ask "$Q" --index-dir "$IDX" --verbose
done

# --- 5. ask: unanswerable (abstention) -----------------------------------
echo; echo "===== 5. ASK — unanswerable (abstention must show its work) ====="
echo "----- Q: What was MTN Uganda's H1 2024 revenue? (not in this corpus) -----"
time adtc-rag ask "What was MTN Uganda's H1 2024 revenue?" --index-dir "$IDX"

# --- 6. done -------------------------------------------------------------
echo; echo "########################################################"
echo "# DONE. Full log: $LOG"
echo "# Hand e2e_run.log back as feedback."
echo "########################################################"
deactivate 2>/dev/null || true
