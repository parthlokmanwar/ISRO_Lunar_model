# Findings — PPT-ready claims (SIH26166)

Each entry: **condition → what works → number → why → where it breaks → evidence.**
N is the number of test locations. "True error" means the error against a
known answer (derived or simulated pairs). The round numbers point into
`docs/EXPERIMENT_LOG.md`. Everything here is regenerable with `scripts/eval/`.

Status as of 2026-09-28. Round 2/3 and Round 4 numbers (fixed pipeline) are
usable. Section Z lists the numbers that must **not** be used any more.

---

## Headline claims

### F1. RMSE cannot tell you whether a registration is right. Two independent matchers agreeing can.
- **Condition:** every derived/simulated pair with a known answer (173 results that produced a model).
- **Result:**
  - Accepting results with RMSE < 1.5 px: **75%** of them are right; 38 are wrong, some by up to 35 000 px.
  - Accepting only results where DISK+LightGlue and SIFT agree within 3 px and there are ≥ 15 inliers: **99%** right (1 wrong in 106).
- **Why:** RMSE only measures whether the surviving points agree *with each other*. Five wrong but mutually consistent points fit a homography exactly. Two unrelated methods rarely make the *same* mistake.
- **Starkest single case:** grazing illumination, SIFT: 5 inliers, **RMSE 0.0001 px, true error 1194 px** (demo scenario s4).
- **Breaks:** the agreement check rejects 24 right answers, the ones only one matcher could solve. It says "unconfirmed"; it doesn't say "wrong".
- **Evidence:** Round 3-A; `eval/figures/round_2/rmse_vs_truth.png`; `examples/README.md`.
- **Why it matters for the PS:** the PS lists RMSE as an evaluation metric. The ISRO study (arXiv 2509.04775) ranks methods by RMSE. We show where that ranking can mislead, and what to use alongside it.

### F2. Two matchers + an agreement check beat either one alone, and the gain holds on held-out data.
- **Condition:** derived/simulated pairs; policy fixed before scoring; dev/test split by location.
- **Result (test split):** success **84%** (vs SIFT 76%, DISK 67%), precision 97%. Answers labelled **CONFIRMED were right 52/52**.
- **Why:** the failure regions are complementary (F3–F6 below).
- **Breaks:** illumination change ≥ 90°: nothing succeeds, and 3 UNCONFIRMED answers there were wrong.
- **Evidence:** Round 3-D; `eval/results/round_3_policy.json`.

### F3. We found and fixed a defect that had been discarding 98% of LightGlue's matches.
- **Condition:** our own integration of kornia's `LightGlueMatcher`.
- **Result:** the wrapper treated LightGlue's match *score* as a distance. On a real OHRC pair it kept **25 of 1223** matches, the 25 LightGlue trusted least. Fixed: real OHRC inliers **15 → 1051** (demo scenario s1). The fix improved every family on the **held-out test split** and hurt none.
- **Why it matters:** it was found by the evaluation, not by looking at the demo, which looked plausible throughout. An honest slide on "how we validated": the harness asserts which detector actually ran, and compares against a baseline on every pair.
- **Evidence:** Round 1 (R1-P1), Round 2; commit `8693948`.

---

## Per-challenge claims (PS challenges)

### F4. Scale (R3): OHRC ↔ TMC-2 registers at sub-pixel accuracy once ~275 TMC-2 pixels of ground are shared.
- **Condition:** OHRC tiles through a TMC-2 sensor model at the true ratio (≈ 14.5×), footprint swept, 6 locations each.
- **Result (median true error / success):**
  - 1.3 km footprint (~275 TMC px): **0.26 px, 6/6 for both matchers**
  - 2.6 km (~550 TMC px): **0.07–0.09 px, 6/6**
  - 640 m (~137 TMC px): SIFT 6/6, DISK 2/6
  - 320 m (~69 TMC px): SIFT 4/6, DISK 0/6
- **Why:** below ~140 coarse pixels there isn't enough structure for DISK's learned features. SIFT's scale space still finds blobs.
- **Breaks:** < ~70 TMC px. Also: this is a sensor *model* (DERIVED), not a real OHRC–TMC pair; none exists in our data (the strips are 42° of longitude apart).
- **Design rule for the pipeline:** cut cross-sensor tiles by *ground footprint* (≥ ~1.3 km for OHRC→TMC), not by pixel count.
- **Evidence:** Round 2 (R2-O2); `sweep_F3_scale_footprint_footprint_px.png`.

