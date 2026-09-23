"""
RADAR-4060: Offline Radiologist-Readable HTML Report Generator.

Converts raw 146-column RADAR inference CSV or score dictionaries into a
fully offline, clinically readable HTML report with complete Vietnamese
medical terminology, top findings ranking, organ grouping, and safe local
search/filter controls.

Safety & Clinical Specifications (docs/RADIOLOGIST_REPORT_SPEC.md):
- Numeric output is strictly labeled 'Điểm mô hình' (model score).
- Explicitly states: 'Điểm mô hình phản ánh mức độ phù hợp giữa hình ảnh
  và finding mà RADAR học được; đây không phải xác suất bệnh đã được hiệu chỉnh.'
- No binary positive/negative classification.
- No universal clinical cutoff (e.g., 0.5) is imposed.
- 100% offline: zero external CDNs, fonts, telemetry, or network calls.
- All untrusted text is safely HTML-escaped.
"""

import argparse
import datetime
import html
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from RADAR_inference.vietnamese_terminology import (
        FINDING_MAPPING_VI,
        ORGAN_MAPPING_VI,
        parse_finding_label,
    )
except ImportError:
    from vietnamese_terminology import (
        FINDING_MAPPING_VI,
        ORGAN_MAPPING_VI,
        parse_finding_label,
    )

DISCLAIMER_TEXT = (
    "Điểm mô hình phản ánh mức độ phù hợp giữa hình ảnh và finding mà RADAR "
    "học được; đây không phải xác suất bệnh đã được hiệu chỉnh."
)

