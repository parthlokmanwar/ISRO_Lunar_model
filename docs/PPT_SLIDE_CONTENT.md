# Recommended SIH slide content

Use only the phrases and numbers below. All numbers are traceable to `docs/FINDINGS.md`; figure names are the curated copies in `eval/figures/ppt_selects/`.

## 1. Title

- Lunar Correspondence Engine
- Chandrayaan-2 multi-sensor registration
- Trust only what two independent matchers agree on
- Provenance: real pairs plus derived/simulated cases carrying known truth
- Figure: `real_ohrc_overlay.png` — real registered product (F8).

## 2. Proposed Solution

- Perceive: DISK + LightGlue and SIFT + FLANN
- Verify: agreement within 3 px with at least 15 inliers
- CONFIRMED answers: 52/52 right on held-out known-truth cases
- RMSE alone: 38 wrong answers accepted; one had 0.0001 px RMSE and 1194 px true error
- Figure: `rmse_vs_truth.png` — why the second matcher is needed (F1, F2).

## 3. Technical Approach

- PDS4 footprints -> correlation lock -> native-resolution shared tiles
- CLAHE + shadow suppression; MAGSAC++ homography
- Cross-sensor rule: at least ~1.3 km shared ground footprint for OHRC -> TMC-2
- Known-truth scale result: 0.26 px at 1.3 km; 0.07–0.09 px at 2.6 km
- Real stereo caveat: 40/60 SUCCESS; remaining tiles show structured parallax
- Figures: `checkerboard_cross_sensor.png` and `tmc_stereo_residuals.png` (F4, F9).

## 4. Feasibility & Viability

- Held-out evaluation across the six measured challenge families
- CPU only: SIFT 0.22 s/pair; DISK + LightGlue 2.1–2.5 s/pair
- One fixed policy; test success 84%, test precision 97%
- No GPU or training required for the measured pipeline
- Illumination boundary: DISK succeeds 3/5 at 60° but 0/5 at 75°; shadow normalization does not move that boundary
- Figures: `illumination_sweep_round4_baseline.png` and `illumination_sweep_round4_shadow_norm.png` — measured 0/45/60/75/90/135/180° comparison.

## 5. Impact & Benefits

- 3-year OHRC revisit: 14/14 locked tiles registered
- Independent real-pair agreement: median 0.47 px; map precision 0.09 px
- Known-truth sub-pixel results: scale, viewpoint and IIRS band tests
- Coverage map is registration confidence, not a slope or boulder hazard map
- Stereo output should become disparity/DEM-aware rather than a single plane
- Figures: `real_ohrc_checkerboard.png` and `iirs_matches.png` (F7, F8).

## 6. Research & References

- Used: DISK, LightGlue, SIFT/FLANN, MAGSAC++
- Adds known-truth error and cross-method agreement to RMSE-based comparison
- Future test target, not current method: illumination-invariant representation for the >=90° gap
- Data used: Chandrayaan-2 OHRC, TMC-2 and IIRS; no LRO/SELENE overlap was available
- Figure: `iirs_matches.png` — band-to-band evidence without implying cross-instrument overlap (F7, F11).

## Figure status

The Round 4 illumination figures are regenerated from the restored PDS4 data. Shadow normalization is shown as tested-but-not-adopted; it improves 45° but does not improve the held-out DISK result or the 75° boundary.
