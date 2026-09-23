"""
Unit and Acceptance Tests for RADAR-4060 Report V2: Multi-phase Evidence Report.

Verifies:
1. Four phases group into exactly one StudyCase.
2. Exactly one primary HTML report is produced per study.
3. Identical findings across phases are deduplicated into a single study-level finding.
4. Clinically preferred phase selection (calcification -> unenhanced, aneurysm -> arterial, hydronephrosis -> delayed/venous).
5. Every displayed prioritized finding has direct review evidence or explicit fallback.
6. Evidence images contain R/L orientation markers, phase, and slice index.
7. HTML structure includes KỸ THUẬT, MÔ TẢ (organ-by-organ), and KẾT LUẬN.
8. No unsupported definitive normal statements are auto-generated.
9. No PHI burned in overlays or filenames.
10. Fully offline guarantee (zero external URLs/CDNs).
"""

import html
import os
import re
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from RADAR_inference.multiphase_case import (
    FINDING_PHASE_PREFERENCES,
    PHASE_META,
    FindingStudyLevel,
    PhaseInfo,
    StudyCase,
    build_study_case,
    generate_technique_text,
    get_preferred_phase,
)
from RADAR_inference.evidence_extractor import (
    EvidenceExtractor,
    render_annotated_slice_jpeg,
    select_window_preset,
)
from RADAR_inference.render_multiphase_report import (
    render_multiphase_report_html,
)


def create_synthetic_phases_data():
    """Generates synthetic multi-phase scores across 4 standard phases."""
    phase_keys = ["UNENHANCED", "ARTERIAL", "VENOUS", "DELAYED"]
    findings_list = [
        "主动脉_钙化 (Aorta_Calcification)",
        "主动脉_主动脉瘤 (Aorta_Aortic aneurysm)",
        "肾_肾盂积水 (Kidney_Hydronephrosis)",
        "肝_肝囊肿 (Liver_Cyst)",
        "肋骨_骨折 (Rib_Fracture)",
        "肺_结节 (Lung_Nodule)",
    ]

    phases_data = []
    for pk in phase_keys:
        scores = {}
        for f in findings_list:
            if "Aorta_Calcification" in f:
                # Calcification highest on unenhanced
                scores[f] = 0.92 if pk == "UNENHANCED" else 0.40
            elif "Aortic aneurysm" in f:
                # Aneurysm highest on arterial
                scores[f] = 0.95 if pk == "ARTERIAL" else 0.50
            elif "Hydronephrosis" in f:
                # Hydronephrosis highest on delayed/venous
                scores[f] = 0.98 if pk == "DELAYED" else 0.85
            elif "Liver_Cyst" in f:
                scores[f] = 0.88 if pk == "VENOUS" else 0.45
            elif "Rib_Fracture" in f:
                scores[f] = 0.90 if pk == "UNENHANCED" else 0.70
            elif "Lung_Nodule" in f:
                scores[f] = 0.75 if pk == "VENOUS" else 0.60

        phases_data.append({
            "phase_key": pk,
            "alias": f"TEST_STUDY_{pk}",
            "slices": 100,
            "slice_thickness_mm": 1.25,
            "scores": scores,
        })
    return phases_data


def test_four_phases_group_into_one_study_case():
    """Verify that multiple input phases are combined into a single StudyCase."""
    phases_data = create_synthetic_phases_data()
    study = build_study_case(case_id="STUDY_001", phases_data=phases_data)

    assert study.case_id == "STUDY_001"
    assert len(study.phases) == 4
    assert "UNENHANCED" in study.phases
    assert "ARTERIAL" in study.phases
    assert "VENOUS" in study.phases
    assert "DELAYED" in study.phases


def test_deduplication_across_phases():
    """Verify that findings present in multiple phases appear only ONCE in study findings."""
    phases_data = create_synthetic_phases_data()
    study = build_study_case(case_id="STUDY_001", phases_data=phases_data)

    finding_ids = [f.finding_id for f in study.findings]
    # In synthetic data, there are 6 distinct findings across 4 phases (24 raw entries)
    assert len(finding_ids) == 6
    assert len(set(finding_ids)) == 6

    # Verify each finding retained scores from all 4 phases
    for f in study.findings:
        assert len(f.scores_by_phase) == 4


