# Lunar Correspondence Engine

Multi-sensor image registration for Chandrayaan-2 (SIH26166). Given two lunar
observations of the same ground — taken years apart, by different instruments, or
under different illumination — it finds the correspondence between them and
reports how accurate that answer actually is.

---

## Run locally

The current release is designed for localhost. Docker is not required. The
registration pipeline works without API keys.

### 1. Prepare the Python environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

Place the extracted Chandrayaan-2 products under `data/`; see
[`data/README.md`](data/README.md). The products are intentionally excluded from
Git because they are several gigabytes in total.

### 2. Build the scenario catalogue

```bash
python scripts/build_scenarios.py
```

### 3. Start the API

```powershell
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite development server proxies API requests
to `http://localhost:8001`.

For a production-style local preview, run `npm run build` and then start
FastAPI again; it will serve the generated frontend from `frontend/dist`.

To regenerate the worked examples in `examples/`:

```bash
python scripts/build_examples.py
```

---

## What the pipeline does

1. **Locate.** PDS4 labels give each strip's four ground corners, which fixes an
   affine map between pixel and selenographic coordinates. Intersecting two
   footprints gives the ground they share.
2. **Lock on.** The labels are a prior, not truth. On this dataset the OHRC
   cross-date pair is off by about **184 m across-track and 2 km along-track** —
   larger than a whole tile — so the pipeline correlates the two strips at
   reduced scale to find the real overlap, then refines. A lock is accepted only
   if the correlation peak is unambiguous, or if the correction it asks for is
   small enough to be within the label accuracy we already assume. Otherwise the
   pair is rejected rather than matched blind.
3. **Cut.** Tiles come out of the shared footprint at **native sensor
   resolution**, read through a memory-mapped window so a 1.4 GB product never
   loads whole. Tiles that are mostly fill, or too featureless to match, are
   screened out.
4. **Normalise.** CLAHE equalisation and instrument-aware preparation. Shadow
   normalisation was evaluated separately, but is not enabled by default because
   it did not improve held-out performance or the measured high-angle limit.
5. **Detect and match.** DISK keypoints, LightGlue correspondences; SIFT + FLANN
   as a fallback that needs no weights.
6. **Fit.** MAGSAC++ homography with reprojection RMSE, median and p90 — plus,
   where the scenario has a known transform, the **true corner error**.
7. **Assess.** Where across the frame the terrain produced reliable
   correspondences.

---

## The scenarios, and what is real in them

Every scenario states its provenance, in the API, the interface and the examples.

| Scenario | Provenance | What it tests |
|---|---|---|
| Equatorial OHRC cross-date | `REAL` | 3-year revisit, different sun elevation |
| TMC-2 stereo fore/nadir | `REAL` | Parallax under identical illumination |
| Cross-sensor OHRC → TMC-2 | `DERIVED` | 14× ground-scale gap |
| Grazing illumination change | `SIMULATED` | Shadows falling along a different axis |
| IIRS NIR vs SWIR | `DERIVED` | Genuinely multi-modal, across the 3 µm band |

- `REAL` — two unmodified Chandrayaan-2 observations of the same ground.
- `DERIVED` — real pixels through a sensor or band model, displaced by a
  transform we chose.
- `SIMULATED` — real pixels, modelled illumination, displaced by a transform we
  chose.

The last three are derived because **the dataset contains no real counterpart for
them**: OHRC sits at 23°E and TMC-2 at 66°E, so those strips never see the same
ground. Rather than match them anyway and report a number, they are built from
real pixels by a transform we control — which buys something a real cross-mission
pair could not: a known answer to check against.

---

## Why there are two accuracy numbers

Reprojection RMSE only says the surviving correspondences agree *with each other*.
A confident fit to the wrong correspondences can post an excellent RMSE.

From `examples/README.md`, both detectors on the scenarios where the answer is
known (regenerated 2026-09-18, after the LightGlue confidence fix):

| Scenario | Detector | Inliers | RMSE (px) | True error (px) |
|---|---|---|---|---|
| Cross-sensor OHRC → TMC-2 | DISK + LightGlue | 856/937 | 1.293 | 0.34 |
| Cross-sensor OHRC → TMC-2 | SIFT + FLANN | 199/233 | 0.442 | 0.31 |
| Grazing illumination | DISK + LightGlue | 312/685 | 1.771 | 4.75 |
| **Grazing illumination** | **SIFT + FLANN** | **5/15** | **0.0001** | **1194** |
| IIRS NIR vs SWIR | DISK + LightGlue | 1246/1311 | 1.369 | 0.88 |
| IIRS NIR vs SWIR | SIFT + FLANN | 20/45 | 0.721 | 1.57 |

The highlighted row posts the best RMSE in the table while sitting 1194 px
from the right answer: under changed lighting SIFT locks onto five mutually
consistent but incorrect correspondences and fits them exactly. Across the
full evaluation (173 results with a known answer), accepting on RMSE < 1.5 px
lets 38 wrong answers through; requiring the two matchers to agree lets one
through. See `docs/FINDINGS.md`.

This is why the interface shows ground-truth error **above** RMSE wherever it
exists, and flags a fit with too few inliers as degenerate rather than reporting
its residual as an achievement.

---

## Results on real data

