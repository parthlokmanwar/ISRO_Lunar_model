# Experiment log — Lunar Correspondence Engine (SIH26166)

Method: `docs/EVAL_PROMPT.md`. Problem statement and requirement IDs (R1–R11):
`docs/PS.md`. Every number in this file is produced by a script in
`scripts/eval/` and stored row by row in `eval/results/`.

---

## 0. Pre-registration (written 2026-09-18, before any Round 1 number existed)

Everything in this section was fixed before the first evaluation run. If any
definition is later judged wrong, a new definition is added next to it and both
are reported. Nothing here is edited after the fact.

### 0.1 What is being evaluated

The **current production pipeline**, exactly as `POST /api/match` runs it:
8-bit tiles → CLAHE (clip 3.0, 8×8) + shadow suppression (threshold 10) →
detection/matching → MAGSAC++ (threshold 3.0 px) → homography. Keypoint
budget 2048, match confidence floor 0.10, matching grid ≤ 1024 px. If image B's
size differs from A's, B is resized to A, as the API does.

Two matcher arms run on **every** instance, with identical pre/post-processing:

| Arm | Detector + matcher | Role |
|---|---|---|
| M1 | DISK + LightGlue (kornia, pretrained) | production default |
| M2 | SIFT + FLANN, Lowe ratio | classical baseline, and the independent method for cross-checking |

Each run asserts which detector actually ran, so a silent fallback from M1 to
SIFT cannot contaminate the M1 rows.

### 0.2 Test families

"Source" = image A (moving), "reference" = image B (fixed), as in the PS.

| Family | Provenance | Pairs | What varies | PS req. |
|---|---|---|---|---|
| F1 `real_ohrc` | REAL | OHRC 2021-04-02 (A) → OHRC 2024-03-30 (B) | location: grid over the label overlap, 3 across × 12 along | R5, R6, R7 |
| F2 `real_tmc` | REAL | TMC-2 fore (A) → TMC-2 nadir (B), same orbit | location: 2 across × 40 along the ~876 km overlap | R2 (stereo), R6, R7 |
| F3 `scale_footprint` | DERIVED | OHRC tile → TMC-2 sensor model at the **true** GSD ratio (4.46 m / OHRC GSD) | ground footprint F = 1024, 2048, 4096, 8192 OHRC px (≈ 69, 137, 275, 550 TMC px) × 6 locations | R3, R4 |
| F4 `illum_azimuth` | SIMULATED | OHRC tile relit twice: sun elev 15° (A) vs 22° (B) | Δazimuth = 0, 45, 90, 135, 180° × 5 locations | R1 |
| F5 `iirs_bands` | DERIVED | IIRS NIR bands 30–60 (A) vs SWIR bands 110–140 (B) | location: windows along the IIRS strip | R4 |
| F6 `viewpoint` | DERIVED | OHRC tile vs the same tile under an uncompensated geometric change | rotation 0, 10, 30, 90, 180°; zoom 1.25, 1.5, 2.0× — × 4 locations | R2, R3 |

Rules shared by the derived and simulated families (F3–F6):
- Source tiles come from all three OHRC strips (2021, 2024, and 2023 at 62°N),
  so terrain is not only equatorial.
- Every instance also gets a small random "pointing" transform, seeded:
  rotation ±5°, zoom 0.95–1.05, shift ±20 px, keystone ±5·10⁻⁶. For F6 the swept
  transform replaces the rotation/zoom part.
- To avoid mirrored border content, the transform is applied to a larger read
  and the central crop is kept (F3, F4, F6). F5 cannot be padded (the IIRS
  strip is 250 px wide) and uses reflected borders, as scenario S5 does.
- All random draws use fixed seeds, recorded per row.

Real families (F1, F2):
- Tiles are cut by the production correlation lock (`services/coreg.locate_overlap`).
  A location where the lock is rejected is recorded as `NO_LOCK`: it counts
  against end-to-end success and is also reported separately.
- **Tiles are not screened for texture.** The scenario builder drops tiles with
  texture < 3.0. Doing that here would quietly remove the hardest terrain from
  the evaluation. Only fill is screened (usable fraction ≥ 0.55), and texture
  is recorded.

### 0.3 Metrics

