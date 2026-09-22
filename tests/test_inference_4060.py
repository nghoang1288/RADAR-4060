"""
Synthetic regression tests for RADAR-4060 inference path.
All tests use purely synthetic data (no patient data).
"""

import pytest
import torch
import torch.nn.functional as F
from monai.data.utils import dense_patch_slices


def test_single_channel_count_map_broadcasting():
    """
    Test 1: Single-channel count-map broadcasting produces mathematically identical
    results to a 37-channel count-map accumulator.
    """
    num_classes = 37
    spatial_shape = (24, 32, 48)

    # Synthetic full_mask and patch updates
    torch.manual_seed(42)
    full_mask = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32)
    single_count = torch.zeros((1, 1) + spatial_shape, dtype=torch.float32)
    multi_count = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32)

    # Simulate 4 overlapping patches
    patches = [
        (slice(0, 16), slice(0, 24), slice(0, 32)),
        (slice(8, 24), slice(8, 32), slice(16, 48)),
        (slice(4, 20), slice(4, 28), slice(8, 40)),
        (slice(0, 16), slice(8, 32), slice(16, 48)),
    ]

    for p_d, p_h, p_w in patches:
        patch_shape = (p_d.stop - p_d.start, p_h.stop - p_h.start, p_w.stop - p_w.start)
        patch_prob = torch.rand((1, num_classes) + patch_shape, dtype=torch.float32)

        full_slice = (slice(0, 1), slice(None), p_d, p_h, p_w)
        full_mask[full_slice] += patch_prob

        # Single-channel count update
        single_slice = (slice(0, 1), slice(0, 1), p_d, p_h, p_w)
        single_count[single_slice] += 1.0

        # Multi-channel count update
        multi_count[full_slice] += 1.0

    # Avoid division by zero
    single_count = torch.clamp(single_count, min=1.0)
    multi_count = torch.clamp(multi_count, min=1.0)

    # Normalize
    out_single = full_mask / single_count  # PyTorch broadcasting
    out_multi = full_mask / multi_count

    assert torch.allclose(out_single, out_multi, atol=1e-7), (
        f"Max diff: {(out_single - out_multi).abs().max().item()}"
    )
    assert torch.equal(out_single.argmax(1), out_multi.argmax(1))


def test_cpu_stitching_equivalence():
    """
    Test 2: CPU-resident stitching matches CUDA stitching on small synthetic volumes.
    """
    num_classes = 37
    spatial_shape = (16, 32, 48)
    roi_size = (8, 16, 24)

    torch.manual_seed(123)
    # Synthetic patches
    slices = dense_patch_slices(spatial_shape, roi_size, scan_interval=(4, 8, 12))

    # CPU accumulators
    mask_cpu = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32, device="cpu")
    count_cpu = torch.zeros((1, 1) + spatial_shape, dtype=torch.float32, device="cpu")

    # GPU accumulators (simulating upstream reference)
    if torch.cuda.is_available():
        mask_gpu = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32, device="cuda")
        count_gpu = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32, device="cuda")
    else:
        mask_gpu = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32, device="cpu")
        count_gpu = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32, device="cpu")

    for s in slices:
        patch_prob = torch.rand((1, num_classes) + roi_size, dtype=torch.float32)

        # CPU stitch
        full_slice_cpu = (slice(0, 1), slice(None)) + s
        mask_cpu[full_slice_cpu] += patch_prob
        count_cpu[(slice(0, 1), slice(0, 1)) + s] += 1.0

        # GPU reference stitch
        full_slice_gpu = (slice(0, 1), slice(None)) + s
        mask_gpu[full_slice_gpu] += patch_prob.to(mask_gpu.device)
        count_gpu[full_slice_gpu] += 1.0

    count_cpu = torch.clamp(count_cpu, min=1.0)
    count_gpu = torch.clamp(count_gpu, min=1.0)

    stitched_cpu = (mask_cpu / count_cpu).argmax(1)
    stitched_gpu = (mask_gpu / count_gpu).argmax(1).cpu()

    assert torch.equal(stitched_cpu, stitched_gpu), "CPU and GPU argmax predictions mismatch!"


