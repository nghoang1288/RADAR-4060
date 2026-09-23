#!/usr/bin/env bash
set -euo pipefail

# Setup script for RADAR-4060 inference environment in WSL2 (Ubuntu)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${VENV_DIR:-${HOME}/.venvs/radar-4060}"

echo "=== RADAR-4060 WSL Environment Setup ==="

# Check nvidia-smi
if command -v nvidia-smi &>/dev/null; then
    echo "--> NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
    echo "WARNING: nvidia-smi not found. CUDA acceleration might not work."
fi

# Ensure uv is installed
if ! command -v uv &>/dev/null && [ ! -f "${HOME}/.local/bin/uv" ]; then
    echo "--> Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="${HOME}/.local/bin:${PATH}"

# Install Python 3.10 via uv
echo "--> Ensuring Python 3.10 is available..."
uv python install 3.10

# Create virtual environment
if [ ! -d "${VENV_DIR}" ]; then
    echo "--> Creating virtual environment at ${VENV_DIR}..."
    uv venv "${VENV_DIR}" --python 3.10
else
    echo "--> Virtual environment already exists at ${VENV_DIR}"
fi

# Install dependencies
echo "--> Installing inference dependencies from requirements-inference.txt..."
uv pip install --python "${VENV_DIR}" -r "${REPO_ROOT}/requirements-inference.txt"

echo "=== Setup complete! ==="
echo "Activate environment using: source ${VENV_DIR}/bin/activate"
