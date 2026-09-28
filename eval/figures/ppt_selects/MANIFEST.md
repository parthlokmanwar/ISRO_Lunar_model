# PPT figure shortlist

| File | Caption | Evidence |
|---|---|---|
| `rmse_vs_truth.png` | Reprojection RMSE is not a truth metric; wrong low-RMSE fits remain visible against ground truth. | F1 |
| `checkerboard_cross_sensor.png` | Cross-sensor alignment after the OHRC -> TMC-2 sensor model and known transform. | F4 |
| `illumination_sweep_round4_baseline.png` | Round 4 baseline at 0°/45°/60°/75°/90°/135°/180°: DISK succeeds 3/5 at 60° and 0/5 at 75°. | F13 |
| `illumination_sweep_round4_shadow_norm.png` | Shadow normalization improves DISK at 45° from 4/5 to 5/5, but does not move the 75° boundary. | F13 |
| `real_ohrc_overlay.png` | Real three-year OHRC revisit after correlation lock and registration. | F8 |
| `real_ohrc_checkerboard.png` | Checkerboard inspection of real OHRC alignment; use with agreement/precision, not ground-truth accuracy. | F8 |
| `tmc_stereo_residuals.png` | Structured fore/nadir residuals expose relief/parallax beyond a single homography. | F9 |
| `iirs_matches.png` | NIR/SWIR band-to-band correspondences across the 3 µm band. | F7 |

The Round 4 illumination figures are produced from the restored PDS4 products; the shadow-normalized version is a negative/non-adopted preprocessing result.
