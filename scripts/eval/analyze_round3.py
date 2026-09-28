"""
Round 3 analyses. No new matching: everything is computed from the Round 2
inlier sets saved in eval/cache/runs/round_2/.

    python scripts/eval/analyze_round3.py

A. Trust gates, calibrated where the answer is known (F3-F6).
   Can the pipeline tell, without ground truth, when its own answer is wrong?
   Gates tested: inlier count >= 15; the two arms agreeing within 3 px; both.
   For each: of the results the gate accepts, how many are actually right
   (grid error <= 2 px), and how many right results it rejects. This is also
   the calibration of the 'confirmed' rule used for the real pairs.

B. Is the residual on real pairs geometry or noise? (stereo question)
   1. Spatial coherence: correlation between each inlier's residual vector and
      the mean residual of its 8 nearest neighbours. Noise -> ~0. A surface
      the homography cannot describe (parallax from relief) -> high.
   2. Model test: held-out error of a homography vs a smooth non-planar model
      (homography + 2nd-order polynomial correction), same 70/30 splits. If the
      extra freedom only fits noise, held-out error does not drop.
   Control: F6 (synthetic, exactly planar) must show neither effect.

C. Registration-map precision on real pairs (added metric, see log).
   Split the inliers into random halves, fit a homography to each, measure the
   grid disagreement between the two maps; median over 20 splits, divided by
   2 (two independent half-size fits -> a full-size fit is roughly half as
   variable in distance terms: sqrt(2) for halving N, sqrt(2) for differencing
   two fits). Precision, not truth: a bias shared by both halves is invisible.
"""
from __future__ import annotations

import json

import cv2
import numpy as np
import pandas as pd

from common import CACHE_DIR, RESULTS_DIR, RUNS_DIR, map_disagreement_px, save_json, seed_for

TAG = "round_2"
ARMS = ("M1_disk_lightglue", "M2_sift_flann")
SHAPE = (1024, 1024)


def load_run(inst_id, arm):
    d = np.load(RUNS_DIR / TAG / f"{inst_id}__{arm}.npz")
    H = d["H"] if d["H"].size == 9 else None
    return H, d["pts_a"].astype(np.float64), d["pts_b"].astype(np.float64)


# --------------------------------------------------------------------------- #
# A. trust gates                                                               #
# --------------------------------------------------------------------------- #
def trust_gates(df, inst):
    rows = []
    gt = df[df.grid_err_px.notna() | df.verdict.isin(["FAILURE", "MARGINAL", "SUCCESS"])]
    gt = gt[gt.family.str[:2].isin(["F3", "F4", "F5", "F6"]) & (gt.status == "OK")]
    for iid, g in gt.groupby("id"):
        shape = SHAPE
        Hs = {arm: load_run(iid, arm)[0] for arm in ARMS}
        agree = map_disagreement_px(Hs[ARMS[0]], Hs[ARMS[1]], shape) \
            if all(h is not None for h in Hs.values()) else None
        if inst[iid].get("family", "").startswith("F5"):
            shape = (744, 248)
            agree = map_disagreement_px(Hs[ARMS[0]], Hs[ARMS[1]], shape) \
                if all(h is not None for h in Hs.values()) else None
        for r in g.itertuples():
            ge = r.grid_err_px
            rows.append({"id": iid, "family": r.family, "arm": r.arm,
                         "correct": bool(pd.notna(ge) and ge <= 2.0),
                         "has_model": pd.notna(ge),
                         "inl15": bool(r.n_inliers >= 15 and not str(r.degenerate).lower() == "true"),
                         "agree3": bool(agree is not None and agree <= 3.0),
                         "rmse_ok": bool(pd.notna(r.rmse_px) and r.rmse_px < 1.5)})
    t = pd.DataFrame(rows)
    t = t[t.has_model]
    out = {}
    for name, acc in (("rmse<1.5 only (what most pipelines report)", t.rmse_ok),
                      ("inliers>=15", t.inl15),
                      ("arms agree <=3 px", t.agree3),
                      ("inliers>=15 AND agree", t.inl15 & t.agree3)):
        a = t[acc]
        rej = t[~acc]
        out[name] = {
            "results_with_a_model": int(len(t)),
            "accepted": int(len(a)),
            "accepted_but_wrong": int((~a.correct).sum()),
            "precision": round(float(a.correct.mean()), 4) if len(a) else None,
            "right_but_rejected": int(rej.correct.sum()),
            "wrong_total": int((~t.correct).sum()),
        }
    return out


# --------------------------------------------------------------------------- #
# B. geometry vs noise                                                         #
# --------------------------------------------------------------------------- #
def _poly_feats(p, s=1024.0):
    x, y = p[:, 0] / s - 0.5, p[:, 1] / s - 0.5
    return np.stack([x * x, x * y, y * y], 1)


def _fit_h_poly(pa, pb):
    """Homography, then a 2nd-order polynomial correction to what it leaves."""
    H, _ = cv2.findHomography(pa.reshape(-1, 1, 2), pb.reshape(-1, 1, 2), 0)
    if H is None:
        return None
    proj = cv2.perspectiveTransform(pa.reshape(-1, 1, 2), H).reshape(-1, 2)
    F = np.hstack([_poly_feats(pa), np.ones((len(pa), 1))])
    coef, *_ = np.linalg.lstsq(F, pb - proj, rcond=None)
    return H, coef


