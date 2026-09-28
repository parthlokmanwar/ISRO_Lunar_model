# PPT Revision Plan — AstroBytes / SIH26166

Source audited: `Serial_No_3_AstroBytes(CR 43)  (1).pdf`, the submitted six-slide deck. Status and numbers below are based on the fixed Round 2/3/4 evaluation documented in `docs/FINDINGS.md`, `docs/EXPERIMENT_LOG.md`, and `docs/REQUIREMENTS_SCORECARD.md`.

Use this document as the copy-paste plan for one revised six-slide deck. Keep the existing AstroBytes and SIH visual identity, but make the evidence boundary visible on the slide itself. Do not claim a capability as implemented merely because it is a planned stage or a cited paper.

## Slide 1 — Title

### Bullet: SMART INDIA HACKATHON 2026
STATUS: TRUE.
NEW: Keep: `SMART INDIA HACKATHON 2026`.
WHY: This is the event identity, not a technical claim.
FIGURE: None.

### Bullet: Problem Statement ID – SIH26166
STATUS: TRUE.
NEW: Keep: `Problem Statement ID — SIH26166`.
WHY: Matches the submitted problem statement.
FIGURE: None.

### Bullet: Multi-modal, Sun angle and scale invariant image correspondence using Chandrayaan-2 optical images (OHRC, TMC and IIRS)
STATUS: FIX WORDING.
NEW: `Reliable Chandrayaan-2 image correspondence across sensors, scale, viewpoint and tested illumination conditions` with the smaller subtitle `OHRC, TMC-2 and IIRS evidence; illumination robustness is partial and measured`.
WHY: The current system addresses multi-sensor, scale and viewpoint cases, but F13 measures a practical illumination boundary between 60° and 75° in the tested scenes. “Invariant” overstates the result.
FIGURE: Use a small three-sensor input strip only if it is already present; no new figure is required.

### Bullet: Theme — Space Technology
STATUS: TRUE.
NEW: Keep: `Theme — Space Technology`.
WHY: Administrative metadata.
FIGURE: None.

### Bullet: PS Category — Software
STATUS: TRUE.
NEW: Keep: `PS Category — Software`.
WHY: Administrative metadata.
FIGURE: None.

### Bullet: Team Name — AstroBytes
STATUS: TRUE.
NEW: Keep: `Team AstroBytes`.
WHY: Team identity.
FIGURE: None.

## Slide 2 — Proposed Solution

### Bullet: Perceive → Verify (two-stage strategy)
STATUS: FIX WORDING.
NEW: `Perceive → cross-check → register`.
WHY: The implemented reliability gate is agreement between two independent matchers, followed by geometric filtering. The old “verify” wording suggests the unimplemented crater-pattern verifier.
FIGURE: Use `eval/figures/ppt_selects/rmse_vs_truth.png` beside the agreement-gate explanation; evidence F1.

### Bullet: Not a black-box model — a perceive-then-verify approach for higher reliability
STATUS: FIX WORDING.
NEW: `A fixed, auditable two-matcher policy: DISK+LightGlue and SIFT+FLANN, followed by geometric checks and agreement gating.`
WHY: This is more precise than a general black-box contrast and names the actual policy used in the evaluation.
FIGURE: None required; a simple two-branch diagram is enough.

### Bullet: Multi-instrument input — Chandrayaan-2 images from OHRC, TMC and IIRS with different resolutions and sun angles
STATUS: TRUE WITH LIMIT.
NEW: `Inputs: OHRC, TMC-2 and IIRS products with different resolution, modality and acquisition conditions. IIRS NIR↔SWIR and OHRC→TMC-2 sensor-model tests are measured; direct OHRC↔IIRS/TMC↔IIRS overlap is not in the current archive.`
WHY: F4 and F7 support the tested cases, while the scorecard marks full cross-instrument coverage PARTLY because the archive has no direct OHRC/IIRS or TMC/IIRS overlap.
FIGURE: Use `eval/figures/ppt_selects/checkerboard_cross_sensor.png` for OHRC→TMC-2 and `eval/figures/ppt_selects/iirs_matches.png` for IIRS bands.

### Bullet: Sensor-aware preprocessing corrects brightness, contrast, resolution and sensor differences to bring all images to a common form
STATUS: FIX WORDING.
NEW: `Sensor-aware preprocessing: PDS4 metadata, radiometric handling, resolution/footprint alignment and instrument-specific preparation.`
WHY: Avoid promising a universal normalization step. Shadow normalization was tested, improved one 45° case, but did not improve held-out DISK success and is not adopted.
FIGURE: Use `eval/figures/ppt_selects/illumination_sweep_round4_shadow_norm.png` only with the caption `tested, not adopted`; evidence F13.

### Bullet: Perception: Feature Matching — Pretrained SuperPoint detects key points; SuperGlue matches them across scale, rotation and viewpoint
STATUS: CONTRADICTED.
NEW: `Perception: DISK detects learned features; LightGlue matches them. SIFT+FLANN is the independent classical comparator.`
WHY: SuperPoint/SuperGlue are not the current implementation. The deck must not state that they ran. LightGlue is used through Kornia; SIFT+FLANN is used through OpenCV.
FIGURE: None required.