REPORT_CSS = """
:root {
  --bg-primary: #f8fafc;
  --bg-card: #ffffff;
  --border-color: #e2e8f0;
  --text-main: #1e293b;
  --text-muted: #64748b;
  --primary-blue: #1e40af;
  --primary-light: #eff6ff;
  --accent-amber: #d97706;
  --accent-amber-bg: #fffbeb;
  --accent-amber-border: #fde68a;
  --score-bar-bg: #e2e8f0;
  --score-bar-fill: #3b82f6;
  --rank-badge-bg: #0f172a;
  --rank-badge-text: #ffffff;
  --table-stripe: #f8fafc;
  --table-hover: #f1f5f9;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-main);
  line-height: 1.5;
  padding: 24px;
}

.report-container {
  max-width: 1200px;
  margin: 0 auto;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* Header */
.report-header {
  padding: 28px 32px 20px;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(to right, #1e3a8a, #2563eb);
  color: #ffffff;
}

.header-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}

.header-title-row h1 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.header-subtitle {
  font-size: 14px;
  color: #bfdbfe;
  margin-top: 4px;
}

.header-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.badge {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

.badge strong {
  margin-right: 4px;
}

/* Alert Disclaimer */
.disclaimer-card {
  margin: 20px 32px;
  padding: 16px 20px;
  border-radius: 8px;
  background-color: var(--accent-amber-bg);
  border-left: 5px solid var(--accent-amber);
  border-top: 1px solid var(--accent-amber-border);
  border-right: 1px solid var(--accent-amber-border);
  border-bottom: 1px solid var(--accent-amber-border);
}

.disclaimer-card h3 {
  font-size: 14px;
  font-weight: 700;
  color: #92400e;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.disclaimer-card p {
  font-size: 13.5px;
  color: #78350f;
  line-height: 1.5;
}

/* Section styling */
.report-section {
  padding: 20px 32px;
  border-bottom: 1px solid var(--border-color);
}

.section-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px;
}

.section-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-subtitle {
  font-size: 13px;
  color: var(--text-muted);
}

/* Top 12 Cards Grid */
.top-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.finding-card {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.finding-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.08);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.rank-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  background: #1e293b;
  color: #ffffff;
}

.organ-tag {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--primary-blue);
  background: var(--primary-light);
  padding: 2px 8px;
  border-radius: 4px;
  max-width: 170px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-finding-name {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 2px;
  line-height: 1.35;
}

.card-finding-en {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 10px;
  font-style: italic;
}

.card-score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px dashed #f1f5f9;
}

.score-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 600;
}

.score-val {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.score-bar-bg {
  height: 6px;
  background: var(--score-bar-bg);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 4px;
}

.score-bar-fill {
  height: 100%;
  background: var(--score-bar-fill);
  border-radius: 3px;
}

/* Organ Grouping Grid */
.organ-groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.organ-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
}

.organ-card-header {
  background: #f8fafc;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.organ-card-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #1e293b;
}

.organ-count-badge {
  font-size: 11px;
  color: var(--text-muted);
  background: #e2e8f0;
  padding: 1px 6px;
  border-radius: 10px;
}

.organ-findings-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.organ-finding-item {
  padding: 8px 14px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.organ-finding-item:last-child {
  border-bottom: none;
}

.item-left {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.item-name-vi {
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-name-en {
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.case-rank-tag {
  font-size: 10.5px;
  color: var(--text-muted);
  background: #f1f5f9;
  padding: 1px 5px;
  border-radius: 3px;
  font-variant-numeric: tabular-nums;
}

/* Full Table & Filter Controls */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.filter-input {
  flex: 1;
  min-width: 220px;
  padding: 8px 12px;
  font-size: 13px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  outline: none;
  background: #ffffff;
}

.filter-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.filter-select {
  padding: 8px 12px;
  font-size: 13px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
}

.filter-btn {
  padding: 8px 14px;
  font-size: 12.5px;
  font-weight: 600;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  color: #334155;
  cursor: pointer;
}

.filter-btn:hover {
  background: #f1f5f9;
}

.filter-counter {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: auto;
  font-weight: 500;
}

details.collapsible-section {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
}

details.collapsible-section summary {
  padding: 14px 20px;
  font-size: 14.5px;
  font-weight: 700;
  background: #f8fafc;
  cursor: pointer;
  user-select: none;
  color: #1e293b;
  outline: none;
}

details.collapsible-section summary:hover {
  background: #f1f5f9;
}

details.collapsible-section[open] summary {
  border-bottom: 1px solid var(--border-color);
}

.details-content {
  padding: 16px 20px;
}

/* Data Table */
.table-responsive {
  overflow-x: auto;
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.findings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  text-align: left;
}

.findings-table th {
  background: #f1f5f9;
  color: #334155;
  font-weight: 700;
  padding: 10px 12px;
  border-bottom: 2px solid var(--border-color);
  white-space: nowrap;
}

.findings-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #e2e8f0;
}

.findings-table tr:nth-child(even) td {
  background: var(--table-stripe);
}

.findings-table tr:hover td {
  background: var(--table-hover);
}

.findings-table tr.top-highlight td {
  font-weight: 600;
}

.score-cell {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  text-align: right;
  min-width: 90px;
}

/* Footer */
.report-footer {
  padding: 16px 32px;
  background: #f8fafc;
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

@media print {
  body {
    padding: 0;
    background: #ffffff;
  }
  .report-container {
    border: none;
    box-shadow: none;
  }
  .filter-bar, details.collapsible-section summary {
    display: none;
  }
  details.collapsible-section {
    border: none;
  }
  details.collapsible-section[open] .details-content {
    padding: 0;
  }
}
"""

REPORT_JS = """
function filterFindings() {
  var input = document.getElementById("findingSearch");
  var filterText = input ? input.value.toLowerCase().trim() : "";
  var organSelect = document.getElementById("organFilter");
  var selectedOrgan = organSelect ? organSelect.value : "";
  
  var table = document.getElementById("findingsTableBody");
  if (!table) return;
  
  var rows = table.getElementsByTagName("tr");
  var visibleCount = 0;
  
  for (var i = 0; i < rows.length; i++) {
    var row = rows[i];
    var organ = row.getAttribute("data-organ") || "";
    var textVi = (row.getAttribute("data-vi") || "").toLowerCase();
    var textEn = (row.getAttribute("data-en") || "").toLowerCase();
    var organVi = (row.getAttribute("data-organ-vi") || "").toLowerCase();
    
    var matchesOrgan = !selectedOrgan || organ === selectedOrgan;
    var matchesText = !filterText || 
                      textVi.indexOf(filterText) !== -1 || 
                      textEn.indexOf(filterText) !== -1 || 
                      organVi.indexOf(filterText) !== -1;
    
    if (matchesOrgan && matchesText) {
      row.style.display = "";
      visibleCount++;
    } else {
      row.style.display = "none";
    }
  }
  
  var counterEl = document.getElementById("visibleCount");
  if (counterEl) {
    counterEl.textContent = "Hiển thị: " + visibleCount + " / " + rows.length + " finding";
  }
}

function resetFilters() {
  var input = document.getElementById("findingSearch");
  if (input) input.value = "";
  var organSelect = document.getElementById("organFilter");
  if (organSelect) organSelect.value = "";
  filterFindings();
}

function toggleReviewCheck(box) {
  var row = box.closest("tr");
  if (row) {
    if (box.checked) {
      row.style.opacity = "0.6";
    } else {
      row.style.opacity = "1";
    }
  }
}
"""