| Metric | Definition |
|---|---|
| `grid_err_px` (primary, F3–F6) | Mean over a 16×16 grid of reference-image points q of ‖H_est⁻¹q − H_true⁻¹q‖, in **source (A) pixels** of the matching grid. The error of the registration map itself, in the units the PS asks for ("sub-pixel accuracy of source image"). |
| `corner_err_px` (secondary) | Mean corner error, as in the app and the PPT (kept for continuity). |
| `heldout_px` (primary, F1–F2) | Inliers split 70/30 at random, 20 times (seeded). Least-squares homography on the 70%, RMSE on the held-out 30%, median over the 20 splits. Needs ≥ 10 inliers. |
| `agree_px` (F1–F2) | The grid metric above, computed between M1's and M2's homographies. Two unrelated methods agreeing is evidence; one method agreeing with itself is not. |
| `ncc_before` / `ncc_after` | Normalised cross-correlation of the raw 8-bit tiles, identity alignment vs A warped by H_est, over the valid overlap. |
| `rmse_px`, `median_px`, `p90_px` | Reprojection residuals of the inliers (as in the app). |
| `unif_cells` | Fraction of a 4×4 grid over the source image holding ≥ 1 inlier. |
| `unif_hull` | Convex-hull area of the inliers ÷ source image area. |
| `t_*_ms` | Wall-clock per stage: preprocessing, detection+matching, robust fit, total. CPU only; machine recorded. |
| `texture` | `texture_score` of the 8-bit source tile. |

### 0.4 Verdicts

**Families with ground truth (F3–F6):**
- `SUCCESS`: non-degenerate, ≥ 15 inliers, `grid_err_px` ≤ 2.0
- `MARGINAL`: a model, ≥ 8 inliers, `grid_err_px` ≤ 10.0, not SUCCESS
- `FAILURE`: anything else (no model, < 8 inliers, or > 10 px)
- flag `SUBPIXEL`: SUCCESS and `grid_err_px` < 1.0 (the PS target)
- flag `FALSE_CONFIDENCE`: `rmse_px` < 1.5 while `grid_err_px` > 10 (the
  "RMSE lies" case)

**Real families (F1–F2):**
- `NO_LOCK`: the correlation lock rejected the location
- `SUCCESS`: ≥ 15 inliers, `heldout_px` ≤ 2.0, **and confirmed**. Confirmed means
  `agree_px` ≤ 3.0 against the other arm, or, only when the other arm has no
  usable model (< 8 inliers), `ncc_after − ncc_before` ≥ 0.05
- `MARGINAL`: a model, ≥ 8 inliers, `heldout_px` ≤ 5.0, not SUCCESS
- `FAILURE`: anything else
- flag `SUBPIXEL`: SUCCESS and `heldout_px` < 1.0

Known limit, stated up front: held-out error is measured on inliers that were
already selected for consistency within 3 px, so it measures how stable the fit
is, not its truth. That is why confirmation by an independent method is
required for SUCCESS on real pairs.

**Uniformity:** flag `UNIFORM` when `unif_cells` ≥ 0.75 (12 of 16 cells).

### 0.5 Terrain classes

`texture` tertiles, computed per family over every evaluated location
**before** matching: `low`, `mid`, `high`. These are texture classes, measured
from pixels. They are not geological labels: "low texture" means few gradients
at this resolution, which usually means smooth mare, but that is not assumed.

### 0.6 Dev / test split

- F1, F2: along-track index `i`; block = `i // 3`; even block → `dev`, odd → `test`.
  Neighbouring tiles look alike, so the split is by block, not per tile.
- F3–F6: by source location; all condition levels at one location share a split.
  Even location index → `dev`, odd → `test`.

Round 1 is observation only, so it reports both splits. From Round 2 on,
changes are designed on `dev` and are only claimed if they hold on `test`.

### 0.7 What Round 1 reports

Per family and arm: counts per verdict, SUCCESS and SUBPIXEL rates, the median
of the primary error, median inliers, UNIFORM rate, median runtime. Rates per
sweep level (F3, F4, F6) and per terrain tertile (F1, F2). Rates come with
Wilson 95% intervals, because N per cell is small.

---

## Rounds

*(Round entries follow below as they are run.)*

### Round 1 — OBSERVE the pipeline as it was (run 2026-09-18)

Data: `eval/results/round_1.csv` (422 rows = 211 instances × 2 arms),
summary `eval/results/round_1_summary.md`. Runtime 437 s on an Intel
Raptor Lake CPU (28 logical cores), no GPU.

Deviation to record: `round_1_meta.json` lists commit `18d7b86`, but the run
also included the uncommitted padding fix (R1-O0 below), committed next as
`b5ede16`. No other code differed.

