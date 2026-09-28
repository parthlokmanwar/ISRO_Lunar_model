# Evaluation prompt — Lunar Correspondence Engine (SIH26166)

Revised 2026-09-18 from the draft prompt written in the PPT-planning chat. The
draft's method (observe → hypothesise → test narrowly → analyse → observe again)
is kept unchanged. What is added here are facts about *this* dataset and codebase
that the draft could not know, and the rigour rules that stop the evaluation
from quietly grading itself. Sections marked **[NEW]** are additions.

---

## CONTEXT

Lunar Correspondence Engine (SIH26166). Read, in order:
`SESSIONHANDOFF20260909.md`, the latest `SESSIONHANDOFF*.md`, `README.md`,
`examples/README.md`.

Current state: FastAPI backend, 5 scenarios, DISK+LightGlue primary matcher,
SIFT+FLANN baseline, MAGSAC++, correlation-lock geolocation fix,
REAL/DERIVED/SIMULATED provenance. CPU only (no CUDA); one match ≈ 2 s.

**The deliverable of this work is measured evidence, not features.** Build only
what is needed to measure something. Every build task must end in a number, a
table, a figure, or a documented failure case. Do not change the UI.

---

## [NEW] DATA REALITY — read before planning any round

Measured on 2026-09-18 from the PDS4 labels:

| Product | Where | Sun el / az |
|---|---|---|
| OHRC 2021-04-02 (d18) | 0.2–1.1°N, 23.4–23.5°E | 10.1° / 268.8° |
| OHRC 2024-03-30 (d18) | 0.4°S–0.4°N, 23.5–23.6°E | 7.3° / 269.8° |
| OHRC 2023-08-20 (n18) | **62.4–63.3°N, 76.4–76.6°E** | 15.7° / 119.8° |
| TMC-2 fore + nadir (2019-12-08) | 0–30°N, 65.7–66.4°E | 63.7° / 240.6° |
| IIRS (2020-01-09) | 24.7°S–5.1°N, 0.4–1.2°E | not in label |

Only **two** real overlapping pairs exist:
- OHRC 2021 × OHRC 2024 — overlap ≈ 1.2 km × 4.5 km (≈ 60 non-overlapping
  1024 px tiles at 0.3 m/px, before removing fill).
- TMC-2 fore × nadir — overlap ≈ 33 km × 876 km, spanning ~30° of latitude
  (hundreds of tiles, across many terrain types).

Consequences:
1. "10–15 pairs per scenario" means **10–15+ tile locations** sampled along
   these overlaps, not 10–15 separate image products. Do not invent pairs.
2. The real OHRC pair differs by only ~3° sun elevation and ~1° azimuth. It
   tests **temporal change**, not illumination change. Do not use it as
   evidence of illumination invariance.
3. The TMC-2 pair is **stereo**. A single homography is the wrong model on
   relief; part of its residual is terrain height, not matching error. Treat
   large structured residuals there as a possible finding (parallax), not as
   a bug to "fix" by loosening thresholds.
4. The 2023 OHRC strip overlaps nothing, but it is real high-latitude terrain
   under a different sun. It is a legitimate source for new DERIVED/SIMULATED
   locations, which adds terrain diversity the equatorial strips lack.
5. DERIVED/SIMULATED scenarios can be regenerated at many source locations
   with many transforms, and **every one carries ground truth**. This is
   where large N with true error is cheap. Use it.

---

## [NEW] HOW ACCURACY IS JUDGED

This project's headline finding is that RMSE lies: SIFT posted RMSE 0.138 px
while 821 px from the truth. The evaluation must not fall into the same trap.

- **DERIVED/SIMULATED:** true corner error against the known homography is
  the primary metric. RMSE is secondary.
- **REAL pairs (no ground truth):** never report RMSE alone. Also report:
  - **Held-out error**: fit on a random 70% of inliers, measure the error on
    the other 30%; repeat 20× with fixed seeds; report the median.
  - **Independent agreement**: the corner distance between homographies from
    two independent methods (e.g. DISK+LightGlue vs SIFT, or vs the
    correlation-lock offset). Agreement between unrelated methods is evidence;
    agreement of a method with itself is not.
  - **Photometric check**: NCC of the aligned tiles before and after warping.
- **Degenerate fits** (≤ 4 inliers, or ≤ 8 for any success verdict) are never
  successes, whatever their RMSE.

### Pre-registered definitions (write these into the log BEFORE Round 1 runs)

Fix these before seeing any numbers, and do not change them afterwards. If a
change is justified, add a new definition and report both.

- **SUCCESS / MARGINAL / FAILURE** — thresholds on true error (or held-out
  error for REAL), plus minimum inlier count. Example: SUCCESS = true error
  ≤ 2 px and ≥ 15 inliers; FAILURE = true error > 10 px, or < 8 inliers, or
  no model.
- **Uniformity** — one fixed formula, e.g. the fraction of a 4×4 grid's cells
  holding ≥ 1 inlier, and the inlier convex-hull area ÷ tile area.
- **Terrain class** — objective, from a measured quantity (e.g.
  `texture_score` in `services/raster.py`, split at fixed quantiles), assigned
  before matching. Never label terrain by eye after seeing the result.