def extract_ranked_findings(
    raw_scores: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Given a dictionary of column_header -> score, parses all findings,
    sorts strictly descending by score, and assigns 1-based ranks.
    """
    parsed_items = []
    for col_header, score in raw_scores.items():
        if col_header == "file_name":
            continue
        try:
            val = float(score)
        except (ValueError, TypeError):
            continue
        info = parse_finding_label(col_header)
        parsed_items.append({
            "organ_vi": info["organ_vi"],
            "finding_vi": info["finding_vi"],
            "organ_en": info["organ_en"],
            "finding_en": info["finding_en"],
            "full_en": info["full_en"],
            "full_cn": info["full_cn"],
            "raw_column": info["raw_column"],
            "score": val,
        })

    # Sort strictly descending by score
    parsed_items.sort(key=lambda x: x["score"], reverse=True)

    # Assign 1-based ranks
    for rank, item in enumerate(parsed_items, 1):
        item["rank"] = rank

    return parsed_items


def group_findings_by_organ(
    ranked_findings: List[Dict[str, Any]],
    top_per_organ: int = 3
) -> Dict[str, Dict[str, Any]]:
    """
    Groups findings by Vietnamese organ name, sorted by each organ's top score.
    Returns dict:
      organ_vi -> {
        "organ_en": str,
        "all_findings": list,
        "top_findings": list (up to top_per_organ),
        "max_score": float
      }
    """
    groups: Dict[str, Dict[str, Any]] = {}
    for item in ranked_findings:
        ovi = item["organ_vi"]
        if ovi not in groups:
            groups[ovi] = {
                "organ_en": item["organ_en"],
                "all_findings": [],
                "top_findings": [],
                "max_score": item["score"],
            }
        groups[ovi]["all_findings"].append(item)

    # For each organ, take top N and determine ordering
    for ovi, g in groups.items():
        g["top_findings"] = g["all_findings"][:top_per_organ]
        g["max_score"] = g["all_findings"][0]["score"] if g["all_findings"] else 0.0

    # Sort organs by highest finding score descending
    sorted_organs = dict(
        sorted(groups.items(), key=lambda kv: kv[1]["max_score"], reverse=True)
    )
    return sorted_organs


def render_html_report(
    ranked_findings: List[Dict[str, Any]],
    case_id: str = "LOCAL_CASE",
    series_alias: Optional[str] = None,
    scan_timestamp: Optional[str] = None,
    model_version: str = "RADAR-4060 FP16",
    top_n_overall: int = 12,
    top_n_per_organ: int = 3,
) -> str:
    """
    Generates a complete, self-contained, fully offline HTML report.
    Guarantees no external CDNs, scripts, or fonts. All text is HTML-escaped.
    """
    safe_case_id = html.escape(str(case_id))
    safe_series = html.escape(str(series_alias or "Series 01"))
    safe_time = html.escape(
        str(scan_timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    safe_model = html.escape(str(model_version))
    disclaimer_esc = html.escape(DISCLAIMER_TEXT)

    top_overall = ranked_findings[:top_n_overall]
    organ_groups = group_findings_by_organ(ranked_findings, top_per_organ=top_n_per_organ)

    # Build Top 12 Cards
    top_cards_html = []
    for item in top_overall:
        rank_str = f"#{item['rank']}"
        score_val = f"{item['score']:.3f}"
        pct = min(100, max(0, int(item["score"] * 100)))
        top_cards_html.append(f"""
        <div class="finding-card">
          <div>
            <div class="card-top">
              <span class="rank-pill">{rank_str}</span>
              <span class="organ-tag" title="{html.escape(item['organ_vi'])}">{html.escape(item['organ_vi'])}</span>
            </div>
            <div class="card-finding-name">{html.escape(item['finding_vi'])}</div>
            <div class="card-finding-en">{html.escape(item['finding_en'])}</div>
          </div>
          <div>
            <div class="card-score-row">
              <span class="score-label">Điểm mô hình</span>
              <span class="score-val">{score_val}</span>
            </div>
            <div class="score-bar-bg" title="Điểm mô hình: {score_val}">
              <div class="score-bar-fill" style="width: {pct}%;"></div>
            </div>
          </div>
        </div>
        """)
    top_cards_rendered = "\n".join(top_cards_html)

    # Build Organ Grouping Cards
    organ_cards_html = []
    unique_organs_for_filter = []
    for ovi, g in organ_groups.items():
        unique_organs_for_filter.append((ovi, g["organ_en"]))
        list_items = []
        for f in g["top_findings"]:
            s_val = f"{f['score']:.3f}"
            list_items.append(f"""
            <li class="organ-finding-item">
              <div class="item-left">
                <span class="item-name-vi" title="{html.escape(f['finding_vi'])}">{html.escape(f['finding_vi'])}</span>
                <span class="item-name-en">{html.escape(f['finding_en'])}</span>
              </div>
              <div class="item-right">
                <span class="case-rank-tag">#{f['rank']}</span>
                <span class="score-val">{s_val}</span>
              </div>
            </li>
            """)
        rendered_list = "\n".join(list_items)
        organ_cards_html.append(f"""
        <div class="organ-card">
          <div class="organ-card-header">
            <span class="organ-card-title">{html.escape(ovi)}</span>
            <span class="organ-count-badge">{len(g['all_findings'])} finding</span>
          </div>
          <ul class="organ-findings-list">
            {rendered_list}
          </ul>
        </div>
        """)
    organ_cards_rendered = "\n".join(organ_cards_html)

    # Build Full 146 Table Rows
    table_rows_html = []
    for item in ranked_findings:
        is_top = "top-highlight" if item["rank"] <= top_n_overall else ""
        s_val = f"{item['score']:.3f}"
        table_rows_html.append(f"""
        <tr class="{is_top}" 
            data-organ="{html.escape(item['organ_en'])}" 
            data-organ-vi="{html.escape(item['organ_vi'])}" 
            data-vi="{html.escape(item['finding_vi'])}" 
            data-en="{html.escape(item['finding_en'])}">
          <td style="text-align: center; color: var(--text-muted); font-weight: 600;">{item['rank']}</td>
          <td>
            <strong>{html.escape(item['organ_vi'])}</strong>
            <span style="font-size: 11px; color: var(--text-muted); display: block;">{html.escape(item['organ_en'])}</span>
          </td>
          <td>
            <span>{html.escape(item['finding_vi'])}</span>
          </td>
          <td style="color: var(--text-muted); font-style: italic;">
            {html.escape(item['finding_en'])}
          </td>
          <td class="score-cell">{s_val}</td>
          <td style="text-align: center;">
            <input type="checkbox" onchange="toggleReviewCheck(this)" title="Đánh dấu đã rà soát" />
          </td>
        </tr>
        """)
    table_rows_rendered = "\n".join(table_rows_html)

    # Filter Options
    filter_opts = ['<option value="">-- Tất cả cơ quan ({}) --</option>'.format(len(organ_groups))]
    for ovi, oen in unique_organs_for_filter:
        filter_opts.append(f'<option value="{html.escape(oen)}">{html.escape(ovi)} ({html.escape(oen)})</option>')
    filter_options_rendered = "\n".join(filter_opts)

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RADAR-4060 Báo cáo Hỗ trợ Rà soát CT - {safe_case_id}</title>
  <style>
{REPORT_CSS}
  </style>
</head>
<body>

<div class="report-container">
  <!-- Header -->
  <header class="report-header">
    <div class="header-title-row">
      <div>
        <h1>RADAR-4060 BÁO CÁO HỖ TRỢ RÀ SOÁT HÌNH ẢNH CT BỤNG</h1>
        <div class="header-subtitle">Hệ thống gợi ý phát hiện đa cơ quan (146 findings) &bull; Dành cho Bác sĩ Chẩn đoán hình ảnh</div>
      </div>
    </div>
    <div class="header-badges">
      <span class="badge"><strong>Mã ca:</strong> {safe_case_id}</span>
      <span class="badge"><strong>Chuỗi/Phase:</strong> {safe_series}</span>
      <span class="badge"><strong>Thời gian xử lý:</strong> {safe_time}</span>
      <span class="badge"><strong>Mô hình:</strong> {safe_model}</span>
      <span class="badge"><strong>Quy mô:</strong> 146 findings / 18 cơ quan</span>
    </div>
  </header>

  <!-- Mandatory Clinical Disclaimer -->
  <aside class="disclaimer-card" role="alert">
    <h3>LƯU Ý QUAN TRỌNG VỀ ĐIỂM MÔ HÌNH</h3>
    <p>
      <strong>{disclaimer_esc}</strong>
      Báo cáo này là công cụ hỗ trợ rà soát (review aid), sắp xếp theo mức độ phù hợp hình ảnh nhằm hạn chế bỏ sót tổn thương.
      Không sử dụng điểm mô hình như một kết luận chẩn đoán xác định và không áp dụng ngưỡng nhị phân dương/âm tính cố định.
    </p>
  </aside>

  <!-- Section 1: Top 12 Overall -->
  <section class="report-section">
    <div class="section-header">
      <div class="section-title">
        <span>⭐ Ưu tiên rà lại (Top {len(top_overall)})</span>
      </div>
      <div class="section-subtitle">Xếp hạng theo Điểm mô hình cao nhất trên toàn bộ 146 finding (Ưu tiên rà lại)</div>
    </div>
    <div class="top-grid">
      {top_cards_rendered}
    </div>
  </section>

  <!-- Section 2: Grouped by Organ (Top 3 per organ) -->
  <section class="report-section">
    <div class="section-header">
      <div class="section-title">
        <span>🏥 Phân loại theo cơ quan (Tối đa {top_n_per_organ} finding hàng đầu mỗi cơ quan)</span>
      </div>
      <div class="section-subtitle">Sắp xếp các nhóm cơ quan theo điểm finding cao nhất</div>
    </div>
    <div class="organ-groups-grid">
      {organ_cards_rendered}
    </div>
  </section>

  <!-- Section 3: Expandable Full 146 Table with Search -->
  <section class="report-section">
    <details class="collapsible-section" open>
      <summary>📋 Toàn bộ 146 finding (Ưu tiên rà lại &amp; Các finding khác - Bộ lọc ngoại tuyến)</summary>
      <div class="details-content">
        <div class="filter-bar">
          <input type="text" id="findingSearch" class="filter-input" onkeyup="filterFindings()" placeholder="🔍 Gõ tên finding (Tiếng Việt hoặc Tiếng Anh)..." />
          <select id="organFilter" class="filter-select" onchange="filterFindings()">
            {filter_options_rendered}
          </select>
          <button type="button" class="filter-btn" onclick="resetFilters()">Đặt lại bộ lọc</button>
          <span id="visibleCount" class="filter-counter">Hiển thị: {len(ranked_findings)} / {len(ranked_findings)} finding</span>
        </div>

        <div class="table-responsive">
          <table class="findings-table">
            <thead>
              <tr>
                <th style="width: 48px; text-align: center;">Hạng</th>
                <th style="width: 180px;">Cơ quan</th>
                <th>Tên Finding (Tiếng Việt)</th>
                <th style="width: 240px;">Thuật ngữ Tiếng Anh</th>
                <th style="width: 110px; text-align: right;">Điểm mô hình</th>
                <th style="width: 80px; text-align: center;">Đã rà</th>
              </tr>
            </thead>
            <tbody id="findingsTableBody">
              {table_rows_rendered}
            </tbody>
          </table>
        </div>
      </div>
    </details>

    <!-- Section 4: Audit & Technical Metadata -->
    <details class="collapsible-section">
      <summary>⚙️ Thông tin kỹ thuật & Kiểm toán an toàn dữ liệu</summary>
      <div class="details-content" style="font-size: 13px; color: var(--text-muted); line-height: 1.6;">
        <p><strong>Kiến trúc & Tối ưu hóa:</strong> RADAR ViT-B (Alibaba DAMO Academy) + Bert-base Chinese tokenization, trích xuất đặc trưng đa cơ quan.</p>
        <p><strong>Cơ chế tiết kiệm bộ nhớ:</strong> CPU-resident volume stitching, single-channel count map, patch streaming, trilinear interpolation on CPU.</p>
        <p><strong>Môi trường:</strong> RTX 4060 8GB VRAM envelope (&le; 7.5 GB), FP16 Autocast Inference Mode.</p>
        <p><strong>An toàn dữ liệu y tế:</strong> Báo cáo chạy 100% offline tại máy trạm cục bộ. Tuyệt đối không gửi dữ liệu hình ảnh, thông tin bệnh nhân hay điểm dự đoán qua internet.</p>
      </div>
    </details>
  </section>

  <!-- Footer -->
  <footer class="report-footer">
    <div>RADAR-4060 Clinical Review Aid &bull; Phiên bản nghiên cứu &amp; thử nghiệm lâm sàng</div>
    <div>Báo cáo ngoại tuyến độc lập &bull; 100% Offline</div>
  </footer>
</div>

<script>
{REPORT_JS}
</script>
</body>
</html>
"""
    return html_content


def render_report_from_csv(
    csv_path: str,
    output_html_path: str,
    row_index: int = 0,
    case_id: Optional[str] = None,
    series_alias: Optional[str] = None,
) -> str:
    """
    Loads inference CSV and writes self-contained HTML report.
    """
    if pd is None:
        raise RuntimeError("pandas is required to read CSV files.")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV file at {csv_path} is empty.")

    if row_index >= len(df):
        raise IndexError(f"Row index {row_index} out of range (total {len(df)} rows).")

    row = df.iloc[row_index]
    raw_scores = {}
    csv_case = None

    for col in df.columns:
        if col == "file_name":
            csv_case = str(row[col])
        else:
            raw_scores[col] = float(row[col])

    # Determine safe case ID
    inferred_id = case_id
    if not inferred_id:
        if csv_case:
            base = os.path.basename(csv_case)
            for ext in [".nii.gz", ".nii", ".dcm"]:
                if base.endswith(ext):
                    base = base[: -len(ext)]
            inferred_id = base
        else:
            inferred_id = f"CASE_{row_index+1:03d}"

    ranked = extract_ranked_findings(raw_scores)
    html_out = render_html_report(
        ranked_findings=ranked,
        case_id=inferred_id,
        series_alias=series_alias,
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    return output_html_path


def main():
    parser = argparse.ArgumentParser(
        description="Render offline radiologist HTML report from RADAR CSV output."
    )
    parser.add_argument("--csv-path", "--csv", required=True, help="Path to RADAR inference CSV file.")
    parser.add_argument("--output-html", "--output", required=True, help="Path to output HTML report.")
    parser.add_argument("--row-index", type=int, default=0, help="Row index to render (default: 0).")
    parser.add_argument("--case-id", default=None, help="Safe anonymized case ID (default: derived from file_name).")
    parser.add_argument("--series-alias", default=None, help="Series/Phase alias (e.g. 'Arterial', 'Venous', 'Series 01').")

    args = parser.parse_args()
    out = render_report_from_csv(
        csv_path=args.csv_path,
        output_html_path=args.output_html,
        row_index=args.row_index,
        case_id=args.case_id,
        series_alias=args.series_alias,
    )
    print(f"[RADAR-4060] Radiologist HTML report rendered successfully to: {out}")


if __name__ == "__main__":
    main()
