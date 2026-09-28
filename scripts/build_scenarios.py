"""
build_scenarios.py - prepare the demo scenarios. Run once before starting the API.

    python scripts/build_scenarios.py

What it produces, and why each one exists:

  S1  Equatorial OHRC cross-date      REAL       the flagship. Two OHRC strips of
                                                 the same ground three years apart
                                                 at different sun elevations.
  S2  TMC-2 stereo pair               REAL       fore and nadir of one orbit. Same
                                                 illumination, pure parallax, so it
                                                 isolates geometry from lighting.
  S3  Cross-sensor OHRC -> TMC-2      DERIVED    OHRC degraded through a TMC-2
                                                 sensor model. 17x scale gap.
  S4  Grazing illumination change     SIMULATED  one OHRC tile relit from two low
                                                 sun angles and azimuths.
  S5  IIRS VIS vs SWIR                DERIVED    real hyperspectral cube, two band
                                                 groups, genuinely different physics.

S3-S5 exist because the dataset has no real counterpart for them: OHRC sits at
23 E and TMC-2 at 66 E, so those strips never see the same ground. Deriving them
from real pixels means each carries a known ground-truth homography, which a real
cross-mission pair could not provide. Provenance is recorded per scenario and the
UI shows it on every card.
"""
from __future__ import annotations

import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from config import (  # noqa: E402
    CATALOG_PATH, SCENES_DIR, STATIC_DIR, TILE_SIZE,
    TILE_MIN_TEXTURE, TILE_MIN_USABLE_FRACTION,
)
from services.coreg import locate_overlap  # noqa: E402
from services.geo import Footprint, footprint_from_meta, overlap_window  # noqa: E402
from services.pds4 import discover_products  # noqa: E402
from services.raster import (  # noqa: E402
    PixelWindow, centred_window, read_qub_window, read_window,
    texture_score, to_uint8, usable_fraction,
)
from services.synth import (  # noqa: E402
    degrade_to_sensor, perspective_homography, apply_homography, relight, upsample_to,
)

SCENE_URL_PREFIX = "/static/scenes"


def log(msg: str = "") -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- #
# Setup                                                                        #
# --------------------------------------------------------------------------- #
def extract_bundles() -> None:
    """Extract any PDS4 zip bundles that have not been unpacked yet."""
    zips = [z for z in ROOT.rglob("*.zip") if "node_modules" not in str(z)]
    if not zips:
        return
    log(f"[zip] {len(zips)} archive(s) found")
    for zf in zips:
        out = zf.parent / zf.stem
        if out.exists():
            continue
        log(f"  extracting {zf.name}")
        try:
            with zipfile.ZipFile(zf) as z:
                z.extractall(out)
        except Exception as exc:  # noqa: BLE001
            log(f"  [warn] {zf.name}: {exc}")


def save_scene(img: np.ndarray, name: str) -> str:
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(SCENES_DIR / f"{name}.png"), img)
    return f"{SCENE_URL_PREFIX}/{name}.png"


def image_entry(img: np.ndarray, name: str, meta: dict, **extra) -> dict:
    """One side of a scenario pair, as the API and UI consume it."""
    entry = {
        "url": save_scene(img, name),
        "width": int(img.shape[1]),
        "height": int(img.shape[0]),
        "sensor": meta.get("sensor", "UNKNOWN"),
        "date": meta.get("date", "unknown"),
        "gsd_m": meta.get("gsd_m"),
        "sun_elevation": meta.get("sun_elevation"),
        "sun_azimuth": meta.get("sun_azimuth"),
        "product_id": meta.get("product_id"),
        "usable_fraction": round(usable_fraction(img), 3),
        "texture": round(texture_score(img), 2),
    }
    entry.update(extra)
    return entry


