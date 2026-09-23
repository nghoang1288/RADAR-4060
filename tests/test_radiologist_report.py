"""
Regression and Acceptance Tests for RADAR-4060 Radiologist Report Generator.

Verifies:
- Strict score sorting descending and consecutive ranks.
- 100% Vietnamese medical terminology mapping coverage for all 146 findings and 18 organs.
- Full HTML escaping of untrusted input strings (prevent XSS).
- Complete offline guarantee (zero external CDNs, fonts, or http/https links).
- Mandatory clinical disclaimer wording and absence of uncalibrated probability/binary claims.
- Public demo case reference ranking (Cardiomegaly ~0.833, Aortic calcification ~0.697, Atherosclerosis ~0.578).
"""

import html
import os
import re
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from RADAR_inference.vietnamese_terminology import (
    FINDING_MAPPING_VI,
    ORGAN_MAPPING_VI,
    parse_finding_label,
)
from RADAR_inference.render_radiologist_report import (
    DISCLAIMER_TEXT,
    extract_ranked_findings,
    group_findings_by_organ,
    render_html_report,
    render_report_from_csv,
)

DEMO_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "results",
    "RADAR_infer_results_demo_4060.csv",
)


def test_score_sorting_order():
    """Verify that extract_ranked_findings sorts strictly descending by model score."""
    sample_scores = {
        "Aorta_Calcification": 0.450,
        "Heart_Cardiomegaly": 0.890,
        "Liver_Cyst": 0.120,
        "Kidney_Stone": 0.670,
        "Spleen_Splenomegaly": 0.330,
    }
    ranked = extract_ranked_findings(sample_scores)
    assert len(ranked) == 5

    # Check strictly descending
    for i in range(len(ranked) - 1):
        assert ranked[i]["score"] >= ranked[i + 1]["score"]
        assert ranked[i]["rank"] == i + 1

    assert ranked[0]["finding_en"] == "Cardiomegaly"
    assert ranked[0]["score"] == 0.890
    assert ranked[-1]["finding_en"] == "Cyst"
    assert ranked[-1]["score"] == 0.120


def test_vietnamese_mapping_coverage_all_146():
    """Verify that all 146 findings from demo CSV have valid Vietnamese mappings."""
    if not os.path.exists(DEMO_CSV_PATH):
        pytest.skip(f"Demo CSV not found at {DEMO_CSV_PATH}")

    import pandas as pd
    df = pd.read_csv(DEMO_CSV_PATH)
    finding_cols = [c for c in df.columns if c != "file_name"]

    assert len(finding_cols) == 146, f"Expected 146 findings, got {len(finding_cols)}"

    missing_translations = []
    organs_found = set()

    for col in finding_cols:
        info = parse_finding_label(col)
        # Verify finding has a Vietnamese translation not equal to the raw column header
        if info["finding_vi"] == col or not info["finding_vi"]:
            missing_translations.append(col)
        # Verify organ has a valid Vietnamese translation
        organs_found.add(info["organ_vi"])
        assert info["organ_vi"] != "", f"Missing organ for column: {col}"

    assert len(missing_translations) == 0, f"Found {len(missing_translations)} unmapped findings: {missing_translations}"
    assert len(organs_found) == 18, f"Expected 18 unique organs, got {len(organs_found)}"


def test_html_escaping_untrusted_input():
    """Verify that untrusted input (case_id, series_alias, finding text) is escaped."""
    malicious_case_id = '<script>alert("xss")</script>'
    malicious_series = '"><img src=x onerror=alert(1)>'
    malicious_scores = {
        'Aorta_<b>BoldFinding</b>': 0.75,
    }

    ranked = extract_ranked_findings(malicious_scores)
    html_output = render_html_report(
        ranked_findings=ranked,
        case_id=malicious_case_id,
        series_alias=malicious_series,
    )

    # Raw script/img tags must NOT be present
    assert "<script>alert" not in html_output
    assert "<img src=x onerror" not in html_output
    assert "<b>BoldFinding</b>" not in html_output

    # Escaped versions MUST be present
    assert html.escape(malicious_case_id) in html_output
    assert html.escape(malicious_series) in html_output


