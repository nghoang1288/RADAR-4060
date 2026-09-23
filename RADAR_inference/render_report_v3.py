"""
RADAR-4060 Report V3: Clinical Audit Compliant Radiologist Report.

Implements all corrections from docs/CLINICAL_AUDIT_V3.md:
1. Single primary model input series (Portal-venous / Venous preferred; no score fusion).
2. Candidate selection strictly based on model prompt boundary (score >= 0.5), no forced Top-N.
3. Two-layer report: Unreviewed candidates do not auto-populate formal KẾT LUẬN.
4. Faithful evidence: Canonical NIfTI orientation (RAS+), literal R/L markers, physical Z (mm).
5. Supplementary phase review images clearly separated from primary model evidence.
6. Explicit RADAR-146 Anatomical Coverage Matrix, blocking unsupported normal claims.
7. 100% offline self-contained HTML (zero CDNs, telemetry, or external fonts).
"""

import html
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from RADAR_inference.coverage_matrix import ANATOMICAL_COVERAGE_MATRIX
from RADAR_inference.multiphase_case import CONVENTIONAL_ORGAN_ORDER, PHASE_META

REPORT_V3_CSS = """
:root {
  --bg-primary: #f8fafc;
  --bg-card: #ffffff;
  --border-color: #cbd5e1;
  --border-subtle: #e2e8f0;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --primary-blue: #1d4ed8;
  --accent-amber: #d97706;
  --accent-amber-bg: #fffbeb;
  --accent-amber-border: #fde68a;
  --status-accepted-bg: #f0fdf4;
  --status-accepted-border: #86efac;
  --status-accepted-text: #166534;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-main);
  line-height: 1.5;
  padding: 24px;
}

.report-container {
  max-width: 1120px;
  margin: 0 auto;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

/* Header */
.report-header {
  padding: 24px 32px 18px;
  background: linear-gradient(135deg, #0f172a, #1e3a8a);
  color: #ffffff;
}

.header-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.header-subtitle {
  font-size: 13px;
  color: #93c5fd;
  margin-top: 3px;
}

.primary-phase-banner {
  margin-top: 14px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12.5px;
}

.phase-pill {
  padding: 3px 10px;
  border-radius: 9999px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

.phase-pill.primary {
  background: #2563eb;
  color: #ffffff;
  border: 1px solid #60a5fa;
}

/* Mandatory Warnings */
.alert-card {
  margin: 16px 32px;
  padding: 12px 18px;
  border-radius: 8px;
  background-color: var(--accent-amber-bg);
  border-left: 5px solid var(--accent-amber);
  border-top: 1px solid var(--accent-amber-border);
  border-right: 1px solid var(--accent-amber-border);
  border-bottom: 1px solid var(--accent-amber-border);
  font-size: 13px;
  color: #78350f;
  line-height: 1.5;
}

/* Layer Sections */
.layer-title {
  padding: 10px 32px;
  background: #f1f5f9;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
  font-weight: 800;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-section {
  padding: 20px 32px;
  border-bottom: 1px solid var(--border-subtle);
}

.section-head {
  font-size: 15.5px;
  font-weight: 700;
  color: #1e3a8a;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Layer 1: Candidates */
.candidate-card {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.candidate-head {
  padding: 10px 16px;
  background: #f8fafc;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.candidate-title {
  font-size: 14.5px;
  font-weight: 700;
  color: #0f172a;
}

.candidate-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  background: #0f172a;
  color: #ffffff;
  font-variant-numeric: tabular-nums;
}

/* Review buttons */
.btn-review {
  border: 1px solid #cbd5e1;
  background: #ffffff;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-review:hover { background: #f1f5f9; }
.btn-review.active-accept { background: #16a34a; color: white; border-color: #15803d; }
.btn-review.active-reject { background: #dc2626; color: white; border-color: #b91c1c; }
.btn-review.active-uncertain { background: #ca8a04; color: white; border-color: #a16207; }

.evidence-container {
  padding: 12px 16px;
}

.evidence-flex {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.evidence-panel {
  border: 1px solid #334155;
  border-radius: 6px;
  overflow: hidden;
  background: #000000;
  width: 330px;
  max-width: 100%;
}

.evidence-panel img {
  width: 100%;
  display: block;
  cursor: zoom-in;
}

.evidence-caption {
  padding: 6px 10px;
  background: #0f172a;
  color: #cbd5e1;
  font-size: 11px;
  line-height: 1.4;
}

/* Layer 2: Formal Report */
.formal-box {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 14px 18px;
}

.conclusion-formal-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.conclusion-formal-item {
  padding: 8px 12px;
  background: #ffffff;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  margin-bottom: 6px;
  font-size: 13.5px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.copy-btn {
  background: #1d4ed8;
  color: #ffffff;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}

.copy-btn:hover { background: #1e40af; }

.organ-row {
  padding: 8px 0;
  border-bottom: 1px dashed var(--border-subtle);
  font-size: 13.5px;
}

.organ-row:last-child { border-bottom: none; }

.coverage-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-top: 10px;
}

.coverage-table th, .coverage-table td {
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  text-align: left;
}

.coverage-table th { background: #f1f5f9; color: #334155; }

/* Lightbox Modal */
.modal {
  display: none;
  position: fixed;
  z-index: 9999;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  align-items: center;
  justify-content: center;
}

.modal img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 4px;
}

@media print {
  body { padding: 0; background: #ffffff; }
  .report-container { border: none; box-shadow: none; max-width: 100%; }
  .btn-review, .copy-btn, .modal, .layer-title { display: none !important; }
  .report-header { background: #0f172a !important; color: white !important; }
}
"""

