"""Narrow LoFTR probe for the Round 4 illumination failures.

This is an evaluation-only test of the available detector-free matcher. It is
not wired into the production dual-matcher policy. The cases are fixed before
the run: two 75/90-degree failures plus one 60-degree control.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "eval"))

from common import corner_err_px  # noqa: E402
from services.preprocessing import normalize_for_matching  # noqa: E402

CASES = (
    "F4_illum_azimuth_L0_daz60",
    "F4_illum_azimuth_L0_daz75",
    "F4_illum_azimuth_L0_daz90",
)


def main() -> None:
    import kornia.feature as KF

    instances = {
        r["id"]: r
        for r in json.loads((ROOT / "eval/cache/instances.json").read_text())["instances"]
    }
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    matcher = KF.LoFTR(pretrained="outdoor").eval().to(device)
    out = []
    for case in CASES:
        rec = instances[case]
        a = cv2.imread(str(ROOT / "eval/cache/tiles" / rec["tile_a"]), cv2.IMREAD_GRAYSCALE)
        b = cv2.imread(str(ROOT / "eval/cache/tiles" / rec["tile_b"]), cv2.IMREAD_GRAYSCALE)
        a, _ = normalize_for_matching(a, suppress_shadows=True)
        b, _ = normalize_for_matching(b, suppress_shadows=True)
        batch = {
            "image0": torch.from_numpy(a).float()[None, None].to(device) / 255.0,
            "image1": torch.from_numpy(b).float()[None, None].to(device) / 255.0,
        }
        with torch.inference_mode():
            pred = matcher(batch)
        p0 = pred["keypoints0"].detach().cpu().numpy()
        p1 = pred["keypoints1"].detach().cpu().numpy()
        H = None
        inliers = 0
        rmse = None
        if len(p0) >= 4:
            H, mask = cv2.findHomography(p0, p1, cv2.USAC_MAGSAC, 3.0,
                                         maxIters=10000, confidence=0.9999)
            if H is not None and mask is not None:
                keep = mask.ravel().astype(bool)
                inliers = int(keep.sum())
                proj = cv2.perspectiveTransform(p0[keep].reshape(-1, 1, 2), H).reshape(-1, 2)
                rmse = float(np.sqrt(np.mean(np.sum((proj - p1[keep]) ** 2, axis=1))))
        true_err = corner_err_px(H, np.array(rec["H_true"]), a.shape)
        out.append({"id": case, "matches": int(len(p0)), "inliers": inliers,
                    "rmse_px": rmse, "true_error_px": true_err})
        print(out[-1], flush=True)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
