"""
RADAR-4060: Canonical NIfTI Orientation and Physical Coordinate Tools.

Ensures strict compliance with docs/CLINICAL_AUDIT_V3.md Section E:
- Canonicalizes any input NIfTI volume to RAS+ using nibabel.as_closest_canonical.
- Extracts axial slices formatted in standard radiological view:
    * Left side of screen = Patient Right (literal 'R' marker)
    * Right side of screen = Patient Left (literal 'L' marker)
    * Top of screen = Anterior ('A')
    * Bottom of screen = Posterior ('P')
- Derives physical Z position in mm from image affine transformation.
- Guarantees zero patient PHI burned into images.
"""

import base64
import io
from typing import Optional, Tuple
import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Clinical window leveling presets
WINDOW_PRESETS = {
    "SOFT_TISSUE": {"name": "Mô mềm", "wl": 40, "ww": 400, "wl_ww_str": "WL 40 / WW 400"},
    "BONE": {"name": "Xương", "wl": 400, "ww": 1800, "wl_ww_str": "WL 400 / WW 1800"},
    "LUNG": {"name": "Phổi", "wl": -600, "ww": 1500, "wl_ww_str": "WL -600 / WW 1500"},
    "CALCIFICATION": {"name": "Vôi hóa / Sỏi", "wl": 100, "ww": 600, "wl_ww_str": "WL 100 / WW 600"},
}


def load_canonical_nifti(nii_path: str) -> Tuple[np.ndarray, np.ndarray, Tuple[float, float, float]]:
    """
    Loads NIfTI and returns (canonical_data_ras, canonical_affine, voxel_spacings).
    Canonical orientation is guaranteed to be RAS+:
      Axis 0: Left -> Right
      Axis 1: Posterior -> Anterior
      Axis 2: Inferior -> Superior
    """
    nii = nib.load(nii_path)
    c_nii = nib.as_closest_canonical(nii)
    data = c_nii.get_fdata(dtype=np.float32)
    affine = c_nii.affine
    header = c_nii.header
    zooms = header.get_zooms()[:3]
    return data, affine, zooms


def get_physical_z_mm(affine: np.ndarray, slice_idx_0based: int) -> float:
    """Computes exact physical Z coordinate in millimeters from canonical affine."""
    # Center voxel in X and Y
    coord_voxel = np.array([0.0, 0.0, float(slice_idx_0based), 1.0])
    coord_phys = affine @ coord_voxel
    return float(coord_phys[2])


def extract_radiological_axial_slice(
    data_ras: np.ndarray,
    slice_idx_0based: int,
    preset_key: str = "SOFT_TISSUE",
) -> Tuple[np.ndarray, str]:
    """
    Extracts 2D axial slice in radiological viewing convention:
      - Rows: Anterior on top, Posterior on bottom
      - Columns: Patient Right on screen Left, Patient Left on screen Right
    Returns (uint8_2d_image, preset_display_string).
    """
    preset = WINDOW_PRESETS.get(preset_key, WINDOW_PRESETS["SOFT_TISSUE"])
    total_z = data_ras.shape[2]
    clamped_z = max(0, min(total_z - 1, slice_idx_0based))

    # In RAS+: data_ras[x, y, z]
    # x is Left -> Right (0 is Left, -1 is Right)
    # y is Posterior -> Anterior (0 is Posterior, -1 is Anterior)
    slice_xy = data_ras[:, :, clamped_z]

    # For radiological view:
    # Top = Anterior -> y should go from -1 down to 0
    # Left = Patient Right -> x should go from -1 down to 0
    # Image shape should be (height=Y, width=X)
    # slice_xy[x, y] -> transpose to (y, x), then flip y (top=Anterior) and flip x (left=Right)
    # y is axis 1, x is axis 0:
    # slice_xy.T has shape (Y, X). Row 0 is y=0 (Posterior).
    # To have Anterior on top: flip rows vertically (y[::-1, :])
    # To have Patient Right on left: flip columns horizontally (x[:, ::-1])
    slice_radio = slice_xy.T[::-1, ::-1]

    # Apply window leveling
    lower = preset["wl"] - (preset["ww"] / 2.0)
    upper = preset["wl"] + (preset["ww"] / 2.0)
    clamped = np.clip(slice_radio, lower, upper)
    norm = ((clamped - lower) / preset["ww"]) * 255.0
    return norm.astype(np.uint8), preset["wl_ww_str"]


def render_canonical_evidence_jpeg(
    slice_hu_2d: np.ndarray,
    phys_z_mm: float,
    slice_idx_1based: int,
    total_slices: int,
    phase_label: str,
    preset_name: str,
    wl_ww_str: str,
    provenance_label: str = "Window mô hình chấm điểm cao nhất",
    series_alias: str = "SERIES",
    target_width: int = 512,
    quality: int = 82,
) -> str:
    """
    Renders an annotated review slice with literal R / L markers,
    physical Z coordinates, slice index, window preset, and provenance badge.
    Outputs base64 data URI string. Zero PHI.
    """
    img = Image.fromarray(slice_hu_2d).convert("RGB")
    w, h = img.size
    if w != target_width:
        new_h = int(h * (target_width / w))
        img = img.resize((target_width, new_h), Image.Resampling.BILINEAR)
        w, h = img.size

    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Literal R and L markers (Specification Section E: literal R and L markers, not P/T)
    # Left side of screen = Patient Right ('R')
    draw.rectangle([(8, h // 2 - 12), (32, h // 2 + 12)], fill=(0, 0, 0))
    draw.text((16, h // 2 - 6), "R", fill=(255, 230, 0), font=font)

    # Right side of screen = Patient Left ('L')
    draw.rectangle([(w - 32, h // 2 - 12), (w - 8, h // 2 + 12)], fill=(0, 0, 0))
    draw.text((w - 24, h // 2 - 6), "L", fill=(255, 230, 0), font=font)

    # Top banner: Phase & Window Preset
    top_text = f"{phase_label} | {preset_name} ({wl_ww_str})"
    draw.rectangle([(6, 6), (len(top_text) * 7 + 16, 26)], fill=(15, 23, 42))
    draw.text((12, 10), top_text, fill=(255, 255, 255), font=font)

    # Bottom banner: Slice Index, Physical Z, Provenance
    bottom_text = f"Lát {slice_idx_1based}/{total_slices} (Z: {phys_z_mm:.1f}mm) | {provenance_label}"
    draw.rectangle([(6, h - 26), (len(bottom_text) * 7 + 16, h - 6)], fill=(15, 23, 42))
    draw.text((12, h - 22), bottom_text, fill=(203, 213, 225), font=font)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"