### F5. Viewpoint (R2): SIFT is rotation-invariant; DISK+LightGlue is not.
- **Condition:** same-sensor tiles under uncompensated rotation (0–180°) and zoom (1.25–2×), 4 locations each.
- **Result:**
  - SIFT: 32/32 success, all sub-pixel (median 0.06–0.71 px).
  - DISK: sub-pixel up to 30° rotation and 2× zoom, then **0/8 at 90° and 180°**.
- **Why:** DISK's descriptors are learned from upright imagery and have no orientation normalisation. SIFT assigns each keypoint a dominant orientation.
- **Breaks:** DISK beyond ~30–90°. For orbital imagery the rotation between passes is usually small, and is known from the labels. That is a pre-rotation step to add, not a reason to drop DISK.
- **Evidence:** Round 2 (R2-O1); `sweep_F6_viewpoint_rot.png`, `pair_F6_viewpoint_L0_rot90.png`.

### F6. Illumination (R1): learned matching survives a 45° change in sun azimuth; classical matching doesn't. Nothing survives ≥ 90°.
- **Condition:** real OHRC terrain relit at sun elevation 15° vs 22°, azimuth difference 0–180°, 5 locations each (SIMULATED).
- **Result (success rate):**
  - at 45°: DISK **4/5, 1.4 px**; SIFT **0/5**, confidently wrong (≈ 700 px, RMSE < 1.3 px)
  - at 90–180°: **0/10 per level for both**
- **Why:** shadows switch sides of every crater, so intensity patterns stop corresponding. A learned descriptor tolerates partial change; gradient histograms don't.
- **Breaks:** ≥ 90° azimuth change, which is the regime the PPT's crater-pattern check was meant for. It is not implemented, so this is a measured open problem, not a solved one.
- **Evidence:** Round 2 (R2-O3); `sweep_F4_illum_azimuth_delta_azimuth_deg.png`, `pair_F4_illum_azimuth_L0_daz90.png`.

### F7. Multi-modal (R4): IIRS NIR ↔ SWIR (across the 3 µm hydration band) — DISK+LightGlue 14/14, sub-pixel on 13.
- **Condition:** real IIRS radiance, bands 30–60 vs 110–140, 14 windows along the strip, known transform (DERIVED).
- **Result:**
  - DISK: 14/14 success, **13/14 sub-pixel**, median 0.65–0.77 px, ~1200 inliers.
  - SIFT: 8/14, with 3 confident wrong answers.
- **Why:** band-to-band contrast inverts in places. A learned descriptor copes; gradient orientation histograms don't.
- **Breaks:** not tested across *instruments* (no IIRS footprint overlaps OHRC or TMC in our data).
- **Evidence:** Round 2; `pair_F5_iirs_bands_L03.png`.

### F8. Multi-temporal, real data (R5): 3-year OHRC revisit — every locked tile registered, and two independent methods agree to 0.47 px.
- **Condition:** OHRC 2021-04-02 → 2024-03-30, 14 locked tiles (real, no ground truth).
- **Result:**
  - 14/14 SUCCESS with both matchers (~1000 inliers each).
  - DISK and SIFT maps agree to a median **0.47 px**.
  - Map precision **0.09 px**; per-point held-out error 1.4 px.
- **Why the per-point error stays above 1 px:** the residuals are spatially structured (coherence 0.8, against 0.03 on a synthetic control). That points to local relief or shadow shift, not matching noise.
- **Breaks:**
  - Half the label-predicted overlap failed the correlation lock (NO_LOCK). The PDS4 geolocation is off by ~1.4 km along track, so part of the "overlap" isn't real overlap.
  - Sub-pixel accuracy against truth can't be proven on real data. What we can show: sub-pixel *precision* and sub-pixel *agreement*.
- **Evidence:** Rounds 2, 3-B, 3-C.

### F9. Stereo (R2 / viewpoint, real): TMC-2 fore/nadir — 40/60 SUCCESS; the other 20 are terrain, not matching.
- **Condition:** 60 locked tiles along 876 km of the TMC-2 stereo pair.
- **Result:**
  - SUCCESS **40/60** for both matchers (identical verdicts); 20 MARGINAL.
  - The MARGINAL tiles have strongly structured residuals (coherence **0.77** vs 0.36 on SUCCESS tiles).
  - A smooth global correction doesn't remove them.
