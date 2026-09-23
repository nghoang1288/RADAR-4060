"""
RADAR-4060 Report V2: Unified Multi-phase Evidence Report Generator.

Renders ONE comprehensive radiologist-readable HTML report for a multi-phase CT study,
featuring:
1. Standard Vietnamese abdominal CT layout: KỸ THUẬT, MÔ TẢ (organ-by-organ), KẾT LUẬN.
2. Direct inline evidence image panels for every prioritized finding.
3. Clinically selected study-level review scores with expandable per-phase breakdowns.
4. Offline interactive radiologist review controls (Phù hợp / Không phù hợp / Chưa chắc).
5. "Sao chép KẾT LUẬN đã rà soát" clipboard action.
6. Print-friendly CSS for clinical documentation.
7. 100% offline self-contained HTML (zero CDNs, telemetry, or external fonts).
"""

import html
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from RADAR_inference.multiphase_case import (
    CONVENTIONAL_ORGAN_ORDER,
    FindingStudyLevel,
    PhaseInfo,
    StudyCase,
)

REPORT_V2_CSS = """
:root {
  --bg-primary: #f8fafc;
  --bg-card: #ffffff;
  --border-color: #cbd5e1;
  --border-subtle: #e2e8f0;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --primary-blue: #1d4ed8;
  --primary-light: #eff6ff;
  --accent-amber: #d97706;
  --accent-amber-bg: #fffbeb;
  --accent-amber-border: #fde68a;
  --status-accepted-bg: #f0fdf4;
  --status-accepted-border: #86efac;
  --status-accepted-text: #166534;
  --status-rejected-bg: #fef2f2;
  --status-rejected-border: #fca5a5;
  --status-rejected-text: #991b1b;
  --status-uncertain-bg: #fefce8;
  --status-uncertain-border: #fde047;
  --status-uncertain-text: #854d0e;
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
  max-width: 1100px;
  margin: 0 auto;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* Header */
.report-header {
  padding: 24px 32px 18px;
  background: linear-gradient(135deg, #1e3a8a, #2563eb);
  color: #ffffff;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 12px;
}

.header-title {
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.header-subtitle {
  font-size: 13.5px;
  color: #bfdbfe;
  margin-top: 3px;
}

.phase-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.phase-chip {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.phase-chip.active {
  background: #ffffff;
  color: #1e3a8a;
}

/* Mandatory Clinical Alert Box */
.disclaimer-card {
  margin: 18px 32px;
  padding: 14px 18px;
  border-radius: 8px;
  background-color: var(--accent-amber-bg);
  border-left: 5px solid var(--accent-amber);
  border-top: 1px solid var(--accent-amber-border);
  border-right: 1px solid var(--accent-amber-border);
  border-bottom: 1px solid var(--accent-amber-border);
}

.disclaimer-title {
  font-size: 13px;
  font-weight: 700;
  color: #92400e;
  text-transform: uppercase;
  margin-bottom: 3px;
}

.disclaimer-text {
  font-size: 13px;
  color: #78350f;
  line-height: 1.45;
}

/* Section Common */
.report-section {
  padding: 20px 32px;
  border-bottom: 1px solid var(--border-subtle);
}

.section-head {
  font-size: 16px;
  font-weight: 700;
  color: #1e3a8a;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.technique-box {
  background: #f8fafc;
  padding: 12px 16px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  font-size: 13.5px;
  color: #334155;
  line-height: 1.55;
}

/* Conclusion Block */
.conclusion-container {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 16px 20px;
}

.conclusion-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.copy-btn {
  background: #2563eb;
  color: #ffffff;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.copy-btn:hover { background: #1d4ed8; }

.conclusion-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.conclusion-item {
  padding: 10px 14px;
  margin-bottom: 8px;
  background: #ffffff;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  transition: all 0.2s;
}

.conclusion-item.accepted {
  background: var(--status-accepted-bg);
  border-color: var(--status-accepted-border);
}

.conclusion-item.rejected {
  opacity: 0.45;
  text-decoration: line-through;
  background: var(--status-rejected-bg);
}

.conclusion-item-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

.conclusion-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  background: #0f172a;
  color: #ffffff;
  font-variant-numeric: tabular-nums;
}

.phase-badge {
  font-size: 11.5px;
  padding: 2px 7px;
  border-radius: 4px;
  background: #e0f2fe;
  color: #0369a1;
  font-weight: 600;
}

/* Organ by Organ Descriptions */
.organ-block {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px dashed var(--border-subtle);
}

.organ-block:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.organ-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.organ-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}

.organ-normal-text {
  font-size: 13.5px;
  color: var(--text-muted);
  font-style: italic;
  padding: 6px 0 6px 4px;
}

.finding-evidence-card {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-top: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.finding-card-head {
  padding: 10px 16px;
  background: #f8fafc;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.finding-title-vi {
  font-size: 14.5px;
  font-weight: 700;
  color: #0f172a;
}

.finding-title-en {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 6px;
  font-weight: 400;
  font-style: italic;
}

.finding-card-body {
  padding: 14px 16px;
}

.review-controls {
  display: flex;
  gap: 6px;
  align-items: center;
}

.btn-review {
  border: 1px solid #cbd5e1;
  background: #ffffff;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-review:hover { background: #f1f5f9; }
.btn-review.active-accept { background: #16a34a; color: white; border-color: #15803d; }
.btn-review.active-reject { background: #dc2626; color: white; border-color: #b91c1c; }
.btn-review.active-uncertain { background: #ca8a04; color: white; border-color: #a16207; }

/* Evidence Image Panel */
.evidence-gallery {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.evidence-thumb-card {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
  background: #000000;
  width: 320px;
  max-width: 100%;
}

.evidence-img {
  width: 100%;
  display: block;
  cursor: zoom-in;
}

.evidence-caption {
  padding: 6px 10px;
  background: #0f172a;
  color: #94a3b8;
  font-size: 11px;
  display: flex;
  justify-content: space-between;
}

.phase-scores-details {
  margin-top: 10px;
  font-size: 12px;
  color: #475569;
}

.phase-scores-details summary {
  cursor: pointer;
  color: var(--primary-blue);
  font-weight: 600;
}

/* Full Table */
.full-table-section details {
  background: #f8fafc;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.full-table-section summary {
  padding: 14px 20px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
}

.full-table-content {
  padding: 14px 20px;
  background: #ffffff;
  border-top: 1px solid var(--border-color);
}

.filter-row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 240px;
  padding: 7px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 13px;
}

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
  box-shadow: 0 0 20px rgba(0,0,0,0.5);
}

/* Print CSS */
@media print {
  body { padding: 0; background: #ffffff; color: #000000; }
  .report-container { border: none; box-shadow: none; max-width: 100%; }
  .copy-btn, .review-controls, .filter-row, .full-table-section, .modal { display: none !important; }
  .finding-evidence-card { break-inside: avoid; border: 1px solid #999; }
  .evidence-thumb-card { width: 240px; }
  .report-header { background: #1e3a8a !important; color: #ffffff !important; -webkit-print-color-adjust: exact; }
}
"""

