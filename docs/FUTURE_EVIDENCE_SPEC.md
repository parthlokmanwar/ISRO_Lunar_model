# Future evidence specifications

These are optional follow-up experiments, not current validated claims.

## RIFT2 or equivalent

- Target failure: F13 illumination changes at 75° and above.
- Narrow first test: the three worst baseline cases
  `F4_illum_azimuth_L0_daz75`, `F4_illum_azimuth_L0_daz90` and
  `F4_illum_azimuth_L2_daz90`.
- Keep fixed: the same relit pixels, pointing homographies, truth metric,
  15-inlier/2-pixel SUCCESS rule and held-out dev/test split.
- Report: true corner error, inliers, RMSE, runtime and matched-point figures.
- Adoption rule: expand only if it improves at least one 75°/90° case without
  degrading the 0°/45° controls. RIFT2 is not installed. A LoFTR probe was
  prepared, but its pretrained weights could not be downloaded because the
  upstream certificate failed; therefore no structural-matcher result is
  claimed.

## DEM-backed stereo validation

- Target finding: F9 structured residuals in TMC-2 fore/nadir imagery.
- Required input: a DEM or DTM covering the 33 km × 876 km stereo overlap,
  with a documented vertical datum and geolocation.
- Test: compare residual direction/magnitude against predicted relief
  disparity; report correlation and held-out improvement over the homography.
- Until this exists, F9 remains “consistent with parallax,” not proven by DEM.

## External lunar reference

- Target requirement: R11 and the untested cross-instrument cases in R4.
- Required input: an LRO NAC or SELENE/TMC image whose footprint genuinely
  overlaps one of the OHRC strips, with metadata and a usable pixel raster.
- Test: run the same correlation-lock, dual-matcher agreement and known/held-
  out metrics where a ground-truth transform can be established.
- No such product is present locally, so no external-mission claim is made.