- **Why:** fore and nadir see relief from different angles (parallax). No single plane (homography) can model that.
- **Implication:** for stereo, the right output is disparity or a DEM, not a homography. That's a design statement the PPT can make.
- **Breaks:** not proven against a DEM (none in our data).
- **Evidence:** Round 3-B.

### F10. Terrain: texture predicts success on real data.
- **Condition:** TMC-2 tiles split into texture tertiles, assigned before matching.
- **Result (success):** high texture **18/20** (sub-pixel 12/20); low 11/20; mid 11/20. Same for both matchers.
- **Why:** smooth mare gives fewer distinctive structures at 5 m/px.
- **Evidence:** Round 2 summary, F2 by terrain.

### F11. Runtime on a CPU (no GPU).
- SIFT+FLANN **0.22 s** per 1024 px pair; DISK+LightGlue **2.1–2.5 s**; IIRS 0.09 s vs 1.8 s.
- Machine: Intel Raptor Lake (28 logical CPUs), no CUDA.
- Running both matchers (F2) costs ≈ 2.7 s per pair on a CPU.
- **Evidence:** every round CSV, `t_total_ms`.

### F12. Uniform distribution (R7).
- Share of locations where inliers cover ≥ 12 of 16 grid cells (Round 2):
  - DISK: F1 14/14, F2 39/60, F5 14/14
  - SIFT: F1 14/14, F2 42/60
- Coverage is limited by terrain (low-texture regions), not by the matcher.
- **Evidence:** Round 2 summary, `UNIFORM` column.

### F13. Illumination boundary refined; shadow normalization helps 45° but does not move the limit.
- **Condition:** 35 simulated locations: 5 source locations at 0°, 45°, 60°, 75°, 90°, 135° and 180° azimuth difference; baseline versus broad-field shadow normalization. Both runs used the same truth, matchers and geometric thresholds.
- **Result:** baseline DISK success was 5/5, 4/5, 3/5, 0/5, 0/5, 0/5, 0/5 by angle. Shadow normalization changed this to 5/5, 5/5, 3/5, 0/5, 0/5, 0/5, 0/5. DISK held-out test success stayed 5/14 in both configurations.
- **Why:** radiometric correction recovers one 45° case, but it does not restore stable appearance correspondence at 75° or beyond. The exact practical transition is between 60° and 75° for these scenes.
- **Breaks:** SIFT remains unreliable beyond 45° (0/5 at 60° and 75° in both configurations); RIFT2/equivalent was not tested. Shadow normalization is not adopted as a production change because it does not improve the held-out DISK result or the ≥75° boundary.
- **Evidence:** Round 4 entries in `docs/EXPERIMENT_LOG.md`; `eval/results/round_4_baseline.csv`; `eval/results/round_4_shadow_norm.csv`; `eval/figures/ppt_selects/illumination_sweep_round4_baseline.png`; matched-point figures in `eval/figures/round_4_baseline/` and `round_4_shadow_norm/`.

---

## Z. Numbers that must not be used any more

| Number | Where it appeared | Why it's invalid |
|---|---|---|
| 53/118 inliers, 44.9%, RMSE 1.849 px, true error 1.78 px (cross-sensor) | PPT slide 2 mockup, README, handoff | Produced with the inverted-confidence defect. Current: 856/937, RMSE 1.29 px, true error **0.34 px** |
| 15/31 inliers, RMSE 1.654 px (real OHRC) | README, handoff, app | Same defect. Current: **1051/1094**, RMSE 1.24 px |
| 14/31 inliers (real TMC) | README, handoff | Same defect. Current: **501/523**, RMSE 0.96 px |
| "IIRS: DISK+LightGlue 21/58, 1.83 px" | detector comparison (README, examples, handoff) | That run was **SIFT** (silent fallback). Current DISK: **1246/1311, 0.88 px** |
| 247/615, 4.43 px (grazing illumination, DISK) | README, handoff | Same defect. Current: 312/685, 4.75 px |
| 821.6 px (SIFT, grazing illumination) | README, handoff | Current regenerated value: **1194 px, RMSE 0.0001 px**. The point stands, and is stronger |
