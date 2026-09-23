"""
RADAR-4060 Report V2: Evidence Image Extractor & Review Panel Generator.

Extracts representative axial CT slices from NIfTI volumes, applies clinical
window leveling presets (Soft tissue, Bone, Lung, Calcification), embeds
orientation markers (R/L), slice index, phase metadata, and clinical review
labels without burning any patient PHI.

Follows docs/REPORT_V2_MULTIPHASE_EVIDENCE_SPEC.md Section 3:
- Never label evidence images as lesion localization or AI proof.
- Labeled as 'Ảnh gợi ý rà lại' or 'Lát cắt tham khảo'.
- Includes R/L markers, phase, slice index, window preset.
- 100% offline self-contained base64 JPEG encoding.
"""

import base64
import io
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import SimpleITK as sitk
except ImportError:
    sitk = None

from RADAR_inference.multiphase_case import EvidenceImage, FindingStudyLevel, PhaseInfo

# Clinical window leveling presets (Specification Section 3)
WINDOW_PRESETS = {
    "SOFT_TISSUE": {
        "name": "Mô mềm",
        "wl": 40,
        "ww": 400,
        "wl_ww_str": "WL 40 / WW 400",
    },
    "BONE": {
        "name": "Xương",
        "wl": 400,
        "ww": 1800,
        "wl_ww_str": "WL 400 / WW 1800",
    },
    "LUNG": {
        "name": "Phổi",
        "wl": -600,
        "ww": 1500,
        "wl_ww_str": "WL -600 / WW 1500",
    },
    "CALCIFICATION": {
        "name": "Vôi hóa / Sỏi",
        "wl": 100,
        "ww": 600,
        "wl_ww_str": "WL 100 / WW 600",
    },
}

# Anatomical Z-depth relative ranges for abdominal CT (inferior=0.0, superior=1.0)
ORGAN_ANATOMICAL_Z_RATIO = {
    "Lung": 0.88,
    "Heart": 0.90,
    "Rib": 0.75,
    "Liver": 0.72,
    "Spleen": 0.74,
    "Stomach": 0.70,
    "Aorta": 0.65,
    "Adrenal gland": 0.68,
    "Gallbladder": 0.62,
    "Pancreas": 0.60,
    "Portal vein": 0.62,
    "Duodenum": 0.55,
    "Kidney": 0.52,
    "Small bowel": 0.45,
    "Large bowel": 0.40,
    "Bladder": 0.18,
    "Sacrum": 0.20,
    "Esophagus": 0.85,
}


def select_window_preset(organ_en: str, finding_en: str) -> str:
    """Selects the clinically appropriate CT window preset for an organ/finding."""
    f_lower = finding_en.lower()
    o_lower = organ_en.lower()

    if o_lower == "lung" or "pleural" in f_lower or "pneumothorax" in f_lower or "atelectasis" in f_lower:
        return "LUNG"
    elif o_lower in ("rib", "sacrum") or "fracture" in f_lower or "bone" in f_lower:
        return "BONE"
    elif "stone" in f_lower or "calcification" in f_lower or "calculus" in f_lower or "lithiasis" in f_lower:
        return "CALCIFICATION"
    else:
        return "SOFT_TISSUE"


def apply_window_level(slice_hu: np.ndarray, wl: float, ww: float) -> np.ndarray:
    """Applies window/level linear transform to 2D HU slice and returns uint8 [0, 255]."""
    lower = wl - (ww / 2.0)
    upper = wl + (ww / 2.0)
    clamped = np.clip(slice_hu, lower, upper)
    norm = ((clamped - lower) / ww) * 255.0
    return norm.astype(np.uint8)


