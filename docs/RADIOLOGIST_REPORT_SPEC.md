# RADAR-4060 Radiologist Report Specification

## Goal

Convert the raw 146-column RADAR CSV into a local, offline, radiologist-readable HTML report.

The HTML is a review aid. It must not reinterpret RADAR scores as calibrated probabilities or clinical diagnoses.

## Required wording

Always call the numeric output:
- "Điểm mô hình" / "model score"

Never call it:
- probability of disease;
- xác suất mắc bệnh;
- positive/negative by default;
- sensitivity/specificity for an individual case.

The report must visibly state:
"Điểm mô hình phản ánh mức độ phù hợp giữa hình ảnh và finding mà RADAR học được; đây không phải xác suất bệnh đã được hiệu chỉnh."

## Default layout

1. Case header using a safe local case ID, never patient name.
2. "Finding ưu tiên rà lại" = top findings ranked by score, not a diagnostic threshold.
3. Group findings by organ/system in Vietnamese.
4. For each finding show:
   - Vietnamese finding name;
   - model score to 3 decimals;
   - optional English label in smaller text;
   - rank within the case.
5. Default view should show the top 12 overall findings.
6. Each organ section should show up to its top 3 findings.
7. Add a "Hiện toàn bộ 146 finding" expandable section.
8. Add an expandable raw-data/debug section containing the full table.
9. Provide search/filter in the HTML if simple to implement without external JS/CDN.
10. Fully offline: no CDN, telemetry, external fonts, or network calls.

## Clinical display behavior

Do not use red/green "positive/negative" semantics without validated finding-specific thresholds.

Use neutral review labels:
- "Ưu tiên rà lại" for top-ranked items.
- "Các finding khác" for lower-ranked items.

Any optional display filter must be explicitly labeled as a display filter, not a clinical cutoff.

## Vietnamese terminology

Create a maintainable mapping file for organ and finding names, for example:
- Aorta -> Động mạch chủ
- Heart -> Tim
- Liver -> Gan
- Kidney -> Thận
- Adrenal gland -> Tuyến thượng thận
- Gallbladder -> Túi mật/đường mật as appropriate
- Pancreas -> Tụy
- Spleen -> Lách
- Large bowel -> Đại tràng
- Small bowel -> Ruột non
- Stomach -> Dạ dày
- Bladder -> Bàng quang
- Portal vein -> Tĩnh mạch cửa
- Esophagus -> Thực quản
- Lung -> Phổi
- Rib -> Xương sườn
- Sacrum -> Xương cùng

Translate all 146 findings into medically natural Vietnamese. Keep the original English label as secondary metadata for auditability.

## Demo acceptance

For the upstream demo case, verify the top-ranked findings include the expected high scores from the reference CSV, including approximately:
- Cardiomegaly ~0.833
- Aortic calcification ~0.697
- Atherosclerosis ~0.578

Do not hard-code those values into the renderer; use them only as a regression check.

## Local patient case

After the report renderer passes demo validation, process local alias `LOCAL_CASE_001`.

The actual filesystem path mapping must stay outside Git.

Expected local workflow:
1. Extract the ZIP to a temporary local-only directory.
2. Inventory DICOM series locally.
3. Never upload DICOM/header/pixel data.
4. Ignore scouts/localizers, dose reports, derived screenshots, and obviously non-diagnostic series.
5. Identify abdominal CT diagnostic series suitable for RADAR.
6. Prefer contrast-enhanced axial soft-tissue diagnostic series.
7. If multiple eligible contrast phases exist, do not silently choose one:
   - process each eligible phase separately;
   - preserve a safe local series alias;
   - present one report section per series/phase.
8. Convert eligible DICOM series to NIfTI locally with dcm2niix or an equivalent local tool.
9. Do not place patient names in output filenames.
10. Run `inference_4060.py` and render the HTML report locally.
11. Save local outputs beneath the configured runtime root, not inside the Git checkout.
12. GitHub result JSON may record only non-PHI operational facts (number of series, runtime, peak VRAM, success/failure, local report alias/path with patient-identifying components removed).

## Safety

The report is research-only and requires radiologist review.