| Scenario | Inliers | Inlier ratio | RMSE | On the ground |
|---|---|---|---|---|
| Equatorial OHRC cross-date | 1051/1094 | 96% | 1.24 px | 0.39 m |
| TMC-2 stereo fore/nadir | 501/523 | 96% | 0.96 px | 4.6 m |

Across 14 locked OHRC tiles, DISK + LightGlue and SIFT agree to a median
0.47 px; across 60 TMC-2 tiles, 40 register cleanly and the other 20 carry
structured residuals consistent with stereo parallax. Details and every other
measurement: `docs/EXPERIMENT_LOG.md`.

The refined illumination sweep now covers 0°, 45°, 60°, 75°, 90°, 135° and
180° sun-azimuth differences: DISK succeeds on 3/5 at 60° and 0/5 at 75° and
beyond. Shadow normalization improves the 45° result from 4/5 to 5/5 but does
not move the boundary, so it is documented as tested but not adopted.

---

## Evaluation

`scripts/eval/` rebuilds 211 test locations across six families (real OHRC,
real TMC-2 stereo, OHRC→TMC-2 scale, illumination, IIRS bands, viewpoint) and
runs both matchers on every one:

```bash
cd scripts/eval
python build_instances.py
python run_round.py --round <N>
python summarize.py ../../eval/results/round_<N>.csv
```

Method and pre-registered definitions: `docs/EVAL_PROMPT.md`,
`docs/EXPERIMENT_LOG.md`. PPT-ready claims: `docs/FINDINGS.md`. Requirement
coverage: `docs/REQUIREMENTS_SCORECARD.md`.

---

## Layout

- **Left** — scenario library with provenance, and the pipeline controls
  (detector, robust estimator, inlier threshold, CLAHE, confidence floor,
  keypoint budget). Every control changes the result; nothing there is decorative.
- **Centre** — a WebGL stage where each step happens to the actual images:
  normalisation crossfades, real keypoints scatter onto each plane, real
  correspondences run between them, rejected ones drop out, and image A warps
  onto B by the estimated homography. Drag to orbit, scroll to zoom.
- **Right** — accuracy first, then the evidence behind it, the estimated
  transform, coverage and per-stage timings. Nothing is shown until it has been
  measured; there are no placeholder values.
- **Bottom** — stage transport with the real measured duration of each step.
  Arrow keys step, space plays.
- **Header** — **Examples** opens the recorded runs and their figures.
- **Assistant** (optional) can answer questions about the current run from its
  measured metrics. The registration pipeline does not depend on external AI or
  speech services.

---

## `examples/`

Complete recorded runs, regenerable with `scripts/build_examples.py`, each with
six figures:

- `checkerboard.png` — alternating tiles from A-warped and B. The honest test:
  features either run straight across the seams or they do not.
- `matches.png` — inliers bright, rejected in red.
- `overlay.png` — A in red over B in cyan; grey means registered.
- `keypoints.png`, `residuals.png`, `pair.png`.

They double as a regression check: the figures are rendered from the same code
path the API serves, so if a number in the interface disagrees with one recorded
here, something has changed.

---

## Layout of the repo

```
backend/
  services/
    geo.py              footprint geometry, pixel <-> lon/lat, overlap
    raster.py           windowed native-resolution reads, correct PDS4 dtypes
    coreg.py            correlation lock that corrects the label geometry
    pds4.py             label parsing
    synth.py            sensor and illumination models for derived scenarios
    preprocessing.py    CLAHE and shadow handling
    feature_matching.py DISK + LightGlue, SIFT + FLANN fallback
    geometric.py        MAGSAC++, error statistics, ground-truth error
  routers/              health, scenarios, match, analytics, examples, vyom
frontend/src/
  components/           LeftRail, Stage3D, StageOverlay, Stepper, RightRail,
                        Examples, Assistant
  state/useStore.js     one source of truth for everything drawn
scripts/
  build_scenarios.py    cuts the tiles, builds the catalogue
  build_examples.py     runs everything, renders the figures
examples/               generated: figures, metrics, README
```

---

## Notes and limits

- Until 2026-09-18 the real pairs gave only 14–15 inliers. That was not the
  imagery: the LightGlue wrapper inverted match confidence and kept the least
  confident 2% of matches. Fixed; see `docs/EXPERIMENT_LOG.md`, Round 2.
- **TMC-2 and IIRS products are 16-bit** (`UnsignedLSB2`). Reading them as 8-bit
  returns noise that still looks plausible at thumbnail size.
- The coverage map shows where correspondences were reliable. It is not a slope
  or boulder hazard assessment and should not be presented as a landing decision.
- The assistant is optional. The registration pipeline works without
  `OPENROUTER_API_KEY` or `ELEVENLABS_API_KEY`.
- Copy `backend/.env.example` to `backend/.env` to configure keys. `.env` is
  gitignored.
- PPT-ready slide content and a curated figure shortlist live in
  `docs/PPT_SLIDE_CONTENT.md` and `eval/figures/ppt_selects/`, including the
  Round 4 baseline and shadow-normalization comparison.
- Optional future evidence specifications for RIFT2, DEM-backed stereo and
  external lunar references are in `docs/FUTURE_EVIDENCE_SPEC.md`.
