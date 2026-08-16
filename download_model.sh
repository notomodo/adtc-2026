#!/usr/bin/env bash
# Download the submission model weight (Qwen2.5-3B-Instruct, GGUF Q4_K_M).
#
# Rules this script obeys (ADTC 2026 submission template):
#   - Idempotent: safe to run repeatedly; skips when the file is already present.
#   - No credentials: public URL only (Hugging Face official Qwen repo).
#   - Output path exactly matches `_runtime.model_path` in metadata.json.
#   - Integrity: verifies the file size AND sha256 before declaring success,
#     so a truncated/corrupt download never passes silently.
#
# Source: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF
# License: Qwen Research (non-commercial) — see DECISIONS.md D4 / docs/model_comparison.md

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$HERE/model"
MODEL_FILE="$MODEL_DIR/qwen2.5-3b-instruct-q4_k_m.gguf"
MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"

# From the HF tree API (2026-08-14): size in bytes and canonical sha256.
EXPECTED_SIZE=2104932768
EXPECTED_SHA256="626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"

mkdir -p "$MODEL_DIR"

if [[ -f "$MODEL_FILE" ]]; then
  actual_size="$(stat -c %s "$MODEL_FILE" 2>/dev/null || stat -f %z "$MODEL_FILE")"
  if [[ "$actual_size" == "$EXPECTED_SIZE" ]]; then
    echo "model already present at $MODEL_FILE ($((actual_size / 1024 / 1024)) MB) — skipping download"
    exit 0
  fi
  echo "partial/corrupt file found ($actual_size bytes != $EXPECTED_SIZE) — re-downloading"
  rm -f "$MODEL_FILE"
fi

echo "downloading $MODEL_URL → $MODEL_FILE (~2.0 GB)…"
if command -v curl > /dev/null 2>&1; then
  curl -L --fail --retry 3 --progress-bar -o "$MODEL_FILE.partial" "$MODEL_URL"
elif command -v wget > /dev/null 2>&1; then
  wget --show-progress -O "$MODEL_FILE.partial" "$MODEL_URL"
else
  echo "error: neither curl nor wget found" >&2
  exit 1
fi

actual_size="$(stat -c %s "$MODEL_FILE.partial" 2>/dev/null || stat -f %z "$MODEL_FILE.partial")"
if [[ "$actual_size" != "$EXPECTED_SIZE" ]]; then
  echo "error: size mismatch — expected $EXPECTED_SIZE, got $actual_size" >&2
  rm -f "$MODEL_FILE.partial"
  exit 1
fi

echo "verifying sha256…"
if command -v sha256sum > /dev/null 2>&1; then
  actual_sha="$(sha256sum "$MODEL_FILE.partial" | awk '{print $1}')"
elif command -v shasum > /dev/null 2>&1; then
  actual_sha="$(shasum -a 256 "$MODEL_FILE.partial" | awk '{print $1}')"
else
  echo "warning: no sha256 tool found — size check only" >&2
  actual_sha=""
fi
if [[ -n "$actual_sha" && "$actual_sha" != "$EXPECTED_SHA256" ]]; then
  echo "error: sha256 mismatch — expected $EXPECTED_SHA256, got $actual_sha" >&2
  rm -f "$MODEL_FILE.partial"
  exit 1
fi

mv "$MODEL_FILE.partial" "$MODEL_FILE"
echo "done: $MODEL_FILE (sha256 $EXPECTED_SHA256)"
