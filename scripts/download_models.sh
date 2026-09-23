#!/usr/bin/env bash
set -euo pipefail

# Script to download RADAR model checkpoint and tokenizer for 4060 inference
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${1:-${REPO_ROOT}/ckpt}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "--> Target directory: ${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"

"${PYTHON_BIN}" - <<EOF
import os
import sys
from huggingface_hub import snapshot_download

target_dir = os.path.abspath("${TARGET_DIR}")
print(f"Downloading checkpoint and BERT weights to: {target_dir}")

patterns = [
    "checkpoint_radar_pretrain.pth",
    "bert-base-chinese/*"
]

snapshot_download(
    repo_id="radar-generalist/RADAR",
    repo_type="model",
    local_dir=target_dir,
    allow_patterns=patterns,
    local_dir_use_symlinks=False
)
print("Download completed successfully.")
EOF
