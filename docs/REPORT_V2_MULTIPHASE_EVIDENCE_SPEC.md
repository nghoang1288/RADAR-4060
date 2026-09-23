# RADAR-4060 Report V2 — Single Multi-phase Study + Direct Review Images

## Purpose

Replace the current "one HTML per CT phase" output with ONE patient/study-level radiologist review report.

The report is based on a conventional Vietnamese abdominal CT structure:
1. KỸ THUẬT
2. MÔ TẢ — organ-by-organ
3. KẾT LUẬN

This is a research review aid, not an autonomous final diagnosis.

## 1. One patient = one report

For one local case/study containing multiple eligible phases:
- Non-contrast
- Arterial
- Portal venous / venous
- Delayed

Create exactly ONE study report.

Do not produce four separate primary reports.

Internally retain one inference result per phase, but fuse them into a study-level data model:

```
StudyCase
  phases[]
  findings[]
    finding_id
    organ
    scores_by_phase
    preferred_phase
    selected_phase
    review_score
    evidence[]
```

### Study-level score rule

Do NOT average all phases blindly.

For each finding:
1. consult a maintainable finding/organ phase-preference mapping;
2. select the best available clinically preferred phase;
3. use that selected phase's model score as the study-level "Điểm mô hình" used for ranking;
4. if no preferred phase exists, use the highest available phase score as a clearly marked fallback;
5. preserve all phase scores in an expandable "Điểm theo từng thì" section.

This score remains an uncalibrated model score, not a disease probability.

### Initial phase preferences

Implement a maintainable mapping, with reasonable defaults:

- calcification / stone / hyperattenuating material -> non-contrast preferred;
- aortic dissection / aneurysm / arterial lesion -> arterial preferred;
- portal vein thrombosis, abdominal inflammatory change, most solid-organ lesions and metastases -> portal venous preferred;
- collecting system / urinary excretory assessment -> delayed preferred when available;
- pleural/lung findings -> best diagnostic phase available, generally portal venous unless a dedicated lung series exists;
- bone/rib/sacrum -> any diagnostic phase, with bone window for evidence rendering.

Finding-specific overrides take precedence over organ defaults.

Do not claim this phase mapping is clinically validated; it is a review-display heuristic.

## 2. Report structure based on the provided normal abdominal CT format

### KỸ THUẬT

Generate one technique paragraph from actual local series metadata, for example:

"Chụp CLVT ổ bụng đa thì trước và sau tiêm thuốc cản quang, gồm thì không tiêm, động mạch, tĩnh mạch cửa và thì muộn; tái tạo lát cắt ... mm."

Use actual detected phases and slice thickness. Do not invent a phase that is absent.

### MÔ TẢ

Use concise organ-by-organ Vietnamese prose, following a conventional abdominal CT order.

Preferred order:
1. Gan
2. Tĩnh mạch cửa
3. Đường mật trong gan / ống mật chủ
4. Túi mật
5. Tụy
6. Lách
7. Tuyến thượng thận
8. Thận phải
9. Thận trái
10. Dạ dày / ruột when relevant
11. Động mạch chủ and major vessels
12. Bàng quang
13. Tiểu khung
14. Hạch
15. Dịch tự do / màng phổi
16. Phổi đáy, xương và các cấu trúc khác when RADAR has prioritized findings

Do NOT auto-write unsupported definitive normal claims such as "không thấy khối" merely because a score is low.

For an organ with no displayed prioritized finding, use neutral wording such as:
"Chưa có finding nổi bật được RADAR ưu tiên rà lại ở [organ] trong dữ liệu hiện tại."

For an organ with prioritized findings, write concise draft text, e.g.:
"Động mạch chủ: RADAR ưu tiên rà lại vôi hóa thành động mạch chủ (điểm mô hình ...), xơ vữa động mạch chủ (...)."

Each abnormal/prioritized finding in MÔ TẢ must be followed immediately by its evidence image panel.

### KẾT LUẬN

Summarize only the most important study-level prioritized findings in short Vietnamese radiology style.

Do not copy all 146 labels into the conclusion.

Keep score badges visually beside the conclusion item rather than embedding a misleading percentage into the sentence.

Add a visible "Dự thảo hỗ trợ rà soát — cần bác sĩ xác nhận" label.