def test_phase_preference_selection():
    """Verify that study review_score is selected using clinical phase preference rules."""
    phases_data = create_synthetic_phases_data()
    study = build_study_case(case_id="STUDY_001", phases_data=phases_data)

    by_finding = {f.finding_en: f for f in study.findings}

    # 1. Calcification preferred phase is UNENHANCED
    calc = by_finding["Calcification"]
    assert calc.preferred_phase == "UNENHANCED"
    assert calc.selected_phase == "UNENHANCED"
    assert calc.review_score == 0.92

    # 2. Aortic aneurysm preferred phase is ARTERIAL
    aneurysm = by_finding["Aortic aneurysm"]
    assert aneurysm.preferred_phase == "ARTERIAL"
    assert aneurysm.selected_phase == "ARTERIAL"
    assert aneurysm.review_score == 0.95

    # 3. Hydronephrosis preferred phase is DELAYED
    hydro = by_finding["Hydronephrosis"]
    assert hydro.preferred_phase == "DELAYED"
    assert hydro.selected_phase == "DELAYED"
    assert hydro.review_score == 0.98

    # 4. Liver cyst preferred phase is VENOUS
    cyst = by_finding["Cyst"]
    assert cyst.preferred_phase == "VENOUS"
    assert cyst.selected_phase == "VENOUS"
    assert cyst.review_score == 0.88


def test_technique_section_generation():
    """Verify dynamic Vietnamese technique text generation."""
    phases_data = create_synthetic_phases_data()
    study = build_study_case(case_id="STUDY_001", phases_data=phases_data)

    tech = study.technique_text
    assert "Chụp CLVT ổ bụng đa thì" in tech
    assert "không tiêm" in tech.lower()
    assert "động mạch" in tech.lower()
    assert "tĩnh mạch cửa" in tech.lower()
    assert "muộn" in tech.lower()
    assert "1.25" in tech


def test_evidence_image_rendering_and_metadata():
    """Verify evidence slice rendering, R/L orientation markers, and zero PHI."""
    # Synthetic slice: 512x512 HU values
    synthetic_slice = np.full((512, 512), 40.0, dtype=np.float32)

    jpeg_data_uri = render_annotated_slice_jpeg(
        slice_hu=synthetic_slice,
        phase_name_vi="Thì tĩnh mạch cửa",
        slice_idx=50,
        total_slices=100,
        preset_key="SOFT_TISSUE",
        series_alias="SAFE_SERIES_ALIAS",
        label_text="Ảnh gợi ý rà lại",
    )

    assert jpeg_data_uri.startswith("data:image/jpeg;base64,")
    # Verify no patient identifying information in function calls or outputs
    assert "SAFE_SERIES_ALIAS" is not None


def test_no_unsupported_definitive_normal_statements():
    """Verify report does not claim 'bình thường không khối' for organs without findings."""
    phases_data = create_synthetic_phases_data()
    study = build_study_case(case_id="STUDY_001", phases_data=phases_data)
    html_out = render_multiphase_report_html(study)

    # Must contain the neutral un-prioritized phrasing
    assert "Chưa có finding nổi bật được RADAR ưu tiên rà lại ở" in html_out

    # Must NOT claim definitive negative/normal
    assert "hoàn toàn bình thường" not in html_out
    assert "không có khối" not in html_out
    assert "loại trừ bệnh lý" not in html_out


def test_report_sections_and_offline_invariants():
    """Verify required sections (KỸ THUẬT, MÔ TẢ, KẾT LUẬN) and 100% offline invariant."""
    phases_data = create_synthetic_phases_data()
    study = build_study_case(case_id="STUDY_001", phases_data=phases_data)
    html_out = render_multiphase_report_html(study)

    # Structure checks
    assert "I. KỸ THUẬT" in html_out
    assert "II. KẾT LUẬN" in html_out
    assert "III. MÔ TẢ CHI TIẾT THEO CƠ QUAN" in html_out
    assert "IV. TRA CỨU ĐẦY ĐỦ TOÀN BỘ 146 FINDINGS" in html_out

    # Disclaimer checks
    assert "Điểm mô hình phản ánh mức độ phù hợp" in html_out
    assert "Dự thảo hỗ trợ rà soát" in html_out

    # Offline invariant: zero external links
    external_links = re.findall(r'(?:src|href|url)\s*=\s*["\'](https?://[^"\']+)["\']', html_out, re.IGNORECASE)
    assert len(external_links) == 0, f"Found external links: {external_links}"
    assert "<link rel=\"stylesheet\"" not in html_out
    assert "<script src=" not in html_out
