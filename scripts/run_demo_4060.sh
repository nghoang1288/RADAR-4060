#!/usr/bin/env bash
set -euo pipefail

# Run RADAR inference on public demo case with RTX 4060 8GB optimizations
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${VENV_DIR:-${HOME}/.venvs/radar-4060}"
PYTHON_BIN="${VENV_DIR}/bin/python"

if [ ! -f "${PYTHON_BIN}" ]; then
    echo "Virtual environment not found at ${VENV_DIR}. Please run scripts/setup_wsl.sh first."
    exit 1
fi

IMG_DIR="${1:-${REPO_ROOT}/data/demo_cases}"
SAVE_DIR="${2:-${REPO_ROOT}/results}"
SAVE_TAG="${3:-demo_4060}"

echo "=== Running RADAR-4060 Inference ==="
echo "Input directory:  ${IMG_DIR}"
echo "Output directory: ${SAVE_DIR}"
echo "Save tag:         ${SAVE_TAG}"

"${PYTHON_BIN}" "${REPO_ROOT}/RADAR_inference/inference_4060.py" \
    --img-dir "${IMG_DIR}" \
    --save-dir "${SAVE_DIR}" \
    --save-tag "${SAVE_TAG}" \
    --amp fp16 \
    --stitch-device cpu \
    --device cuda \
    --profile-memory

echo "=== Inference completed successfully! ==="
