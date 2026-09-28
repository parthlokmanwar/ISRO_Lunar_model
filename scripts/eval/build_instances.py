"""
Build the evaluation instances once, so every round runs on identical pairs.

    python scripts/eval/build_instances.py [--families F1,F2,...]

Writes tiles to eval/cache/tiles/ and the instance list (with ground-truth
homographies, split, texture and seeds) to eval/cache/instances.json. The
families, sweep levels and split rules are the ones pre-registered in
docs/EXPERIMENT_LOG.md section 0.2 / 0.6.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from common import CACHE_DIR, ROOT, TILES_DIR, seed_for

from services.coreg import locate_overlap  # noqa: E402
from services.geo import footprint_from_meta, overlap_window  # noqa: E402
from services.pds4 import discover_products  # noqa: E402
from services.raster import (  # noqa: E402
    PixelWindow, centred_window, read_qub_window, read_window,
    texture_score, to_uint8, usable_fraction,
)
from services.synth import (  # noqa: E402
    degrade_to_sensor, relight, similarity_homography, upsample_to,
)

INSTANCES_PATH = CACHE_DIR / "instances.json"
TILE = 1024
MIN_USABLE = 0.55
TMC_GSD_M = 4.46


def log(msg: str) -> None:
    print(msg, flush=True)


def save_tile(img: np.ndarray, name: str) -> str:
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(TILES_DIR / f"{name}.png"), img)
    return f"{name}.png"


def T(dx: float, dy: float) -> np.ndarray:
    return np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], dtype=np.float64)


def pointing(shape, rng, rotation=None, zoom=None) -> np.ndarray:
    """
    Small random 'pointing' transform (pre-registered ranges): rotation +-5 deg,
    zoom 0.95-1.05, shift +-20 px, keystone +-5e-6. F6 overrides rotation/zoom.
    """
    rot = rng.uniform(-5, 5) if rotation is None else rotation
    z = rng.uniform(0.95, 1.05) if zoom is None else zoom
    H = similarity_homography(shape, rot, z, rng.uniform(-20, 20), rng.uniform(-20, 20))
    tilt = rng.uniform(-5e-6, 5e-6)
    H[2, 0] = tilt
    H[2, 1] = tilt * 0.4
    return H


def warp_crop(big: np.ndarray, H_crop: np.ndarray, m: int, out: int) -> np.ndarray:
    """
    Warp a padded read and keep the central crop, so the kept region never
    contains mirrored border content. H_crop is defined in crop coordinates;
    x_full = x_crop + m, so H_full = T(m) H_crop T(-m).
    """
    H_full = T(m, m) @ H_crop @ T(-m, -m)
    w = cv2.warpPerspective(big, H_full, (big.shape[1], big.shape[0]),
                            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    return w[m:m + out, m:m + out]


def products():
    by = {}
    for p in discover_products(ROOT):
        by[p["meta"]["product_id"]] = p

    def find(sub, sensor):
        for pid, p in by.items():
            if sub in pid and p["meta"]["sensor"] == sensor:
                return p
        raise SystemExit(f"product {sub} ({sensor}) not found")

    return {
        "ohrc_2021": find("20210402", "OHRC"),
        "ohrc_2024": find("20240330", "OHRC"),
        "ohrc_2023": find("20230820", "OHRC"),
        "tmc_fore": find("tmc_ncf", "TMC-2"),
        "tmc_nadir": find("tmc_ncn", "TMC-2"),
        "iirs": find("iir_nri", "IIRS"),
    }


def base_record(fid, family, provenance, loc_index, split, **kw):
    r = {"id": fid, "family": family, "provenance": provenance,
         "loc_index": loc_index, "split": split, "seed": seed_for(fid)}
    r.update(kw)
    return r


# --------------------------------------------------------------------------- #
# F1 / F2 - real pairs                                                          #
# --------------------------------------------------------------------------- #
def build_real(P, family, key_a, key_b, n_across, n_along):
    a, b = P[key_a], P[key_b]
    fa, fb = footprint_from_meta(a["meta"]), footprint_from_meta(b["meta"])
    win = overlap_window(fa, fb)
    gsd_a = float(np.mean(fa.ground_sample_distance_m()))
    gsd_b = float(np.mean(fb.ground_sample_distance_m()))
    log(f"[{family}] overlap {win.width_m:.0f} m x {win.height_m:.0f} m; "
        f"GSD A {gsd_a:.3f} m, B {gsd_b:.3f} m")
    out, seen = [], []
    for i in range(n_along):
        lat = win.lat_min + (win.lat_max - win.lat_min) * (i + 0.5) / n_along
        for j in range(n_across):
            lon = win.lon_min + (win.lon_max - win.lon_min) * (j + 0.5) / n_across
            fid = f"{family}_{i:02d}_{j}"
            split = "dev" if (i // 3) % 2 == 0 else "test"
            rec = base_record(fid, family, "REAL", i, split, along=i, across=j,
                              lon=round(lon, 5), lat=round(lat, 5),
                              gsd_a=round(gsd_a, 4), gsd_b=round(gsd_b, 4),
                              H_true=None)
            t0 = time.perf_counter()
            cr = locate_overlap(a["data"], a["meta"], fa, b["data"], b["meta"], fb,
                                lon, lat, tile_size=TILE)
            rec["coreg"] = cr.as_dict()
            rec["t_coreg_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            if not cr.accepted:
                rec["status"] = "NO_LOCK"
                log(f"  {fid}: NO_LOCK - {cr.reason[:80]}")
                out.append(rec)
                continue
            wa = cr.window_a
            if any(abs(wa.sample0 - s) < 256 and abs(wa.line0 - l) < 256 for s, l in seen):
                rec["status"] = "DUPLICATE"   # clamped onto a tile already taken
                out.append(rec)
                continue
            seen.append((wa.sample0, wa.line0))
            ta = to_uint8(read_window(a["data"], a["meta"], cr.window_a))
            tb = to_uint8(read_window(b["data"], b["meta"], cr.window_b))
            if tb.shape != ta.shape:
                tb = cv2.resize(tb, (ta.shape[1], ta.shape[0]), interpolation=cv2.INTER_CUBIC)
            ua, ub = usable_fraction(ta), usable_fraction(tb)
            rec.update(usable_a=round(ua, 3), usable_b=round(ub, 3),
                       texture=round(texture_score(ta), 3),
                       texture_b=round(texture_score(tb), 3))
            if min(ua, ub) < MIN_USABLE:
                rec["status"] = "FILL"
                out.append(rec)
                continue
            rec.update(status="OK", tile_a=save_tile(ta, f"{fid}_a"),
                       tile_b=save_tile(tb, f"{fid}_b"))
            log(f"  {fid}: OK texture {rec['texture']:.2f} lock "
                f"{'prior' if cr.used_prior else 'corrected'} "
                f"({cr.shift_m_across:.0f} m, {cr.shift_m_along:.0f} m)")
            out.append(rec)
    return out


# --------------------------------------------------------------------------- #
# Derived / simulated                                                           #
# --------------------------------------------------------------------------- #
def ohrc_sources(P, spec):
    """spec: list of (product key, line fraction). Returns (key, product, centre)."""
    out = []
    for key, frac in spec:
        p = P[key]
        m = p["meta"]
        out.append((key, p, int(m["samples"]) // 2, int(int(m["lines"]) * frac)))
    return out


def build_scale(P):
    """F3: true OHRC->TMC-2 GSD ratio, footprint swept."""
    family, out = "F3_scale_footprint", []
    srcs = ohrc_sources(P, [("ohrc_2021", 0.3), ("ohrc_2021", 0.7), ("ohrc_2024", 0.3),
                            ("ohrc_2024", 0.7), ("ohrc_2023", 0.3), ("ohrc_2023", 0.7)])
    for li, (key, p, cs, cl) in enumerate(srcs):
        gsd = float(np.mean(footprint_from_meta(p["meta"]).ground_sample_distance_m()))
        ratio = TMC_GSD_M / gsd
        for F in (1024, 2048, 4096, 8192):
            fid = f"{family}_L{li}_F{F}"
            rng = np.random.default_rng(seed_for(fid))
            m = F // 8
            big = to_uint8(read_window(p["data"], p["meta"], centred_window(cs, cl, F + 2 * m, F + 2 * m)))
            H_disp = pointing((TILE, TILE), rng)
            k = F / TILE
            S = np.diag([1 / k, 1 / k, 1.0])           # big -> display
            H_big = np.linalg.inv(S) @ H_disp @ S
            a_big = big[m:m + F, m:m + F]
            b_big = warp_crop(big, H_big, m, F)
            a = cv2.resize(a_big, (TILE, TILE), interpolation=cv2.INTER_AREA)
            b_native = degrade_to_sensor(b_big, ratio, psf_sigma_px=1.1, noise_sigma=2.5,
                                         seed=seed_for(fid) % 10000)
            b = upsample_to(b_native, (TILE, TILE))
            rec = base_record(fid, family, "DERIVED", li, "dev" if li % 2 == 0 else "test",
                              source=key, level=F, level_name="footprint_px",
                              gsd_src=round(gsd, 4), gsd_ratio=round(ratio, 3),
                              tmc_px=int(b_native.shape[0]),
                              footprint_m=round(F * gsd, 1),
                              H_true=H_disp.tolist(),
                              texture=round(texture_score(a), 3),
                              usable_a=round(usable_fraction(a), 3))
            if rec["usable_a"] < MIN_USABLE:
                rec["status"] = "FILL"
            else:
                rec.update(status="OK", tile_a=save_tile(a, f"{fid}_a"),
                           tile_b=save_tile(b, f"{fid}_b"))
            log(f"  {fid}: {rec['status']} TMC {rec['tmc_px']} px over {rec['footprint_m']:.0f} m")
            out.append(rec)
    return out


def build_illum(P):
    """F4: relit pairs, elevation 15 vs 22 deg, azimuth difference swept."""
    family, out = "F4_illum_azimuth", []
    srcs = ohrc_sources(P, [("ohrc_2021", 0.35), ("ohrc_2024", 0.35), ("ohrc_2023", 0.3),
                            ("ohrc_2023", 0.6), ("ohrc_2021", 0.75)])
    m = 160
    for li, (key, p, cs, cl) in enumerate(srcs):
        big = to_uint8(read_window(p["data"], p["meta"],
                                   centred_window(cs, cl, TILE + 2 * m, TILE + 2 * m)))
        # Round 4 refines the previously observed 45-90 degree boundary.
        for daz in (0, 45, 60, 75, 90, 135, 180):
            fid = f"{family}_L{li}_daz{daz}"
            s = seed_for(fid)
            rng = np.random.default_rng(s)
            az_a, az_b = 45.0, 45.0 + daz
            lit_a = relight(big, 15.0, az_a, relief_scale=22.0, ambient=0.10, seed=s % 1000)
            lit_b = relight(big, 22.0, az_b, relief_scale=22.0, ambient=0.10, seed=s % 1000 + 1)
            H = pointing((TILE, TILE), rng)
            a = lit_a[m:m + TILE, m:m + TILE]
            b = warp_crop(lit_b, H, m, TILE)
            rec = base_record(fid, family, "SIMULATED", li, "dev" if li % 2 == 0 else "test",
                              source=key, level=daz, level_name="delta_azimuth_deg",
                              elev_a=15.0, elev_b=22.0, az_a=az_a, az_b=az_b,
                              shadow_a=round(float((a < 12).mean()), 3),
                              shadow_b=round(float((b < 12).mean()), 3),
                              H_true=H.tolist(), texture=round(texture_score(a), 3),
                              usable_a=round(usable_fraction(big[m:m + TILE, m:m + TILE]), 3))
            rec.update(status="OK", tile_a=save_tile(a, f"{fid}_a"),
                       tile_b=save_tile(b, f"{fid}_b"))
            log(f"  {fid}: shadow {rec['shadow_a']:.0%}/{rec['shadow_b']:.0%}")
            out.append(rec)
    return out


def build_iirs(P):
    """F5: NIR 30-60 vs SWIR 110-140 windows along the IIRS strip."""
    family, out = "F5_iirs_bands", []
    p = P["iirs"]
    meta = p["meta"]
    lines, samples = int(meta["lines"]), int(meta["samples"])
    width = samples - 2
    height = min(TILE, width * 3)
    starts = list(range(200, lines - height - 200, height))
    for li, l0 in enumerate(starts):
        fid = f"{family}_L{li:02d}"
        rng = np.random.default_rng(seed_for(fid))
        win = PixelWindow(1, l0, 1 + width, l0 + height)
        nir = to_uint8(read_qub_window(p["data"], meta, win, 30, 60))
        swir = to_uint8(read_qub_window(p["data"], meta, win, 110, 140))
        H = pointing(swir.shape, rng)
        swir_w = cv2.warpPerspective(swir, H, (swir.shape[1], swir.shape[0]),
                                     flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        rec = base_record(fid, family, "DERIVED", li, "dev" if li % 2 == 0 else "test",
                          line0=l0, H_true=H.tolist(), texture=round(texture_score(nir), 3),
                          usable_a=round(usable_fraction(nir), 3),
                          usable_b=round(usable_fraction(swir), 3))
        if min(rec["usable_a"], rec["usable_b"]) < MIN_USABLE:
            rec["status"] = "FILL"
        else:
            rec.update(status="OK", tile_a=save_tile(nir, f"{fid}_a"),
                       tile_b=save_tile(swir_w, f"{fid}_b"))
        log(f"  {fid}: {rec['status']} line {l0} texture {rec['texture']:.2f}")
        out.append(rec)
    return out


def build_viewpoint(P):
    """F6: uncompensated rotation and zoom on same-sensor tiles."""
    family, out = "F6_viewpoint", []
    srcs = ohrc_sources(P, [("ohrc_2021", 0.5), ("ohrc_2024", 0.6), ("ohrc_2023", 0.45),
                            ("ohrc_2024", 0.2)])
    m = 256
    levels = [("rot", r, 1.0) for r in (0, 10, 30, 90, 180)] + \
             [("zoom", 0.0, z) for z in (1.25, 1.5, 2.0)]
    for li, (key, p, cs, cl) in enumerate(srcs):
        big = to_uint8(read_window(p["data"], p["meta"],
                                   centred_window(cs, cl, TILE + 2 * m, TILE + 2 * m)))
        for kind, rot, zoom in levels:
            lvl = rot if kind == "rot" else zoom
            fid = f"{family}_L{li}_{kind}{lvl:g}"
            rng = np.random.default_rng(seed_for(fid))
            H = pointing((TILE, TILE), rng, rotation=rot, zoom=zoom)
            a = big[m:m + TILE, m:m + TILE]
            b = warp_crop(big, H, m, TILE)
            rec = base_record(fid, family, "DERIVED", li, "dev" if li % 2 == 0 else "test",
                              source=key, level=lvl, level_name=f"{kind}",
                              H_true=H.tolist(), texture=round(texture_score(a), 3),
                              usable_a=round(usable_fraction(a), 3))
            rec.update(status="OK", tile_a=save_tile(a, f"{fid}_a"),
                       tile_b=save_tile(b, f"{fid}_b"))
            out.append(rec)
        log(f"  {family} L{li}: {len(levels)} levels")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", default="F1,F2,F3,F4,F5,F6")
    args = ap.parse_args()
    want = set(args.families.split(","))

    P = products()
    existing = []
    if INSTANCES_PATH.exists():
        existing = json.loads(INSTANCES_PATH.read_text(encoding="utf-8"))["instances"]
    keep = [r for r in existing if r["family"][:2] not in want]

    builders = {
        "F1": lambda: build_real(P, "F1_real_ohrc", "ohrc_2021", "ohrc_2024", 3, 12),
        "F2": lambda: build_real(P, "F2_real_tmc", "tmc_fore", "tmc_nadir", 2, 40),
        "F3": lambda: build_scale(P),
        "F4": lambda: build_illum(P),
        "F5": lambda: build_iirs(P),
        "F6": lambda: build_viewpoint(P),
    }
    new = []
    for fam in sorted(want):
        t0 = time.perf_counter()
        log(f"\n=== {fam} ===")
        new += builders[fam]()
        log(f"=== {fam} built in {time.perf_counter() - t0:.0f}s")

    instances = keep + new
    INSTANCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    INSTANCES_PATH.write_text(json.dumps({"instances": instances}, indent=1),
                              encoding="utf-8")
    ok = sum(r["status"] == "OK" for r in instances)
    log(f"\n{len(instances)} instances ({ok} OK) -> {INSTANCES_PATH}")


if __name__ == "__main__":
    main()
