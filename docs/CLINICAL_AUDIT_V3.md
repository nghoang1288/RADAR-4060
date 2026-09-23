# RADAR-4060 Clinical Audit V3 — Correct Model Use, Candidate Filtering, and Faithful Evidence

## Why V3 is required

The V2 report can look clinically polished while being technically misleading.

Confirmed issues in V2:
1. It always selects Top 12 findings, forcing abnormalities even when the study may be normal.
2. It scores four CT phases independently and then selects a phase by handcrafted clinical preference. This phase-fusion policy is not an upstream-validated RADAR inference protocol.
3. Evidence images are NOT currently tied to the actual model-scoring window. They are selected from fixed organ Z-ratios.
4. Evidence images do not robustly normalize NIfTI orientation before adding R/L markers.
5. Displayed physical Z position is estimated from slice number rather than read from the image affine/direction.
6. The conventional abdominal report template contains structures/negative statements that RADAR does not necessarily cover. Low score must never be converted into a normal statement.

V3 must prioritize technical faithfulness over a polished autonomous-looking report.

## A. Use one primary model input series

RADAR is a research model for contrast-enhanced abdominal CT.

For a multi-phase local study:

1. Detect all phases for human review.
2. Select ONE primary RADAR inference series.
3. If a diagnostic portal-venous / venous phase is present, use it as the default primary RADAR input.
4. Do NOT fuse non-contrast, arterial, venous and delayed RADAR scores into one diagnostic score.
5. Do NOT use a handcrafted "best phase per finding" score as the primary patient-level inference.
6. Other phases remain available as supplementary radiologist review images.
7. Optional experimental inference on other phases may be retained only behind an "Experimental / ngoài protocol tham chiếu" panel and must not affect the formal candidate list or conclusion.

If no suitable contrast-enhanced venous/portal-venous series can be identified confidently:
- stop automatic formal report generation;
- mark the study "không có series tham chiếu phù hợp cho RADAR";
- still allow manual image browsing.

## B. Remove forced Top-N abnormalities

Delete the rule:
`top_prioritized_findings = study_findings[:12]`

The model output for a finding is produced by a two-way softmax and the upstream demo writes the positive component.

V3 candidate display logic:

- `score >= 0.5`: "RADAR nghiêng về prompt dương tính — cần rà lại".
- `score < 0.5`: hidden from the default candidate list, but always available in the complete table.

This 0.5 is NOT a validated clinical threshold and must be visibly labeled:
"Ngưỡng 0,5 chỉ là ranh giới mô hình nghiêng về prompt dương tính so với prompt âm tính, không phải ngưỡng chẩn đoán đã hiệu chỉnh."

Do not automatically place a candidate into a final clinical conclusion merely because score >= 0.5.

## C. Human-in-the-loop report state

The report has two distinct layers.

### Layer 1 — RADAR candidates

Automatic:
- finding name;
- model score;
- primary inference phase;
- faithful model evidence;
- supplementary relevant phase images;
- review buttons: Phù hợp / Không phù hợp / Chưa chắc.

### Layer 2 — Radiologist-reviewed report

KỸ THUẬT / MÔ TẢ / KẾT LUẬN must be generated from:
- findings the radiologist explicitly marked "Phù hợp";
- optionally manually added free-text findings.

Rejected or unreviewed RADAR candidates must not silently appear in KẾT LUẬN.

If no candidate has been accepted:
- do not output "CT bình thường";
- show "Chưa có finding RADAR nào được bác sĩ xác nhận trong phiên rà soát này."

The normal abdominal CT document supplied by the user is a formatting template, not ground truth and not permission to auto-fill normal statements.

## D. Faithful evidence: remove fixed anatomical Z-ratio

Delete the use of `ORGAN_ANATOMICAL_Z_RATIO` for finding-specific evidence.

Implement true per-window evidence capture in `inference_4060.py`.