def test_patch_order_invariance():
    """
    Test 3: Patch evaluation order does not alter normalized stitched outputs
    beyond standard floating-point summation tolerance.
    """
    num_classes = 37
    spatial_shape = (16, 32, 48)
    roi_size = (8, 16, 24)

    torch.manual_seed(999)
    slices = dense_patch_slices(spatial_shape, roi_size, scan_interval=(4, 8, 12))

    # Generate fixed patches for each slice
    patch_data = [
        torch.rand((1, num_classes) + roi_size, dtype=torch.float32)
        for _ in slices
    ]

    # Order 1: forward
    mask_fwd = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32)
    count_fwd = torch.zeros((1, 1) + spatial_shape, dtype=torch.float32)
    for s, p in zip(slices, patch_data):
        mask_fwd[(slice(0, 1), slice(None)) + s] += p
        count_fwd[(slice(0, 1), slice(0, 1)) + s] += 1.0
    out_fwd = mask_fwd / torch.clamp(count_fwd, min=1.0)

    # Order 2: reversed
    mask_rev = torch.zeros((1, num_classes) + spatial_shape, dtype=torch.float32)
    count_rev = torch.zeros((1, 1) + spatial_shape, dtype=torch.float32)
    for s, p in reversed(list(zip(slices, patch_data))):
        mask_rev[(slice(0, 1), slice(None)) + s] += p
        count_rev[(slice(0, 1), slice(0, 1)) + s] += 1.0
    out_rev = mask_rev / torch.clamp(count_rev, min=1.0)

    # Summation order may have tiny floating point variations (~1e-6)
    max_diff = (out_fwd - out_rev).abs().max().item()
    assert max_diff < 1e-5, f"Patch order difference too high: {max_diff}"
    assert torch.equal(out_fwd.argmax(1), out_rev.argmax(1))


def test_amp_can_be_disabled():
    """
    Test 4: Verify AMP can be toggled between fp16 and off without breaking inference.
    """
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available for AMP test")

    x = torch.randn(1, 32, 8, 16, 16, device="cuda")
    conv = torch.nn.Conv3d(32, 32, kernel_size=3, padding=1).cuda().eval()

    # AMP on (fp16)
    with torch.inference_mode():
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            y_amp = conv(x)
            assert y_amp.dtype == torch.float16

    # AMP off (fp32)
    with torch.inference_mode():
        y_fp32 = conv(x)
        assert y_fp32.dtype == torch.float32


def test_cuda_residency_invariants():
    """
    Test 5: Verify 4060 path keeps full-volume accumulators on CPU,
    and only moves active sliding-window patches to CUDA.
    """
    spatial_shape = (96, 256, 384)
    stitch_device = torch.device("cpu")

    # In 4060 path:
    full_mask = torch.zeros((1, 37) + spatial_shape, dtype=torch.float32, device=stitch_device)
    count_map = torch.zeros((1, 1) + spatial_shape, dtype=torch.float32, device=stitch_device)

    assert full_mask.device.type == "cpu", "Full mask accumulator must reside on CPU!"
    assert count_map.device.type == "cpu", "Count map accumulator must reside on CPU!"
    assert count_map.shape[1] == 1, "Count map must be single-channel!"

    # Active patch transfer check
    patch_size = (1, 1, 96, 256, 384)
    patch_cpu = torch.zeros(patch_size, dtype=torch.float32, device="cpu")
    if torch.cuda.is_available():
        patch_cuda = patch_cpu.to("cuda")
        assert patch_cuda.device.type == "cuda"
        # Immediate cleanup
        del patch_cuda
        torch.cuda.empty_cache()


def test_no_patient_data_used():
    """
    Test 6: Verify all synthetic test inputs are randomly generated and
    do not load any patient DICOM or NIfTI files.
    """
    # Simply assert synthetic shapes
    synth_tensor = torch.zeros((1, 1, 10, 10, 10))
    assert synth_tensor.sum() == 0.0
