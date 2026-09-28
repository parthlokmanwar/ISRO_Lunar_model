# Summary — round_1.csv

## F1_real_ohrc (REAL)

Excluded before matching (fill / duplicate): 8 locations.

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 28 | 4/28 (14%, CI 6–31) | 0/28 (0%, CI 0–12) | 8 | 2 | 14 | 2.16 | 18.50 | 2/14 (14%, CI 4–40) | 2478.40 |
| M2_sift_flann | 28 | 12/28 (43%, CI 27–61) | 0/28 (0%, CI 0–12) | 2 | 0 | 14 | 1.43 | 821.50 | 14/14 (100%, CI 78–100) | 232.85 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 15 | 2/15 (13%, CI 4–38) | 0/15 (0%, CI 0–20) | 3 | 1 | 9 | 2.18 | 19.50 | 2/6 (33%, CI 10–70) | 2478.40 |
| M1_disk_lightglue | test | 13 | 2/13 (15%, CI 4–42) | 0/13 (0%, CI 0–23) | 5 | 1 | 5 | 2.14 | 16.00 | 0/8 (0%, CI 0–32) | 2481.10 |
| M2_sift_flann | dev | 15 | 4/15 (27%, CI 11–52) | 0/15 (0%, CI 0–20) | 2 | 0 | 9 | 1.39 | 851.50 | 6/6 (100%, CI 61–100) | 233.60 |
| M2_sift_flann | test | 13 | 8/13 (62%, CI 36–82) | 0/13 (0%, CI 0–23) | 0 | 0 | 5 | 1.44 | 803.50 | 8/8 (100%, CI 68–100) | 232.80 |

**By terrain (texture tertile)**

| arm | terrain | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | high | 5 | 1/5 (20%, CI 4–62) | 0/5 (0%, CI 0–43) | 4 | 0 | 0 | 2.14 | 20.00 | 0/5 (0%, CI 0–43) | 2465.00 |
| M1_disk_lightglue | low | 5 | 3/5 (60%, CI 23–88) | 0/5 (0%, CI 0–43) | 1 | 1 | 0 | 1.62 | 24.00 | 2/5 (40%, CI 12–77) | 2371.30 |
| M1_disk_lightglue | mid | 4 | 0/4 (0%, CI 0–49) | 0/4 (0%, CI 0–49) | 3 | 1 | 0 | 2.50 | 13.00 | 0/4 (0%, CI 0–49) | 2505.25 |
| M2_sift_flann | high | 5 | 4/5 (80%, CI 38–96) | 0/5 (0%, CI 0–43) | 1 | 0 | 0 | 1.45 | 817.00 | 5/5 (100%, CI 57–100) | 233.80 |
| M2_sift_flann | low | 5 | 4/5 (80%, CI 38–96) | 0/5 (0%, CI 0–43) | 1 | 0 | 0 | 1.44 | 768.00 | 5/5 (100%, CI 57–100) | 231.80 |
| M2_sift_flann | mid | 4 | 4/4 (100%, CI 51–100) | 0/4 (0%, CI 0–49) | 0 | 0 | 0 | 1.38 | 850.00 | 4/4 (100%, CI 51–100) | 237.60 |

## F2_real_tmc (REAL)

Excluded before matching (fill / duplicate): 3 locations.

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 77 | 27/77 (35%, CI 25–46) | 0/77 (0%, CI 0–5) | 22 | 11 | 17 | 1.68 | 20.50 | 17/60 (28%, CI 19–41) | 2119.60 |
| M2_sift_flann | 77 | 34/77 (44%, CI 34–55) | 19/77 (25%, CI 16–35) | 26 | 0 | 17 | 1.29 | 294.50 | 42/60 (70%, CI 57–80) | 227.20 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 41 | 18/41 (44%, CI 30–59) | 0/41 (0%, CI 0–9) | 10 | 6 | 7 | 1.54 | 23.00 | 11/34 (32%, CI 19–49) | 2118.85 |
| M1_disk_lightglue | test | 36 | 9/36 (25%, CI 14–41) | 0/36 (0%, CI 0–10) | 12 | 5 | 10 | 1.89 | 17.50 | 6/26 (23%, CI 11–42) | 2121.70 |
| M2_sift_flann | dev | 41 | 20/41 (49%, CI 34–64) | 12/41 (29%, CI 18–44) | 14 | 0 | 7 | 1.22 | 283.00 | 22/34 (65%, CI 48–79) | 224.10 |
| M2_sift_flann | test | 36 | 14/36 (39%, CI 25–55) | 7/36 (19%, CI 10–35) | 12 | 0 | 10 | 1.44 | 303.50 | 20/26 (77%, CI 58–89) | 227.40 |