### Bullet: Verification: Crater-Pattern Check — validate matches using spatial relationships among nearby craters
STATUS: UNSUPPORTED.
NEW: `Cross-check: retain geometrically consistent matches and confirm only when DISK+LightGlue and SIFT+FLANN agree within the fixed policy.`
WHY: A crater-pattern verifier is not implemented. F1 shows the actual agreement gate: 99% right, 1 wrong in 106 accepted confirmations; F2 records 52/52 CONFIRMED answers right on the held-out evaluation.
FIGURE: Use `eval/figures/ppt_selects/rmse_vs_truth.png`; caption `low RMSE alone can be wrong; independent agreement is the reliability gate`.

### Bullet: Robust under extreme illumination
STATUS: CONTRADICTED.
NEW: `Measured illumination result: DISK succeeds 5/5 at 0°, 4/5 at 45°, 3/5 at 60°, and 0/5 at 75° or more in the Round 4 simulated sweep.`
WHY: F13 shows partial robustness, not extreme-illumination invariance. Shadow normalization changes 45° from 4/5 to 5/5 but does not move the 75° boundary; held-out DISK remains 5/14.
FIGURE: Use `eval/figures/ppt_selects/illumination_sweep_round4_baseline.png` and, optionally, the shadow-normalized figure as a negative result.

### Bullet: Refinement & Output — Sub-pixel precision, evenly spread matches
STATUS: FIX WORDING.
NEW: `Output: registered image, overlay, keypoints, matches, inliers, homography and CSV/JSON export. Report precision, true/held-out error, agreement and grid coverage separately.`
WHY: The API outputs these artifacts. A dedicated sub-pixel refinement stage is not implemented. Sub-pixel results are measured under stated conditions: scale, viewpoint/zoom, IIRS bands and real-data precision, not universal source-image accuracy.
FIGURE: Use `eval/figures/ppt_selects/real_ohrc_checkerboard.png` for real-data inspection, with the caption `agreement/precision, not ground-truth accuracy`.

### Bullet: IISRO's Space Applications Centre (2025) found even top matching methods lose accuracy under harsh lighting — our solution directly targets this gap
STATUS: FIX WORDING.
NEW: `The 2025 ISRO study motivates the problem. Our evaluation measures where the fixed DISK/SIFT policy works and where illumination remains unresolved.`
WHY: Correct the typo to `ISRO`, cite the study as motivation, and avoid implying that the current system closes the harsh-lighting gap.
FIGURE: None required; cite `arXiv:2509.04775` in the footer.

### Bullet: Illumination variation — crater spatial patterns stay stable across sun angles → handled by verification
STATUS: CONTRADICTED.
NEW: `Illumination variation: learned matching tolerates the tested 45° change and partly 60°; the measured boundary is between 60° and 75°. Crater-pattern verification is future work.`
WHY: No crater-pattern verification exists in the implementation, and the measured result does not support “handled” across sun angles.
FIGURE: `illumination_sweep_round4_baseline.png`, evidence F13.

### Bullet: Viewpoint and scale variation — perception stage (SuperPoint + SuperGlue) recognizes features despite shift, rotation, or zoom
STATUS: FIX WORDING.
NEW: `Viewpoint/scale: SIFT succeeds 32/32 across the tested rotation/zoom sweep; DISK is sub-pixel through 30° rotation and 2× zoom but fails at 90° and 180° without pre-rotation. At the true OHRC→TMC-2 ratio, ≥~275 TMC-2 pixels of shared ground gives 6/6 success for both matchers.`
WHY: Replace the wrong model names and universal claim with F4/F5 limits.
FIGURE: Use `eval/figures/ppt_selects/checkerboard_cross_sensor.png`; cite F4/F5 in the footer.

### Bullet: Cross-instrument matching (OHRC ↔ TMC ↔ IIRS) — sensor-aware preprocessing makes all three cameras comparable
STATUS: FIX WORDING.
NEW: `Measured multimodal cases: OHRC→TMC-2 sensor-model registration and IIRS NIR↔SWIR band matching. Full three-instrument overlap remains untested because the current archive has no direct common footprint.`
WHY: This preserves the demonstrated work without claiming a result that the data cannot support.
FIGURE: `checkerboard_cross_sensor.png` and `iirs_matches.png`.

### Bullet: Sub-pixel accuracy & uniform match distribution — dedicated refinement ensures sub-pixel precision and matches spread across the full image
STATUS: CONTRADICTED.
NEW: `Measured precision and coverage: sub-pixel results hold in the stated derived/IIRS conditions; grid coverage is strong on textured terrain and falls on smooth mare. No dedicated refinement guarantee.`
WHY: F12 reports DISK coverage of 14/14 for F1, 39/60 for F2 and 14/14 for F5 at ≥12/16 grid cells; F10 reports high-texture success 18/20 versus 11/20 for low and mid texture.
FIGURE: Use `eval/figures/ppt_selects/tmc_stereo_residuals.png` only for the terrain/stereo caveat; no new figure needed for grid coverage.

