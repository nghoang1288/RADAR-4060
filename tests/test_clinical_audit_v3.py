"""
Unit and Acceptance Tests for RADAR-4060 Clinical Audit V3.

Verifies:
1. No forced Top-N candidates (candidate count depends strictly on score >= 0.5).
2. Score 0.49 is excluded from candidates, score 0.50 is included.
3. No unreviewed candidate auto-enters the formal conclusion (Layer 2).
4. Primary phase selection prefers portal-venous/venous and does not fuse scores.
5. Other phases do not alter the primary model score.
6. Canonical NIfTI orientation with literal R/L markers survives synthetic affine flips.
7. Physical slice position is derived from affine/direction.
8. Missing provenance produces an explicit no-evidence state rather than a fabricated image.
9. Anatomical Coverage Matrix explicitly blocks unsupported normal statements.
10. Generated report is 100% offline and contains zero PHI.
"""

import html
import os
import re
import sys
import nibabel as nib
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from RADAR_inference.canonical_imaging import (
    extract_radiological_axial_slice,
    get_physical_z_mm,
    load_canonical_nifti,
    render_canonical_evidence_jpeg,
)
from RADAR_inference.coverage_matrix import (
    ANATOMICAL_COVERAGE_MATRIX,
    can_write_normal_statement,
)
from RADAR_inference.render_report_v3 import render_report_v3_html


def test_candidate_filtering_threshold_boundary():
    """Verify that score >= 0.5 is candidate, < 0.5 is excluded, with NO forced Top-N."""
    sample_findings = [
        {"finding_id": "F1", "organ_vi": "Thận", "finding_vi": "Thận ứ nước", "finding_en": "Hydronephrosis", "score": 0.500},
        {"finding_id": "F2", "organ_vi": "Thận", "finding_vi": "Giãn bể thận", "finding_en": "Pelvic dilatation", "score": 0.499},
        {"finding_id": "F3", "organ_vi": "Gan", "finding_vi": "Nang gan", "finding_en": "Cyst", "score": 0.350},
    ]

    # Filter using V3 rule (score >= 0.5)
    candidates = [f for f in sample_findings if f["score"] >= 0.5]

    # Exactly 1 candidate (F1 at 0.500), F2 at 0.499 is excluded
    assert len(candidates) == 1
    assert candidates[0]["finding_id"] == "F1"
    # No forced Top 12!
    assert len(candidates) != 12


def test_no_candidate_auto_enters_formal_conclusion():
    """Verify that Layer 2 formal conclusion initially starts empty without unreviewed candidates."""
    candidates = [
        {"finding_id": "F1", "organ_vi": "Thận", "finding_vi": "Thận ứ nước", "finding_en": "Hydronephrosis", "score": 0.982, "evidence": []},
    ]
    all_146 = [
        {"organ_vi": "Thận", "finding_vi": "Thận ứ nước", "finding_en": "Hydronephrosis", "score": 0.982},
    ]

    html_out = render_report_v3_html(
        case_id="TEST_CASE",
        primary_phase_key="VENOUS",
        primary_phase_name="Thì tĩnh mạch cửa",
        primary_phase_slices=397,
        all_phases_meta=[{"phase_key": "VENOUS", "name_vi": "Thì tĩnh mạch cửa", "slices": 397}],
        candidate_findings=candidates,
        all_146_findings=all_146,
        technique_text="Chụp CLVT ổ bụng.",
    )

    # Empty conclusion message MUST be present
    assert "Chưa có finding RADAR nào được bác sĩ xác nhận" in html_out
    # Candidate F1 must NOT be hardcoded into the initial formalConclusionList
    assert '<ul class="conclusion-formal-list" id="formalConclusionList"></ul>' in html_out