**R1-O0 — found before the run, by the harness's detector assertion.** On
the 248 × 744 px IIRS tile, DISK found keypoints in the reflect padding, and
LightGlue rejected them as out of range. The pipeline then fell back to SIFT
without the result saying so. Consequence: the IIRS row in the old detector
comparison (README, `examples/`, 09-09 handoff), "DISK + LightGlue 21/58
inliers, 1.83 px", was SIFT output under the wrong label. Fixed before Round 1
(padding keypoints dropped); `build_examples.py` now labels the detector that
actually ran.

Headline Round 1 table (SUCCESS rate, pre-registered verdicts; N = locations):

| Family | M1 DISK+LightGlue | M2 SIFT+FLANN |
|---|---|---|
| F1 real OHRC (N=28, 14 NO_LOCK) | 4/28 | 12/28 |
| F2 real TMC (N=77, 17 NO_LOCK) | 27/77 | 34/77 |
| F3 scale / footprint (N=24) | 12/24 | 22/24 |
| F4 illumination (N=25) | 4/25 | 5/25 |
| F5 IIRS NIR↔SWIR (N=14) | 14/14 | 8/14 |
| F6 viewpoint (N=32) | 16/32 | 32/32 |

Failure patterns:

- **R1-P1 — DISK+LightGlue returns very few matches on 1024 px tiles.**
  Median putative matches from 2048 keypoints: 27 (F1), 59 (F2), 37 (F3),
  41 (F6). Even on a near-identical pair (F6 rot=0: the same tile under a
  small pointing change) it gave 12–61, where SIFT gave ~1145. Yet on the
  small IIRS tiles it gave ~275. The number is too low to be a property of
  a matcher that works this well on IIRS.
- **R1-P2 — DISK+LightGlue fails at rotation ≥ 90°** (F6: 0/4 at 90°, 0/4 at
  180°), while SIFT succeeds at every rotation.
- **R1-P3 — both arms collapse once the sun azimuth changes by ≥ 45°**
  (F4: 0 SUCCESS for either arm at 45/90/135/180°). SIFT fails
  *confidently*: 19 of its 20 failures there post RMSE < 1.5 px while being
  185–16 000 px wrong (FALSE_CONFIDENCE). DISK fails more gracefully: median
  3.3 px at 45° and 3.7 px at 90° (MARGINAL, not wrong by hundreds).
- **R1-P4 — resolution gap: a minimum ground footprint.** At the true
  OHRC→TMC-2 ratio (~14.5×), SIFT succeeds from 2048 OHRC px (≈ 137 TMC px,
  ≈ 640 m); DISK needs 4096 (≈ 275 TMC px, ≈ 1.3 km). At 1024 OHRC px
  (≈ 69 TMC px) DISK fits 6 degenerate models, every one with RMSE < 1.5 px
  and true error 364–35 700 px.
- **R1-P5 — real OHRC cross-date: nobody reaches sub-pixel.** Held-out
  error ≈ 1.4 px (SIFT) and 2.2 px (DISK); 0/28 SUBPIXEL. Half the grid
  locations fail the correlation lock (NO_LOCK). They sit in the southern
  third of the label-predicted overlap, which the ~1.4 km along-track label
  error puts outside the real overlap.
- **R1-P6 — texture matters on TMC-2.** High- vs low-texture tertile
  SUCCESS: DISK 70% vs 35%, SIFT 80% vs 45%.
- **R1-P7 — runtime.** SIFT ≈ 0.23 s per pair, DISK+LightGlue ≈ 2.1–2.5 s
  (CPU).

Caveat on F1 correction values: the label-predicted centre in strip A is
clamped near the strip end, so `coreg_shift_along_m` in these rows mixes the
clamp with the label error. It must not be quoted as the label error.

### Round 2 — HYPOTHESIZE and TEST: R1-P1

Competing hypotheses for R1-P1, non-tool first:

- **H2a (integration bug):** our wrapper filters or scores LightGlue's
  output incorrectly.
- H2b (preprocessing): CLAHE + shadow zeroing removes what DISK needs on
  large tiles.
- H2c (scale): at 1024 px DISK's detections are dominated by fine noise.
- H2d (tool / domain gap): DISK descriptors do not discriminate lunar
  texture.

**Narrow test (dev tiles F6_L0_rot0, F1_06_0; plus F5_L03 for contrast):**
raw LightGlue output vs what the wrapper keeps.