**By terrain (texture tertile)**

| arm | terrain | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | high | 20 | 14/20 (70%, CI 48–85) | 0/20 (0%, CI 0–16) | 4 | 2 | 0 | 1.53 | 41.00 | 11/20 (55%, CI 34–74) | 2090.75 |
| M1_disk_lightglue | low | 20 | 7/20 (35%, CI 18–57) | 0/20 (0%, CI 0–16) | 9 | 4 | 0 | 1.69 | 18.00 | 3/20 (15%, CI 5–36) | 2132.10 |
| M1_disk_lightglue | mid | 20 | 6/20 (30%, CI 15–52) | 0/20 (0%, CI 0–16) | 9 | 5 | 0 | 1.96 | 16.50 | 3/20 (15%, CI 5–36) | 2119.25 |
| M2_sift_flann | high | 20 | 16/20 (80%, CI 58–92) | 12/20 (60%, CI 39–78) | 4 | 0 | 0 | 0.94 | 266.00 | 16/20 (80%, CI 58–92) | 226.70 |
| M2_sift_flann | low | 20 | 9/20 (45%, CI 26–66) | 4/20 (20%, CI 8–42) | 11 | 0 | 0 | 1.34 | 318.00 | 11/20 (55%, CI 34–74) | 226.95 |
| M2_sift_flann | mid | 20 | 9/20 (45%, CI 26–66) | 3/20 (15%, CI 5–36) | 11 | 0 | 0 | 1.59 | 303.50 | 15/20 (75%, CI 53–89) | 227.40 |

## F3_scale_footprint (DERIVED)

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 24 | 12/24 (50%, CI 31–69) | 11/24 (46%, CI 28–65) | 3 | 9 | 0 | 0.85 | 28.50 | 11/24 (46%, CI 28–65) | 2431.80 |
| M2_sift_flann | 24 | 22/24 (92%, CI 74–98) | 20/24 (83%, CI 64–93) | 2 | 0 | 0 | 0.28 | 173.00 | 22/24 (92%, CI 74–98) | 223.20 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 12 | 5/12 (42%, CI 19–68) | 5/12 (42%, CI 19–68) | 3 | 4 | 0 | 2.34 | 22.00 | 5/12 (42%, CI 19–68) | 2428.60 |
| M1_disk_lightglue | test | 12 | 7/12 (58%, CI 32–81) | 6/12 (50%, CI 25–75) | 0 | 5 | 0 | 0.83 | 36.00 | 6/12 (50%, CI 25–75) | 2431.80 |
| M2_sift_flann | dev | 12 | 11/12 (92%, CI 65–99) | 10/12 (83%, CI 55–95) | 1 | 0 | 0 | 0.29 | 196.50 | 11/12 (92%, CI 65–99) | 225.90 |
| M2_sift_flann | test | 12 | 11/12 (92%, CI 65–99) | 10/12 (83%, CI 55–95) | 1 | 0 | 0 | 0.27 | 171.00 | 11/12 (92%, CI 65–99) | 221.50 |

**By sweep level**

| arm | lvl | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | footprint_px=1024.0 | 6 | 0/6 (0%, CI 0–39) | 0/6 (0%, CI 0–39) | 0 | 6 | 0 | 741.39 | 5.00 | 0/6 (0%, CI 0–39) | 2221.60 |
| M1_disk_lightglue | footprint_px=2048.0 | 6 | 1/6 (17%, CI 3–56) | 1/6 (17%, CI 3–56) | 2 | 3 | 0 | 3.45 | 5.00 | 2/6 (33%, CI 10–70) | 2431.80 |
| M1_disk_lightglue | footprint_px=4096.0 | 6 | 5/6 (83%, CI 44–97) | 4/6 (67%, CI 30–90) | 1 | 0 | 0 | 0.85 | 52.00 | 6/6 (100%, CI 61–100) | 3116.30 |
| M1_disk_lightglue | footprint_px=8192.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.60 | 36.00 | 3/6 (50%, CI 19–81) | 2422.90 |
| M2_sift_flann | footprint_px=1024.0 | 6 | 4/6 (67%, CI 30–90) | 2/6 (33%, CI 10–70) | 2 | 0 | 0 | 1.71 | 30.00 | 4/6 (67%, CI 30–90) | 207.05 |
| M2_sift_flann | footprint_px=2048.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.38 | 112.50 | 6/6 (100%, CI 61–100) | 224.85 |
| M2_sift_flann | footprint_px=4096.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.26 | 249.00 | 6/6 (100%, CI 61–100) | 223.10 |
| M2_sift_flann | footprint_px=8192.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.07 | 895.50 | 6/6 (100%, CI 61–100) | 230.10 |

FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): F3_scale_footprint_L0_F1024 [M1_disk_lightglue] rmse 0.00 / true 364.3445, F3_scale_footprint_L1_F1024 [M1_disk_lightglue] rmse 0.75 / true 35731.609, F3_scale_footprint_L2_F1024 [M1_disk_lightglue] rmse 0.15 / true 426.9786, F3_scale_footprint_L3_F1024 [M1_disk_lightglue] rmse 1.33 / true 4884.4094, F3_scale_footprint_L4_F1024 [M1_disk_lightglue] rmse 0.20 / true 820.8985, F3_scale_footprint_L5_F1024 [M1_disk_lightglue] rmse 0.53 / true 661.8879

## F4_illum_azimuth (SIMULATED)

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 25 | 4/25 (16%, CI 6–35) | 3/25 (12%, CI 4–30) | 8 | 13 | 0 | 3.31 | 7.00 | 9/25 (36%, CI 20–55) | 2323.30 |
| M2_sift_flann | 25 | 5/25 (20%, CI 9–39) | 5/25 (20%, CI 9–39) | 1 | 19 | 0 | 696.19 | 5.00 | 5/25 (20%, CI 9–39) | 226.10 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 15 | 3/15 (20%, CI 7–45) | 2/15 (13%, CI 4–38) | 4 | 8 | 0 | 3.25 | 7.00 | 6/15 (40%, CI 20–64) | 2323.30 |
| M1_disk_lightglue | test | 10 | 1/10 (10%, CI 2–40) | 1/10 (10%, CI 2–40) | 4 | 5 | 0 | 3.38 | 10.50 | 3/10 (30%, CI 11–60) | 2273.10 |
| M2_sift_flann | dev | 15 | 3/15 (20%, CI 7–45) | 3/15 (20%, CI 7–45) | 1 | 11 | 0 | 573.15 | 5.00 | 3/15 (20%, CI 7–45) | 230.40 |
| M2_sift_flann | test | 10 | 2/10 (20%, CI 6–51) | 2/10 (20%, CI 6–51) | 0 | 8 | 0 | 937.14 | 5.50 | 2/10 (20%, CI 6–51) | 224.20 |

**By sweep level**

| arm | lvl | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | delta_azimuth_deg=0.0 | 5 | 4/5 (80%, CI 38–96) | 3/5 (60%, CI 23–88) | 1 | 0 | 0 | 0.75 | 67.00 | 4/5 (80%, CI 38–96) | 2073.00 |
| M1_disk_lightglue | delta_azimuth_deg=135.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 131.41 | 0.00 | 0/5 (0%, CI 0–43) | 2287.90 |
| M1_disk_lightglue | delta_azimuth_deg=180.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 41.85 | 4.00 | 0/5 (0%, CI 0–43) | 2323.30 |
| M1_disk_lightglue | delta_azimuth_deg=45.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 5 | 0 | 0 | 3.25 | 163.00 | 5/5 (100%, CI 57–100) | 3544.80 |
| M1_disk_lightglue | delta_azimuth_deg=90.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 2 | 3 | 0 | 3.69 | 0.00 | 0/5 (0%, CI 0–43) | 2446.60 |
| M2_sift_flann | delta_azimuth_deg=0.0 | 5 | 5/5 (100%, CI 57–100) | 5/5 (100%, CI 57–100) | 0 | 0 | 0 | 0.26 | 1048.00 | 5/5 (100%, CI 57–100) | 228.80 |
| M2_sift_flann | delta_azimuth_deg=135.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 749.79 | 4.00 | 0/5 (0%, CI 0–43) | 231.20 |
| M2_sift_flann | delta_azimuth_deg=180.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 1056.07 | 5.00 | 0/5 (0%, CI 0–43) | 219.40 |
| M2_sift_flann | delta_azimuth_deg=45.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 1 | 4 | 0 | 696.19 | 6.00 | 0/5 (0%, CI 0–43) | 225.20 |
| M2_sift_flann | delta_azimuth_deg=90.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 1872.60 | 5.00 | 0/5 (0%, CI 0–43) | 226.10 |

FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): F4_illum_azimuth_L0_daz90 [M2_sift_flann] rmse 0.30 / true 1872.5986, F4_illum_azimuth_L0_daz135 [M2_sift_flann] rmse 0.00 / true 436.3154, F4_illum_azimuth_L0_daz180 [M2_sift_flann] rmse 1.21 / true 520.3606, F4_illum_azimuth_L1_daz45 [M2_sift_flann] rmse 0.04 / true 736.1909, F4_illum_azimuth_L1_daz90 [M2_sift_flann] rmse 0.00 / true 1421.3863, F4_illum_azimuth_L1_daz135 [M2_sift_flann] rmse 0.00 / true 749.7874, F4_illum_azimuth_L1_daz180 [M2_sift_flann] rmse 0.00 / true 12662.3159, F4_illum_azimuth_L2_daz45 [M2_sift_flann] rmse 0.00 / true 185.536, F4_illum_azimuth_L2_daz90 [M2_sift_flann] rmse 0.00 / true 597.2354, F4_illum_azimuth_L2_daz135 [M2_sift_flann] rmse 0.00 / true 1722.2907, F4_illum_azimuth_L2_daz180 [M1_disk_lightglue] rmse 0.77 / true 41.8489, F4_illum_azimuth_L2_daz180 [M2_sift_flann] rmse 1.04 / true 1056.0745, F4_illum_azimuth_L3_daz45 [M2_sift_flann] rmse 0.11 / true 1123.871, F4_illum_azimuth_L3_daz90 [M2_sift_flann] rmse 0.00 / true 5146.8041, F4_illum_azimuth_L3_daz135 [M1_disk_lightglue] rmse 1.25 / true 131.4114, F4_illum_azimuth_L3_daz135 [M2_sift_flann] rmse 0.01 / true 750.4084, F4_illum_azimuth_L3_daz180 [M1_disk_lightglue] rmse 1.42 / true 35.9163, F4_illum_azimuth_L3_daz180 [M2_sift_flann] rmse 0.00 / true 2963.3602, F4_illum_azimuth_L4_daz45 [M2_sift_flann] rmse 1.06 / true 696.1895, F4_illum_azimuth_L4_daz90 [M2_sift_flann] rmse 0.00 / true 16065.2959, F4_illum_azimuth_L4_daz135 [M2_sift_flann] rmse 1.29 / true 651.7165, F4_illum_azimuth_L4_daz180 [M1_disk_lightglue] rmse 0.00 / true 773.7001, F4_illum_azimuth_L4_daz180 [M2_sift_flann] rmse 0.00 / true 573.1507

## F5_iirs_bands (DERIVED)

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 14 | 14/14 (100%, CI 78–100) | 9/14 (64%, CI 39–84) | 0 | 0 | 0 | 0.94 | 219.00 | 14/14 (100%, CI 78–100) | 1837.70 |
| M2_sift_flann | 14 | 8/14 (57%, CI 33–79) | 4/14 (29%, CI 12–55) | 2 | 4 | 0 | 1.72 | 22.00 | 6/14 (43%, CI 21–67) | 90.15 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 7 | 7/7 (100%, CI 65–100) | 3/7 (43%, CI 16–75) | 0 | 0 | 0 | 1.02 | 213.00 | 7/7 (100%, CI 65–100) | 1840.80 |
| M1_disk_lightglue | test | 7 | 7/7 (100%, CI 65–100) | 6/7 (86%, CI 49–97) | 0 | 0 | 0 | 0.84 | 225.00 | 7/7 (100%, CI 65–100) | 1786.10 |
| M2_sift_flann | dev | 7 | 3/7 (43%, CI 16–75) | 2/7 (29%, CI 8–64) | 2 | 2 | 0 | 1.80 | 24.00 | 3/7 (43%, CI 16–75) | 88.10 |
| M2_sift_flann | test | 7 | 5/7 (71%, CI 36–92) | 2/7 (29%, CI 8–64) | 0 | 2 | 0 | 1.63 | 20.00 | 3/7 (43%, CI 16–75) | 90.30 |

FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): F5_iirs_bands_L09 [M2_sift_flann] rmse 0.23 / true 447.7624, F5_iirs_bands_L10 [M2_sift_flann] rmse 0.01 / true 393.6179, F5_iirs_bands_L11 [M2_sift_flann] rmse 0.21 / true 344.2571

