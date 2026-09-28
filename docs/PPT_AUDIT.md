# PPT audit — "Serial_No_3_AstroBytes(CR 43).pdf" vs measured results

Every claim on the submitted deck, checked against the code and the evaluation
(`docs/FINDINGS.md`, `docs/EXPERIMENT_LOG.md`). Audited 2026-09-18.

Verdict key:
- **TRUE** — the claim is supported as written.
- **FIX WORDING** — the substance is right, the wording isn't.
- **UNSUPPORTED** — not built or not measured.
- **CONTRADICTED** — measurement says otherwise.
- **STALE** — the number came from the defective pipeline.

The deck's own "Perceive → Verify" structure can be kept. What changes is
what sits in the Verify box (see the last section).

---

## Slide 2 — Proposed solution / How it addresses the problem / Innovation

| # | Claim on slide | Verdict | What is actually true |
|---|---|---|---|
| 2.1 | "Pretrained SuperPoint detects key points, SuperGlue matches them" | **FIX WORDING** | DISK detects, LightGlue matches (LightGlue is SuperGlue's successor). And the measured best design runs **two** matchers — DISK+LightGlue and SIFT — and checks their agreement (F2). |
| 2.2 | "Verification: Crater-Pattern Check … robust under extreme illumination" | **UNSUPPORTED** | Not implemented. Measured: *no* method survives a sun-azimuth change ≥ 90° (F6). Replace with the verification we *have* and measured: cross-matcher agreement, 99% precision where the truth is known (F1). Keep crater patterns only as future work aimed at the measured ≥ 90° gap. |
| 2.3 | "Sensor-aware preprocessing corrects brightness, contrast, resolution and sensor differences" | **FIX WORDING** | CLAHE + shadow suppression, and resampling to a common grid by GSD. No sensor-specific radiometric model. Better claim: "tiles cut by *ground footprint*; OHRC→TMC needs ≥ ~1.3 km" (F4). |
| 2.4 | "Refinement & Output: sub-pixel precision, evenly spread matches" | **FIX WORDING** | There is no separate refinement stage. Sub-pixel is *measured*, not engineered: sub-pixel with known truth on scale, viewpoint and IIRS (F4, F5, F7); real-pair map precision 0.09–0.19 px (F8). Coverage measured (F12). |
| 2.5 | "Illumination: crater spatial patterns stay stable → handled by verification" | **CONTRADICTED** as implemented | Measured limit: 45° azimuth OK with DISK (4/5), ≥ 90° fails for everything (F6). State the limit honestly, with the number. |
| 2.6 | "Viewpoint & scale: SuperPoint + SuperGlue recognizes features despite shift, rotation, zoom" | **FIX WORDING / PARTLY CONTRADICTED** | The learned matcher (DISK) **fails at ≥ 90° rotation**; SIFT handles all rotations (F5). Scale: sub-pixel above a measured footprint (F4). |
| 2.7 | "Cross-instrument OHRC ↔ TMC ↔ IIRS" | **FIX WORDING** | Measured: OHRC→TMC (sensor model) and IIRS NIR↔SWIR (real bands). OHRC↔IIRS untested: no overlapping data. Don't draw the triangle as done. |
| 2.8 | "Confidence filtering + RANSAC remove inconsistent matches" | **TRUE** (now) | MAGSAC++ plus a confidence floor. Note: the confidence filter was **inverted** until 2026-09-18 and kept only the worst 2% of matches (F3). It is correct now. |
| 2.9 | Mockup: 1.78 px GT error, RMSE 1.849 px, 44.9%, 53/118 | **STALE** | Current (same scenario): **856/937 (91%), RMSE 1.29 px, true error 0.34 px**. Retake the screenshot. |
| 2.10 | "ISRO SAC (2025) found even top matching methods lose accuracy under harsh lighting" | **TRUE, with a nuance** | arXiv 2509.04775 (Makharia, Singla et al., 5 Sep 2025): SuperGlue lowest RMSE and fastest; SIFT and AKAZE degrade under polar lighting. Affiliation isn't shown on the abstract page; confirm "SAC" from the PDF. They **rank by RMSE**; our F1 shows why RMSE alone can mislead. That's a respectful, strong differentiator. |
| 2.11 | "Built on ISRO's 2025 findings — extends SuperGlue approach" | **FIX WORDING** | Better: "extends their comparison with ground-truth error and cross-method agreement, because RMSE rated a 1194 px-wrong answer as 0.0001 px". |

## Slide 3 — Technical approach

| # | Claim | Verdict | Reality |
|---|---|---|---|
| 3.1 | OHRC ~0.32 m, TMC ~5 m | **TRUE** | Labels: OHRC 0.307–0.314 m, TMC-2 4.59–4.82 m. |
| 3.2 | "IIRS band selection / PCA" | **FIX WORDING** | Band-group averaging (30–60, 110–140); no PCA. |
| 3.3 | Step 2 "Multi-modal representation: texture, edges, structural cues, spectral" | **UNSUPPORTED** | Not built. Remove, or mark as future. |
| 3.4 | Step 3 "SuperPoint + SuperGlue (primary), LoFTR / RIFT2 (alternatives)" | **FIX WORDING** | DISK+LightGlue + SIFT+FLANN, run together with an agreement check. LoFTR and RIFT2 were not used. RIFT2 is the natural next test for the ≥ 90° illumination gap. |
| 3.5 | Step 5 "Sub-pixel refinement: local neighbourhood refinement" | **UNSUPPORTED** | No refinement stage. Sub-pixel is achieved and measured without it. |
| 3.6 | Step 6 "Spatial distribution check … select distributed matches" | **FIX WORDING** | Coverage is measured and shown (4×4 grid, coverage map); matches are not re-selected for distribution. |
| 3.7 | Step 7 "Affine / Homography / RPC" | **FIX WORDING** | Homography only. For stereo we now have evidence a plane is the wrong model (F9). Say so: that's depth. |
| 3.8 | Output metrics "RMSE, MAE, SSIM" | **FIX WORDING** | We report RMSE, median, p90, inliers, inlier ratio, **true error, held-out error, cross-method agreement, map precision, coverage**. No SSIM. Replace the list. |
| 3.9 | Stack: SuperPoint, SuperGlue, LoFTR, RIFT2 | **CONTRADICTED** | Used: DISK, LightGlue (kornia), SIFT/FLANN (OpenCV), MAGSAC++. |
| 3.10 | Stack: Whisper, Coqui TTS, LiveKit | **CONTRADICTED** | Browser Web Speech API (speech to text), OpenRouter LLM, ElevenLabs text-to-speech with a browser fallback. |
| 3.11 | Stack: Rasterio, GDAL, SciPy | **CONTRADICTED** | Custom memory-mapped PDS4 reader; none of these libraries are used. |
| 3.12 | Stack: Docker, Flask | **CONTRADICTED** | FastAPI only; Docker files are stale and unused. |
| 3.13 | Hardware: NVIDIA GPU (RTX) | **CONTRADICTED — and it's better** | Everything runs on a **CPU**: 0.22 s (SIFT) / 2.3 s (DISK) per pair (F11). "No GPU needed" is a feasibility strength. |
| 3.14 | C++ for performance modules | **UNSUPPORTED** | None. |

## Slide 4 — Feasibility and viability

| # | Claim | Verdict | Reality |
|---|---|---|---|
| 4.1 | Technical feasibility "High … + crater spatial-pattern verification (published mid-2025)" | **FIX WORDING** | Drop the crater part. Replace with "measured on 211 test locations across 6 challenge families". |
| 4.2 | Data feasibility "High … DEM tiles … No access blockers" | **CONTRADICTED in part** | Access is fine; *co-location* is the real constraint. Of 6 products, only **2 pairs overlap**. IIRS overlaps nothing. No DEM was used. Reframe: "data is open; finding co-located cross-sensor observations is the bottleneck. Our tool screens overlap automatically and refuses non-overlapping pairs (NO_LOCK)." |
| 4.3 | Timeline: prototype without training | **TRUE** | Pretrained only. |
| 4.4 | Infrastructure "inference lightweight" | **TRUE** | CPU numbers (F11). |
| 4.5 | Scalability "generalizes … without per-region tuning" | **TRUE within tested families** | One configuration; the gain holds on held-out locations (F2, R10). |
| 4.6 | Risk: sparse-feature terrain | **TRUE, now quantified** | High- vs low-texture TMC: 18/20 vs 11/20 (F10). |
| 4.7 | Strategy: "confidence scoring flags low-confidence regions" | **TRUE, now quantified** | Coverage map + CONFIRMED/UNCONFIRMED status; CONFIRMED was right 52/52 (F2). |
| 4.8 | Strategy: illumination handled by geometry-based verification | **UNSUPPORTED** | See 2.2. |
| 4.9 | Domain gap: "DEM-based synthetic fine-tuning (Phase 2)" | **KEEP as future, now backed by numbers** | Measured where the pretrained matcher breaks: rotation ≥ 90°, footprint < 140 TMC px, azimuth ≥ 90°. Those are the fine-tuning targets. |

## Slide 5 — Impact

| # | Claim | Verdict | Reality |
|---|---|---|---|
| 5.1 | "Sub-pixel level with high inlier ratio and low RMSE" | **FIX WORDING** | Say "sub-pixel against ground truth (0.07–0.9 px) and confirmed by two independent matchers". "Low RMSE" is exactly the metric we showed can mislead. |
| 5.2 | "Supports autonomous navigation and precision landing" | **OVERCLAIM** | Our coverage map shows where the correspondences are reliable, not slope or boulder hazards. Soften to "a registration layer that downstream hazard-mapping can build on". |
| 5.3 | "Change detection, multi-temporal datasets" | **TRUE** | 3-year OHRC revisit registered (F8). |
| 5.4 | Social/economic/environmental benefit boxes | Not measurable | Generic. Judges discount these; the space is better spent on F1/F2. |

## Slide 6 — Research and references

| # | Claim | Verdict | Reality |
|---|---|---|---|
| 6.1 | ISRO study exists (arXiv 2509.04775) | **TRUE** | See 2.10. |
| 6.2 | "SuperGlue gave the most accurate, fastest results" | **TRUE as a quote of that paper** | "Most accurate" there means lowest RMSE. |
| 6.3 | "SuperGlue — AI matching model used in our solution" | **CONTRADICTED** | Not used. Cite LightGlue (Lindenberger et al., ICCV 2023) and DISK (Tyszkiewicz et al., NeurIPS 2020). |
| 6.4 | "LoFTR — AI matching model used in our solution" | **CONTRADICTED** | Not used. |
| 6.5 | Data used: NASA LRO, JAXA SELENE | **CONTRADICTED** | Only Chandrayaan-2 (6 products) was used. Move these to "next data" (they are how R11 would be met). |
| 6.6 | "Permanently shadowed regions get zero sunlight — a physical limit" | **TRUE** | And our illumination sweep puts a number on the practical limit short of that (≥ 90° azimuth change). |

## What the Verify box should say instead (one line each)

- **Perceive:** two unrelated matchers (learned DISK+LightGlue, classical SIFT), because they fail in different places (F5–F7).
- **Verify:** accept only what both agree on. Where the truth is known, CONFIRMED was right 52/52 times; RMSE alone would have let 38 wrong answers through (F1, F2).
- **Report:** true error where known; agreement, map precision and coverage where not. Never RMSE alone.

## Round 4 audit (2026-09-27)

- The illumination claim remains **PARTLY MET**: Round 4 measures DISK 3/5 at
  60° and 0/5 at 75°, 90°, 135° and 180°. The transition is gradual between
  45° and 75°, not a claimed hard cliff at 90°.
- Shadow normalization was evaluated: it improves DISK at 45° from 4/5 to 5/5,
  but does not improve 60° or 75° and leaves held-out DISK success at 5/14.
  It is tested-but-not-adopted.
- RIFT2/equivalent remains untested. It may be named only as a future test
  aimed at the measured ≥90° gap, never as part of the current stack.
- The new slide brief and figure manifest use the Round 4 illumination figures
  and the updated F13 values.
