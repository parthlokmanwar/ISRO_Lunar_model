# Requirements scorecard — SIH26166

Requirement IDs and verbatim wording: `docs/PS.md`. Evidence: `docs/FINDINGS.md`
(claim F#) and `docs/EXPERIMENT_LOG.md` (round). Status as of 2026-09-28, fixed
pipeline (Round 2/3/4).

Status key: **MET** (measured, holds on held-out data) · **PARTLY** (met under
stated conditions, with a measured limit) · **NOT MET** (measured failure, or
not addressable with this data).

| ID | Requirement (PS wording) | Measured result | Status | Evidence |
|---|---|---|---|---|
| R1 | Illumination variation — "changes in sun azimuth and elevation" | 35 simulated locations at 0°, 45°, 60°, 75°, 90°, 135°, 180°. Baseline DISK: 5/5, 4/5, 3/5, 0/5, 0/5, 0/5, 0/5. Shadow normalization: 5/5, 5/5, 3/5, 0/5, 0/5, 0/5, 0/5. | **PARTLY** — preprocessing helps at 45° but the measured boundary remains between 60° and 75°; ≥75° is not solved | F6; F13; Round 4 |
| R2 | Viewpoint variation — "shifted, scaled, rotated, or perspective-distorted" | Rotation 0–180° and zoom to 2×: SIFT 32/32 sub-pixel. DISK fails at ≥ 90° rotation. Real stereo (TMC fore/nadir): 40/60 SUCCESS; the rest is parallax a plane can't model. | **MET** for rotation/zoom/shift (with SIFT, or DISK + pre-rotation); **PARTLY** for real stereo | F5, F9 |
| R3 | Scale variation — "vastly different … spatial resolutions … scale ratios" | At the true OHRC→TMC ratio (~14.5×): sub-pixel with ≥ ~275 TMC px of shared ground (6/6, 0.26 px). SIFT still works at ~137 TMC px. | **MET** above the measured footprint limit (derived) | F4; R2-O2 |
| R4 | Multi-modal — OHRC, TMC and IIRS | IIRS NIR↔SWIR: 14/14, 13/14 sub-pixel (DISK). OHRC→TMC: sensor model only. OHRC↔IIRS and TMC↔IIRS: **untested** — no overlapping footprints in the data. | **PARTLY** | F4, F7 |
| R5 | Different times | Real OHRC, 3 years apart: 14/14 locked tiles SUCCESS; methods agree to 0.47 px. Half the label overlap fails the lock (label error ~1.4 km). | **MET** where the ground truly overlaps | F8 |
| R6 | Sub-pixel accuracy of the source image | With known truth: sub-pixel on scale (≥ 1.3 km footprint) 12/12, viewpoint ≤ 30° and zoom ≤ 2× 24/24 (both matchers), IIRS 13/14. Real pairs: map *precision* 0.09–0.19 px and inter-method agreement 0.47 px (OHRC), but per-point held-out error 1.4 px; accuracy against truth can't be measured on real data. | **MET** with truth (derived); **PARTLY** on real data (precision and agreement, not truth) | F4–F8; R3-C |
| R7 | Uniform distribution of matches | ≥ 12/16 grid cells covered: F1 14/14, F5 14/14, F2 39–42/60. Coverage drops on low-texture ground. | **MET** on textured terrain; **PARTLY** on smooth mare | F10, F12 |
| R8 | Registered product + match points | API returns the warped image, overlay, all keypoints, matches, inliers, homography; CSV/JSON export. | **MET** | app, `/api/export/*` |
| R9 | Evaluation metrics (RMSE, inlier count, inlier ratio …) | All reported, plus true error, held-out error, cross-method agreement, map precision, coverage. We also show RMSE's limit: 25% of results with RMSE < 1.5 px were wrong. | **MET, and extended** | F1 |
| R10 | Generic — no per-case tuning | One configuration across 6 families, 211 locations, 3 sensors. The two-matcher policy is fixed, not tuned per scene, and its gain holds on held-out locations. | **MET** (within tested families) | F2 |
| R11 | Chandrayaan-2 vs "Lunar reference images" | No non-Chandrayaan reference (e.g. LRO NAC, SELENE) in the dataset. | **NOT MET** (data not acquired) | PS.md note |

## Gaps worth closing before the final round (ordered by value per hour)

1. **R1 beyond 45°** — the biggest measured gap. Restore the source PDS4 data,
   run the registered 60°/75° observation, then test shadow normalization before
   any illumination-invariant representation.
2. **R11 / R4** — acquire one LRO NAC (or SELENE TC) product overlapping an
   OHRC strip. That gives a real cross-mission pair and the "Lunar reference
   image" the PS names.
3. **R2 for DISK** — pre-rotate by the label-known orbit heading; re-measure F6.
4. **R6 on real data** — a DEM would let the stereo residual be checked against
   relief (turning F9 from "consistent with" into "shown").