## 3. Every reported finding must have direct review images

Every finding that appears in:
- "Finding ưu tiên rà lại",
- MÔ TẢ,
- KẾT LUẬN

must have at least one inline image immediately associated with it.

The raw/debug table of all 146 findings does not require 146 image panels.

### Important localization limitation

RADAR's public model is not a validated lesion-localization model.

Therefore never label evidence images as:
- lesion localization;
- vị trí tổn thương do AI xác định;
- proof / chứng minh tổn thương.

Use:
- "Ảnh gợi ý rà lại"
- "Vùng mô hình sử dụng để chấm điểm"
- "Lát cắt tham khảo"

### Finding-specific evidence selection

Enhance inference to retain lightweight LOCAL-ONLY per-window evidence metadata.

For each sliding window and finding scored in that window, retain:
- phase alias;
- window coordinates;
- finding score for that window;
- organ ID/name;
- optionally the organ segmentation mask needed to select a representative slice.

Do not store full activation tensors.

For each study-level finding:
1. choose the selected/preferred phase;
2. identify the contributing sliding window with the highest local score for that finding;
3. within that window, use the organ segmentation to choose a representative axial slice;
4. default representative slice: slice with greatest relevant organ-mask area within the selected high-scoring window;
5. generate 1-3 adjacent review images centered around that slice;
6. crop with enough surrounding anatomy for orientation/context, not a tiny isolated crop;
7. allow click-to-enlarge.

This is a "highest-scoring model window + organ context" visualization, not lesion localization.

If window-level finding evidence cannot be recovered reliably for a finding, do not fabricate it. Fall back to an organ-centered representative image and visibly label it:
"Ảnh cơ quan tham khảo — chưa định vị finding."

### Window presets

Use clinically sensible display presets:
- abdominal soft tissue: approximately WL 40 / WW 400;
- lung: approximately WL -600 / WW 1500;
- bone: approximately WL 400 / WW 1800;
- calcification/stone: choose a suitable non-contrast high-contrast preset while retaining soft-tissue context.

Allow the user to switch preset locally if practical.

### Image annotations

Each displayed review image must show:
- R/L orientation markers;
- phase;
- slice index / total slices;
- window preset;
- safe series alias only;
- optional organ contour / evaluated-window outline as a toggle.

Do not burn patient name, MRN, accession number, DOB, or raw DICOM identifiers into images.

Prefer self-contained embedded JPEG/WebP images inside the HTML if report size remains reasonable. Otherwise use a local relative assets directory.

## 4. Multi-phase UI

At the top of the single report show detected phases as chips/tabs:
- Không tiêm
- Động mạch
- Tĩnh mạch cửa
- Muộn

These are navigation/filter controls inside ONE report, not links to separate reports.

For each finding show:
- study-level "Điểm mô hình";
- selected phase;
- expandable per-phase scores;
- direct evidence images.

## 5. Radiologist review controls

Add simple offline controls per displayed finding:
- "Phù hợp"
- "Không phù hợp"
- "Chưa chắc"

These controls are local-only.

Provide:
- "Sao chép KẾT LUẬN đã rà soát"
- print-friendly CSS / Print-to-PDF support.

Do not upload review decisions.

## 6. Local real-case re-test

After synthetic and public-demo tests pass, re-run LOCAL_CASE_001 using the already configured local alias.

Requirements:
- identify the four previously eligible phases as a single study;
- run/inherit per-phase inference results;
- create ONE combined report;
- do not create four primary reports;
- generate evidence images for every displayed prioritized finding;
- keep all patient-derived output local;
- GitHub terminal result contains only aggregate non-PHI operational facts.

## 7. Tests

Add tests for:
1. four phases group into one StudyCase;
2. one study produces exactly one primary HTML report;
3. same finding across phases deduplicates to one study-level finding;
4. phase-preference selection works for representative categories;
5. all displayed prioritized findings contain >=1 evidence image or an explicit organ-reference fallback;
6. no displayed finding is silently missing an image;
7. images include R/L, phase and slice metadata;
8. HTML contains KỸ THUẬT, MÔ TẢ and KẾT LUẬN sections;
9. no unsupported definitive normal statements are auto-generated;
10. no PHI in generated filenames or image overlays;
11. report remains fully offline;
12. real-case local output count is one combined primary report.