### Bullet: Reliability, not just accuracy — confidence filtering + RANSAC remove inconsistent matches → output is reliable, not just numerous
STATUS: FIX WORDING.
NEW: `Reliability gate: confidence filtering, RANSAC/geometric consistency, and independent matcher agreement. Confirmed answers were right 52/52 on the held-out evaluation; unconfirmed means unresolved, not automatically wrong.`
WHY: This is the measured behavior in F1/F2 and avoids equating an inlier fit with truth.
FIGURE: `rmse_vs_truth.png`.

### Bullet: Crater-relationship verification; uses terrain structure for robust matching, inspired by 2025 research
STATUS: UNSUPPORTED.
NEW: `Future extension: terrain-aware or crater-aware verification after a separately evaluated implementation.`
WHY: The concept is not part of the current tested pipeline.
FIGURE: None; do not show a crater-verification result that was not measured.

### Bullet: Built on ISRO's 2025 findings — extends the validated SuperGlue approach to solve the illumination weakness
STATUS: CONTRADICTED.
NEW: `Built on the ISRO study as problem context; current implementation uses DISK+LightGlue and SIFT+FLANN, and reports the remaining illumination limit.`
WHY: The ISRO paper is literature context, not validation of the current implementation or a license to claim SuperGlue was used.
FIGURE: None required.

### Bullet: Focused on Chandrayaan-2 challenge — specifically designed for OHRC, TMC and IIRS cross-instrument alignment
STATUS: FIX WORDING.
NEW: `Focused on Chandrayaan-2: tested OHRC, TMC-2 and IIRS products, with direct cross-instrument coverage limited by the available footprints.`
WHY: Matches the actual archive and R4 scorecard status.
FIGURE: `checkerboard_cross_sensor.png` and `iirs_matches.png`.

### Bullet: Precise, Reliable, Practical — sub-pixel accuracy, verified matches, and built using pretrained models with available resources
STATUS: FIX WORDING.
NEW: `Auditable and practical: CPU-only inference, measured agreement, registered products and explicit failure limits.`
WHY: “Sub-pixel” and “verified” need conditions; CPU performance is directly measured in F11.
FIGURE: None required.

## Slide 3 — Technical Approach

### Bullet: Input data — Chandrayaan-2 multi-sensor imagery: OHRC ~0.32 m, TMC ~5 m, IIRS representative band/PCA to 2D
STATUS: FIX WORDING.
NEW: `Input data: OHRC, TMC-2 and IIRS Chandrayaan-2 products. Use the product metadata and PDS4 labels; show the IIRS representation actually used in the evaluation.`
WHY: Keep the sensor context, but avoid implying that every product is directly co-registered or that PCA is a universal production step.
FIGURE: Keep the existing sensor thumbnails if they are real project data.

### Bullet: Sensor-Aware Preprocessing — radiometric correction, geometric correction, noise reduction, resolution alignment, illumination/shadow handling, IIRS band selection/PCA
STATUS: FIX WORDING.
NEW: `Preprocessing: PDS4 label/data read, numeric scaling, instrument-aware crop/resize and band selection for the evaluated IIRS pair. Shadow normalization was evaluated as an experiment and is not the production default.`
WHY: This describes the code path and the F13 decision without promising every listed operation for every input.
FIGURE: None required.

### Bullet: Multi-Modal Representation — texture features, edges, structural terrain cues, multi-scale features, spectral information for IIRS
STATUS: FIX WORDING.
NEW: `Image preparation for matching: grayscale/radiometric views and instrument-specific bands feed the learned and classical matchers. No trained multimodal CNN representation is part of the current pipeline.`
WHY: The deck presents a learned multimodal representation that does not exist as a measured component.
FIGURE: `iirs_matches.png` for the actual NIR/SWIR case.

### Bullet: Learned Correspondence Matching — SuperPoint + SuperGlue (primary); LoFTR / RIFT2 (alternatives)
STATUS: CONTRADICTED.
NEW: `Correspondence matching — DISK + LightGlue (primary); SIFT + FLANN (independent comparator). LoFTR was probed but blocked before inference by pretrained-weight certificate verification; RIFT2 was not installed or tested.`
WHY: This is the actual stack and an honest account of the alternatives.
FIGURE: None required.

### Bullet: Confidence + Geometric Verification — confidence filtering, RANSAC, geometrically consistent inliers
STATUS: TRUE WITH REFRAME.
NEW: `Confidence and geometry: filter matcher outputs, estimate a transform with MAGSAC++, retain geometrically consistent inliers, then apply the fixed cross-matcher agreement policy.`
WHY: This is implemented. Replace generic “verification” with the concrete operations.
FIGURE: `rmse_vs_truth.png`.