REPORT_V2_JS = """
function openModal(imgSrc) {
  var modal = document.getElementById("imgModal");
  var modalImg = document.getElementById("modalImg");
  if (modal && modalImg) {
    modalImg.src = imgSrc;
    modal.style.display = "flex";
  }
}

function closeModal() {
  var modal = document.getElementById("imgModal");
  if (modal) {
    modal.style.display = "none";
  }
}

function setReviewStatus(findingId, status) {
  var card = document.getElementById("card_" + findingId);
  var conclItem = document.getElementById("concl_" + findingId);
  
  if (card) {
    var btns = card.querySelectorAll(".btn-review");
    btns.forEach(function(b) {
      b.classList.remove("active-accept", "active-reject", "active-uncertain");
    });
    
    if (status === 'ACCEPT') {
      var b = card.querySelector(".btn-accept");
      if (b) b.classList.add("active-accept");
      if (conclItem) {
        conclItem.classList.remove("rejected");
        conclItem.classList.add("accepted");
      }
    } else if (status === 'REJECT') {
      var b = card.querySelector(".btn-reject");
      if (b) b.classList.add("active-reject");
      if (conclItem) {
        conclItem.classList.remove("accepted");
        conclItem.classList.add("rejected");
      }
    } else {
      var b = card.querySelector(".btn-uncertain");
      if (b) b.classList.add("active-uncertain");
      if (conclItem) {
        conclItem.classList.remove("accepted", "rejected");
      }
    }
  }
}

function copyReviewedConclusion() {
  var items = document.querySelectorAll(".conclusion-item");
  var lines = [];
  items.forEach(function(it) {
    if (!it.classList.contains("rejected")) {
      var textEl = it.querySelector(".conclusion-text");
      if (textEl) {
        lines.push("- " + textEl.textContent.trim());
      }
    }
  });
  
  var finalText = "KẾT LUẬN (Đã rà soát qua RADAR-4060):\\n" + lines.join("\\n");
  navigator.clipboard.writeText(finalText).then(function() {
    alert("Đã sao chép KẾT LUẬN vào bộ nhớ tạm!");
  }).catch(function(err) {
    alert("Không thể sao chép: " + err);
  });
}

function filterAllFindings() {
  var q = document.getElementById("tblSearch").value.toLowerCase().trim();
  var rows = document.querySelectorAll("#fullFindingsBody tr");
  rows.forEach(function(r) {
    var text = r.textContent.toLowerCase();
    r.style.display = text.indexOf(q) !== -1 ? "" : "none";
  });
}
"""


