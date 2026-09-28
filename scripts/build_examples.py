"""
build_examples.py - run every scenario and save the results as a browsable set.

    python scripts/build_examples.py

Writes to examples/ :

    index.json                 every run's metrics and figure paths
    README.md                  a table you can read without starting anything
    <id>/pair.png              the two input tiles, labelled
    <id>/keypoints.png         detections on each tile
    <id>/matches.png           inliers, and rejected correspondences
    <id>/overlay.png           A warped onto B, false-coloured
    <id>/checkerboard.png      alternating tiles from each image
    <id>/residuals.png         per-correspondence error, drawn where it occurred
    <id>/result.json           the full API response

The point of the folder is that the project can be shown, and checked, without a
running server: the figures are rendered from the same API responses the UI
draws, so if a number in the interface disagrees with one here, something is
wrong. The checkerboard is the honest test of alignment - features either run
straight across the tile boundaries or they do not.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from config import SCENES_DIR  # noqa: E402
from services.geometric import (  # noqa: E402
    decompose_homography, error_stats, ground_truth_error,
    ransac_filter, reprojection_errors, warp_image,
)
from services.feature_matching import match_images  # noqa: E402
from services.preprocessing import normalize_for_matching  # noqa: E402
from services.scenarios import list_scenarios  # noqa: E402

OUT = ROOT / "examples"

# BGR, matching the interface palette so figures and UI read as one thing.
C_A = (192, 200, 94)     # teal
C_B = (101, 167, 232)    # amber
C_BAD = (95, 113, 224)   # red
C_TEXT = (238, 234, 232)
C_PANEL = (20, 15, 12)

FONT = cv2.FONT_HERSHEY_SIMPLEX


def log(m=""):
    print(m, flush=True)


def load_gray(url: str) -> np.ndarray:
    img = cv2.imread(str(SCENES_DIR / Path(url).name), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(url)
    return img


def to_bgr(g: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)


def banner(img: np.ndarray, text: str, color=C_TEXT, height: int = 34) -> np.ndarray:
    """A caption strip above an image, so every figure is self-describing."""
    strip = np.full((height, img.shape[1], 3), C_PANEL, np.uint8)
    cv2.putText(strip, text, (10, height - 11), FONT, 0.48, color, 1, cv2.LINE_AA)
    return np.vstack([strip, img])


def side_by_side(a: np.ndarray, b: np.ndarray, gap: int = 14) -> np.ndarray:
    h = max(a.shape[0], b.shape[0])
    out = np.full((h, a.shape[1] + gap + b.shape[1], 3), C_PANEL, np.uint8)
    out[:a.shape[0], :a.shape[1]] = a
    out[:b.shape[0], a.shape[1] + gap:] = b
    return out


# --------------------------------------------------------------------------- #
# figures                                                                      #
# --------------------------------------------------------------------------- #
def fig_pair(a, b, sc) -> np.ndarray:
    ia = sc["image_a"]
    ib = sc["image_b"]

    def label(rec):
        bits = [rec.get("sensor", "?")]
        if rec.get("gsd_m"):
            bits.append(f"{rec['gsd_m']} m/px")
        if rec.get("sun_elevation") is not None:
            bits.append(f"sun {rec['sun_elevation']:.1f} deg")
        if rec.get("date") and rec["date"] != "unknown":
            bits.append(rec["date"])
        return "  ".join(bits)

    return side_by_side(
        banner(to_bgr(a), f"A  {label(ia)}", C_A),
        banner(to_bgr(b), f"B  {label(ib)}", C_B),
    )


def fig_keypoints(a, b, ka, kb) -> np.ndarray:
    ca, cb = to_bgr(a), to_bgr(b)
    for x, y in ka:
        cv2.circle(ca, (int(x), int(y)), 2, C_A, -1, cv2.LINE_AA)
    for x, y in kb:
        cv2.circle(cb, (int(x), int(y)), 2, C_B, -1, cv2.LINE_AA)
    return side_by_side(
        banner(ca, f"A  {len(ka)} keypoints", C_A),
        banner(cb, f"B  {len(kb)} keypoints", C_B),
    )


def fig_matches(a, b, ka, kb, matches, gap: int = 14) -> np.ndarray:
    """
    Inliers in teal-to-amber, rejected in red.

    Rejected correspondences are drawn first and faintly, so the surviving
    consensus is what stands out - which is the actual content of the RANSAC
    step.
    """
    ca, cb = to_bgr(a), to_bgr(b)
    canvas = side_by_side(ca, cb, gap)
    off = ca.shape[1] + gap
    overlay = canvas.copy()

    for m in matches:
        if m.get("inlier"):
            continue
        pa, pb = ka[m["idx_a"]], kb[m["idx_b"]]
        cv2.line(overlay, (int(pa[0]), int(pa[1])),
                 (int(pb[0]) + off, int(pb[1])), C_BAD, 1, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.32, canvas, 0.68, 0, canvas)

    n_in = 0
    for m in matches:
        if not m.get("inlier"):
            continue
        n_in += 1
        pa, pb = ka[m["idx_a"]], kb[m["idx_b"]]
        conf = float(m.get("confidence", 0.5))
        col = tuple(int(C_A[i] + (C_B[i] - C_A[i]) * 0.5) for i in range(3))
        col = tuple(int(c * (0.55 + conf * 0.45)) for c in col)
        cv2.line(canvas, (int(pa[0]), int(pa[1])),
                 (int(pb[0]) + off, int(pb[1])), col, 1, cv2.LINE_AA)
        cv2.circle(canvas, (int(pa[0]), int(pa[1])), 3, C_A, -1, cv2.LINE_AA)
        cv2.circle(canvas, (int(pb[0]) + off, int(pb[1])), 3, C_B, -1, cv2.LINE_AA)

    n_out = len(matches) - n_in
    return banner(canvas, f"{n_in} inliers (bright) and {n_out} rejected (red) of {len(matches)}")


def fig_overlay(warped, b) -> np.ndarray:
    """
    A in red, B in cyan. Grey means the two agree; coloured fringes are the error.

    A 50/50 blend hides misalignment in a uniform haze; this does not.
    """
    h, w = b.shape[:2]
    if warped.shape[:2] != (h, w):
        warped = cv2.resize(warped, (w, h), interpolation=cv2.INTER_LINEAR)
    out = np.zeros((h, w, 3), np.uint8)
    out[:, :, 2] = warped
    out[:, :, 1] = b
    out[:, :, 0] = b
    return banner(out, "A warped onto B  -  grey = registered, red/cyan fringe = residual error")


def fig_checkerboard(warped, b, cells: int = 8) -> np.ndarray:
    """Alternating tiles. Features either run straight across the seams or they do not."""
    h, w = b.shape[:2]
    if warped.shape[:2] != (h, w):
        warped = cv2.resize(warped, (w, h), interpolation=cv2.INTER_LINEAR)
    out = to_bgr(b.copy())
    wb = to_bgr(warped)
    ch, cw = max(1, h // cells), max(1, w // cells)
    for r in range(cells):
        for c in range(cells):
            if (r + c) % 2:
                continue
            y0, x0 = r * ch, c * cw
            out[y0:y0 + ch, x0:x0 + cw] = wb[y0:y0 + ch, x0:x0 + cw]
    for r in range(1, cells):
        cv2.line(out, (0, r * ch), (w, r * ch), (60, 60, 60), 1)
        cv2.line(out, (r * cw, 0), (r * cw, h), (60, 60, 60), 1)
    return banner(out, f"{cells}x{cells} checkerboard of A-warped and B  -  look along the seams")


def fig_residuals(b, ka, inliers, errors) -> np.ndarray:
    """Each inlier drawn where it sits, sized and coloured by its own error."""
    out = to_bgr((b * 0.45).astype(np.uint8))
    if len(errors):
        emax = max(float(np.percentile(errors, 95)), 1e-6)
        for m, e in zip(inliers, errors):
            x, y = ka[m["idx_a"]]
            t = min(1.0, float(e) / emax)
            col = (int(192 * (1 - t) + 95 * t), int(200 * (1 - t) + 113 * t),
                   int(94 * (1 - t) + 224 * t))
            cv2.circle(out, (int(x), int(y)), int(3 + t * 8), col, 1, cv2.LINE_AA)
            cv2.circle(out, (int(x), int(y)), 2, col, -1, cv2.LINE_AA)
        cap = (f"{len(errors)} inliers  -  small teal = low error, "
               f"large red = high (p95 {emax:.2f} px)")
    else:
        cap = "no inliers to plot"
    return banner(out, cap)


# --------------------------------------------------------------------------- #
def run_scenario(sc: dict) -> dict | None:
    sid = sc["id"]
    log(f"\n[{sid}] {sc['title']}  ({sc['provenance']})")
    out_dir = OUT / sid
    out_dir.mkdir(parents=True, exist_ok=True)

    a = load_gray(sc["image_a"]["url"])
    b = load_gray(sc["image_b"]["url"])
    if b.shape != a.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_CUBIC)

    t0 = time.perf_counter()
    pa, _ = normalize_for_matching(a)
    pb, _ = normalize_for_matching(b)
    mr = match_images(pa, pb)
    if not mr.matches:
        log("  no correspondences; skipped")
        return None

    inliers, H, diag = ransac_filter(mr.keypoints_a, mr.keypoints_b, mr.matches)
    keys = {(m["idx_a"], m["idx_b"]) for m in inliers}
    all_matches = [dict(m, inlier=(m["idx_a"], m["idx_b"]) in keys) for m in mr.matches]
    errors = reprojection_errors(mr.keypoints_a, mr.keypoints_b, inliers, H)
    stats = error_stats(errors)
    elapsed = (time.perf_counter() - t0) * 1000

    gt_h = sc.get("ground_truth_homography")
    gt = ground_truth_error(H, np.array(gt_h) if gt_h else None, a.shape) if gt_h else None
    gsd = sc["image_a"].get("gsd_m") or 0.0

    cv2.imwrite(str(out_dir / "pair.png"), fig_pair(a, b, sc))
    cv2.imwrite(str(out_dir / "keypoints.png"),
                fig_keypoints(a, b, mr.keypoints_a, mr.keypoints_b))
    cv2.imwrite(str(out_dir / "matches.png"),
                fig_matches(a, b, mr.keypoints_a, mr.keypoints_b, all_matches))
    if H is not None:
        warped = warp_image(a, H, b.shape[:2])
        cv2.imwrite(str(out_dir / "overlay.png"), fig_overlay(warped, b))
        cv2.imwrite(str(out_dir / "checkerboard.png"), fig_checkerboard(warped, b))
    cv2.imwrite(str(out_dir / "residuals.png"),
                fig_residuals(b, mr.keypoints_a, inliers, errors))

    entry = {
        "id": sid,
        "title": sc["title"],
        "provenance": sc["provenance"],
        "challenge": sc.get("challenge", ""),
        "notes": sc.get("notes", ""),
        "sensor_a": sc["image_a"].get("sensor"),
        "sensor_b": sc["image_b"].get("sensor"),
        "gsd_m": gsd,
        "tile_px": [int(a.shape[1]), int(a.shape[0])],
        "detector": mr.detector,
        "matcher": mr.matcher,
        "metrics": {
            "num_keypoints_a": int(len(mr.keypoints_a)),
            "num_keypoints_b": int(len(mr.keypoints_b)),
            "num_matches": len(mr.matches),
            "num_inliers": len(inliers),
            "inlier_ratio": round(len(inliers) / max(len(mr.matches), 1), 4),
            "rmse_px": round(stats["rmse"], 4),
            "median_error_px": round(stats["median"], 4),
            "p90_error_px": round(stats["p90"], 4),
            "rmse_m": round(stats["rmse"] * gsd, 4) if gsd else None,
            "degenerate": bool(diag.get("degenerate")),
            "warning": diag.get("warning", ""),
            "elapsed_ms": round(elapsed, 1),
        },
        "ground_truth_error": gt,
        "homography": H.tolist() if H is not None else None,
        "homography_decomposed": decompose_homography(H),
        "coreg": sc.get("coreg"),
        "figures": {
            n: f"examples/{sid}/{n}.png"
            for n in ("pair", "keypoints", "matches", "overlay", "checkerboard", "residuals")
            if (out_dir / f"{n}.png").exists()
        },
    }
    (out_dir / "result.json").write_text(json.dumps(entry, indent=2), encoding="utf-8")

    gt_s = f", true error {gt['mean_corner_error_px']:.2f} px" if gt else ""
    log(f"  {len(inliers)}/{len(mr.matches)} inliers "
        f"({entry['metrics']['inlier_ratio'] * 100:.0f}%), "
        f"RMSE {stats['rmse']:.3f} px{gt_s}")
    return entry


def detector_comparison(scenarios: list) -> list:
    """
    Run both detectors on every scenario that has a known transform.

    This is the most useful thing the examples folder contains, because it shows
    the one failure mode a demo can otherwise hide. On the illumination scenario
    SIFT locks onto five mutually consistent but wrong correspondences and fits
    them exactly, reporting a spectacular 0.14 px reprojection RMSE while sitting
    hundreds of pixels from the true transform. Only the ground-truth column
    reveals it. Nothing in the pipeline's own output would.
    """
    rows = []
    for sc in scenarios:
        gt_h = sc.get("ground_truth_homography")
        if not gt_h:
            continue
        for det, label in (("auto", "DISK + LightGlue"), ("sift", "SIFT + FLANN")):
            try:
                a = load_gray(sc["image_a"]["url"])
                b = load_gray(sc["image_b"]["url"])
                if b.shape != a.shape:
                    b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_CUBIC)
                pa, _ = normalize_for_matching(a)
                pb, _ = normalize_for_matching(b)
                mr = match_images(pa, pb, detector=det)
                if not mr.matches:
                    continue
                inl, H, diag = ransac_filter(mr.keypoints_a, mr.keypoints_b, mr.matches)
                errs = reprojection_errors(mr.keypoints_a, mr.keypoints_b, inl, H)
                st = error_stats(errs)
                gt = ground_truth_error(H, np.array(gt_h), a.shape)
            except Exception as exc:  # noqa: BLE001
                log(f"  [warn] {sc['id']}/{det}: {exc}")
                continue

            rows.append({
                "scenario": sc["id"],
                "scenario_title": sc["title"],
                # What actually ran, not what was asked for: a failed learned
                # path falls back to SIFT, and labelling by request once
                # published SIFT numbers under the DISK + LightGlue name.
                "detector": f"{mr.detector} + {mr.matcher}",
                "requested": label,
                "num_matches": len(mr.matches),
                "num_inliers": len(inl),
                "inlier_ratio": round(len(inl) / max(len(mr.matches), 1), 4),
                "rmse_px": round(st["rmse"], 4),
                "true_error_px": round(gt["mean_corner_error_px"], 3) if gt else None,
                "degenerate": bool(diag.get("degenerate")),
            })
            t = rows[-1]
            log(f"  {sc['id']:24s} {label:17s} "
                f"inl {t['num_inliers']:4d}/{t['num_matches']:<4d} "
                f"RMSE {t['rmse_px']:7.3f}  true {t['true_error_px']}")
    return rows


def write_readme(entries: list, comparison: list) -> None:
    lines = [
        "# Worked examples",
        "",
        "Generated by `python scripts/build_examples.py`. Each row is a real run of the",
        "pipeline; the figures beside it are rendered from that same run.",
        "",
        "**Provenance** is stated for every scenario and carried through the interface:",
        "",
        "- `REAL` - two genuine Chandrayaan-2 observations of the same ground.",
        "- `DERIVED` - real pixels through a sensor or band model, displaced by a transform we chose.",
        "- `SIMULATED` - real pixels, modelled illumination, displaced by a transform we chose.",
        "",
        "Only DERIVED and SIMULATED can report a **ground-truth error**, because only there",
        "do we know the answer. That column is the one to trust: reprojection RMSE just says",
        "the inliers agree with each other, and a confident fit to wrong correspondences can",
        "post a good RMSE while being badly wrong.",
        "",
        "| Scenario | Provenance | Inliers | Inlier ratio | RMSE (px) | On ground | Ground-truth error |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in entries:
        m = e["metrics"]
        gt = e.get("ground_truth_error")
        lines.append(
            f"| {e['title']} | `{e['provenance']}` | {m['num_inliers']}/{m['num_matches']} | "
            f"{m['inlier_ratio'] * 100:.1f}% | {m['rmse_px']:.3f} | "
            f"{(str(round(m['rmse_m'], 3)) + ' m') if m.get('rmse_m') else '-'} | "
            f"{(str(round(gt['mean_corner_error_px'], 2)) + ' px') if gt else 'n/a'} |"
        )

    if comparison:
        lines += [
            "",
            "## Why reprojection RMSE is not enough",
            "",
            "Both detectors, run on the scenarios where the answer is known. Read the",
            "last two columns together:",
            "",
            "| Scenario | Detector | Inliers | RMSE (px) | True error (px) |",
            "|---|---|---|---|---|",
        ]
        for r in comparison:
            flag = ""
            if r["true_error_px"] is not None and r["true_error_px"] > 50:
                flag = "  **&larr; wrong**"
            lines.append(
                f"| {r['scenario_title']} | {r['detector']} | "
                f"{r['num_inliers']}/{r['num_matches']} | {r['rmse_px']:.3f} | "
                f"{r['true_error_px']}{flag} |"
            )
        lines += [
            "",
            "The illumination row is the one to look at. SIFT reports the best",
            "reprojection RMSE in the whole table while being hundreds of pixels from the",
            "right answer: under opposed lighting it locks onto a handful of mutually",
            "consistent but incorrect correspondences and fits them exactly. A pipeline",
            "reporting only RMSE would call that its best result.",
            "",
            "This is also why the interface shows ground-truth error above RMSE wherever",
            "it exists, and why it flags a fit with too few inliers as degenerate.",
            "",
        ]

    lines += ["", "## Figures", ""]
    for e in entries:
        lines += [
            f"### {e['title']}  ({e['provenance']})",
            "",
            f"{e['sensor_a']} against {e['sensor_b']} at {e['gsd_m']} m/px. {e['challenge']}",
            "",
            e["notes"],
            "",
        ]
        for name, path in e["figures"].items():
            lines.append(f"![{name}](../{path})")
        lines.append("")

    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    scenarios = list_scenarios()
    if not scenarios:
        log("No scenarios. Run: python scripts/build_scenarios.py")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    log(f"Rendering worked examples for {len(scenarios)} scenario(s) -> {OUT}")

    entries = [e for sc in scenarios if (e := run_scenario(sc)) is not None]
    if not entries:
        log("\nNothing produced.")
        return 1

    log("\n[comparison] both detectors on the scenarios with a known transform")
    comparison = detector_comparison(scenarios)

    (OUT / "index.json").write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "examples": entries,
        "detector_comparison": comparison,
    }, indent=2), encoding="utf-8")
    write_readme(entries, comparison)

    log(f"\n[done] {len(entries)} example(s)")
    log(f"  {OUT / 'index.json'}")
    log(f"  {OUT / 'README.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
