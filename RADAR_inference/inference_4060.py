#!/usr/bin/env python3
"""
RADAR-4060: Optimized RTX 4060 8GB Inference Path for Alibaba DAMO RADAR.

Key optimizations for 8GB VRAM constraint:
1. CPU-resident full preprocessed CT volume and full-volume stitching tensors.
2. Single-channel overlap count map with broadcasting normalization.
3. Only the active sliding-window patch is transferred to CUDA.
4. Optional CUDA FP16 autocast with torch.inference_mode().
5. Immediate patch output transfer back to CPU accumulator.
6. Preserves default upstream ROI (96, 256, 384), preprocessing, and class semantics.
"""

import os
import sys
import argparse
import time
from pathlib import Path
from contextlib import nullcontext
from typing import List, Tuple, Sequence, Dict, Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm
from torch.utils.data import DataLoader

# Add RADAR_inference directory to path
current_dir = Path(__file__).resolve().parent
repo_root = current_dir.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Configure paths before upstream imports
default_ckpt_dir = str(repo_root / "ckpt")
if "CONFIGS_ROOT" not in os.environ:
    os.environ["CONFIGS_ROOT"] = default_ckpt_dir
if "MODEL_ROOT" not in os.environ:
    os.environ["MODEL_ROOT"] = default_ckpt_dir

import inference_demo
inference_demo.configs_root = os.environ["CONFIGS_ROOT"]
inference_demo.model_root = os.environ["MODEL_ROOT"]

from dynamic_network_architectures.med import XBertEncoder
from dynamic_network_architectures.vision_branch import VisionBranch
from monai import transforms
from monai.data.utils import dense_patch_slices
from transformers import BertTokenizer

# Import upstream components
from inference_demo import (
    masks_to_boxes_3d,
    collate_fn,
    _get_scan_interval,
    center_crop,
    DataFolder,
    RADAR,
)


def get_peak_ram_mb() -> float:
    """Get peak resident set size (RAM) in MB."""
    try:
        import resource
        # ru_maxrss is in kilobytes on Linux
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        return 0.0


def initialize_model(
    checkpoint_path: str,
    configs_root: str,
    device: torch.device,
) -> Tuple[transforms.DivisiblePadd, RADAR]:
    """
    Initialize RADAR model and preprocessing transforms.
    """
    print(f"--> Initializing model from: {checkpoint_path}")
    pad_func = transforms.DivisiblePadd(
        keys=["image", "label"],
        k=32,
        mode="constant",
        constant_values=0,
        method="end",
    )

    # Ensure environment variables are set for upstream code and dynamic architectures
    os.environ["CONFIGS_ROOT"] = os.path.abspath(configs_root)
    os.environ["MODEL_ROOT"] = os.path.abspath(os.path.dirname(checkpoint_path))

    vision_encoder = VisionBranch()
    text_encoder = XBertEncoder.from_config({}, from_pretrained=True)

    # BertTokenizer loaded from configs_root
    bert_dir = os.path.join(configs_root, "bert-base-chinese")
    if not os.path.exists(bert_dir):
        # Fallback to repo ckpt directory
        bert_dir = str(repo_root / "ckpt" / "bert-base-chinese")

    tokenizer = BertTokenizer.from_pretrained(bert_dir)
    text_encoder.resize_token_embeddings(len(tokenizer))

    model = RADAR(
        image_encoder=vision_encoder,
        text_encoder=text_encoder,
    )
    # Ensure model uses tokenizer from correct path
    model.tokenizer = tokenizer

    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model"], strict=False)

    model.eval()
    model.to(device)
    print(f"--> Model initialized and moved to {device}")

    return pad_func, model