REPORT_V3_JS = """
var acceptedFindings = {};

function openModal(src) {
  var m = document.getElementById("imgModal");
  var mi = document.getElementById("modalImg");
  if (m && mi) {
    mi.src = src;
    m.style.display = "flex";
  }
}

function closeModal() {
  var m = document.getElementById("imgModal");
  if (m) m.style.display = "none";
}

function updateFormalLayers() {
  var conclList = document.getElementById("formalConclusionList");
  var emptyMsg = document.getElementById("emptyConclusionMsg");
  if (!conclList) return;
  
  conclList.innerHTML = "";
  var keys = Object.keys(acceptedFindings);
  
  if (keys.length === 0) {
    if (emptyMsg) emptyMsg.style.display = "block";
  } else {
    if (emptyMsg) emptyMsg.style.display = "none";
    keys.forEach(function(k) {
      var item = acceptedFindings[k];
      var li = document.createElement("li");
      li.className = "conclusion-formal-item";
      li.innerHTML = "<span><strong>" + item.organ + "</strong>: " + item.finding + "</span>" +
                     "<span style='font-size: 11px; background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 3px; font-weight: 600;'>Đã xác nhận (" + item.score + ")</span>";
      conclList.appendChild(li);
    });
  }
}

function setCandidateReview(fid, organ, finding, score, status) {
  var card = document.getElementById("cand_" + fid);
  if (card) {
    var btns = card.querySelectorAll(".btn-review");
    btns.forEach(function(b) {
      b.classList.remove("active-accept", "active-reject", "active-uncertain");
    });
    
    if (status === 'ACCEPT') {
      var b = card.querySelector(".btn-accept");
      if (b) b.classList.add("active-accept");
      acceptedFindings[fid] = { organ: organ, finding: finding, score: score };
    } else if (status === 'REJECT') {
      var b = card.querySelector(".btn-reject");
      if (b) b.classList.add("active-reject");
      delete acceptedFindings[fid];
    } else {
      var b = card.querySelector(".btn-uncertain");
      if (b) b.classList.add("active-uncertain");
      delete acceptedFindings[fid];
    }
  }
  updateFormalLayers();
}

function copyFormalConclusion() {
  var keys = Object.keys(acceptedFindings);
  if (keys.length === 0) {
    alert("Chưa có finding nào được xác nhận 'Phù hợp' để sao chép.");
    return;
  }
  var lines = keys.map(function(k) {
    return "- " + acceptedFindings[k].organ + ": " + acceptedFindings[k].finding;
  });
  var text = "KẾT LUẬN CLVT Ổ BỤNG (Đã rà soát lâm sàng):\\n" + lines.join("\\n");
  navigator.clipboard.writeText(text).then(function() {
    alert("Đã sao chép KẾT LUẬN vào bộ nhớ tạm!");
  }).catch(function(e) {
    alert("Lỗi sao chép: " + e);
  });
}
"""