### Bullet: Sub-pixel Refinement — local neighbourhood refinement, fine positional adjustment, sub-pixel coordinates
STATUS: UNSUPPORTED.
NEW: `Quality reporting: compute reprojection RMSE, true/held-out error where truth exists, inter-method agreement, precision and grid coverage. Mark sub-pixel outcomes as condition-dependent.`
WHY: No dedicated refinement stage is implemented, so it cannot be shown as a pipeline step.
FIGURE: `real_ohrc_checkerboard.png` only with the real-data precision caveat.

### Bullet: Spatial Distribution Check — image grid analysis, coverage analysis, select reliable distributed matches
STATUS: TRUE WITH LIMIT.
NEW: `Spatial coverage check: report whether inliers cover ≥12 of 16 grid cells; coverage is strong on textured terrain and weaker on smooth mare.`
WHY: This is supported by F10/F12, but it is a measurement and selection criterion, not a universal guarantee.
FIGURE: Use a small 4×4 grid overlay if already available; otherwise no new figure is required.

### Bullet: Geometric Registration — estimate affine/homography/RPC, warp source to reference, generate registered lunar image
STATUS: FIX WORDING.
NEW: `Geometric registration: estimate the supported transform, warp the source to the reference, and return the registered image plus match/inlier metadata. For TMC fore/nadir stereo, interpret structured residuals as parallax and prefer disparity/DEM work over a single homography.`
WHY: The API returns a registered product, but F9 shows that one plane cannot model all stereo terrain.
FIGURE: Use `real_ohrc_overlay.png` and `tmc_stereo_residuals.png`.

### Bullet: Output — registered multi-sensor lunar imagery; reliable correspondence points; evaluation metrics (RMSE, MAE, SSIM); visual overlays
STATUS: FIX WORDING.
NEW: `Output: registered image, overlay, keypoints, matches, inliers, transform and CSV/JSON export. Metrics: RMSE, inlier count/ratio, true or held-out error, cross-method agreement, map precision and grid coverage.`
WHY: These are the outputs the API and evaluation actually provide. Do not present SSIM or sub-pixel truth as a validated universal result unless it is computed for the shown example.
FIGURE: `real_ohrc_overlay.png`, `real_ohrc_checkerboard.png`, and `rmse_vs_truth.png`.

### Bullet: Technology stack — Python/C++; SuperPoint, SuperGlue, LoFTR, RIFT2; speech/LLM/TTS; NumPy/SciPy/Rasterio/GDAL/Matplotlib; OpenCV/PyTorch/Whisper/Coqui TTS/LiveKit; FastAPI/Flask/Docker/Linux; NVIDIA GPU; VS Code/Jupyter/Git/GitHub
STATUS: CONTRADICTED / STALE.
NEW: `Technology stack: Python; DISK; LightGlue via Kornia; SIFT+FLANN and image operations via OpenCV; MAGSAC++; NumPy/PyTorch; custom PDS4 reader; FastAPI; CPU-only execution. Development: VS Code/Jupyter/Git where applicable.`
WHY: Remove named components not used in the evaluated pipeline: SuperPoint, SuperGlue, LoFTR, RIFT2, Whisper, Rasterio, GDAL, Docker, GPU, voice assistant/chatbot and C++ performance module. “CPU-only” is supported by F11: both matchers cost approximately 2.7 seconds per pair on the measured Intel Raptor Lake machine.
FIGURE: None required.

## Slide 4 — Feasibility and Viability

### Bullet: Technical feasibility — High. SuperPoint/LightGlue (pretrained, open-source, ISRO-validated) + crater spatial-pattern verification
STATUS: CONTRADICTED.
NEW: `Technical feasibility — demonstrated fixed CPU pipeline: DISK+LightGlue plus SIFT+FLANN, MAGSAC++ geometry and agreement gating. Crater-pattern verification is future work.`
WHY: SuperPoint and crater verification are not the measured implementation. “ISRO-validated” should not be attached to the current model stack.
FIGURE: `rmse_vs_truth.png`.

### Bullet: Data feasibility — High. OHRC, TMC, IIRS imagery + DEM tiles + metadata available on ISRO's Pradan portal. No access blockers.
STATUS: FIX WORDING.
NEW: `Data feasibility — demonstrated for the six local Chandrayaan-2 products and their labels. Current archive includes OHRC, TMC-2 and IIRS evidence; no direct OHRC/IIRS or TMC/IIRS overlap, and no DEM ground-truth validation.`
WHY: The project data is usable, but “no access blockers” and “DEM tiles available” are too broad for the evidence used here.
FIGURE: Use the actual sensor figure only; do not imply an overlapping DEM was used.

### Bullet: Timeline feasibility — Realistic. Working prototype (pretrained, no training) within hackathon. Fine-tuning and cross-modal fusion post-hackathon.
STATUS: FIX WORDING.
NEW: `Timeline feasibility — the working prototype runs with pretrained DISK and LightGlue plus classical SIFT+FLANN; fine-tuning, direct cross-instrument overlap and terrain-aware verification remain follow-on work.`
WHY: This separates current delivery from future work and removes the implied SuperPoint/SuperGlue system.
FIGURE: None.

