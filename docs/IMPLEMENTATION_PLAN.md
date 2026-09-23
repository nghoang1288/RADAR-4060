# RADAR-4060 Implementation Plan

## Objective

Create a reproducible, research-only RTX 4060 8GB inference port of Alibaba DAMO RADAR for contrast-enhanced abdominal CT.

- Target repository: `nghoang1288/RADAR-4060`
- Upstream: `alibaba-damo-academy/damo-radar`
- Pinned upstream commit: `0dbf0ece209b77d722588e5e7943014d3db48f7f`
- Preferred runtime: Windows + WSL2 Ubuntu
- Target GPU: NVIDIA RTX 4060 8GB
- Python: 3.10

Do not depend on Prima in any way.

## Phase 0 — Import exact upstream baseline

1. Verify upstream commit `0dbf0ece209b77d722588e5e7943014d3db48f7f` exists.
2. Preserve upstream Git history, `LICENSE`, `THIRD_PARTY_LICENSES.md`, and copyright notices.
3. Add/retain an `upstream` remote pointing to Alibaba DAMO RADAR.
4. Replace the temporary bootstrap `main` with that exact upstream commit using the one-time bootstrap exception in `ANTIGRAVITY_BRIDGE.md`.
5. Create implementation branch `antigravity/radar-20260922-001` from the exact imported baseline.
6. Copy this plan into `docs/IMPLEMENTATION_PLAN.md` on the implementation branch.

## Why the 8GB port is needed

The upstream inference path uses 3D Conv/UNet processing and full-volume tensors. The main risk on an 8GB GPU is not only model weights but also 3D activations and full-resolution 37-channel stitching/probability tensors.

The first port should change memory placement, not model semantics.

## Memory architecture target

CPU:
- full preprocessed CT volume;
- full-volume probability accumulator;
- overlap/count accumulator;
- final stitched probability/segmentation;
- serialization/reporting.

GPU:
- model weights;
- one active sliding-window patch at a time;
- temporary 3D activations;
- temporary patch output.

Required first-pass behavior:
1. Keep the full CT volume on CPU.
2. Transfer only the active patch to CUDA.
3. Use `torch.inference_mode()`.
4. Use CUDA autocast FP16 by default, with an explicit opt-out.
5. Move the patch prediction back to CPU immediately after inference.
6. Keep the full probability accumulator on CPU.
7. Replace a 37-channel overlap/count map with a single-channel count map and broadcast during normalization.
8. Avoid unnecessary duplicate full-resolution 37-channel tensors.
9. Preserve upstream default ROI `(96, 256, 384)`.
10. Do not quantize model weights, lower input resolution, change preprocessing, or alter thresholds in the reference 4060 path.

## Phase 1 — Minimal reproducible inference environment

Create:
- `requirements-inference.txt`;
- `scripts/setup_wsl.sh`;
- `scripts/download_models.sh`;
- `scripts/run_demo_4060.sh`;
- `scripts/profile_demo_4060.sh`.

Rules:
- Python 3.10.
- Install only packages needed by the inference path.
- Do not blindly install the full legacy upstream requirements file.
- Record exact Python, PyTorch, CUDA runtime, NVIDIA driver, MONAI, SimpleITK, transformers and nibabel versions.
- Git-ignore checkpoints and generated outputs.

## Phase 2 — Baseline characterization

Use only the upstream public demo NIfTI.

Record:
- whether the original inference path completes or OOMs;
- peak CUDA allocated memory;
- peak CUDA reserved memory;
- wall-clock runtime;
- CPU RAM peak if practical;
- exact failure location if OOM.

Do not change the model merely to make the baseline complete.

## Phase 3 — 4060 inference path

Prefer a dedicated entry point:
`RADAR_inference/inference_4060.py`

Expose at least:
- `--img-dir`
- `--save-dir`
- `--device cuda|cpu`
- `--amp fp16|off`
- `--stitch-device cpu|cuda` (default: cpu)
- `--roi-size 96 256 384`
- `--profile-memory`
- `--checkpoint`

Reuse upstream logic rather than forking large amounts of code.

Preserve:
- preprocessing;
- class count/order;
- output semantics;
- reference ROI.

## Phase 4 — Regression tests

Add synthetic tests proving:
1. single-channel count-map broadcasting equals a multi-channel reference;
2. CPU stitching equals reference stitching on a small synthetic volume;
3. patch order does not materially alter the result beyond floating-point tolerance;
4. AMP can be disabled;
5. the 4060 path does not keep full-volume 37-channel accumulators on CUDA;
6. tests use no patient data.

## Phase 5 — Public-demo validation

The optimized public demo should:
- complete without CUDA OOM on RTX 4060 8GB, or produce a precise measured blocker;
- preserve upstream ROI by default;
- target peak CUDA reserved memory <= 7.5 GB;
- emit expected inference outputs;
- record wall-clock runtime;
- record exact environment versions.

Numerical comparison:
- compare optimized output with upstream public/reference output where available;
- report mean absolute difference;
- report max absolute difference;
- investigate max score delta > 0.02 before calling the port validated;
- do not claim clinical equivalence from this numerical check.

If it still OOMs:
1. identify the exact peak/failure stage;
2. remove avoidable duplicate tensors;
3. consider suppressing unused deep-supervision inference outputs only if semantics remain unchanged;
4. consider chunked post-processing;
5. only then propose a smaller ROI as an explicitly non-reference fallback.

## Phase 6 — Usability

After the 8GB gate passes:
- one-command WSL setup;
- one-command model download;
- one-command public demo;
- Windows/WSL path notes;
- clear research-only disclaimer;
- upstream attribution;
- known limitations.

Initial supported input remains NIfTI.

Do not add PACS/DICOM integration until the public-demo NIfTI path is stable.

## Phase 7 — Optional radiologist-facing output

Only after inference stability:
- transform score output into local HTML;
- organize findings anatomically;
- support configurable thresholds;
- show review-aid slices only when technically justified;
- do not imply representative images prove localization unless the model actually localizes;
- keep all patient-derived outputs local and Git-ignored.

## Acceptance gate for the first task

1. `main` is the exact pinned upstream baseline before code changes.
2. `agent-control` remains RADAR-only.
3. Implementation branch exists.
4. Optimized inference preserves default ROI.
5. Full-volume stitching is CPU-resident in 4060 mode.
6. Synthetic tests pass.
7. Public demo completes on RTX 4060 8GB without OOM, OR an exact measured blocker is documented.
8. `docs/BENCHMARK.md` records environment, peak VRAM, runtime and numerical delta.
9. No patient-derived files or checkpoints are committed.
10. A PR is opened to `main` but not merged.