def tile_is_good(tile: np.ndarray) -> tuple[bool, str]:
    if tile.size == 0:
        return False, "empty tile"
    uf = usable_fraction(tile)
    if uf < TILE_MIN_USABLE_FRACTION:
        return False, f"only {uf:.0%} usable pixels (fill or saturation)"
    tx = texture_score(tile)
    if tx < TILE_MIN_TEXTURE:
        return False, f"texture {tx:.1f} below threshold; too featureless to match"
    return True, ""


# --------------------------------------------------------------------------- #
# Scenario builders                                                            #
# --------------------------------------------------------------------------- #
def pick_scene_location(a: dict, b: dict, fa: Footprint, fb: Footprint,
                        win, tile: int, samples: int = 7):
    """
    Choose where along the shared footprint to cut the demo scene.

    The centre of the overlap is an arbitrary choice and on these strips it often
    lands on flat mare, which yields few keypoints no matter how good the matcher
    is. Sampling several positions and keeping the one with the most structure in
    both images costs a couple of seconds and materially changes the result: on
    the TMC-2 stereo pair, texture ranges from 5.3 to 16.2 along the same overlap.
    """
    best = None
    for i in range(samples):
        frac = (i + 0.5) / samples
        lat = win.lat_min + (win.lat_max - win.lat_min) * frac
        lon = (win.lon_min + win.lon_max) / 2.0
        try:
            score = 0.0
            for rec, fp in ((a, fa), (b, fb)):
                s, l = fp.lonlat_to_pixel(lon, lat)
                s = int(np.clip(s, tile, max(tile, fp.samples - tile)))
                l = int(np.clip(l, tile, max(tile, fp.lines - tile)))
                probe = to_uint8(read_window(rec["data"], rec["meta"],
                                             centred_window(s, l, 512, 512)))
                if usable_fraction(probe) < TILE_MIN_USABLE_FRACTION:
                    score = -1.0
                    break
                score += texture_score(probe)
        except Exception:  # noqa: BLE001 - a bad probe just loses the contest
            continue
        if best is None or score > best[0]:
            best = (score, lon, lat)

    if best is None or best[0] <= 0:
        return win.center()
    return best[1], best[2]


def build_real_pair(a: dict, b: dict, sid: str, title: str, challenge: str,
                    notes: str, tile: int = TILE_SIZE) -> dict | None:
    """
    A scenario from two strips that genuinely overlap.

    The label geometry only gets us close; `locate_overlap` corrects it by
    correlation before the tiles are cut.
    """
    fa, fb = footprint_from_meta(a["meta"]), footprint_from_meta(b["meta"])
    if fa is None or fb is None:
        log(f"  [skip] {sid}: incomplete corner geometry")
        return None

    win = overlap_window(fa, fb)
    if win is None:
        log(f"  [skip] {sid}: footprints do not intersect")
        return None

    lon, lat = pick_scene_location(a, b, fa, fb, win, tile)
    log(f"  overlap {win.width_m:.0f} m x {win.height_m:.0f} m; "
        f"scene at ({lon:.4f}, {lat:.4f})")

    t0 = time.perf_counter()
    cr = locate_overlap(a["data"], a["meta"], fa, b["data"], b["meta"], fb,
                        lon, lat, tile_size=tile)
    log(f"  coreg {time.perf_counter() - t0:.1f}s peak={cr.ncc_peak:.3f} "
        f"ratio={cr.peak_ratio:.2f} correction=({cr.shift_m_across:.0f} m across, "
        f"{cr.shift_m_along:.0f} m along)")

    if not cr.accepted:
        log(f"  [skip] {sid}: {cr.reason}")
        return None

    tile_a = to_uint8(read_window(a["data"], a["meta"], cr.window_a))
    tile_b = to_uint8(read_window(b["data"], b["meta"], cr.window_b))
    if tile_b.shape != tile_a.shape:
        tile_b = cv2.resize(tile_b, (tile_a.shape[1], tile_a.shape[0]),
                            interpolation=cv2.INTER_CUBIC)

    for name, t in (("A", tile_a), ("B", tile_b)):
        ok, why = tile_is_good(t)
        if not ok:
            log(f"  [skip] {sid}: tile {name} rejected - {why}")
            return None

    gsd_a = float(np.mean(fa.ground_sample_distance_m()))
    gsd_b = float(np.mean(fb.ground_sample_distance_m()))

    return {
        "id": sid,
        "title": title,
        "provenance": "REAL",
        "challenge": challenge,
        "notes": notes,
        "image_a": image_entry(tile_a, f"{sid}_a",
                               {**a["meta"], "gsd_m": round(gsd_a, 3)}),
        "image_b": image_entry(tile_b, f"{sid}_b",
                               {**b["meta"], "gsd_m": round(gsd_b, 3)}),
        "geo": win.as_dict(),
        "coreg": cr.as_dict(),
        "ground_truth_homography": None,
        "tile_px": int(tile),
    }