### Bullet: Infrastructure feasibility — High. Inference is lightweight; full training/fine-tuning needs far less compute than ISRO's existing systems.
STATUS: FIX WORDING.
NEW: `Infrastructure feasibility — CPU-only inference is measured: SIFT+FLANN 0.22 s per 1024 px pair, DISK+LightGlue 2.1–2.5 s, and both matchers approximately 2.7 s per pair.`
WHY: F11 supports a concrete claim; comparative claims about ISRO infrastructure are not measured here.
FIGURE: No figure required; put F11 in a small callout.

### Bullet: Deployment viability — slots into ISRO's existing pipeline as a preprocessing/registration layer feeding tools like ISIS (non-rip & replace)
STATUS: FIX WORDING.
NEW: `Deployment viability — FastAPI exposes registration and evidence outputs as a separable preprocessing/registration service. ISIS integration is a future adapter, not used in this evaluation.`
WHY: ISIS is cited but not part of the current implementation. Avoid claiming an existing pipeline integration.
FIGURE: None.

### Bullet: Maintenance viability — built on actively maintained open-source libraries (Kornia, OpenCV)
STATUS: TRUE WITH REFRAME.
NEW: `Maintenance viability — current implementation depends on Kornia/PyTorch, OpenCV and a small custom PDS4 reader; pin versions and preserve the evaluation harness.`
WHY: This is accurate and more useful for reproducibility.
FIGURE: None.

### Bullet: Scalability viability — generalizes across image pairs and regions without per-region tuning — full archive scaling, not redesign
STATUS: FIX WORDING.
NEW: `Scalability viability — one fixed policy was evaluated across 6 families, 211 locations and 3 sensors; claims remain bounded by tested footprints, texture and illumination.`
WHY: R10 supports the fixed-policy result, but not unrestricted full-archive generalization.
FIGURE: Use `real_ohrc_overlay.png` or `iirs_matches.png` as examples, not as proof of all archive coverage.

### Bullet: Illumination extremes — near-terminator vs near-noon shots can distort shadows and weaken geometry-based verification
STATUS: TRUE WITH REFRAME.
NEW: `Illumination extremes — shadow changes weaken correspondence. Round 4 measures DISK at 5/5, 4/5, 3/5, then 0/5 across 0°, 45°, 60°, 75°; ≥75° is not solved in these scenes.`
WHY: Keep the risk, but remove the implication that crater geometry currently resolves it.
FIGURE: `illumination_sweep_round4_baseline.png`.

### Bullet: Cross-instrument resolution gap — IIRS lower resolution vs OHRC high resolution; naive normalization can lose IIRS spectral value
STATUS: TRUE WITH LIMIT.
NEW: `Cross-instrument resolution/modality gap — OHRC→TMC-2 is evaluated with a sensor model; IIRS NIR↔SWIR is evaluated band-to-band. Direct three-instrument overlap is untested.`
WHY: This matches F4/F7 and the R4 scorecard.
FIGURE: `checkerboard_cross_sensor.png` and `iirs_matches.png`.

### Bullet: Sparse-feature terrain — flat mare regions or eroded terrain weaken both perception and verification
STATUS: TRUE.
NEW: `Sparse-feature terrain — high texture succeeds 18/20; low and mid texture each succeed 11/20. Coverage drops on smooth mare.`
WHY: F10 provides the measured feasibility limit.
FIGURE: `tmc_stereo_residuals.png` only if its caption emphasizes terrain residuals; otherwise use the existing terrain thumbnails.

### Bullet: Pretrained-model domain gap — base models trained on Earth imagery, validated as best-available but not identical to lunar terrain
STATUS: TRUE WITH REFRAME.
NEW: `Pretrained-model domain gap — DISK is used without lunar fine-tuning; performance is measured on Chandrayaan-2-derived and real data, with illumination, viewpoint and texture limits reported.`
WHY: This is the honest risk statement; “validated as best available” is not itself a result.
FIGURE: None required.

### Bullet: Strategies to overcome challenges — two-stage design; when brightness-based perception weakens, geometry-based verification (crater spatial relationships, lighting-invariant) keeps working
STATUS: CONTRADICTED.
NEW: `Current strategy — use two independent matchers and agreement gating; report unresolved cases. Future strategy — evaluate terrain/crater-aware or illumination-invariant representations against held-out data.`
WHY: The stated crater/lighting-invariant verifier does not exist and cannot be shown as a working remedy.
FIGURE: `rmse_vs_truth.png`.

### Bullet: Strategies — sensor-aware preprocessing per instrument
STATUS: TRUE WITH LIMIT.
NEW: `Current strategy — instrument-aware reading, scaling, crop/resize and band preparation; preserve the original labels and sensor metadata.`
WHY: Accurate and implementable without overclaiming universal harmonization.
FIGURE: `checkerboard_cross_sensor.png`.