def render_report_v3_html(
    case_id: str,
    primary_phase_key: str,
    primary_phase_name: str,
    primary_phase_slices: int,
    all_phases_meta: List[Dict[str, Any]],
    candidate_findings: List[Dict[str, Any]],
    all_146_findings: List[Dict[str, Any]],
    technique_text: str,
    scan_time: Optional[str] = None,
) -> str:
    """
    Renders unified Clinical Audit V3 HTML report.
    All untrusted dynamic text is passed through html.escape().
    """
    import datetime

    safe_case = html.escape(str(case_id))
    safe_time = html.escape(scan_time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    safe_tech = html.escape(technique_text)
    safe_primary_name = html.escape(primary_phase_name)

    # Phase pills
    phase_pills = []
    for p in all_phases_meta:
        is_pri = (p["phase_key"] == primary_phase_key)
        cls = "phase-pill primary" if is_pri else "phase-pill"
        role = " (Thì mô hình chính)" if is_pri else " (Thì đối chiếu bổ sung)"
        phase_pills.append(
            f'<span class="{cls}">'
            f'<strong>{html.escape(p["name_vi"])}</strong> ({p["slices"]} lát){role}'
            f'</span>'
        )
    rendered_phase_pills = "\n".join(phase_pills)

    # Layer 1: Candidate Cards (Score >= 0.5)
    candidate_cards = []
    for c in candidate_findings:
        safe_fid = html.escape(c["finding_id"]).replace(" ", "_").replace("(", "").replace(")", "").replace("/", "")
        safe_organ = html.escape(c["organ_vi"])
        safe_finding = html.escape(c["finding_vi"])
        safe_en = html.escape(c["finding_en"])
        score_val = f"{c['score']:.3f}"

        # Evidence panels
        ev_panels = []
        for ev in c.get("evidence", []):
            ev_panels.append(f"""
            <div class="evidence-panel">
              <img src="{ev['base64_jpeg']}" onclick="openModal(this.src)" title="Bấm để phóng to" alt="Evidence" />
              <div class="evidence-caption">
                <div style="display: flex; justify-content: space-between;">
                  <strong>{html.escape(ev['phase_name'])}</strong>
                  <span>Lát {ev['slice_idx']}/{ev['total_slices']}</span>
                </div>
                <div style="color: #94a3b8;">Z: {ev['phys_z_mm']:.1f}mm | {html.escape(ev['preset_name'])}</div>
                <div style="font-size: 10px; color: #60a5fa; margin-top: 2px;">{html.escape(ev['provenance_label'])}</div>
              </div>
            </div>
            """)

        rendered_evidence = "\n".join(ev_panels) if ev_panels else (
            '<div style="font-size: 12.5px; color: #94a3b8; padding: 10px;">Không có bằng chứng không gian tin cậy từ lần inference này.</div>'
        )

        candidate_cards.append(f"""
        <div class="candidate-card" id="cand_{safe_fid}">
          <div class="candidate-head">
            <div>
              <span class="candidate-title">{safe_organ} &bull; {safe_finding}</span>
              <span style="font-size: 12px; color: var(--text-muted); margin-left: 6px; font-style: italic;">({safe_en})</span>
            </div>
            <div class="candidate-meta">
              <span class="score-badge">Điểm RADAR: {score_val}</span>
              <div class="review-controls">
                <button type="button" class="btn-review btn-accept" onclick="setCandidateReview('{safe_fid}', '{safe_organ}', '{safe_finding}', '{score_val}', 'ACCEPT')">✓ Phù hợp</button>
                <button type="button" class="btn-review btn-reject" onclick="setCandidateReview('{safe_fid}', '{safe_organ}', '{safe_finding}', '{score_val}', 'REJECT')">✗ Không phù hợp</button>
                <button type="button" class="btn-review btn-uncertain" onclick="setCandidateReview('{safe_fid}', '{safe_organ}', '{safe_finding}', '{score_val}', 'UNCERTAIN')">? Chưa chắc</button>
              </div>
            </div>
          </div>
          <div class="evidence-container">
            <div class="evidence-flex">
              {rendered_evidence}
            </div>
          </div>
        </div>
        """)

    rendered_candidates = "\n".join(candidate_cards) if candidate_cards else (
        '<div style="padding: 16px; background: #f8fafc; border-radius: 6px; color: #64748b; font-style: italic;">Không có finding nào đạt ngưỡng ranh giới mô hình dương tính (&ge; 0,5) trong thì này.</div>'
    )

    # Layer 2: MÔ TẢ organ rows
    organ_rows = []
    for organ_en, organ_title_vi in CONVENTIONAL_ORGAN_ORDER:
        organ_rows.append(f"""
        <div class="organ-row">
          <strong>{html.escape(organ_title_vi)}</strong>: 
          <span style="color: var(--text-muted); font-style: italic;">
            Chưa có finding nổi bật được RADAR ưu tiên rà lại ở {html.escape(organ_title_vi)} trong dữ liệu hiện tại.
          </span>
        </div>
        """)
    rendered_organ_rows = "\n".join(organ_rows)

    # Coverage matrix rows
    cov_rows = []
    for item in ANATOMICAL_COVERAGE_MATRIX:
        cov_rows.append(f"""
        <tr>
          <td><strong>{html.escape(item['structure'])}</strong></td>
          <td><span style="font-weight: 600; color: {'#16a34a' if 'đầy đủ' in item['status'] else ('#ca8a04' if 'một phần' in item['status'] else '#dc2626')};">{html.escape(item['status'])}</span></td>
          <td>{item['radar_findings_count']}</td>
          <td style="color: #475569;">{html.escape(item['description'])}</td>
        </tr>
        """)
    rendered_cov_rows = "\n".join(cov_rows)

    # All 146 Table
    table_rows = []
    for rank, f in enumerate(all_146_findings, 1):
        table_rows.append(f"""
        <tr>
          <td style="text-align: center; color: #64748b;">{rank}</td>
          <td><strong>{html.escape(f['organ_vi'])}</strong></td>
          <td>{html.escape(f['finding_vi'])}</td>
          <td style="color: #64748b; font-style: italic;">{html.escape(f['finding_en'])}</td>
          <td style="text-align: right; font-weight: 700; font-variant-numeric: tabular-nums;">{f['score']:.3f}</td>
        </tr>
        """)
    rendered_table_rows = "\n".join(table_rows)

    html_out = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RADAR-4060 Báo cáo Rà soát Lâm sàng V3 - {safe_case}</title>
  <style>
{REPORT_V3_CSS}
  </style>
</head>
<body>

<div class="report-container">
  <!-- Header -->
  <header class="report-header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
      <div>
        <div class="header-title">RADAR-4060 BÁO CÁO HỖ TRỢ RÀ SOÁT LÂM SÀNG (V3 AUDIT)</div>
        <div class="header-subtitle">Hệ thống hỗ trợ rà soát CT Bụng &bull; Bằng chứng không gian thực &bull; Kiểm soát lâm sàng 2 lớp</div>
      </div>
      <div style="font-size: 12px; color: #93c5fd; text-align: right;">
        <div><strong>Mã ca:</strong> {safe_case}</div>
        <div><strong>Thời gian:</strong> {safe_time}</div>
      </div>
    </div>
    <div class="primary-phase-banner">
      <span>Thì chụp khảo sát:</span>
      {rendered_phase_pills}
    </div>
  </header>

  <!-- Mandatory Audited Disclaimers -->
  <aside class="alert-card" role="alert">
    <strong>CẢNH BÁO QUAN TRỌNG VỀ ĐIỂM MÔ HÌNH &amp; RANH GIỚI 0,5:</strong>
    <div>
      1. Điểm mô hình phản ánh mức độ phù hợp giữa hình ảnh và finding mà RADAR học được; đây không phải xác suất bệnh đã được hiệu chỉnh.
    </div>
    <div>
      2. Ngưỡng 0,5 chỉ là ranh giới mô hình nghiêng về prompt dương tính so với prompt âm tính, không phải ngưỡng chẩn đoán lâm sàng đã hiệu chỉnh.
    </div>
    <div>
      3. Báo cáo tuân thủ kiến trúc kiểm soát 2 lớp: Các gợi ý chưa được Bác sĩ xác nhận sẽ KHÔNG tự động đưa vào Kết luận chính thức.
    </div>
  </aside>

  <!-- LAYER 1: CANDIDATES -->
  <div class="layer-title">
    <span>LỚP 1: CÁC GỢI Ý RADAR CẦN BÁC SĨ RÀ LẠI (ĐIỂM &ge; 0,5 &bull; {len(candidate_findings)} GỢI Ý)</span>
    <span style="font-size: 11px; font-weight: normal; text-transform: none; color: #475569;">Bấm "✓ Phù hợp" để đưa vào báo cáo chính thức</span>
  </div>
  <section class="report-section">
    {rendered_candidates}
  </section>

  <!-- LAYER 2: FORMAL REPORT -->
  <div class="layer-title" style="background: #e2e8f0;">
    <span>LỚP 2: BÁO CÁO KẾT QUẢ CHẨN ĐOÁN HÌNH ẢNH (BÁC SĨ XÁC NHẬN)</span>
    <span style="font-size: 11px; font-weight: normal; text-transform: none; color: #475569;">Chỉ gồm các finding đã được Bác sĩ duyệt</span>
  </div>

  <!-- KỸ THUẬT -->
  <section class="report-section">
    <div class="section-head">
      <span>I. KỸ THUẬT</span>
    </div>
    <div class="formal-box" style="font-size: 13.5px; line-height: 1.6; color: #334155;">
      {safe_tech}
    </div>
  </section>

  <!-- KẾT LUẬN FORMAL -->
  <section class="report-section">
    <div class="section-head">
      <span>II. KẾT LUẬN (CHÍNH THỨC)</span>
      <button type="button" class="copy-btn" onclick="copyFormalConclusion()">📋 Sao chép KẾT LUẬN đã rà soát</button>
    </div>
    <div class="formal-box">
      <div id="emptyConclusionMsg" style="font-size: 13.5px; color: #64748b; font-style: italic;">
        Chưa có finding RADAR nào được bác sĩ xác nhận trong phiên rà soát này. (Vui lòng bấm nút "✓ Phù hợp" ở các gợi ý Lớp 1 phía trên để đưa tổn thương vào kết luận).
      </div>
      <ul class="conclusion-formal-list" id="formalConclusionList"></ul>
    </div>
  </section>

  <!-- MÔ TẢ ORGAN BY ORGAN -->
  <section class="report-section">
    <div class="section-head">
      <span>III. MÔ TẢ CHI TIẾT THEO CƠ QUAN</span>
    </div>
    <div class="formal-box" style="background: #ffffff;">
      {rendered_organ_rows}
    </div>
  </section>

  <!-- COVERAGE MATRIX -->
  <section class="report-section">
    <details>
      <summary style="font-size: 14.5px; font-weight: 700; color: #1e3a8a; cursor: pointer; text-transform: uppercase;">
        IV. BẢNG ĐỐI CHIẾU PHẠM VI KHẢO SÁT CỦA RADAR-146 (COVERAGE MATRIX)
      </summary>
      <div style="margin-top: 12px;">
        <div style="font-size: 12.5px; color: #64748b; margin-bottom: 8px;">
          Bảng đối chiếu minh bạch các cơ quan được mô hình bao phủ vs các vùng giải phẫu ngoài phạm vi (không được tự động kết luận bình thường).
        </div>
        <table class="coverage-table">
          <thead>
            <tr>
              <th style="width: 25%;">Cấu trúc giải phẫu</th>
              <th style="width: 28%;">Trạng thái RADAR-146</th>
              <th style="width: 12%;">Số finding</th>
              <th>Mô tả phạm vi</th>
            </tr>
          </thead>
          <tbody>
            {rendered_cov_rows}
          </tbody>
        </table>
      </div>
    </details>
  </section>

  <!-- ALL 146 TABLE -->
  <section class="report-section">
    <details>
      <summary style="font-size: 14.5px; font-weight: 700; color: #1e3a8a; cursor: pointer; text-transform: uppercase;">
        V. TRA CỨU ĐẦY ĐỦ TOÀN BỘ 146 FINDINGS (THÌ MÔ HÌNH CHÍNH)
      </summary>
      <div style="margin-top: 12px; overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
          <thead>
            <tr style="background: #f1f5f9; border-bottom: 2px solid #cbd5e1; text-align: left;">
              <th style="padding: 8px 10px; width: 45px; text-align: center;">#</th>
              <th style="padding: 8px 10px; width: 180px;">Cơ quan</th>
              <th style="padding: 8px 10px;">Finding (Tiếng Việt)</th>
              <th style="padding: 8px 10px; width: 240px;">Thuật ngữ Tiếng Anh</th>
              <th style="padding: 8px 10px; width: 100px; text-align: right;">Điểm RADAR</th>
            </tr>
          </thead>
          <tbody>
            {rendered_table_rows}
          </tbody>
        </table>
      </div>
    </details>
  </section>

  <footer style="padding: 16px 32px; background: #f8fafc; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; flex-wrap: wrap;">
    <div>RADAR-4060 V3 Clinical Audit Protocol &bull; RTX 4060 8GB Optimized</div>
    <div>Bảo mật Y tế 100% Cục bộ &bull; Zero PHI Committed</div>
  </footer>
</div>

<!-- Lightbox Modal -->
<div id="imgModal" class="modal" onclick="closeModal()">
  <img id="modalImg" src="" alt="Zoom" />
</div>

<script>
{REPORT_V3_JS}
</script>
</body>
</html>
"""
    return html_out