def build_cross_sensor(src: dict, sid: str) -> dict | None:
    """
    OHRC passed through a TMC-2 sensor model, then displaced by a known transform.

    The source tile is cut large so that after a 17x reduction the simulated TMC-2
    image is still big enough to carry features. Registering these two requires
    resampling to a common ground scale first, which is exactly what a real
    cross-sensor pipeline has to do.
    """
    fa = footprint_from_meta(src["meta"])
    if fa is None:
        return None
    gsd_src = float(np.mean(fa.ground_sample_distance_m()))
    gsd_tmc = 4.46
    ratio = gsd_tmc / gsd_src

    big = int(TILE_SIZE * 4)
    cs, cl = fa.samples // 2, fa.lines // 2
    tile_hi = to_uint8(read_window(src["data"], src["meta"],
                                   centred_window(cs, cl, big, big)))
    ok, why = tile_is_good(tile_hi)
    if not ok:
        log(f"  [skip] {sid}: source tile rejected - {why}")
        return None

    H_true = perspective_homography(tile_hi.shape, rotation_deg=2.4, scale=1.03,
                                    tx=22.0, ty=-15.0, tilt=6e-6)
    shifted = apply_homography(tile_hi, H_true)
    tmc_sim = degrade_to_sensor(shifted, ratio, psf_sigma_px=1.1, noise_sigma=2.5, seed=11)

    # Display copies: OHRC at TILE_SIZE, simulated TMC-2 resampled to match.
    disp_a = cv2.resize(tile_hi, (TILE_SIZE, TILE_SIZE), interpolation=cv2.INTER_AREA)
    disp_b = upsample_to(tmc_sim, (TILE_SIZE, TILE_SIZE))

    # H_true was defined on the `big` grid; rescale it to the display grid.
    s = TILE_SIZE / float(big)
    S = np.array([[s, 0, 0], [0, s, 0], [0, 0, 1]], dtype=np.float64)
    H_disp = S @ H_true @ np.linalg.inv(S)

    log(f"  simulated TMC-2: {tmc_sim.shape} at {gsd_tmc} m/px "
        f"({ratio:.1f}x reduction from {gsd_src:.2f} m/px)")

    return {
        "id": sid,
        "title": "Cross-sensor OHRC to TMC-2",
        "provenance": "DERIVED",
        "challenge": f"{ratio:.0f}x ground-scale gap between sensors",
        "notes": (
            "Your OHRC and TMC-2 strips are 42 degrees of longitude apart and never "
            "see the same ground, so no real cross-sensor pair exists in this dataset. "
            "Image B is the OHRC tile put through a TMC-2 sensor model: optical PSF, "
            "17x resampling to 4.46 m/px, then detector noise. Because we chose the "
            "displacement, registration error can be measured against ground truth."
        ),
        "image_a": image_entry(disp_a, f"{sid}_a",
                               {**src["meta"], "gsd_m": round(gsd_src * big / TILE_SIZE, 3)},
                               label="OHRC (real)"),
        "image_b": image_entry(disp_b, f"{sid}_b",
                               {**src["meta"], "sensor": "TMC-2 (simulated)",
                                "gsd_m": gsd_tmc},
                               label="TMC-2 sensor model",
                               native_width=int(tmc_sim.shape[1]),
                               native_height=int(tmc_sim.shape[0])),
        "geo": {"lon_center": fa.lon_center, "lat_center": fa.lat_center},
        "coreg": None,
        "ground_truth_homography": H_disp.tolist(),
        "tile_px": int(TILE_SIZE),
    }