| Tile | LightGlue matches | score > 0.9 | kept by wrapper |
|---|---|---|---|
| F6_viewpoint_L0_rot0 | 1217 | 1156 | 61 |
| F1_real_ohrc_06_0 | 1223 | 1198 | 25 |
| F5_iirs_bands_L03 | 1363 | 1129 | 234 |

**Why:** kornia's `LightGlueMatcher` returns LightGlue's *matching score*
(higher = more confident) in the slot its API calls "distance". The wrapper
computed `confidence = 1 − score` and kept `confidence ≥ 0.10`, i.e.
**score ≤ 0.90: it discarded every confident match and kept the least
confident 2–17%.** Easy pairs (almost all scores > 0.9) lost the most, which
is why IIRS, the harder pair, kept the most. H2a is confirmed. H2b–H2d are not
needed to explain R1-P1 and stay untested.

Scope of the damage: every DISK+LightGlue number this project has produced
so far — the app's live runs, the five demo scenarios, `examples/`, the
detector comparison, and the PPT mockup (53/118 inliers, 44.9%, 1.849 px,
1.78 px) — came from the worst few percent of LightGlue's matches, with each
match's confidence inverted.

**Fix:** `confidence = score` (the floor 0.10 now means what it says).
**Pre-registered check for Round 2:** re-run all 211 instances, both arms,
unchanged instances, verdicts and thresholds. The fix is claimed only if M1
improves on the **test** split as well as on dev. M2 is re-run too, as a
control: it should reproduce Round 1 up to FLANN's randomness.

### Round 2 — result of the fix (run 2026-09-18)

Data: `eval/results/round_2.csv`, `round_2_summary.md`, figures in
`eval/figures/round_2/`. Same 211 instances, same verdicts. Run with commit
`b5ede16` + the one-line confidence fix, committed as `8693948` while the run
was in progress.

M1 (DISK+LightGlue) SUCCESS, Round 1 → Round 2, **dev | test**:

| Family | dev | test | median inliers R1 → R2 |
|---|---|---|---|
| F1 real OHRC | 2 → 6 | 2 → 8 | 18 → ~1000 |
| F2 real TMC | 18 → 23 | 9 → 17 | 20 → ~730 |
| F3 scale | 5 → 7 | 7 → 7 | 28 → ~560 |
| F4 illumination | 3 → 5 | 1 → 4 | 7 → 7 |
| F5 IIRS | 7 → 7 (SUBPIXEL 3 → 6) | 7 → 7 (SUBPIXEL 6 → 7) | 219 → ~1230 |
| F6 viewpoint | 7 → 12 | 9 → 12 | 22 → ~770 |

**The fix holds on the test split in every family and hurts none.** M2
(SIFT) is unchanged, as a control should be: SIFT and FLANN reproduced
exactly. Its real-pair SUCCESS counts rose only because M1 can now confirm
it.

For the real pairs (F1 dev and test combined), every one of the 14 locked OHRC
tiles is SUCCESS for both arms, and the two unrelated methods agree to a
median **0.47 px** (`agree_px`). TMC: 40 SUCCESS, 20 MARGINAL, identically for
both arms.

What the fixed pipeline shows (these supersede R1-P1…P7 wherever they differ):

- **R2-O1 — the two matchers fail in different places.**
  - DISK+LightGlue: 0/4 at 90° and 180° rotation (F6), where SIFT gets 4/4.
    It needs a larger ground footprint at the OHRC→TMC ratio (F3, below).
  - SIFT: 0/5 at 45° sun-azimuth change, where DISK gets 4/5. SIFT gets 8/14
    on IIRS NIR↔SWIR, where DISK gets 14/14.
- **R2-O2 — scale (F3, true OHRC→TMC-2 ratio).** Median true error by
  footprint:

  | OHRC footprint | ≈ TMC px | ≈ ground | DISK | SIFT |
  |---|---|---|---|---|
  | 1024 | 69 | 320 m | 0/6 | 4/6 |
  | 2048 | 137 | 640 m | 2/6 | 6/6 |
  | 4096 | 275 | 1.3 km | 6/6, 0.26 px | 6/6, 0.26 px |
  | 8192 | 550 | 2.6 km | 6/6, 0.09 px | 6/6, 0.07 px |

  Endpoint: with ≥ ~275 TMC-2 pixels of shared ground, both matchers register
  OHRC to a TMC-2 model at sub-pixel accuracy. Below ~140 TMC px, DISK fails.