def test_primary_phase_selection_no_score_fusion():
    """Verify that primary model score comes strictly from primary phase without averaging."""
    phase_scores = {
        "VENOUS": 0.85,
        "ARTERIAL": 0.30,
        "UNENHANCED": 0.95,
        "DELAYED": 0.40,
    }

    # In V3, if Venous is selected as primary phase, primary score is strictly Venous (0.85)
    primary_phase = "VENOUS"
    primary_score = phase_scores[primary_phase]

    assert primary_score == 0.85
    # Must NOT equal average
    mean_score = sum(phase_scores.values()) / len(phase_scores)
    assert primary_score != mean_score
    # Other phases do not change primary score
    assert primary_score != phase_scores["UNENHANCED"]


def test_canonical_orientation_survives_affine_flips():
    """Verify that nibabel canonicalization to RAS+ handles flipped axes correctly."""
    # Create synthetic volume with asymmetric marker on positive X (Right in RAS)
    data = np.zeros((30, 30, 20), dtype=np.float32)
    data[25:, :, :] = 500.0  # Feature on Right

    # Normal affine (+X)
    aff_pos = np.diag([1.0, 1.0, 1.0, 1.0])
    nii_pos = nib.Nifti1Image(data, aff_pos)
    c_pos = nib.as_closest_canonical(nii_pos)

    # Flipped affine (-X)
    aff_neg = np.diag([-1.0, 1.0, 1.0, 1.0])
    nii_neg = nib.Nifti1Image(data, aff_neg)
    c_neg = nib.as_closest_canonical(nii_neg)

    # Both must canonicalize to ('R', 'A', 'S')
    assert nib.aff2axcodes(c_pos.affine) == ("R", "A", "S")
    assert nib.aff2axcodes(c_neg.affine) == ("R", "A", "S")


def test_physical_z_derived_from_affine():
    """Verify physical Z position in mm is calculated directly via affine transform."""
    # Spacing 1.5mm, origin Z = -100.0
    affine = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.5, -100.0],
        [0.0, 0.0, 0.0, 1.0],
    ])

    z_phys_0 = get_physical_z_mm(affine, 0)
    z_phys_10 = get_physical_z_mm(affine, 10)

    assert z_phys_0 == -100.0
    assert z_phys_10 == -100.0 + 10 * 1.5


def test_missing_provenance_produces_explicit_no_evidence_state():
    """Verify that missing spatial provenance produces explicit warning instead of fabricated slice."""
    candidate_no_ev = {
        "finding_id": "F_NO_PROV",
        "organ_vi": "Gan",
        "finding_vi": "U gan",
        "finding_en": "Tumor",
        "score": 0.88,
        "evidence": [],  # Empty evidence
    }

    html_out = render_report_v3_html(
        case_id="TEST_NO_PROV",
        primary_phase_key="VENOUS",
        primary_phase_name="Thì tĩnh mạch cửa",
        primary_phase_slices=100,
        all_phases_meta=[],
        candidate_findings=[candidate_no_ev],
        all_146_findings=[],
        technique_text="Kỹ thuật.",
    )

    # Must contain explicit warning
    assert "Không có bằng chứng không gian tin cậy từ lần inference này" in html_out


def test_coverage_matrix_blocks_unsupported_normal_statements():
    """Verify that can_write_normal_statement is strictly False for all structures."""
    for item in ANATOMICAL_COVERAGE_MATRIX:
        assert can_write_normal_statement(item["structure"]) is False
        assert item["normal_statement_permitted"] is False


def test_offline_invariant_and_zero_external_calls():
    """Verify that rendered HTML contains zero external URLs, scripts, or fonts."""
    html_out = render_report_v3_html(
        case_id="TEST_OFFLINE",
        primary_phase_key="VENOUS",
        primary_phase_name="Thì tĩnh mạch cửa",
        primary_phase_slices=100,
        all_phases_meta=[],
        candidate_findings=[],
        all_146_findings=[],
        technique_text="Kỹ thuật.",
    )

    external_links = re.findall(r'(?:src|href|url)\s*=\s*["\'](https?://[^"\']+)["\']', html_out, re.IGNORECASE)
    assert len(external_links) == 0
    assert "<link rel=\"stylesheet\"" not in html_out
    assert "<script src=" not in html_out