### Bullet: Strategies — confidence-scoring stage flags low-confidence regions explicitly instead of silent weak matches
STATUS: TRUE WITH REFRAME.
NEW: `Current strategy — expose matcher confidence, geometric status, agreement status and coverage in the output; label non-confirmed results as unresolved.`
WHY: Better aligned with F1/F2 than the vague “low confidence” claim.
FIGURE: `rmse_vs_truth.png`.

### Bullet: Strategies — DEM-based synthetic fine-tuning (Phase 2) using ISRO's DEM data to create lunar-specific training pairs
STATUS: FUTURE.
NEW: `Future work — DEM-based synthetic pairs and lunar-specific fine-tuning, subject to acquiring suitable DEM overlap and validating on held-out scenes.`
WHY: No such fine-tuning was used in the current results.
FIGURE: None; label this as future work, not a completed strategy.

## Slide 5 — Impact and Benefits

### Bullet: Reliable Lunar Image Registration → Better Maps → Smarter Decisions
STATUS: FIX WORDING.
NEW: `Measured registration evidence → better-aligned image products → better-supported analysis`.
WHY: “Smarter decisions” is too broad for the measured prototype; keep the impact chain tied to the registered product.
FIGURE: Use `real_ohrc_overlay.png` as the hero evidence.

### Bullet: Image 1 + Image 2 → Registered Image; different sun angle/illumination/viewpoint → AI matching → one consistent lunar view
STATUS: FIX WORDING.
NEW: `Two lunar observations → fixed matching and geometric registration → registered image plus correspondence evidence. Show the conditions for the example and do not label every case “consistent.”`
WHY: F13 shows illumination limits, and F9 shows stereo parallax limits.
FIGURE: `real_ohrc_overlay.png` and `real_ohrc_checkerboard.png`.

### Bullet: ISRO & Space Research Community — enables high-precision lunar basemaps for landing-site assessment, hazard mapping and mission planning; supports long-term monitoring and change detection
STATUS: UNSUPPORTED / TOO STRONG.
NEW: `ISRO and space research — provides a reproducible registration/evidence layer for research datasets and multi-temporal inspection. Landing-site assessment, hazard mapping and change detection are future applications, not validated outputs.`
WHY: The project did not validate landing or hazard decisions.
FIGURE: `real_ohrc_overlay.png`, captioned as a registration demonstration.

### Bullet: Lunar Scientists & Researchers — facilitates cross-instrument data fusion (OHRC, TMC, IIRS) for geological and mineralogical studies; helps discover new lunar features and scientific insights
STATUS: FIX WORDING.
NEW: `Lunar researchers — supports tested OHRC/TMC-2 sensor-model registration and IIRS NIR↔SWIR correspondence, with direct three-instrument fusion left as future work.`
WHY: This keeps the scientific use case proportional to the data coverage.
FIGURE: `checkerboard_cross_sensor.png` and `iirs_matches.png`.

### Bullet: Mapping & Data Teams — reduces registration errors and improves spatial accuracy (sub-pixel level) with high inlier ratio and low RMSE; provides consistent reliable multi-temporal lunar datasets
STATUS: FIX WORDING.
NEW: `Mapping/data teams — receive registered images and match metadata with RMSE, inliers, agreement, precision and coverage. Sub-pixel performance is condition-dependent; real OHRC results show 0.09 px map precision and 0.47 px inter-method agreement, not ground-truth accuracy.`
WHY: F8 distinguishes real-data precision/agreement from unavailable real-data truth.
FIGURE: `real_ohrc_checkerboard.png` and `rmse_vs_truth.png`.

### Bullet: Future Lunar Missions — reusable registration layer for multi-mission, multi-instrument datasets; supports autonomous navigation and precision landing systems
STATUS: FUTURE / UNSUPPORTED.
NEW: `Future missions — the API shape could support additional sensors after acquiring overlapping reference data and validating the new domain. Autonomous navigation and precision landing are outside the current evidence.`
WHY: R11 is NOT MET: no LRO NAC or SELENE product was acquired or evaluated.
FIGURE: None; do not show LRO/SELENE as current data.

### Bullet: Social benefit — drives STEM interest; creates research/internship opportunities; builds India's global reputation
STATUS: LOW-VALUE / UNSUPPORTED.
NEW: `Replace this box with: reproducible evidence, explicit failure reporting and reusable registration outputs for lunar-data research.`
WHY: The social claims are generic and do not strengthen the technical submission.
FIGURE: None.

### Bullet: Economic benefit — lowers mission costs; reduces manual effort; supports commercial space ecosystem
STATUS: LOW-VALUE / UNSUPPORTED.
NEW: `Replace this box with: CPU-only prototype runtime and a separable API reduce the operational barrier to testing registration workflows; mission-cost savings are not measured.`
WHY: F11 supports runtime, not economic savings.
FIGURE: None.

### Bullet: Environmental benefit — identify lunar resources and water ice; understand lunar climate evolution; support sustainable space missions
STATUS: UNSUPPORTED.
NEW: `Replace this box with: better-aligned imagery can support later scientific analysis, but resource detection, water-ice identification and climate conclusions were not evaluated.`
WHY: These outcomes are outside the current experiments.
FIGURE: None.