### Dev / test split — stops us overfitting the fix

Split tile locations into **dev** (used to diagnose and design fixes) and
**test** (held out). A fix found in Round N is only claimed if it also improves
the **test** locations. Report both. This is what makes the improvement
claims defensible in front of judges.

---

## GOVERNING RULE

We do not know in advance how any external technique will behave on real
Chandrayaan-2 data. No technique gets named as "the plan" because a paper,
benchmark, or reputation recommends it. A technique is only tested if a
specific, observed failure in OUR data gives a concrete reason to try it.
Every addition traces back to a numbered observation, never the reverse.

This is a repeating cycle, not a one-pass checklist:
`OBSERVE → HYPOTHESIZE → TEST NARROWLY → ANALYZE WHY → OBSERVE AGAIN`

---

## ROUND STRUCTURE (repeat every cycle)

### STEP 1 — OBSERVE
Run the current pipeline across the tile locations and derived instances for
the scenario type under study. Log every run:

| Pair ID | Scenario | Split | Terrain | Inliers | RMSE | Held-out / true err | P90 | Uniformity | Runtime | Verdict | Note |

Group failures into **patterns** (e.g. "5 of 8 low-texture tiles across two
scenario types gave < 15 inliers regardless of matcher"). Keep the pair IDs
behind each pattern.

### STEP 2 — HYPOTHESIZE
For each pattern, write specific, falsifiable causes, not fixes. Always
include at least one **non-tool** cause (preprocessing, data choice, scene
content, model choice such as homography-vs-parallax) before any
"a different matcher would help" cause.

A lead already observed on 2026-09-18, not yet tested: on s1, CLAHE clip 8
(other settings default) gave 72 matches / 49 inliers, against 31 / 15 at
clip 3. Preprocessing may be limiting the real pairs more than the matcher.

### STEP 3 — TEST NARROWLY
The smallest test that separates the competing hypotheses, on the failing
**dev** pairs only. Change one thing at a time. If a technique is expensive
to integrate (e.g. a dense matcher on CPU), try it on the 2–3 worst cases
first and record runtime per pair. Runtime is a result, not a nuisance.

Candidate tools, only once a hypothesis names their target cause (examples,
not a plan): RoMa or MINIMA-RoMa (dense, large scale or modality gaps),
XoFTR (cross-modal), ALIKED/SuperPoint + LightGlue (detector swap), LoFTR
(detector-free, ships with kornia).

### STEP 4 — ANALYZE WHY
Look at the matched points on the images, not just the score. Save the
figure. Explain the mechanism. Log positive, negative and inconclusive
results with equal care in `docs/EXPERIMENT_LOG.md`. "We tried X and it was
worse because Y" is evidence.

### STEP 5 — OBSERVE AGAIN
Re-run on the affected scenario, and on adjacent ones, to catch side effects
(a fix for low texture may hurt cratered terrain). Confirm on the **test**
split. A new failure pattern starts a new round.

---

## CONVERGENCE

Once cycling is exhausted or time-boxed, write the final summary in
`docs/EXPERIMENT_LOG.md`: the evidence-based strategy the rounds actually
support. Every claim cites its round number.

---

## [NEW] DELIVERABLES

- `docs/EXPERIMENT_LOG.md` — pre-registered definitions, every round, and the
  convergence summary.
- `scripts/eval/` — the scripts that produced every number. One command
  regenerates every table from scratch (fixed seeds, versions recorded).
- `eval/results/round_N.csv` — raw per-pair rows for each round. Never
  overwrite an earlier round.
- `eval/figures/` — the figures cited in the log.
- `docs/REQUIREMENTS_SCORECARD.md` — each problem-statement requirement →
  the measured number that addresses it → round number → honest status
  (met / partly met / not met, with the reason). Requirements to cover, at
  least: sub-pixel / high accuracy, uniform distribution of correspondences,
  multi-sensor, multi-temporal, illumination (sun-angle) invariance, scale
  difference, runtime / practicality. Paste the exact PS text into
  `docs/PS.md` so the scorecard quotes it word for word.
- `docs/FINDINGS.md` — short, PPT-ready: one row per claim, with the number,
  its confidence (N, split), the round, and the figure path. This is the file
  taken to the PPT chat.

---

## OUT OF SCOPE for this work

Crater-relationship verification, the multi-modal fusion network, model
fine-tuning, Docker, UI changes. If a hypothesis genuinely calls for one of
these, write a short spec (what data, what expected gain, measured against
which round), not code.

The fine-tuning spec should be backed by a **domain-gap measurement** from
the rounds: where the Earth-trained matcher fails on lunar terrain, by
terrain class, with numbers.

---

## HARD RULES

- No named external technique enters as a plan before a hypothesis naming its
  target cause exists in the log.
- At least one non-tool hypothesis per pattern, before any tool swap.
- Definitions are fixed before the numbers are seen.
- Fixes are claimed only if they hold on the held-out test split.
- RMSE is never reported alone as accuracy.
- Every presentation claim traces to a round number and a regenerable script.
- Negative and surprising results are as valuable as positive ones and are
  never omitted.
- Commit after each round (`git`), so every number can be traced to the code
  that produced it.