## F6_viewpoint (DERIVED)

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 32 | 16/32 (50%, CI 34–66) | 12/32 (38%, CI 23–55) | 8 | 8 | 0 | 1.25 | 22.00 | 9/32 (28%, CI 16–45) | 2193.65 |
| M2_sift_flann | 32 | 32/32 (100%, CI 89–100) | 32/32 (100%, CI 89–100) | 0 | 0 | 0 | 0.15 | 974.50 | 28/32 (88%, CI 72–95) | 229.30 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 16 | 7/16 (44%, CI 23–67) | 5/16 (31%, CI 14–56) | 4 | 5 | 0 | 1.41 | 16.50 | 6/16 (38%, CI 18–61) | 2206.70 |
| M1_disk_lightglue | test | 16 | 9/16 (56%, CI 33–77) | 7/16 (44%, CI 23–67) | 4 | 3 | 0 | 0.74 | 31.50 | 3/16 (19%, CI 7–43) | 2175.05 |
| M2_sift_flann | dev | 16 | 16/16 (100%, CI 81–100) | 16/16 (100%, CI 81–100) | 0 | 0 | 0 | 0.17 | 1090.00 | 14/16 (88%, CI 64–97) | 231.00 |
| M2_sift_flann | test | 16 | 16/16 (100%, CI 81–100) | 16/16 (100%, CI 81–100) | 0 | 0 | 0 | 0.13 | 959.50 | 14/16 (88%, CI 64–97) | 228.80 |

**By sweep level**

| arm | lvl | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | rot=0.0 | 4 | 3/4 (75%, CI 30–95) | 3/4 (75%, CI 30–95) | 1 | 0 | 0 | 0.65 | 42.50 | 1/4 (25%, CI 5–70) | 2157.40 |
| M1_disk_lightglue | rot=10.0 | 4 | 4/4 (100%, CI 51–100) | 3/4 (75%, CI 30–95) | 0 | 0 | 0 | 0.50 | 59.50 | 3/4 (75%, CI 30–95) | 2165.60 |
| M1_disk_lightglue | rot=180.0 | 4 | 0/4 (0%, CI 0–49) | 0/4 (0%, CI 0–49) | 0 | 4 | 0 | 728.08 | 0.00 | 0/4 (0%, CI 0–49) | 2319.30 |
| M1_disk_lightglue | rot=30.0 | 4 | 2/4 (50%, CI 15–85) | 0/4 (0%, CI 0–49) | 2 | 0 | 0 | 1.81 | 35.00 | 4/4 (100%, CI 51–100) | 2986.80 |
| M1_disk_lightglue | rot=90.0 | 4 | 0/4 (0%, CI 0–49) | 0/4 (0%, CI 0–49) | 1 | 3 | 0 | 809.09 | 2.00 | 0/4 (0%, CI 0–49) | 2470.95 |
| M1_disk_lightglue | zoom=1.25 | 4 | 3/4 (75%, CI 30–95) | 3/4 (75%, CI 30–95) | 1 | 0 | 0 | 0.31 | 38.00 | 1/4 (25%, CI 5–70) | 2135.60 |
| M1_disk_lightglue | zoom=1.5 | 4 | 3/4 (75%, CI 30–95) | 2/4 (50%, CI 15–85) | 0 | 1 | 0 | 0.78 | 26.00 | 0/4 (0%, CI 0–49) | 2163.85 |
| M1_disk_lightglue | zoom=2.0 | 4 | 1/4 (25%, CI 5–70) | 1/4 (25%, CI 5–70) | 3 | 0 | 0 | 2.80 | 13.00 | 0/4 (0%, CI 0–49) | 2212.55 |
| M2_sift_flann | rot=0.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.06 | 1145.00 | 4/4 (100%, CI 51–100) | 231.30 |
| M2_sift_flann | rot=10.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.10 | 1072.50 | 4/4 (100%, CI 51–100) | 229.50 |
| M2_sift_flann | rot=180.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.71 | 1144.00 | 4/4 (100%, CI 51–100) | 231.65 |
| M2_sift_flann | rot=30.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.23 | 958.50 | 4/4 (100%, CI 51–100) | 228.55 |
| M2_sift_flann | rot=90.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.53 | 1150.50 | 4/4 (100%, CI 51–100) | 232.25 |
| M2_sift_flann | zoom=1.25 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.10 | 816.00 | 4/4 (100%, CI 51–100) | 229.35 |
| M2_sift_flann | zoom=1.5 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.13 | 594.50 | 4/4 (100%, CI 51–100) | 225.60 |
| M2_sift_flann | zoom=2.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.18 | 321.00 | 0/4 (0%, CI 0–49) | 225.75 |

FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): F6_viewpoint_L2_rot90 [M1_disk_lightglue] rmse 0.00 / true 1614.8046, F6_viewpoint_L2_rot180 [M1_disk_lightglue] rmse 0.00 / true 728.0778