### Bullet: Technology & long-term benefit — advances multimodal AI/geospatial technology; reusable framework for Moon/Mars; positions India as global leader
STATUS: FIX WORDING.
NEW: `Technology benefit — a reusable, CPU-only registration API and evaluation harness with explicit metrics and failure boundaries. Extension beyond Chandrayaan-2 remains future work.`
WHY: This is supported by the artifact, while Moon/Mars generalization and leadership claims are not experimentally established.
FIGURE: Use a small API/output schematic, not a planetary application claim.

### Bullet: National & strategic advantage — strengthens India's leadership; enables self-reliant solutions for future lunar/interplanetary missions
STATUS: UNSUPPORTED.
NEW: `Reproducible national capability — uses Chandrayaan-2 data, open libraries and an auditable evaluation path; future mission transfer requires new overlap data and validation.`
WHY: Keeps the national relevance without claiming strategic outcomes the prototype did not measure.
FIGURE: None.

## Slide 6 — Research and References

### Bullet: ISRO is already researching this exact problem — SAC scientists published a 2025 study testing image-matching methods on real Chandrayaan-2 data
STATUS: TRUE AS CONTEXT.
NEW: `ISRO/SAC published a 2025 Chandrayaan-2 image-matching study; cite it as problem context and comparison literature, not as validation of our implementation.`
WHY: This is supported by the cited paper, but the deck must distinguish the paper's experiments from ours.
FIGURE: None.

### Bullet: Classical methods (SIFT, ASIFT, AKAZE) degrade near the poles, where lunar lighting is harsh — confirmed by that same ISRO study
STATUS: TRUE AS LITERATURE CONTEXT.
NEW: `The cited study motivates illumination-aware evaluation. Our own F13 sweep measures a separate fixed-pipeline boundary: DISK 4/5 at 45°, 3/5 at 60°, and 0/5 at 75° in the tested scenes.`
WHY: Do not present a literature result as if it were our exact experiment.
FIGURE: `illumination_sweep_round4_baseline.png`.

### Bullet: SuperGlue gave the most accurate, fastest results of everything ISRO tested — directly validates our technology choice
STATUS: CONTRADICTED.
NEW: `Literature context: the ISRO paper compares methods by its own protocol. Current implementation choice: DISK+LightGlue with SIFT+FLANN as an independent cross-check.`
WHY: SuperGlue did not run in this project, and literature performance does not validate the current implementation.
FIGURE: None.

### Bullet: Existing tools (ISIS, Ames Stereo Pipeline) already support Chandrayaan-2 but rely on the same classical matching that struggles under harsh lighting
STATUS: UNSUPPORTED.
NEW: `Related tools: ISIS/Ames Stereo Pipeline may be relevant integration references; neither is used in the current evaluation. The current prototype uses a custom PDS4 reader and FastAPI.`
WHY: The deck should not claim internals or integration that were not inspected and measured here.
FIGURE: None.

### Bullet: Permanently shadowed polar regions get zero sunlight — a genuine physical limit of the field, not a flaw in our approach
STATUS: TRUE GENERAL FACT, BUT OUT OF SCOPE.
NEW: `Physical boundary: permanently shadowed regions may lack usable optical correspondence. Separately, our tested illumination limit reaches 0/5 DISK success at 75° and beyond in the Round 4 scenes.`
WHY: Keep the physical context, but distinguish it from the measured algorithmic limit.
FIGURE: `illumination_sweep_round4_baseline.png` if space permits.

### Bullet: SuperGlue — AI matching model used in our solution
STATUS: CONTRADICTED.
NEW: `DISK + LightGlue — learned matcher used in the current solution. SuperGlue — literature context only.`
WHY: Correct the implementation record.
FIGURE: None.

### Bullet: LoFTR — AI matching model used in our solution
STATUS: CONTRADICTED.
NEW: `LoFTR — attempted as an evaluation probe, but pretrained weights were blocked before inference by certificate verification; not used in reported results.`
WHY: Honest experiment status; do not imply a LoFTR result.
FIGURE: None.

### Bullet: ISIS Software — existing NASA/USGS tool for Moon image processing
STATUS: FIX WORDING.
NEW: `ISIS — related external tool/reference; not used in the current pipeline. Current data access uses a custom PDS4 reader.`
WHY: Avoid presenting a reference tool as a project dependency.
FIGURE: None.

### Bullet: ISRO Chandrayaan-2 data — pradan.issdc.gov.in
STATUS: TRUE.
NEW: `Data used: Chandrayaan-2 OHRC, TMC-2 and IIRS products obtained from the ISRO/PRADAN archive; list the six local products only if the slide has room.`
WHY: This is the actual data source and should be the primary data reference.
FIGURE: None.

### Bullet: NASA Moon images (LRO) — lroc.sese.asu.edu
STATUS: FIX WORDING.
NEW: `Future reference data: LRO NAC overlap to be acquired for the PS lunar-reference-image requirement; not used in this evaluation.`
WHY: R11 is NOT MET because no LRO/SELENE reference product was acquired.
FIGURE: None.