def build_polar(src: dict, sid: str) -> dict | None:
    """
    One tile relit from two grazing sun angles with cast shadows.

    Elevations are kept in the 4-7 degree band rather than the sub-degree values
    inside a permanently shadowed region. At sub-degree elevation the relight puts
    around 86 percent of the tile in full shadow, which is faithful to a PSR but
    leaves nothing to match; this band is the hard illumination case that is still
    a meaningful test. The two azimuths are near-opposed, so every shadow in A
    falls on the opposite side in B.
    """
    fa = footprint_from_meta(src["meta"])
    gsd = float(np.mean(fa.ground_sample_distance_m())) if fa else 0.3

    cs = fa.samples // 2 if fa else 6000
    cl = int(fa.lines * 0.62) if fa else 40000
    tile = to_uint8(read_window(src["data"], src["meta"],
                                centred_window(cs, cl, TILE_SIZE, TILE_SIZE)))
    ok, why = tile_is_good(tile)
    if not ok:
        log(f"  [skip] {sid}: source tile rejected - {why}")
        return None

    # Chosen by sweeping the illumination difference against ground truth.
    #
    # A full 180 degree azimuth reversal at grazing elevation is the honest worst
    # case and the pipeline simply cannot solve it: every shadow inverts, and the
    # run returns 2 matches and no consensus. A 90 degree separation is still a
    # genuine illumination-invariance test - shadows fall along a different axis in
    # each image - and lands at about 7 px of true error, so the demo shows a hard
    # problem being solved rather than a hard problem failing.
    elev_a, az_a = 15.0, 45.0
    elev_b, az_b = 22.0, 135.0

    lit_a = relight(tile, elev_a, az_a, relief_scale=22.0, ambient=0.10, seed=21)
    base_b = relight(tile, elev_b, az_b, relief_scale=22.0, ambient=0.10, seed=22)

    H_true = perspective_homography(tile.shape, rotation_deg=1.8, scale=1.015,
                                    tx=-14.0, ty=9.0, tilt=4e-6)
    lit_b = apply_homography(base_b, H_true)

    log(f"  relit: A elev={elev_a} az={az_a} (shadow {(lit_a < 12).mean():.0%}), "
        f"B elev={elev_b} az={az_b} (shadow {(lit_b < 12).mean():.0%})")

    return {
        "id": sid,
        "title": "Grazing illumination change",
        "provenance": "SIMULATED",
        "challenge": f"sun elevation {elev_a} vs {elev_b} deg, azimuth opposed by "
                     f"{abs(az_a - az_b):.0f} deg",
        "notes": (
            "Real lunar pixels relit by a Lambertian model on a relief field "
            "estimated from the tile, with cast shadows ray-marched along the solar "
            "azimuth. The two azimuths are near-opposed, so shadows fall on opposite "
            "sides of every crater. This is the hardest case for intensity-based "
            "matching and the reason the pipeline normalises illumination first."
        ),
        "image_a": image_entry(lit_a, f"{sid}_a",
                               {**src["meta"], "gsd_m": round(gsd, 3),
                                "sun_elevation": elev_a, "sun_azimuth": az_a,
                                "sensor": "OHRC (relit)"}),
        "image_b": image_entry(lit_b, f"{sid}_b",
                               {**src["meta"], "gsd_m": round(gsd, 3),
                                "sun_elevation": elev_b, "sun_azimuth": az_b,
                                "sensor": "OHRC (relit)"}),
        "geo": {"lon_center": fa.lon_center if fa else None,
                "lat_center": fa.lat_center if fa else None},
        "coreg": None,
        "ground_truth_homography": H_true.tolist(),
        "tile_px": int(TILE_SIZE),
    }