- **R2-O3 — illumination (F4).** Past 45° of sun-azimuth change, every
  method fails (0/20 SUCCESS for either arm at 90–180°). SIFT fails
  *confidently*: its wrong answers post RMSE ≤ 1.3 px. The breaking point
  lies between 45° and 90°.
- **R2-O4 — FALSE_CONFIDENCE still happens after the fix:** 22 SIFT rows
  and 12 DISK rows with RMSE < 1.5 px and a true error > 10 px.
- **R2-O5 — runtime:** SIFT 0.22 s, DISK+LightGlue 2.1–2.5 s per 1024 px pair
  (CPU), IIRS 0.09 s vs 1.8 s.

### Round 3 — analyses on the saved Round 2 inliers (no new matching)

Scripts: `scripts/eval/analyze_round3.py`, `scripts/eval/policy_round3.py`.
Data: `eval/results/round_3_summary.json`, `round_3_geometry.csv`,
`round_3_policy.json`.

**R3-A — can the pipeline tell when its own answer is wrong?** Calibrated on
the families with a known answer (F3–F6, 173 results that produced a model;
right = true error ≤ 2 px):

| Trust rule | Accepted | Accepted but wrong | Precision | Right but rejected |
|---|---|---|---|---|
| RMSE < 1.5 px (what most pipelines report) | 152 | 38 | 75% | 16 |
| ≥ 15 inliers | 133 | 5 | 96% | 2 |
| both matchers agree ≤ 3 px | 108 | 2 | 98% | 24 |
| ≥ 15 inliers AND agree | 106 | 1 | 99% | 25 |

This also calibrates the "confirmed" rule used for the real pairs.

**R3-D — a two-matcher policy** (fixed before scoring). Run both matchers:
- if both give ≥ 15 inliers and agree ≤ 3 px → CONFIRMED;
- if only one gives ≥ 15 inliers → UNCONFIRMED;
- otherwise → REJECT.

| Policy | dev success | test success | test precision |
|---|---|---|---|
| DISK alone (≥ 15 inliers) | 62% | 67% | 94% |
| SIFT alone (≥ 15 inliers) | 66% | 76% | 100% |
| **both + agreement** | **78%** | **84%** | **97%** |

CONFIRMED answers: 52/52 right. UNCONFIRMED: 24 right, 3 wrong (all three in
the illumination family). The policy's gain holds on the test split.
Endpoint: the two matchers are complementary, and their agreement is a free,
ground-truth-free confidence signal.

**R3-B — is the real-pair residual noise or geometry?** Coherence is the
correlation between each inlier's residual and its 8 neighbours' mean
residual.

| Set | Coherence | Held-out gain from a smooth non-planar correction |
|---|---|---|
| F6 synthetic planar (control) | 0.02–0.06 | ≈ 0% |
| F1 real OHRC cross-date | 0.78–0.86 | 5% |
| F2 real TMC stereo | 0.56–0.61 | 2–3% |
| F2 TMC MARGINAL tiles | 0.77 | 3% |
| F2 TMC SUCCESS tiles | 0.36 | — |

Reading:
- The residuals on real pairs are **spatially structured**, not noise.
- A smooth global correction barely helps, so the structure is **local**.
- On the TMC stereo pair, the tiles that miss SUCCESS are exactly the
  structured ones.

This fits local terrain parallax (relief seen from the fore and nadir angles),
which no single plane can model. Stereo needs a disparity or DEM model, not a
homography. It is not yet proven: there is no DEM here to correlate against.
F1's structure has a competing explanation, still open: shadow edges move
between sun elevations 10.1° and 7.3°, which shifts where features are
detected.

**R3-C — precision of the registration map on real pairs (added metric).**
Definition: split the inliers into halves 20×, fit a homography to each half,
take the grid disagreement between the two maps, median ÷ 2. This is a new
definition. It is reported *alongside* the pre-registered held-out metric,
not instead of it.

Results:
- Median map precision: **F1 0.09 px, F2 0.15–0.19 px**; < 1 px for 100% of
  F1 tiles and 98–100% of F2 tiles.
- Per-point held-out error stays ≈ 1.4 px.

Reading: the fitted map is stable far below a pixel. The ~1.4 px per-point
error is the local structure from R3-B. Precision is not truth: on real data,
accuracy against truth remains unmeasurable, and the strongest truth-side
evidence is two unrelated methods agreeing to 0.47 px (OHRC).

