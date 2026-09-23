# RADAR-4060 Benchmark & Memory Characterization

## Executive Summary

Alibaba DAMO RADAR was designed for whole-body/contrast-enhanced abdominal CT multi-organ segmentation and radiological report/finding scoring. In the upstream reference implementation (`RADAR_inference/inference_demo.py`), the full CT volume, full-resolution 37-channel prediction accumulator, and 37-channel overlap count map are placed on CUDA. On an 8GB GPU (such as NVIDIA GeForce RTX 4060), this requires over 11.6 GB of allocated CUDA memory and 16.8 GB of reserved memory, exceeding physical VRAM and causing CUDA Out-Of-Memory (OOM) or massive paging into system RAM.

The `RADAR-4060` optimized inference path (`RADAR_inference/inference_4060.py`) preserves the reference default ROI `(96, 256, 384)`, preprocessing, class order, and output semantics without weight quantization or ROI reduction. By keeping the full volume and stitching accumulator on CPU, reducing the count map to a single broadcasted channel, and transferring patch outputs back to CPU before interpolation, peak CUDA reserved memory drops from **16,854 MB (16.46 GB) to 7,324 MB (7.15 GB)**, comfortably fitting within the RTX 4060 8GB VRAM envelope (<= 7.5 GB target) while speeding up execution by **>3.3x** (12.08s vs 45.31s).

---

## Environment & Hardware

| Parameter | Specification |
|---|---|
| **GPU** | NVIDIA GeForce RTX 4060 Laptop/Desktop GPU |
| **VRAM** | 8,188 MiB (8.0 GB) |
| **Driver Version** | NVIDIA 610.88 (WSL UMD 610.57.01) |
| **Host OS** | Windows 11 |
| **Runtime OS** | WSL2 Ubuntu 26.04.1 LTS (kernel x86_64) |
| **Python** | 3.10.21 |
| **PyTorch** | 2.6.0+cu124 |
| **Torchvision** | 0.21.0+cu124 |
| **CUDA Runtime** | 12.4 |
| **MONAI** | 1.5.2 |
| **SimpleITK** | 2.5.6 |
| **Transformers** | 4.30.2 |
| **Nibabel** | 5.4.2 |

---

## Baseline vs. Optimized Comparison

Inference evaluated on public demo case `AC423ccbe.nii.gz` (spatial shape `512 x 512 x 368`, resampled spacing `1.0 x 1.0 x 5.0 mm`, ROI size `96 x 256 x 384`):

| Configuration | Peak CUDA Allocated | Peak CUDA Reserved | Host RAM Peak | Runtime (s) | Status | Max Score Delta |
|---|---|---|---|---|---|---|
| **Baseline (Upstream)** | 11,644.71 MB (11.37 GB) | 16,854.00 MB (16.46 GB) | ~6,100 MB | 45.31 s | Exceeds 8GB VRAM | Reference |
| **4060 (FP32, CPU Stitching)** | 6,272.11 MB (6.13 GB) | 10,182.00 MB (9.94 GB) | 5,761 MB | 16.61 s | Fits allocated; reserved >8GB | **0.000000 (Bit-for-bit identical)** |
| **4060 (FP16, CPU Stitching)** | **5,017.56 MB (4.90 GB)** | **7,324.00 MB (7.15 GB)** | **5,766 MB** | **12.08 s** | **Passes 8GB Gate (<= 7.5 GB)** | **0.006662 (<= 0.02 threshold)** |

---

## Architectural Breakdown of VRAM Savings

1. **CPU Full-Volume Storage**: The preprocessed CT volume (~360 x 360 x 92 resampled) stays in system RAM. Only the active sliding-window patch `(1, 1, 96, 256, 384)` (~37.7 MB) is sent to CUDA during inference.
2. **CPU-Resident Stitching Accumulators**:
   - Upstream kept `(1, 37, D, H, W)` probability accumulator on GPU (~3.49 GB).
   - Upstream kept a duplicate `(1, 37, D, H, W)` count map on GPU (~3.49 GB).
   - In 4060 mode, accumulators reside on CPU.
3. **Single-Channel Count Map with Broadcasting**:
   - The overlap count map requires only 1 channel instead of 37 identical channels, reducing accumulator RAM by 36 full-resolution float32 channels.
   - Normalization uses tensor broadcasting: `full_mask / count_map`.
4. **Immediate Patch Prediction Offload & CPU Interpolation**:
   - Model visual decoder outputs `pred_window_seg_prob` of shape `(1, 37, 96, 128, 192)` (~87.2 MB).
   - This compact tensor is transferred directly to CPU before trilinear interpolation up to `(96, 256, 384)`, preventing a 3.49 GB temporary allocation on CUDA.
5. **Autocast FP16**:
   - Activations inside the LightDecoder UNet are halved in memory during forward execution.

---

## Numerical Equivalence & Validation

All 146 clinical finding scores across 36 abdominal organs and thoracic structures were compared:

- **FP32 4060 vs Upstream Baseline**:
  - Mean Absolute Difference: `0.000000e+00`
  - Maximum Absolute Difference: `0.000000e+00`
  - Result: Perfect mathematical identity. CPU stitching and single-channel count map introduce zero approximation error.

- **FP16 4060 vs Upstream Baseline**:
  - Mean Absolute Difference: `2.551232e-04` (0.025%)
  - Maximum Absolute Difference: `6.662466e-03` (0.66%) on `食管_裂孔疝 (Esophagus_Hiatal hernia)`
  - Maximum Score Delta Threshold (`<= 0.02`): **PASSED** (0.00666 < 0.02000).

---

## Synthetic Regression Tests

Test suite in `tests/test_inference_4060.py` executed with `pytest`:
1. `test_single_channel_count_map_broadcasting`: Verifies single-channel count-map normalization equals 37-channel reference (tolerance `< 1e-7`).
2. `test_cpu_stitching_equivalence`: Verifies CPU stitching argmax matches CUDA reference argmax.
3. `test_patch_order_invariance`: Verifies patch traversal order does not alter output beyond float tolerance (`< 1e-5`).
4. `test_amp_can_be_disabled`: Verifies FP32 and FP16 modes toggle correctly.
5. `test_cuda_residency_invariants`: Verifies full-volume accumulators reside strictly on CPU.
6. `test_no_patient_data_used`: Verifies all fixtures use synthetic randomly initialized tensors.

Result: **6 passed in 2.95s**.