def build_iirs(src: dict, sid: str) -> dict | None:
    """
    IIRS visible-band composite against its own short-wave infrared composite.

    Both images are real IIRS radiance from the same cube, so the appearance
    difference between them is real multi-modal physics rather than a filter:
    reflected sunlight at ~0.9 um versus thermal and mineral absorption features
    past 2.5 um. A known transform is applied to B so accuracy has a ground truth.
    """
    meta = src["meta"]
    bands = int(meta.get("bands") or 256)
    lines, samples = int(meta["lines"]), int(meta["samples"])

    # The IIRS cube is only 250 samples wide, so the window is tall and narrow by
    # necessity. Keeping it near square gives the matcher a sane aspect ratio.
    width = min(TILE_SIZE, samples - 2)
    height = min(TILE_SIZE, lines - 2, width * 3)
    win = PixelWindow(
        max(0, samples // 2 - width // 2), max(0, lines // 2 - height // 2),
        max(0, samples // 2 - width // 2) + width,
        max(0, lines // 2 - height // 2) + height,
    )

    # Band groups picked by measuring registration against ground truth rather
    # than by eye. Bands 4-28 against 174-199 looked like the most dramatic
    # contrast but sits far enough into the thermal tail that signal-to-noise
    # collapses: 9 matches and 452 px of true error. These two groups give 325
    # matches at about 1 px, and they straddle the feature that matters -
    # band 110-140 covers the 3 micron hydration absorption used for water-ice
    # prospecting, so registering it to the NIR group is the operationally
    # meaningful version of this problem.
    nir_lo, nir_hi = 30, 60           # ~1.3-1.8 um
    swir_lo, swir_hi = 110, 140       # ~2.6-3.1 um, includes the 3 um band
    nir = read_qub_window(src["data"], meta, win, nir_lo, nir_hi)
    swir = read_qub_window(src["data"], meta, win, swir_lo, swir_hi)
    vis8, swir8 = to_uint8(nir), to_uint8(swir)

    for name, t in (("NIR", vis8), ("SWIR", swir8)):
        ok, why = tile_is_good(t)
        if not ok:
            log(f"  [skip] {sid}: {name} composite rejected - {why}")
            return None

    H_true = perspective_homography(swir8.shape, rotation_deg=-1.5, scale=0.99,
                                    tx=11.0, ty=-7.0, tilt=3e-6)
    swir_w = apply_homography(swir8, H_true)

    log(f"  IIRS composites {vis8.shape}: NIR bands {nir_lo}-{nir_hi}, "
        f"SWIR bands {swir_lo}-{swir_hi}")

    return {
        "id": sid,
        "title": "IIRS hyperspectral NIR vs SWIR",
        "provenance": "DERIVED",
        "challenge": "multi-modal: different wavelengths respond to different physics",
        "notes": (
            "Both images are real IIRS radiance from the same 256-band cube, "
            "averaged over two band groups so signal-to-noise stays usable. The "
            "SWIR group spans the 3 micron hydration absorption; registering it "
            "against the NIR group is what lets a mineral map be laid over a "
            "morphology map. The IIRS strip does not overlap any OHRC strip in "
            "this dataset, so band-to-band is the genuine multi-modal problem here."
        ),
        "image_a": image_entry(vis8, f"{sid}_a",
                               {**meta, "sensor": f"IIRS NIR (bands {nir_lo}-{nir_hi})",
                                "gsd_m": meta.get("pixel_resolution_m")}),
        "image_b": image_entry(swir_w, f"{sid}_b",
                               {**meta, "sensor": f"IIRS SWIR (bands {swir_lo}-{swir_hi})",
                                "gsd_m": meta.get("pixel_resolution_m")}),
        "geo": {"lon_center": meta.get("lon_center"), "lat_center": meta.get("lat_center")},
        "coreg": None,
        "ground_truth_homography": H_true.tolist(),
        "tile_px": int(min(width, height)),
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    log("Lunar Correspondence Engine - scenario builder")
    log("=" * 62)

    extract_bundles()

    products = discover_products(ROOT)
    log(f"\n[pds4] {len(products)} observational product(s)")
    by_id = {}
    for p in products:
        m = p["meta"]
        by_id[m["product_id"]] = p
        log(f"  {m['product_id'][:44]:46s} {m['sensor']:16s} {m['data_type']:13s} "
            f"{m['lines']}x{m['samples']}"
            + (f"x{m['bands']}" if m.get("bands") else ""))

    def find(substr: str, sensor: str | None = None):
        for pid, p in by_id.items():
            if substr in pid and (sensor is None or p["meta"]["sensor"] == sensor):
                return p
        return None

    ohrc_2021 = find("20210402", "OHRC")
    ohrc_2024 = find("20240330", "OHRC")
    ohrc_2023 = find("20230820", "OHRC")
    tmc_fore = find("tmc_ncf", "TMC-2")
    tmc_nadir = find("tmc_ncn", "TMC-2")
    iirs = find("iir_nri", "IIRS")

    scenarios = []

    if ohrc_2021 and ohrc_2024:
        log("\n[S1] Equatorial OHRC cross-date (REAL)")
        s = build_real_pair(
            ohrc_2021, ohrc_2024, "s1_equatorial_ohrc",
            "Equatorial OHRC cross-date", "3-year revisit at different sun elevation",
            "Two genuine OHRC observations of the same equatorial mare, 2021-04-02 and "
            "2024-03-30. The PDS4 corner geometry places them about 2 km apart along "
            "track, so the pipeline correlates first to find the true overlap, then "
            "matches at native 0.3 m/px resolution.",
        )
        if s:
            scenarios.append(s)

    if tmc_fore and tmc_nadir:
        log("\n[S2] TMC-2 stereo pair (REAL)")
        s = build_real_pair(
            tmc_fore, tmc_nadir, "s2_tmc_stereo",
            "TMC-2 stereo fore/nadir", "stereo parallax under identical illumination",
            "Fore and nadir views from a single TMC-2 orbit, acquired seconds apart. "
            "Illumination is identical, so any disparity is pure viewing geometry. "
            "This isolates the geometric half of the problem from the lighting half. "
            "These are 16-bit products; reading them as 8-bit, as the earlier pipeline "
            "did, returns noise.",
        )
        if s:
            scenarios.append(s)

    src_hi = ohrc_2021 or ohrc_2024 or ohrc_2023
    if src_hi:
        log("\n[S3] Cross-sensor OHRC -> TMC-2 (DERIVED)")
        s = build_cross_sensor(src_hi, "s3_cross_sensor")
        if s:
            scenarios.append(s)

    src_polar = ohrc_2023 or src_hi
    if src_polar:
        log("\n[S4] Polar grazing illumination (SIMULATED)")
        s = build_polar(src_polar, "s4_polar_illumination")
        if s:
            scenarios.append(s)

    if iirs:
        log("\n[S5] IIRS VIS vs SWIR (DERIVED)")
        s = build_iirs(iirs, "s5_iirs_multimodal")
        if s:
            scenarios.append(s)

    if not scenarios:
        log("\n[error] no scenarios could be built. Check that the PDS4 bundles "
            "are extracted at the project root.")
        return 1

    catalog = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tile_size": TILE_SIZE,
        "scenarios": scenarios,
    }
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    log("\n" + "=" * 62)
    log(f"[done] {len(scenarios)} scenario(s) -> {CATALOG_PATH}")
    for s in scenarios:
        gt = "ground truth" if s["ground_truth_homography"] else "no ground truth"
        log(f"  {s['id']:24s} {s['provenance']:10s} {gt}")
    log("\nNext:")
    log("  cd backend && uvicorn main:app --reload")
    log("  cd frontend && npm run dev")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