@torch.inference_mode()
def evaluate_4060(
    pad_func: transforms.DivisiblePadd,
    model: RADAR,
    img_dir: str,
    save_dir: str,
    save_tag: str,
    device: torch.device,
    amp_mode: str = "fp16",
    stitch_device: torch.device = torch.device("cpu"),
    roi_size: Tuple[int, int, int] = (96, 256, 384),
    text_feat_path: str = None,
    profile_memory: bool = False,
) -> Dict[str, Any]:
    """
    4060-optimized evaluation loop.
    Keeps full image and stitching tensors on stitch_device (CPU).
    """
    if text_feat_path is None:
        text_feat_path = str(repo_root / "ckpt" / "infer_text_embedding_radar.pt")

    if not os.path.exists(text_feat_path):
        raise FileNotFoundError(f"Text feature embeddings not found at: {text_feat_path}")

    text_feat_dict = torch.load(text_feat_path, map_location="cpu")
    # Move text features to device for fast dot product
    for k, v in text_feat_dict.items():
        if isinstance(v, torch.Tensor):
            text_feat_dict[k] = v.to(device)

    datafolder = DataFolder(img_dir)
    dataloader = DataLoader(
        datafolder,
        batch_size=1,
        shuffle=False,
        num_workers=2,
        drop_last=False,
        collate_fn=collate_fn,
    )

    sw_batch_size = 1
    overlap = 0.25
    results = []
    organ_feat_dict = {}

    save_path = os.path.join(save_dir, f"RADAR_infer_results_{save_tag}.csv")
    os.makedirs(save_dir, exist_ok=True)

    use_cuda = device.type == "cuda"
    use_amp = (amp_mode == "fp16") and use_cuda

    if use_cuda and profile_memory:
        torch.cuda.reset_peak_memory_stats(device)

    t_start = time.perf_counter()

    for i, (image, test_items, meta_info) in enumerate(tqdm(dataloader, desc="Infer-4060")):
        if use_cuda:
            torch.cuda.empty_cache()

        skip_case = False
        for tmp_s in image.shape[1:]:
            if tmp_s > 1000:
                skip_case = True
                break
        if skip_case:
            print(f"Skipping case with dimension > 1000: {meta_info['file_name']}")
            continue

        fid = meta_info["file_name"]
        organ_feat_dict[fid] = {}

        # KEEP FULL IMAGE ON CPU
        # Shape: [1, 1, D, W, H]
        image_cpu = image[None]
        test_organs = meta_info["test_organ_names"]

        image_size = list(image_cpu.shape[2:])
        num_spatial_dims = len(image_cpu.shape) - 2

        scan_interval = _get_scan_interval(image_size, roi_size, num_spatial_dims, overlap)
        slices = dense_patch_slices(image_size, roi_size, scan_interval)
        num_win = len(slices)
        organ_logits = dict(zip(test_items, [[] for _ in test_items]))

        # Stitching tensors reside on stitch_device (CPU)
        # full_mask: 37 channels (one for each class/organ)
        full_mask = torch.zeros(
            (1, 37) + tuple(image_size), dtype=torch.float32, device=stitch_device
        )
        # count_map: SINGLE channel only (saving 36 full-resolution float32 channels)
        count_map = torch.zeros(
            (1, 1) + tuple(image_size), dtype=torch.float32, device=stitch_device
        )

        for slice_g in range(0, num_win, sw_batch_size):
            slice_range = range(slice_g, min(slice_g + sw_batch_size, num_win))
            unravel_slice = [
                [slice(int(idx / num_win), int(idx / num_win) + 1), slice(None)]
                + list(slices[idx % num_win])
                for idx in slice_range
            ]

            # Move ONLY the active window patch to CUDA
            window_patches = torch.cat([image_cpu[win_slice] for win_slice in unravel_slice]).to(
                device
            )

            autocast_ctx = (
                torch.autocast(device_type="cuda", dtype=torch.float16)
                if use_amp
                else nullcontext()
            )

            with autocast_ctx:
                organ_logits, pred_window_seg_prob = model.forward_test_win(
                    window_patches,
                    None,
                    organ_logits,
                    test_organs,
                    text_feat_dict,
                    organ_feat_dict[fid],
                    None,
                )

            # Transfer patch prediction immediately to stitch_device (CPU)
            pred_seg_cpu = pred_window_seg_prob.to(device=stitch_device, dtype=torch.float32)
            del window_patches, pred_window_seg_prob

            # Trilinear interpolation on CPU avoids ~3.5 GB CUDA allocation
            interpolated_seg_prob = F.interpolate(
                pred_seg_cpu, size=tuple(roi_size), mode="trilinear"
            )
            del pred_seg_cpu

            for ii, slice_idx in enumerate(slice_range):
                full_slice = unravel_slice[ii]
                full_mask[full_slice] += interpolated_seg_prob[ii]

                # Update single-channel count map using broadcasted slice coordinates
                count_slice = (full_slice[0], slice(0, 1)) + tuple(full_slice[2:])
                count_map[count_slice] += 1.0

            del interpolated_seg_prob

        # Single-channel count map normalization via PyTorch broadcasting
        count_map = torch.clamp(count_map, min=1.0)
        stitched_mask = full_mask / count_map
        del full_mask, count_map

        # argmax on CPU gives discrete organ mask (1, 1, D, W, H)
        stitched_mask = stitched_mask.argmax(1).unsqueeze(0)

        # Boundary filtering for organ completeness
        margin = 2
        boundaries = []
        squeeze_stitched_mask = stitched_mask.squeeze(0).squeeze(0)
        for d in range(squeeze_stitched_mask.dim()):
            start_slice = [slice(None)] * squeeze_stitched_mask.dim()
            end_slice = [slice(None)] * squeeze_stitched_mask.dim()

            start_slice[d] = slice(None, margin)
            end_slice[d] = slice(-margin, None)

            boundaries.append(
                squeeze_stitched_mask[tuple(start_slice)][squeeze_stitched_mask[tuple(start_slice)] > 0]
            )
            boundaries.append(
                squeeze_stitched_mask[tuple(end_slice)][squeeze_stitched_mask[tuple(end_slice)] > 0]
            )
        boundaries = torch.cat(boundaries)
        boundary_values = boundaries[boundaries > 0].flatten()
        boundary_organs = torch.unique(boundary_values)

        organ_ids, organ_counts = torch.unique(squeeze_stitched_mask, return_counts=True)
        organ_ids = organ_ids.long()
        organ_counts = organ_counts[organ_ids != 0]
        organ_ids = organ_ids[organ_ids != 0]

        intact_organ_ids = [
            organ_id
            for organ_id, organ_count in zip(organ_ids, organ_counts)
            if organ_id not in boundary_organs
        ]
        intact_organ_ids = torch.tensor(intact_organ_ids, device=stitch_device).long()
        intact_organ_ids = intact_organ_ids - 1

        # Second pass: Targeted crop inference for intact organs not yet scored
        for k, v in organ_logits.items():
            if not len(v):
                organ_name = k.split("_")[0]
                organ_id = datafolder.organs.index(organ_name)

                # Crop on CPU
                organ_mask_binary = torch.eq(stitched_mask, organ_id + 1)
                if not torch.any(organ_mask_binary):
                    continue

                window_patch, window_mask = center_crop(
                    image_cpu,
                    organ_mask_binary,
                    crop_size=roi_size,
                )
                window_mask = window_mask.float()
                window_mask[window_mask == 1] = organ_id + 1

                pad_data = pad_func({"image": window_patch[0], "label": window_mask[0]})
                window_patch = pad_data["image"]

                # Transfer single cropped patch to CUDA
                window_patch_device = window_patch[None].to(device)

                autocast_ctx = (
                    torch.autocast(device_type="cuda", dtype=torch.float16)
                    if use_amp
                    else nullcontext()
                )

                with autocast_ctx:
                    organ_logits, _ = model.forward_test_win(
                        window_patch_device,
                        None,
                        organ_logits,
                        test_organs,
                        text_feat_dict,
                        organ_feat_dict[fid],
                        None,
                        skip_organ=organ_id,
                    )
                del window_patch_device

        # Format patient row
        res = [meta_info["file_name"]] + [""] * len(datafolder.test_items)
        organ_logits_clean = {
            item: probs for item, probs in organ_logits.items() if len(probs) > 0
        }

        for item, probs in organ_logits_clean.items():
            res[datafolder.test_items.index(item) + 1] = float(
                np.concatenate(probs).mean(0)[1]
            )
        results.append(res)

    t_end = time.perf_counter()
    elapsed_time = t_end - t_start

    # Save output CSV
    columns = ["file_name"] + [
        f"{k} ({datafolder.english_mapping[k]})" for k in datafolder.test_items
    ]
    df_results = pd.DataFrame(results, columns=columns)
    df_results.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"--> Inference completed. Results saved to: {save_path}")

    metrics = {
        "elapsed_seconds": elapsed_time,
        "cases_processed": len(results),
        "save_path": save_path,
        "peak_ram_mb": get_peak_ram_mb(),
    }

    if use_cuda:
        peak_alloc = torch.cuda.max_memory_allocated(device) / (1024**2)
        peak_res = torch.cuda.max_memory_reserved(device) / (1024**2)
        metrics["peak_cuda_allocated_mb"] = peak_alloc
        metrics["peak_cuda_reserved_mb"] = peak_res
        print(f"--> [CUDA Memory] Peak Allocated: {peak_alloc:.2f} MB ({peak_alloc/1024:.2f} GB)")
        print(f"--> [CUDA Memory] Peak Reserved:  {peak_res:.2f} MB ({peak_res/1024:.2f} GB)")

    print(f"--> [Timing] Wall-clock elapsed: {elapsed_time:.2f} seconds")
    print(f"--> [System] Peak RAM: {metrics['peak_ram_mb']:.2f} MB")

    return metrics


