#!/usr/bin/env bash
set -euo pipefail

# Profile and benchmark RADAR inference comparing baseline and 4060 paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${VENV_DIR:-${HOME}/.venvs/radar-4060}"
PYTHON_BIN="${VENV_DIR}/bin/python"

if [ ! -f "${PYTHON_BIN}" ]; then
    echo "Virtual environment not found at ${VENV_DIR}. Please run scripts/setup_wsl.sh first."
    exit 1
fi

echo "=== RADAR-4060 Profiling & Benchmark ==="

"${PYTHON_BIN}" - <<EOF
import os
import sys
import time
import pandas as pd
import numpy as np
import torch

repo_root = "${REPO_ROOT}"
inf_dir = os.path.join(repo_root, "RADAR_inference")
sys.path.insert(0, inf_dir)

import inference_4060

print("\n--- System & Environment ---")
print(f"PyTorch version:       {torch.__version__}")
print(f"CUDA available:        {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device name:           {torch.cuda.get_device_name(0)}")
    print(f"Device total memory:   {torch.cuda.get_device_properties(0).total_memory / (1024**2):.1f} MB")

img_dir = os.path.join(repo_root, "data", "demo_cases")
save_dir = os.path.join(repo_root, "results")
ckpt_path = os.path.join(repo_root, "ckpt", "checkpoint_radar_pretrain.pth")

print("\n--- Running Optimized 4060 Inference (FP16, CPU Stitching) ---")
pad_func, model = inference_4060.initialize_model(
    checkpoint_path=ckpt_path,
    configs_root=os.path.join(repo_root, "ckpt"),
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
)

metrics_4060 = inference_4060.evaluate_4060(
    pad_func=pad_func,
    model=model,
    img_dir=img_dir,
    save_dir=save_dir,
    save_tag="benchmark_4060",
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    amp_mode="fp16",
    stitch_device=torch.device("cpu"),
    profile_memory=True
)

print("\n--- Benchmark Summary ---")
print(f"Peak CUDA Allocated:  {metrics_4060.get('peak_cuda_allocated_mb', 0):.2f} MB")
print(f"Peak CUDA Reserved:   {metrics_4060.get('peak_cuda_reserved_mb', 0):.2f} MB")
print(f"Peak Host RAM:        {metrics_4060.get('peak_ram_mb', 0):.2f} MB")
print(f"Wall-clock runtime:   {metrics_4060.get('elapsed_seconds', 0):.2f} s")
EOF
