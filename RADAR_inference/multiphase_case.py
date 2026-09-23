"""
RADAR-4060 Report V2: Multi-phase StudyCase Data Model & Clinical Fusion.

Fuses multiple CT phase inference outputs for a single patient into ONE
unified StudyCase with deduplicated findings, clinical phase preference
selection, conventional Vietnamese abdominal CT report structure
(KỸ THUẬT, MÔ TẢ, KẾT LUẬN), and evidence image bindings.

Follows docs/REPORT_V2_MULTIPHASE_EVIDENCE_SPEC.md:
- One patient / study = One primary HTML report.
- Findings deduplicated across phases.
- Study-level score selection based on finding/organ phase preference mapping.
- No blind averaging across phases.
- No auto-generated unsupported definitive normal statements from low scores.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from RADAR_inference.vietnamese_terminology import (
    FINDING_MAPPING_VI,
    ORGAN_MAPPING_VI,
    parse_finding_label,
)

# Standard phase keys and Vietnamese names
PHASE_META = {
    "UNENHANCED": {
        "name_vi": "Thì không tiêm (Trước tiêm)",
        "short_vi": "Không tiêm",
        "name_en": "Non-contrast Phase",
        "order": 1,
    },
    "ARTERIAL": {
        "name_vi": "Thì động mạch",
        "short_vi": "Động mạch",
        "name_en": "Arterial Phase",
        "order": 2,
    },
    "VENOUS": {
        "name_vi": "Thì tĩnh mạch cửa",
        "short_vi": "Tĩnh mạch cửa",
        "name_en": "Portal Venous Phase",
        "order": 3,
    },
    "DELAYED": {
        "name_vi": "Thì muộn (Bài xuất)",
        "short_vi": "Thì muộn",
        "name_en": "Delayed Phase",
        "order": 4,
    },
}

# Conventional Vietnamese abdominal CT organ reporting order
CONVENTIONAL_ORGAN_ORDER = [
    ("Liver", "Gan & Đường mật trong gan"),
    ("Portal vein", "Tĩnh mạch cửa"),
    ("Gallbladder", "Túi mật & Đường mật ngoài gan"),
    ("Pancreas", "Tụy & Quanh tụy"),
    ("Spleen", "Lách"),
    ("Adrenal gland", "Tuyến thượng thận"),
    ("Kidney", "Thận & Hệ tiết niệu"),
    ("Stomach", "Dạ dày"),
    ("Duodenum", "Tá tràng"),
    ("Small bowel", "Ruột non"),
    ("Large bowel", "Đại tràng"),
    ("Aorta", "Động mạch chủ & Mạch máu lớn"),
    ("Bladder", "Bàng quang & Tiểu khung"),
    ("Lung", "Phổi đáy & Màng phổi"),
    ("Rib", "Xương sườn"),
    ("Sacrum", "Xương cùng"),
]

# Finding/Organ phase preferences (Specification Section 1)
# Format: finding_en substring or exact -> preferred phase
FINDING_PHASE_PREFERENCES = {
    # Calcification / stone / hyperattenuating -> Non-contrast
    "calcification": "UNENHANCED",
    "calcified": "UNENHANCED",
    "stone": "UNENHANCED",
    "calculus": "UNENHANCED",
    "lithiasis": "UNENHANCED",
    "hyperattenuating": "UNENHANCED",
    "appendicolith": "UNENHANCED",
    
    # Arterial vascular / active lesions -> Arterial
    "aortic dissection": "ARTERIAL",
    "aortic aneurysm": "ARTERIAL",
    "aneurysm": "ARTERIAL",
    "atherosclerosis": "ARTERIAL",
    "artery": "ARTERIAL",
    "arterial": "ARTERIAL",
    "nodular enhancement": "ARTERIAL",
    "hypervascular": "ARTERIAL",
    
    # Urinary collecting system / excretion -> Delayed (fallback Venous)
    "hydronephrosis": "DELAYED",
    "renal pelvic dilatation": "DELAYED",
    "renal pelvic cancer": "DELAYED",
    
    # Portal vein & thrombosis -> Venous
    "portal vein": "VENOUS",
    "thrombosis": "VENOUS",
    "varices": "VENOUS",
    
    # Solid organ tumors / cysts / inflammation / bowel -> Venous
    "cyst": "VENOUS",
    "abscess": "VENOUS",
    "metastasis": "VENOUS",
    "carcinoma": "VENOUS",
    "cancer": "VENOUS",
    "hepatocellular": "VENOUS",
    "hemangioma": "VENOUS",
    "cholangiocarcinoma": "VENOUS",
    "cirrhosis": "VENOUS",
    "pancreatitis": "VENOUS",
    "cholecystitis": "VENOUS",
    "colitis": "VENOUS",
    "diverticulum": "VENOUS",
    "appendicitis": "VENOUS",
    "panniculitis": "VENOUS",
    "splenomegaly": "VENOUS",
    "cardiomegaly": "VENOUS",
    "effusion": "VENOUS",
    
    # Bone & Fracture -> Any diagnostic phase (Bone window)
    "fracture": "UNENHANCED",
    "bone destruction": "UNENHANCED",
    "osteitis": "UNENHANCED",
}

# Organ default phase preferences if finding rule does not match
ORGAN_PHASE_PREFERENCES = {
    "Aorta": "ARTERIAL",
    "Portal vein": "VENOUS",
    "Liver": "VENOUS",
    "Gallbladder": "VENOUS",
    "Pancreas": "VENOUS",
    "Spleen": "VENOUS",
    "Kidney": "VENOUS",
    "Adrenal gland": "VENOUS",
    "Stomach": "VENOUS",
    "Duodenum": "VENOUS",
    "Small bowel": "VENOUS",
    "Large bowel": "VENOUS",
    "Bladder": "DELAYED",
    "Lung": "VENOUS",
    "Heart": "VENOUS",
    "Rib": "UNENHANCED",
    "Sacrum": "UNENHANCED",
}


def get_preferred_phase(organ_en: str, finding_en: str) -> str:
    """
    Determines preferred CT phase for a given finding based on clinical heuristics.
    Finding-specific rules take precedence over organ defaults.
    """
    f_lower = finding_en.lower()
    for kw, phase in FINDING_PHASE_PREFERENCES.items():
        if kw in f_lower:
            return phase

    return ORGAN_PHASE_PREFERENCES.get(organ_en, "VENOUS")


@dataclass
class PhaseInfo:
    phase_key: str  # UNENHANCED, ARTERIAL, VENOUS, DELAYED
    alias: str  # safe series alias, e.g. LOCAL_CASE_001_PHASE_VENOUS
    name_vi: str
    slices: int
    slice_thickness_mm: float
    nii_path: Optional[str] = None
    scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class EvidenceImage:
    finding_id: str
    phase_key: str
    phase_name_vi: str
    slice_index: int  # 1-based
    total_slices: int
    z_position_mm: float
    window_preset: str  # SOFT_TISSUE, BONE, LUNG, CALCIFICATION
    window_wl_ww: str  # e.g. "WL 40 / WW 400"
    base64_jpeg: str
    is_organ_fallback: bool = False
    label_text: str = "Ảnh gợi ý rà lại"


@dataclass
class FindingStudyLevel:
    finding_id: str  # raw column header, e.g. '主动脉_钙化 (Aorta_Calcification)'
    organ_vi: str
    organ_en: str
    finding_vi: str
    finding_en: str
    scores_by_phase: Dict[str, float]
    preferred_phase: str
    selected_phase: str
    review_score: float
    is_fallback_phase: bool
    evidence_images: List[EvidenceImage] = field(default_factory=list)
    case_rank: int = 0
    radiologist_status: str = "PENDING"  # PENDING, ACCEPTED, REJECTED, UNCERTAIN


@dataclass
class StudyCase:
    case_id: str
    phases: Dict[str, PhaseInfo] = field(default_factory=dict)
    findings: List[FindingStudyLevel] = field(default_factory=list)
    top_prioritized_findings: List[FindingStudyLevel] = field(default_factory=list)
    technique_text: str = ""
    model_version: str = "RADAR-4060 FP16"

    def get_phase_names_vi(self) -> List[str]:
        ordered = sorted(
            self.phases.values(),
            key=lambda p: PHASE_META.get(p.phase_key, {}).get("order", 99),
        )
        return [p.name_vi for p in ordered]

    def get_max_thickness(self) -> float:
        if not self.phases:
            return 1.25
        return max(p.slice_thickness_mm for p in self.phases.values())


def generate_technique_text(phases: Dict[str, PhaseInfo]) -> str:
    """
    Generates standardized Vietnamese CT technique paragraph from detected phases.
    Uses actual detected phases and slice thickness without inventing absent ones.
    """
    if not phases:
        return "Chụp CLVT ổ bụng khảo sát đa cơ quan; tái tạo lát cắt 1.25 mm."

    phase_short_names = []
    ordered_keys = sorted(
        phases.keys(), key=lambda k: PHASE_META.get(k, {}).get("order", 99)
    )
    for k in ordered_keys:
        meta = PHASE_META.get(k)
        if meta:
            phase_short_names.append(meta["short_vi"].lower())

    thickness = phases[ordered_keys[0]].slice_thickness_mm if ordered_keys else 1.25
    phase_str = ", ".join(phase_short_names)

    return (
        f"Chụp CLVT ổ bụng đa thì trước và sau tiêm thuốc cản quang, gồm các thì: "
        f"{phase_str}; tái tạo lát cắt mỏng {thickness:.2f} mm theo trục ngang (axial)."
    )


def build_study_case(
    case_id: str,
    phases_data: List[Dict[str, Any]],
    top_n_overall: int = 12,
) -> StudyCase:
    """
    Constructs a unified StudyCase from multiple phase outputs.
    Deduplicates identical findings across phases into single study-level findings
    ranked by clinically preferred phase scores.
    """
    study = StudyCase(case_id=case_id)

    # 1. Register all phases
    for pdata in phases_data:
        pkey = pdata["phase_key"].upper()
        pinfo = PhaseInfo(
            phase_key=pkey,
            alias=pdata.get("alias", f"{case_id}_{pkey}"),
            name_vi=PHASE_META.get(pkey, {}).get("name_vi", pkey),
            slices=pdata.get("slices", 0),
            slice_thickness_mm=pdata.get("slice_thickness_mm", 1.25),
            nii_path=pdata.get("nii_path"),
            scores=pdata.get("scores", {}),
        )
        study.phases[pkey] = pinfo

    study.technique_text = generate_technique_text(study.phases)

    # 2. Gather unique findings across all phases
    all_finding_cols = set()
    for pinfo in study.phases.values():
        for col in pinfo.scores.keys():
            if col != "file_name":
                all_finding_cols.add(col)

    study_findings = []
    for col in all_finding_cols:
        info = parse_finding_label(col)
        organ_en = info["organ_en"]
        finding_en = info["finding_en"]
        organ_vi = info["organ_vi"]
        finding_vi = info["finding_vi"]

        # Collect score in each available phase
        scores_by_phase = {}
        for pkey, pinfo in study.phases.items():
            if col in pinfo.scores:
                scores_by_phase[pkey] = float(pinfo.scores[col])

        # Determine preferred phase
        pref_phase = get_preferred_phase(organ_en, finding_en)

        # Select study score: use preferred phase if available, else max score
        if pref_phase in scores_by_phase:
            selected_phase = pref_phase
            review_score = scores_by_phase[pref_phase]
            is_fallback = False
        elif scores_by_phase:
            # Fallback: pick available phase with highest score
            best_phase, best_score = max(scores_by_phase.items(), key=lambda kv: kv[1])
            selected_phase = best_phase
            review_score = best_score
            is_fallback = True
        else:
            selected_phase = pref_phase
            review_score = 0.0
            is_fallback = True

        sf = FindingStudyLevel(
            finding_id=col,
            organ_vi=organ_vi,
            organ_en=organ_en,
            finding_vi=finding_vi,
            finding_en=finding_en,
            scores_by_phase=scores_by_phase,
            preferred_phase=pref_phase,
            selected_phase=selected_phase,
            review_score=review_score,
            is_fallback_phase=is_fallback,
        )
        study_findings.append(sf)

    # 3. Sort study-level findings strictly descending by review_score
    study_findings.sort(key=lambda f: f.review_score, reverse=True)
    for rank, f in enumerate(study_findings, 1):
        f.case_rank = rank

    study.findings = study_findings
    study.top_prioritized_findings = study_findings[:top_n_overall]

    return study