For every primary-phase sliding window:
1. retain its spatial coordinates;
2. record each finding score contributed by that window;
3. record the organ segmentation for the relevant organ in a lightweight form sufficient for evidence selection;
4. do not retain full activations.

For each candidate finding:
1. choose the actual window with the highest positive score for that finding;
2. identify the relevant organ mask within that window;
3. choose the axial slice inside that exact window with the largest organ-mask area;
4. render center slice plus adjacent slices;
5. overlay the evaluated sliding-window rectangle and optional organ contour;
6. label:
   - "Window mô hình chấm điểm cao nhất"
   - never "vị trí tổn thương" or "AI localization".

If a candidate was produced only in the fallback centered-organ second pass:
- use that exact fallback crop/window as the evidence source.

If faithful window provenance is unavailable:
- show "Không có bằng chứng không gian tin cậy từ lần inference này";
- do NOT substitute an arbitrary anatomical slice.

## E. Orientation must be real, not assumed

Before rendering evidence:
1. read NIfTI affine/direction;
2. canonicalize to a documented orientation (RAS+ or LPS) using nibabel/SimpleITK;
3. derive left/right from the canonicalized orientation;
4. use literal R and L markers, not P/T;
5. test with synthetic affine flips.

Do not assume array column 0 is patient right.

Physical slice position:
- derive from affine / SimpleITK TransformIndexToPhysicalPoint;
- do not estimate from `(index - N/2) * thickness`.

## F. Multi-phase supplementary review images

Other phases are useful for the radiologist, but they must be clearly separated from model provenance.

For each accepted/candidate finding:
- Primary model evidence: from the exact primary-phase model window.
- Supplementary review images:
  - calcification/stone -> non-contrast if available;
  - vascular/aortic candidate -> arterial if available;
  - urinary collecting system -> delayed if available;
  - otherwise venous/primary phase.

Supplementary images should be selected by anatomical organ mask / registration where feasible, not by fixed Z-ratio.

Label supplementary images:
"Ảnh thì bổ sung để bác sĩ rà soát — không dùng để tạo điểm RADAR chính."

## G. Coverage matrix

Add a visible coverage section.

For each conventional report line:
- Supported by RADAR finding(s)
- Partially supported
- Not represented in RADAR-146

Never write a normal statement for unsupported areas such as general lymph-node survey, pelvic organs, free fluid, ureters, etc. unless a supported RADAR label actually exists.

## H. Local case re-audit

After unit tests and public demo pass, re-run LOCAL_CASE_001 locally.

Do not use prior four-phase fusion scores.

Required local outputs:
- ONE `LOCAL_CASE_001_RADAR_V3.html`
- primary inference phase explicitly recorded as a safe alias;
- automatic candidate count based on score >= 0.5;
- each candidate has faithful highest-scoring-window evidence;
- supplementary phase images separated from model evidence;
- reviewed formal MÔ TẢ/KẾT LUẬN initially excludes unreviewed candidates.

Also create a LOCAL-ONLY audit CSV/JSON containing:
- finding;
- score;
- candidate yes/no;
- radiologist review status;
- optional note.

Never push this patient-derived audit file to GitHub.

## I. Tests

Required tests:
1. no forced Top-N candidates;
2. score 0.49 hidden by default, score 0.50 included as model-positive-prompt candidate;
3. no candidate auto-enters final conclusion before radiologist acceptance;
4. primary phase selection prefers portal-venous/venous and does not fuse scores;
5. experimental other-phase score cannot change primary score;
6. evidence slice originates from the recorded highest-scoring window;
7. fixed anatomical Z-ratio path is removed for finding evidence;
8. unavailable provenance produces an explicit no-evidence state, not fabricated image;
9. R/L orientation survives synthetic axis flips;
10. physical slice position comes from affine/direction;
11. coverage matrix prevents unsupported normal statements;
12. local patient output remains fully offline and PHI-free on GitHub.