def _apply_h_poly(model, pa):
    H, coef = model
    proj = cv2.perspectiveTransform(pa.reshape(-1, 1, 2), H).reshape(-1, 2)
    return proj + np.hstack([_poly_feats(pa), np.ones((len(pa), 1))]) @ coef


def geometry_vs_noise(pa, pb, H, seed, splits=20):
    n = len(pa)
    if n < 40 or H is None:
        return None
    proj = cv2.perspectiveTransform(pa.reshape(-1, 1, 2), H).reshape(-1, 2)
    res = pb - proj
    # spatial coherence of residuals
    d = np.linalg.norm(pa[:, None, :] - pa[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    nn = np.argsort(d, axis=1)[:, :8]
    neigh = res[nn].mean(axis=1)
    coh = float(np.mean([np.corrcoef(res[:, k], neigh[:, k])[0, 1] for k in (0, 1)]))
    # held-out: homography vs homography + smooth correction
    rng = np.random.default_rng(seed)
    k = int(n * 0.7)
    e_h, e_p = [], []
    for _ in range(splits):
        perm = rng.permutation(n)
        tr, te = perm[:k], perm[k:]
        Hh, _ = cv2.findHomography(pa[tr].reshape(-1, 1, 2), pb[tr].reshape(-1, 1, 2), 0)
        m = _fit_h_poly(pa[tr], pb[tr])
        if Hh is None or m is None:
            continue
        ph = cv2.perspectiveTransform(pa[te].reshape(-1, 1, 2), Hh).reshape(-1, 2)
        pp = _apply_h_poly(m, pa[te])
        e_h.append(np.sqrt(np.mean(np.sum((ph - pb[te]) ** 2, 1))))
        e_p.append(np.sqrt(np.mean(np.sum((pp - pb[te]) ** 2, 1))))
    return {"coherence": coh, "heldout_h": float(np.median(e_h)),
            "heldout_hpoly": float(np.median(e_p)),
            "residual_rms": float(np.sqrt(np.mean(np.sum(res ** 2, 1))))}


# --------------------------------------------------------------------------- #
# C. map precision                                                             #
# --------------------------------------------------------------------------- #
def map_precision(pa, pb, seed, splits=20):
    n = len(pa)
    if n < 20:
        return None
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(splits):
        perm = rng.permutation(n)
        h1, h2 = perm[: n // 2], perm[n // 2:]
        H1, _ = cv2.findHomography(pa[h1].reshape(-1, 1, 2), pb[h1].reshape(-1, 1, 2), 0)
        H2, _ = cv2.findHomography(pa[h2].reshape(-1, 1, 2), pb[h2].reshape(-1, 1, 2), 0)
        v = map_disagreement_px(H1, H2, SHAPE)
        if v is not None:
            out.append(v)
    return float(np.median(out)) / 2.0 if out else None


def main():
    df = pd.read_csv(RESULTS_DIR / f"{TAG}.csv")
    inst = {r["id"]: r for r in json.loads((CACHE_DIR / "instances.json").read_text())["instances"]}

    A = trust_gates(df, inst)

    rows = []
    for r in df[(df.status == "OK") & df.family.str[:2].isin(["F1", "F2", "F6"])].itertuples():
        if r.family.startswith("F6") and not (r.level_name == "rot" and r.level in (0, 10)):
            continue
        H, pa, pb = load_run(r.id, r.arm)
        g = geometry_vs_noise(pa, pb, H, seed_for(r.id))
        mp = map_precision(pa, pb, seed_for(r.id + "mp")) if r.family[:2] in ("F1", "F2") else None
        if g:
            rows.append({"id": r.id, "family": r.family, "arm": r.arm, "terrain": r.terrain,
                         "verdict": r.verdict, "n_inliers": r.n_inliers,
                         "heldout_px": r.heldout_px, "map_precision_px": mp, **g})
    B = pd.DataFrame(rows)
    B.to_csv(RESULTS_DIR / "round_3_geometry.csv", index=False)

    summary = {"A_trust_gates_on_ground_truth": A, "B_C_by_family_arm": {}}
    for (fam, arm), g in B.groupby(["family", "arm"]):
        summary["B_C_by_family_arm"][f"{fam} | {arm}"] = {
            "n": int(len(g)),
            "coherence_median": round(float(g.coherence.median()), 3),
            "heldout_homography_median": round(float(g.heldout_h.median()), 3),
            "heldout_h_plus_poly_median": round(float(g.heldout_hpoly.median()), 3),
            "heldout_drop_pct_median": round(float(((g.heldout_h - g.heldout_hpoly) / g.heldout_h * 100).median()), 1),
            "map_precision_median": (round(float(g.map_precision_px.median()), 3)
                                     if g.map_precision_px.notna().any() else None),
            "map_precision_lt1_frac": (round(float((g.map_precision_px < 1).mean()), 3)
                                       if g.map_precision_px.notna().any() else None),
        }
    for key in ("F2_real_tmc",):
        g = B[B.family == key]
        mar = g[g.verdict == "MARGINAL"]
        suc = g[g.verdict == "SUCCESS"]
        summary[f"{key}_marginal_vs_success"] = {
            "marginal_n": int(len(mar)), "success_n": int(len(suc)),
            "coherence_marginal": round(float(mar.coherence.median()), 3) if len(mar) else None,
            "coherence_success": round(float(suc.coherence.median()), 3) if len(suc) else None,
            "heldout_drop_pct_marginal": round(float(((mar.heldout_h - mar.heldout_hpoly) / mar.heldout_h * 100).median()), 1) if len(mar) else None,
        }
    save_json(RESULTS_DIR / "round_3_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