def test_offline_invariant_no_external_resources():
    """Verify that generated HTML has zero external network calls, CDNs, or scripts."""
    sample_scores = {"Aorta_Calcification": 0.5}
    ranked = extract_ranked_findings(sample_scores)
    html_output = render_html_report(ranked, case_id="TEST_OFFLINE")

    # Disallow http:// and https:// external assets
    # (Note: doctype and xml namespaces might appear, but no href/src http)
    external_links = re.findall(r'(?:src|href|url)\s*=\s*["\'](https?://[^"\']+)["\']', html_output, re.IGNORECASE)
    assert len(external_links) == 0, f"Found external URL references: {external_links}"

    # Disallow external stylesheet links
    assert "<link rel=\"stylesheet\"" not in html_output
    assert "<link rel='stylesheet'" not in html_output

    # Disallow external script tags
    external_scripts = re.findall(r'<script[^>]+src=', html_output, re.IGNORECASE)
    assert len(external_scripts) == 0, f"Found external script tags: {external_scripts}"


def test_clinical_disclaimer_and_terminology():
    """Verify mandatory phrasing and absence of uncalibrated probability or binary labels."""
    sample_scores = {"Heart_Cardiomegaly": 0.85}
    ranked = extract_ranked_findings(sample_scores)
    html_output = render_html_report(ranked, case_id="TEST_CLINICAL")

    # Mandatory exact disclaimer text
    assert DISCLAIMER_TEXT in html_output

    # Must prominently state 'Điểm mô hình'
    assert "Điểm mô hình" in html_output
    assert "Ưu tiên rà lại" in html_output

    # Must NOT label as probability of disease
    assert "xác suất mắc bệnh" not in html_output.lower()
    assert "xác suất bệnh" not in html_output.replace(DISCLAIMER_TEXT, "").lower()


def test_demo_case_expected_ranking_and_scores(tmp_path):
    """
    Verify public demo case scores match reference values:
    - Cardiomegaly ~0.833
    - Aortic calcification ~0.697
    - Atherosclerosis ~0.578
    """
    if not os.path.exists(DEMO_CSV_PATH):
        pytest.skip(f"Demo CSV not found at {DEMO_CSV_PATH}")

    out_html = str(tmp_path / "test_demo_report.html")
    render_report_from_csv(
        csv_path=DEMO_CSV_PATH,
        output_html_path=out_html,
        row_index=0,
    )

    assert os.path.exists(out_html)
    with open(out_html, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Load CSV to check exact rankings
    import pandas as pd
    df = pd.read_csv(DEMO_CSV_PATH)
    raw_scores = {c: float(df.iloc[0][c]) for c in df.columns if c != "file_name"}
    ranked = extract_ranked_findings(raw_scores)

    # Top 1: Cardiomegaly
    top1 = ranked[0]
    assert "Cardiomegaly" in top1["finding_en"]
    assert abs(top1["score"] - 0.833) < 0.01
    assert "Bóng tim to" in top1["finding_vi"] or "Tim to" in top1["finding_vi"]

    # Top 2: Aortic calcification
    top2 = ranked[1]
    assert "Calcification" in top2["finding_en"]
    assert top2["organ_en"] == "Aorta"
    assert abs(top2["score"] - 0.698) < 0.01

    # Top 3: Atherosclerosis
    top3 = ranked[2]
    assert "Atherosclerosis" in top3["finding_en"]
    assert top3["organ_en"] == "Aorta"
    assert abs(top3["score"] - 0.578) < 0.01

    # Verify these scores appear in the rendered HTML
    assert f"{top1['score']:.3f}" in html_content
    assert f"{top2['score']:.3f}" in html_content
    assert f"{top3['score']:.3f}" in html_content