def parse_args():
    parser = argparse.ArgumentParser(
        description="RADAR-4060: 8GB VRAM Optimized Inference Entry Point"
    )
    # Support both --img-dir and --img_dir formats
    parser.add_argument(
        "--img-dir",
        "--img_dir",
        dest="img_dir",
        type=str,
        default=str(repo_root / "data" / "demo_cases"),
        help="Path to input NIfTI image folder.",
    )
    parser.add_argument(
        "--save-dir",
        "--save_dir",
        dest="save_dir",
        type=str,
        default=str(repo_root / "results"),
        help="Path to output results folder.",
    )
    parser.add_argument(
        "--save-tag",
        "--save_tag",
        dest="save_tag",
        type=str,
        default="4060_demo",
        help="Tag suffix for output result CSV.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        choices=["cuda", "cpu"],
        help="Compute device for neural network forward passes.",
    )
    parser.add_argument(
        "--amp",
        type=str,
        default="fp16",
        choices=["fp16", "off"],
        help="Mixed precision mode (fp16 or off).",
    )
    parser.add_argument(
        "--stitch-device",
        "--stitch_device",
        dest="stitch_device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to hold full-volume probability accumulator and count map.",
    )
    parser.add_argument(
        "--roi-size",
        "--roi_size",
        dest="roi_size",
        type=int,
        nargs=3,
        default=[96, 256, 384],
        help="Sliding window ROI spatial dimensions (D, H, W).",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str(repo_root / "ckpt" / "checkpoint_radar_pretrain.pth"),
        help="Path to RADAR model checkpoint.",
    )
    parser.add_argument(
        "--configs-root",
        "--configs_root",
        dest="configs_root",
        type=str,
        default=str(repo_root / "ckpt"),
        help="Directory containing BERT config and tokenizer files.",
    )
    parser.add_argument(
        "--profile-memory",
        "--profile_memory",
        dest="profile_memory",
        action="store_true",
        default=True,
        help="Track and report peak CUDA memory usage.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    device = torch.device(args.device)
    stitch_device = torch.device(args.stitch_device)
    roi_size = tuple(args.roi_size)

    pad_func, model = initialize_model(
        checkpoint_path=args.checkpoint,
        configs_root=args.configs_root,
        device=device,
    )

    metrics = evaluate_4060(
        pad_func=pad_func,
        model=model,
        img_dir=args.img_dir,
        save_dir=args.save_dir,
        save_tag=args.save_tag,
        device=device,
        amp_mode=args.amp,
        stitch_device=stitch_device,
        roi_size=roi_size,
        profile_memory=args.profile_memory,
    )
    return metrics


if __name__ == "__main__":
    main()