def render_annotated_slice_jpeg(
    slice_hu: np.ndarray,
    phase_name_vi: str,
    slice_idx: int,
    total_slices: int,
    preset_key: str,
    series_alias: str,
    label_text: str = "Ảnh gợi ý rà lại",
    quality: int = 80,
    target_width: int = 512,
) -> str:
    """
    Renders an axial slice with clinical orientation markers (R/L), slice info,
    phase badge, and review aid label. Returns base64 data URI string.
    Ensures ZERO patient PHI is burned into the image.
    """
    preset = WINDOW_PRESETS.get(preset_key, WINDOW_PRESETS["SOFT_TISSUE"])
    uint8_img = apply_window_level(slice_hu, preset["wl"], preset["ww"])

    # Create PIL image
    img = Image.fromarray(uint8_img).convert("RGB")
    
    # Resize if needed for lightweight HTML embedding
    w, h = img.size
    if w != target_width:
        new_h = int(h * (target_width / w))
        img = img.resize((target_width, new_h), Image.Resampling.BILINEAR)
        w, h = img.size

    draw = ImageDraw.Draw(img)

    # Use default bitmap font
    font = ImageFont.load_default()

    # Orientation markers:
    # On axial CT: Patient Right is on image LEFT ('P' / 'R'); Patient Left is on image RIGHT ('T' / 'L')
    marker_p_box = [(8, h // 2 - 12), (32, h // 2 + 12)]
    draw.rectangle(marker_p_box, fill=(0, 0, 0, 180))
    draw.text((16, h // 2 - 6), "P", fill=(255, 230, 0), font=font)

    marker_t_box = [(w - 32, h // 2 - 12), (w - 8, h // 2 + 12)]
    draw.rectangle(marker_t_box, fill=(0, 0, 0, 180))
    draw.text((w - 24, h // 2 - 6), "T", fill=(255, 230, 0), font=font)

    # Top banner: Phase & Window Preset
    top_badge = f"{phase_name_vi} | {preset['name']} ({preset['wl_ww_str']})"
    draw.rectangle([(6, 6), (len(top_badge) * 7 + 16, 26)], fill=(15, 23, 42))
    draw.text((12, 10), top_badge, fill=(255, 255, 255), font=font)

    # Bottom banner: Slice & Label
    bottom_badge = f"Lát {slice_idx}/{total_slices} | {label_text}"
    draw.rectangle([(6, h - 26), (len(bottom_badge) * 7 + 16, h - 6)], fill=(15, 23, 42))
    draw.text((12, h - 22), bottom_badge, fill=(203, 213, 225), font=font)

    # Series alias in bottom right
    alias_str = series_alias
    draw.rectangle([(w - len(alias_str) * 7 - 16, h - 26), (w - 6, h - 6)], fill=(15, 23, 42))
    draw.text((w - len(alias_str) * 7 - 10, h - 22), alias_str, fill=(148, 163, 184), font=font)

    # Convert to base64 JPEG
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


class EvidenceExtractor:
    """Manages volume loading, slice selection, and evidence generation for a StudyCase."""

    def __init__(self, volumes: Optional[Dict[str, np.ndarray]] = None):
        # Cache loaded volumes by phase_key: phase_key -> 3D ndarray (Z, Y, X)
        self.cached_volumes: Dict[str, np.ndarray] = volumes or {}

    def load_volume_if_needed(self, phase_info: PhaseInfo) -> Optional[np.ndarray]:
        """Loads NIfTI volume as float32 numpy array (Z, Y, X)."""
        pkey = phase_info.phase_key
        if pkey in self.cached_volumes:
            return self.cached_volumes[pkey]

        nii_path = phase_info.nii_path
        if not nii_path or not os.path.exists(nii_path):
            return None

        if sitk is None:
            return None

        try:
            itk_img = sitk.ReadImage(nii_path)
            arr = sitk.GetArrayFromImage(itk_img).astype(np.float32)  # (Z, Y, X)
            self.cached_volumes[pkey] = arr
            return arr
        except Exception as e:
            print(f"[EvidenceExtractor] Error loading volume for {pkey} from {nii_path}: {e}")
            return None

    def determine_representative_slice(
        self,
        organ_en: str,
        total_slices: int,
    ) -> int:
        """
        Determines the representative 1-based axial slice index for an organ
        based on anatomical CT positioning.
        """
        ratio = ORGAN_ANATOMICAL_Z_RATIO.get(organ_en, 0.50)
        # 1-based slice index
        slice_idx = int(round(ratio * (total_slices - 1))) + 1
        return max(1, min(total_slices, slice_idx))

    def generate_evidence_for_finding(
        self,
        finding: FindingStudyLevel,
        phase_info: PhaseInfo,
        num_slices: int = 1,
    ) -> List[EvidenceImage]:
        """
        Generates 1 to 3 annotated evidence review images for a study finding.
        Uses the selected phase volume. If volume is unavailable, returns empty.
        """
        vol = self.load_volume_if_needed(phase_info)
        if vol is None:
            return []

        total_slices = vol.shape[0]
        center_slice_1based = self.determine_representative_slice(
            finding.organ_en, total_slices
        )

        preset_key = select_window_preset(finding.organ_en, finding.finding_en)
        preset = WINDOW_PRESETS[preset_key]

        evidence_list = []
        # Center slice index
        offsets = [0] if num_slices == 1 else [-2, 0, 2]
        for off in offsets:
            cur_idx_1based = center_slice_1based + off
            if not (1 <= cur_idx_1based <= total_slices):
                continue

            z_0based = cur_idx_1based - 1
            slice_hu = vol[z_0based, :, :]

            # Compute approximate Z position in mm
            z_mm = (cur_idx_1based - (total_slices / 2.0)) * phase_info.slice_thickness_mm

            b64_uri = render_annotated_slice_jpeg(
                slice_hu=slice_hu,
                phase_name_vi=phase_info.name_vi,
                slice_idx=cur_idx_1based,
                total_slices=total_slices,
                preset_key=preset_key,
                series_alias=phase_info.alias,
                label_text="Ảnh gợi ý rà lại",
            )

            ev = EvidenceImage(
                finding_id=finding.finding_id,
                phase_key=phase_info.phase_key,
                phase_name_vi=phase_info.name_vi,
                slice_index=cur_idx_1based,
                total_slices=total_slices,
                z_position_mm=round(z_mm, 1),
                window_preset=preset["name"],
                window_wl_ww=preset["wl_ww_str"],
                base64_jpeg=b64_uri,
                is_organ_fallback=False,
                label_text="Ảnh gợi ý rà lại",
            )
            evidence_list.append(ev)

        return evidence_list