**Open patterns (candidates for Round 4):**
- R2-O1: DISK and rotation. Candidate non-tool test: register against 4
  rotated copies of B.
- R2-O3: illumination ≥ 90°. Candidate hypotheses: shadow zeroing in
  preprocessing (non-tool); an illumination-invariant representation such as
  RIFT2 or phase congruency (tool).
- F3: DISK at < 140 TMC px (5 inliers).
- R3-B: F1 residual structure — parallax or shadow-edge drift?
- F2: 17 NO_LOCK locations on the stereo pair.

### Consequences applied to the app (2026-09-18)

- Both fixes are in `backend/services/feature_matching.py`; the live API now
  runs DISK+LightGlue on every scenario, including IIRS.
- `examples/` was regenerated. Scenario s1 (real OHRC) went from 15/31
  inliers to 1051/1094. The detector comparison now reads, for grazing
  illumination: DISK 312/685, true error 4.75 px; **SIFT 5/15, RMSE
  0.0001 px, true error 1194 px**.

### Round 4 / Round A — illumination boundary refinement (2026-09-28)

**Observe.** The open R2-O3 pattern was the transition between 45° and 90°
sun-azimuth change. With the original PDS4 products restored, the sweep was
rebuilt at `0, 45, 60, 75, 90, 135, 180` degrees for the same five source
locations, elevation pair (15° vs 22°), pointing transforms and known truth.
Each configuration produced 70 rows: 35 locations × 2 matchers.

**Baseline result.**

| Δ azimuth | DISK success | DISK median true error (px) | SIFT success | SIFT median true error (px) |
|---:|---:|---:|---:|---:|
| 0° | 5/5 | 0.061 | 5/5 | 0.234 |
| 45° | 4/5 | 1.396 | 0/5 | 263.459 |
| 60° | 3/5 | 1.993 | 0/5 | 773.004 |
| 75° | 0/5 | 4.262 | 0/5 | 1100.065 |
| 90° | 0/5 | 3.735 | 0/5 | 2519.352 |
| 135° | 0/5 | 131.411 | 0/5 | 633.823 |
| 180° | 0/5 | 773.700 | 0/5 | 705.215 |

The finer sweep changes the stated boundary: for these scenes, DISK reaches
3/5 at 60° but 0/5 at 75°. This is a gradual decline from 45° to 75°, not a
hard cliff exactly at 90°.

**Hypothesis C test — shadow normalization.** Broad-field illumination
division followed by CLAHE was tested on the identical 35 locations. DISK
changed from 4/5 to 5/5 at 45°, stayed 3/5 at 60°, and stayed 0/5 at 75°,
90°, 135° and 180°. SIFT changed from 0/5 to 2/5 at 45° but remained 0/5 at
60° and above. DISK held-out test success was unchanged at 5/14; therefore the
preprocessing change is not adopted as a production fix. The matched-point
figures are saved under `eval/figures/round_4_baseline/` and
`eval/figures/round_4_shadow_norm/`.

**Analysis.** Shadow normalization rescues some moderate-angle appearance
changes but does not address the ≥75° failure. Hypothesis C is partly supported
at 45° and rejected as an explanation for the main boundary. RIFT2 or an
equivalent structural/radiometric-invariant representation remains a future,
narrow test rather than a current pipeline component.

### Round 4 / Round B — requirements and PPT artifacts (2026-09-27)

Verified the existing scorecard against F1-F13, updated R1 with the measured
60°/75° refinement and shadow-normalization result, and produced
`docs/PPT_SLIDE_CONTENT.md` plus the curated `eval/figures/ppt_selects/`
manifest. The slide brief uses only validated numbers and calls the
illumination graphics as Round 4 baseline and tested-but-not-adopted shadow
normalization. `docs/PPT_AUDIT.md` was appended with the Round 4 audit below.

### Round 4 / optional structural matcher probe (2026-09-28)

Hypothesis B was targeted with the available detector-free structural matcher,
Kornia LoFTR, on the pre-registered cases at 60°, 75° and 90°. The
evaluation-only probe is `scripts/eval/test_loftr_round4.py`. It did not reach
inference: Kornia's pretrained outdoor weights were not cached and the
upstream download failed certificate verification. No uninitialized or
partially downloaded model was scored, so this is an inconclusive dependency
result, not a matcher failure. RIFT2 itself is not installed. The production
DISK/SIFT method and F13 conclusions are unchanged.