def render_multiphase_report_html(
    study: StudyCase,
    generated_at: Optional[str] = None,
) -> str:
    """
    Renders the unified Report V2 HTML from a populated StudyCase.
    All untrusted strings are escaped with html.escape().
    """
    import datetime

    safe_case_id = html.escape(study.case_id)
    safe_gen_time = html.escape(
        generated_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    safe_technique = html.escape(study.technique_text)

    # 1. Phase chips
    phase_chips_html = []
    for pkey, pinfo in study.phases.items():
        phase_chips_html.append(
            f'<span class="phase-chip active">'
            f'<strong>{html.escape(pinfo.name_vi)}</strong> &bull; {pinfo.slices} lát'
            f'</span>'
        )
    rendered_phase_chips = "\n".join(phase_chips_html)

    # 2. Build KẾT LUẬN Items (Top prioritized findings)
    conclusion_items_html = []
    for f in study.top_prioritized_findings:
        safe_fid = html.escape(f.finding_id).replace(" ", "_").replace("(", "").replace(")", "").replace("/", "")
        pinfo = study.phases.get(f.selected_phase)
        phase_label = pinfo.name_vi if pinfo else f.selected_phase

        conclusion_items_html.append(f"""
        <li class="conclusion-item accepted" id="concl_{safe_fid}">
          <div class="conclusion-item-left">
            <span style="color: #64748b;">#{f.case_rank}</span>
            <span class="conclusion-text"><strong>{html.escape(f.organ_vi)}</strong>: {html.escape(f.finding_vi)}</span>
            <span style="font-size: 11px; color: #64748b; font-style: italic;">({html.escape(f.finding_en)})</span>
          </div>
          <div class="conclusion-meta">
            <span class="score-badge">Điểm MH: {f.review_score:.3f}</span>
            <span class="phase-badge">{html.escape(phase_label)}</span>
          </div>
        </li>
        """)
    rendered_conclusion_items = "\n".join(conclusion_items_html)

    # 3. Group findings by organ for MÔ TẢ
    findings_by_organ: Dict[str, List[FindingStudyLevel]] = {}
    for f in study.findings:
        findings_by_organ.setdefault(f.organ_en, []).append(f)

    # Build MÔ TẢ section following conventional Vietnamese order
    organ_sections_html = []
    for organ_en, organ_title_vi in CONVENTIONAL_ORGAN_ORDER:
        org_findings = findings_by_organ.get(organ_en, [])
        # Find prioritized findings for this organ (in top_prioritized_findings)
        prioritized_in_org = [
            f for f in study.top_prioritized_findings if f.organ_en == organ_en
        ]

        if not prioritized_in_org:
            # Neutral statement - NO unsupported definitive normal claims!
            organ_sections_html.append(f"""
            <div class="organ-block">
              <div class="organ-title-row">
                <span class="organ-title">{html.escape(organ_title_vi)}</span>
              </div>
              <div class="organ-normal-text">
                Chưa có finding nổi bật được RADAR ưu tiên rà lại ở {html.escape(organ_title_vi)} trong dữ liệu hiện tại.
              </div>
            </div>
            """)
        else:
            # Build detailed cards with inline evidence images for prioritized findings
            cards_html = []
            for f in prioritized_in_org:
                safe_fid = html.escape(f.finding_id).replace(" ", "_").replace("(", "").replace(")", "").replace("/", "")
                pinfo = study.phases.get(f.selected_phase)
                phase_label = pinfo.name_vi if pinfo else f.selected_phase

                # Expandable per-phase breakdown
                phase_breakdown_spans = []
                for pk, sc in sorted(f.scores_by_phase.items()):
                    p_meta = study.phases.get(pk)
                    p_name = p_meta.name_vi if p_meta else pk
                    is_sel = " (Được chọn)" if pk == f.selected_phase else ""
                    phase_breakdown_spans.append(
                        f"<span><strong>{html.escape(p_name)}</strong>: {sc:.3f}{is_sel}</span>"
                    )
                rendered_breakdown = " &bull; ".join(phase_breakdown_spans)

                # Evidence gallery
                evidence_items_html = []
                for ev in f.evidence_images:
                    evidence_items_html.append(f"""
                    <div class="evidence-thumb-card">
                      <img src="{ev.base64_jpeg}" class="evidence-img" onclick="openModal(this.src)" title="Bấm để phóng to" alt="Ảnh lát cắt" />
                      <div class="evidence-caption">
                        <span>Lát {ev.slice_index}/{ev.total_slices} ({ev.window_preset})</span>
                        <span>{html.escape(ev.phase_name_vi)}</span>
                      </div>
                    </div>
                    """)
                rendered_evidence = (
                    "\n".join(evidence_items_html)
                    if evidence_items_html
                    else '<div style="font-size: 12px; color: #94a3b8; padding: 6px;">Ảnh cơ quan tham khảo — chưa định vị finding.</div>'
                )

                cards_html.append(f"""
                <div class="finding-evidence-card" id="card_{safe_fid}">
                  <div class="finding-card-head">
                    <div>
                      <span style="font-size: 11px; background: #0f172a; color: white; padding: 2px 6px; border-radius: 3px; font-weight: 700; margin-right: 6px;">#{f.case_rank}</span>
                      <span class="finding-title-vi">{html.escape(f.finding_vi)}</span>
                      <span class="finding-title-en">({html.escape(f.finding_en)})</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span class="score-badge">Điểm MH: {f.review_score:.3f}</span>
                      <span class="phase-badge">{html.escape(phase_label)}</span>
                      <div class="review-controls">
                        <button type="button" class="btn-review btn-accept active-accept" onclick="setReviewStatus('{safe_fid}', 'ACCEPT')" title="Xác nhận phù hợp">✓ Phù hợp</button>
                        <button type="button" class="btn-review btn-reject" onclick="setReviewStatus('{safe_fid}', 'REJECT')" title="Loại bỏ khỏi kết luận">✗ Không phù hợp</button>
                        <button type="button" class="btn-review btn-uncertain" onclick="setReviewStatus('{safe_fid}', 'UNCERTAIN')" title="Cần rà soát thêm">? Chưa chắc</button>
                      </div>
                    </div>
                  </div>
                  <div class="finding-card-body">
                    <div class="evidence-gallery">
                      {rendered_evidence}
                    </div>
                    <details class="phase-scores-details">
                      <summary>📊 Xem điểm theo từng thì ({len(f.scores_by_phase)} thì)</summary>
                      <div style="margin-top: 6px; padding: 6px 10px; background: #f8fafc; border-radius: 4px; line-height: 1.6;">
                        {rendered_breakdown}
                      </div>
                    </details>
                  </div>
                </div>
                """)

            rendered_cards = "\n".join(cards_html)
            organ_sections_html.append(f"""
            <div class="organ-block">
              <div class="organ-title-row">
                <span class="organ-title">{html.escape(organ_title_vi)}</span>
              </div>
              {rendered_cards}
            </div>
            """)

    rendered_mota_sections = "\n".join(organ_sections_html)

    # 4. Full Table Rows (146 findings)
    full_table_rows = []
    for f in study.findings:
        pinfo = study.phases.get(f.selected_phase)
        p_name = pinfo.name_vi if pinfo else f.selected_phase
        full_table_rows.append(f"""
        <tr>
          <td style="text-align: center; color: #64748b;">{f.case_rank}</td>
          <td><strong>{html.escape(f.organ_vi)}</strong></td>
          <td>{html.escape(f.finding_vi)}</td>
          <td style="color: #64748b; font-style: italic;">{html.escape(f.finding_en)}</td>
          <td style="font-weight: 700; text-align: right; font-variant-numeric: tabular-nums;">{f.review_score:.3f}</td>
          <td><span class="phase-badge">{html.escape(p_name)}</span></td>
        </tr>
        """)
    rendered_full_table_rows = "\n".join(full_table_rows)

    html_out = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RADAR-4060 Báo cáo Nghiên cứu CT Đa thì - {safe_case_id}</title>
  <style>
{REPORT_V2_CSS}
  </style>
</head>
<body>

<div class="report-container">
  <!-- Header -->
  <header class="report-header">
    <div class="header-top">
      <div>
        <div class="header-title">RADAR-4060 BÁO CÁO HỖ TRỢ RÀ SOÁT HÌNH ẢNH CT BỤNG ĐA THÌ</div>
        <div class="header-subtitle">Nghiên cứu suy luận đa cơ quan &bull; Tổng hợp ca bệnh &bull; Đối chiếu ảnh lát cắt trực tiếp</div>
      </div>
      <div style="font-size: 12px; color: #bfdbfe; text-align: right;">
        <div><strong>Mã ca:</strong> {safe_case_id}</div>
        <div><strong>Thời gian xử lý:</strong> {safe_gen_time}</div>
      </div>
    </div>
    <div class="phase-chips">
      {rendered_phase_chips}
    </div>
  </header>

  <!-- Mandatory Clinical Disclaimer -->
  <aside class="disclaimer-card" role="alert">
    <div class="disclaimer-title">Lưu ý quan trọng về Điểm mô hình &amp; Ảnh gợi ý</div>
    <div class="disclaimer-text">
      <strong>Điểm mô hình phản ánh mức độ phù hợp giữa hình ảnh và finding mà RADAR học được; đây không phải xác suất bệnh đã được hiệu chỉnh.</strong>
      Các hình ảnh lát cắt đi kèm là ảnh lát cắt tham khảo do mô hình sử dụng để chấm điểm, không phải là vị trí tổn thương đã được định vị giải phẫu bệnh chính thức.
      Kết quả chỉ phục vụ mục đích hỗ trợ rà soát (review aid), cần Bác sĩ Chẩn đoán hình ảnh xác nhận.
    </div>
  </aside>

  <!-- Section 1: KỸ THUẬT -->
  <section class="report-section">
    <div class="section-head">
      <span>I. KỸ THUẬT</span>
    </div>
    <div class="technique-box">
      {safe_technique}
    </div>
  </section>

  <!-- Section 2: KẾT LUẬN -->
  <section class="report-section">
    <div class="section-head">
      <span>II. KẾT LUẬN (Dự thảo hỗ trợ rà soát)</span>
      <button type="button" class="copy-btn" onclick="copyReviewedConclusion()">📋 Sao chép KẾT LUẬN đã rà soát</button>
    </div>
    <div class="conclusion-container">
      <ul class="conclusion-list">
        {rendered_conclusion_items}
      </ul>
      <div style="font-size: 11.5px; color: #64748b; margin-top: 10px; font-style: italic;">
        * Các finding bị đánh dấu "Không phù hợp" sẽ tự động gạch ngang và không được đưa vào nội dung sao chép.
      </div>
    </div>
  </section>

  <!-- Section 3: MÔ TẢ CHI TIẾT THEO CƠ QUAN -->
  <section class="report-section">
    <div class="section-head">
      <span>III. MÔ TẢ CHI TIẾT THEO CƠ QUAN &amp; ĐỐI CHIẾU HÌNH ẢNH</span>
    </div>
    <div>
      {rendered_mota_sections}
    </div>
  </section>

  <!-- Section 4: TOÀN BỘ 146 FINDINGS -->
  <section class="report-section full-table-section">
    <details>
      <summary>📋 IV. TRA CỨU ĐẦY ĐỦ TOÀN BỘ 146 FINDINGS (Bấm để mở rộng / thu gọn)</summary>
      <div class="full-table-content">
        <div class="filter-row">
          <input type="text" id="tblSearch" class="search-input" onkeyup="filterAllFindings()" placeholder="🔍 Gõ tên finding (Tiếng Việt hoặc Tiếng Anh)..." />
        </div>
        <div style="overflow-x: auto; border: 1px solid #cbd5e1; border-radius: 6px;">
          <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
            <thead>
              <tr style="background: #f1f5f9; color: #334155; border-bottom: 2px solid #cbd5e1;">
                <th style="padding: 8px 10px; width: 45px; text-align: center;">#</th>
                <th style="padding: 8px 10px; width: 180px;">Cơ quan</th>
                <th style="padding: 8px 10px;">Finding (Tiếng Việt)</th>
                <th style="padding: 8px 10px; width: 220px;">Thuật ngữ Tiếng Anh</th>
                <th style="padding: 8px 10px; width: 100px; text-align: right;">Điểm MH</th>
                <th style="padding: 8px 10px; width: 140px;">Thì được chọn</th>
              </tr>
            </thead>
            <tbody id="fullFindingsBody">
              {rendered_full_table_rows}
            </tbody>
          </table>
        </div>
      </div>
    </details>
  </section>

  <!-- Section 5: METADATA & AN TOÀN -->
  <footer style="padding: 16px 32px; background: #f8fafc; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
    <div>RADAR-4060 Report V2 &bull; Tối ưu hóa RTX 4060 8GB (FP16 Autocast)</div>
    <div>100% Cục bộ &bull; Zero PHI Committed</div>
  </footer>
</div>

<!-- Modal Image Zoom -->
<div id="imgModal" class="modal" onclick="closeModal()">
  <img id="modalImg" src="" alt="Ảnh phóng to" />
</div>

<script>
{REPORT_V2_JS}
</script>
</body>
</html>
"""
    return html_out