### Bullet: Japan's Moon data (SELENE) — darts.isas.jaxa.jp/planet/pdap/selene
STATUS: FIX WORDING.
NEW: `Future reference data: SELENE overlap is an alternative to LRO; not used in this evaluation.`
WHY: Same R11 limitation.
FIGURE: None.

## Metrics available for use anywhere in the deck or in Q&A

Use the exact condition beside every number. Do not combine a derived/simulated result with a real-data result without labeling it.

- **F1 reliability:** RMSE < 1.5 px alone was 75% right; 38 accepted results were wrong, with some errors up to 35,000 px. DISK+LightGlue and SIFT agreement within 3 px plus ≥15 inliers was 99% right, 1 wrong in 106.
- **F2 held-out policy:** 84% success versus SIFT 76% and DISK 67%; precision 97%; CONFIRMED answers were right 52/52. The policy rejects some right-but-single-matcher cases as UNCONFIRMED.
- **F3 defect correction:** real OHRC inliers improved from 15 to 1051 after fixing the LightGlue score/distance interpretation; current real OHRC example is 1051/1094 with RMSE 1.24 px.
- **F4 scale:** at the true OHRC→TMC-2 ratio, approximately 275 TMC-2 pixels of shared ground gives 6/6 success for both matchers and median true error 0.26 px; 2.6 km footprint gives 6/6 with 0.07–0.09 px median error.
- **F5 viewpoint:** SIFT 32/32 across the tested rotation/zoom sweep; DISK is sub-pixel through 30° rotation and 2× zoom, then 0/8 at 90° and 180°.
- **F7 IIRS:** DISK 14/14 for IIRS NIR↔SWIR band matching, 13/14 sub-pixel, median 0.65–0.77 px; SIFT 8/14 with 3 confident wrong answers.
- **F8 real OHRC revisit:** 2021-04-02 to 2024-03-30, 14/14 locked tiles succeed; inter-method agreement median 0.47 px; map precision 0.09 px; per-point held-out error 1.4 px. This is not real-data ground-truth accuracy.
- **F9 real TMC stereo:** 40/60 SUCCESS for both matchers; 20 MARGINAL have structured residuals with coherence 0.77 versus 0.36 on SUCCESS tiles, consistent with parallax.
- **F10 terrain:** high texture 18/20 success; low and mid texture 11/20 each.
- **F11 CPU runtime:** SIFT+FLANN 0.22 s per 1024 px pair; DISK+LightGlue 2.1–2.5 s; both matchers approximately 2.7 s per pair; no GPU/CUDA.
- **F12 uniformity:** ≥12/16 grid cells: DISK F1 14/14, F2 39/60, F5 14/14; SIFT F1 14/14, F2 42/60.
- **F13 illumination:** baseline DISK by azimuth 0°/45°/60°/75°/90°/135°/180°: 5/5, 4/5, 3/5, 0/5, 0/5, 0/5, 0/5. Shadow normalization: 5/5, 5/5, 3/5, 0/5, 0/5, 0/5, 0/5. Held-out DISK remains 5/14, so shadow normalization is not adopted.
- **Scorecard summary:** R1 illumination PARTLY; R2 viewpoint MET for tested rotation/zoom with SIFT or pre-rotation and PARTLY for real stereo; R3 scale MET above the footprint limit; R4 multimodal PARTLY; R5 different times MET where overlap is real; R6 sub-pixel MET with truth and PARTLY on real data; R7 uniformity MET on textured terrain and PARTLY on smooth mare; R8 registered product MET; R9 metrics MET and extended; R10 fixed-policy generalization MET within tested families; R11 non-Chandrayaan lunar reference data NOT MET.

## Figures needing generation (if any)

None. All figures referenced above already exist in `eval/figures/ppt_selects/` and are listed in its manifest. If a new illumination figure is desired, regenerate it with:

```powershell
python scripts/eval/plot_illumination_round4.py --baseline eval/results/round_4_baseline.csv --shadow eval/results/round_4_shadow_norm.csv --out eval/figures/ppt_selects
```

Do not add a figure claiming crater-pattern verification, LoFTR performance, RIFT2 performance, LRO/SELENE data, landing-site accuracy, hazard mapping, or universal sub-pixel accuracy unless a new experiment produces the corresponding evidence.

## Final consistency check

- Every old implementation claim in Slides 2–4 and 6 is marked TRUE, FIX WORDING, UNSUPPORTED, CONTRADICTED, or FUTURE.
- Current implementation names are consistent everywhere: DISK, LightGlue via Kornia, SIFT+FLANN via OpenCV, MAGSAC++, custom PDS4 reader, FastAPI, CPU-only.
- The illumination claim is consistent everywhere: partial success through 60° in the tested sweep, 0/5 at 75° and above, shadow normalization not adopted.
- Real-data claims distinguish precision/agreement from ground-truth accuracy and distinguish true overlap from label-predicted overlap.
- No stale Section Z values are used as current results.
- LRO and SELENE are future acquisition references, not data-used claims.
