# Summary — round_2.csv

## F1_real_ohrc (REAL)

Excluded before matching (fill / duplicate): 8 locations.

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 28 | 14/28 (50%, CI 33–67) | 0/28 (0%, CI 0–12) | 0 | 0 | 14 | 1.48 | 986.00 | 14/14 (100%, CI 78–100) | 2493.10 |
| M2_sift_flann | 28 | 14/28 (50%, CI 33–67) | 0/28 (0%, CI 0–12) | 0 | 0 | 14 | 1.43 | 821.50 | 14/14 (100%, CI 78–100) | 227.90 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 15 | 6/15 (40%, CI 20–64) | 0/15 (0%, CI 0–20) | 0 | 0 | 9 | 1.45 | 1047.50 | 6/6 (100%, CI 61–100) | 2495.30 |
| M1_disk_lightglue | test | 13 | 8/13 (62%, CI 36–82) | 0/13 (0%, CI 0–23) | 0 | 0 | 5 | 1.50 | 977.50 | 8/8 (100%, CI 68–100) | 2473.30 |
| M2_sift_flann | dev | 15 | 6/15 (40%, CI 20–64) | 0/15 (0%, CI 0–20) | 0 | 0 | 9 | 1.39 | 851.50 | 6/6 (100%, CI 61–100) | 228.65 |
| M2_sift_flann | test | 13 | 8/13 (62%, CI 36–82) | 0/13 (0%, CI 0–23) | 0 | 0 | 5 | 1.44 | 803.50 | 8/8 (100%, CI 68–100) | 227.80 |

**By terrain (texture tertile)**

| arm | terrain | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | high | 5 | 5/5 (100%, CI 57–100) | 0/5 (0%, CI 0–43) | 0 | 0 | 0 | 1.50 | 971.00 | 5/5 (100%, CI 57–100) | 2494.40 |
| M1_disk_lightglue | low | 5 | 5/5 (100%, CI 57–100) | 0/5 (0%, CI 0–43) | 0 | 0 | 0 | 1.46 | 899.00 | 5/5 (100%, CI 57–100) | 2446.40 |
| M1_disk_lightglue | mid | 4 | 4/4 (100%, CI 51–100) | 0/4 (0%, CI 0–49) | 0 | 0 | 0 | 1.44 | 1021.50 | 4/4 (100%, CI 51–100) | 2521.60 |
| M2_sift_flann | high | 5 | 5/5 (100%, CI 57–100) | 0/5 (0%, CI 0–43) | 0 | 0 | 0 | 1.45 | 817.00 | 5/5 (100%, CI 57–100) | 227.60 |
| M2_sift_flann | low | 5 | 5/5 (100%, CI 57–100) | 0/5 (0%, CI 0–43) | 0 | 0 | 0 | 1.44 | 768.00 | 5/5 (100%, CI 57–100) | 236.20 |
| M2_sift_flann | mid | 4 | 4/4 (100%, CI 51–100) | 0/4 (0%, CI 0–49) | 0 | 0 | 0 | 1.38 | 850.00 | 4/4 (100%, CI 51–100) | 223.10 |

## F2_real_tmc (REAL)

Excluded before matching (fill / duplicate): 3 locations.

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 77 | 40/77 (52%, CI 41–63) | 18/77 (23%, CI 15–34) | 20 | 0 | 17 | 1.40 | 702.00 | 39/60 (65%, CI 52–76) | 2118.00 |
| M2_sift_flann | 77 | 40/77 (52%, CI 41–63) | 19/77 (25%, CI 16–35) | 20 | 0 | 17 | 1.29 | 294.50 | 42/60 (70%, CI 57–80) | 224.55 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 41 | 23/41 (56%, CI 41–70) | 12/41 (29%, CI 18–44) | 11 | 0 | 7 | 1.22 | 688.50 | 21/34 (62%, CI 45–76) | 2117.95 |
| M1_disk_lightglue | test | 36 | 17/36 (47%, CI 32–63) | 6/36 (17%, CI 8–32) | 9 | 0 | 10 | 1.46 | 782.00 | 18/26 (69%, CI 50–83) | 2118.05 |
| M2_sift_flann | dev | 41 | 23/41 (56%, CI 41–70) | 12/41 (29%, CI 18–44) | 11 | 0 | 7 | 1.22 | 283.00 | 22/34 (65%, CI 48–79) | 224.55 |
| M2_sift_flann | test | 36 | 17/36 (47%, CI 32–63) | 7/36 (19%, CI 10–35) | 9 | 0 | 10 | 1.44 | 303.50 | 20/26 (77%, CI 58–89) | 224.20 |

**By terrain (texture tertile)**

| arm | terrain | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median heldout_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | high | 20 | 18/20 (90%, CI 70–97) | 12/20 (60%, CI 39–78) | 2 | 0 | 0 | 0.98 | 964.00 | 16/20 (80%, CI 58–92) | 2113.55 |
| M1_disk_lightglue | low | 20 | 11/20 (55%, CI 34–74) | 3/20 (15%, CI 5–36) | 9 | 0 | 0 | 1.43 | 630.50 | 12/20 (60%, CI 39–78) | 2120.70 |
| M1_disk_lightglue | mid | 20 | 11/20 (55%, CI 34–74) | 3/20 (15%, CI 5–36) | 9 | 0 | 0 | 1.61 | 672.00 | 11/20 (55%, CI 34–74) | 2130.75 |
| M2_sift_flann | high | 20 | 18/20 (90%, CI 70–97) | 12/20 (60%, CI 39–78) | 2 | 0 | 0 | 0.94 | 266.00 | 16/20 (80%, CI 58–92) | 224.85 |
| M2_sift_flann | low | 20 | 11/20 (55%, CI 34–74) | 4/20 (20%, CI 8–42) | 9 | 0 | 0 | 1.34 | 318.00 | 11/20 (55%, CI 34–74) | 222.90 |
| M2_sift_flann | mid | 20 | 11/20 (55%, CI 34–74) | 3/20 (15%, CI 5–36) | 9 | 0 | 0 | 1.59 | 303.50 | 15/20 (75%, CI 53–89) | 225.95 |

## F3_scale_footprint (DERIVED)

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 24 | 14/24 (58%, CI 39–76) | 14/24 (58%, CI 39–76) | 1 | 9 | 0 | 0.29 | 555.50 | 14/24 (58%, CI 39–76) | 2461.70 |
| M2_sift_flann | 24 | 22/24 (92%, CI 74–98) | 20/24 (83%, CI 64–93) | 2 | 0 | 0 | 0.28 | 173.00 | 22/24 (92%, CI 74–98) | 220.00 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 12 | 7/12 (58%, CI 32–81) | 7/12 (58%, CI 32–81) | 1 | 4 | 0 | 0.29 | 555.50 | 7/12 (58%, CI 32–81) | 2464.05 |
| M1_disk_lightglue | test | 12 | 7/12 (58%, CI 32–81) | 7/12 (58%, CI 32–81) | 0 | 5 | 0 | 0.31 | 562.50 | 7/12 (58%, CI 32–81) | 2461.70 |
| M2_sift_flann | dev | 12 | 11/12 (92%, CI 65–99) | 10/12 (83%, CI 55–95) | 1 | 0 | 0 | 0.29 | 196.50 | 11/12 (92%, CI 65–99) | 218.75 |
| M2_sift_flann | test | 12 | 11/12 (92%, CI 65–99) | 10/12 (83%, CI 55–95) | 1 | 0 | 0 | 0.27 | 171.00 | 11/12 (92%, CI 65–99) | 222.45 |

**By sweep level**

| arm | lvl | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | footprint_px=1024.0 | 6 | 0/6 (0%, CI 0–39) | 0/6 (0%, CI 0–39) | 0 | 6 | 0 | 741.39 | 5.00 | 0/6 (0%, CI 0–39) | 2209.60 |
| M1_disk_lightglue | footprint_px=2048.0 | 6 | 2/6 (33%, CI 10–70) | 2/6 (33%, CI 10–70) | 1 | 3 | 0 | 0.75 | 5.00 | 2/6 (33%, CI 10–70) | 2436.55 |
| M1_disk_lightglue | footprint_px=4096.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.26 | 874.00 | 6/6 (100%, CI 61–100) | 3019.95 |
| M1_disk_lightglue | footprint_px=8192.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.09 | 1246.50 | 6/6 (100%, CI 61–100) | 2478.85 |
| M2_sift_flann | footprint_px=1024.0 | 6 | 4/6 (67%, CI 30–90) | 2/6 (33%, CI 10–70) | 2 | 0 | 0 | 1.71 | 30.00 | 4/6 (67%, CI 30–90) | 210.20 |
| M2_sift_flann | footprint_px=2048.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.38 | 112.50 | 6/6 (100%, CI 61–100) | 222.30 |
| M2_sift_flann | footprint_px=4096.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.26 | 249.00 | 6/6 (100%, CI 61–100) | 219.05 |
| M2_sift_flann | footprint_px=8192.0 | 6 | 6/6 (100%, CI 61–100) | 6/6 (100%, CI 61–100) | 0 | 0 | 0 | 0.07 | 895.50 | 6/6 (100%, CI 61–100) | 232.20 |

FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): F3_scale_footprint_L0_F1024 [M1_disk_lightglue] rmse 0.00 / true 364.3445, F3_scale_footprint_L1_F1024 [M1_disk_lightglue] rmse 0.75 / true 35731.609, F3_scale_footprint_L2_F1024 [M1_disk_lightglue] rmse 0.15 / true 426.9786, F3_scale_footprint_L3_F1024 [M1_disk_lightglue] rmse 1.33 / true 4884.4094, F3_scale_footprint_L4_F1024 [M1_disk_lightglue] rmse 0.20 / true 820.8985, F3_scale_footprint_L5_F1024 [M1_disk_lightglue] rmse 0.53 / true 661.8879

## F4_illum_azimuth (SIMULATED)

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 25 | 9/25 (36%, CI 20–55) | 6/25 (24%, CI 11–43) | 3 | 13 | 0 | 1.44 | 7.00 | 10/25 (40%, CI 23–59) | 2317.60 |
| M2_sift_flann | 25 | 5/25 (20%, CI 9–39) | 5/25 (20%, CI 9–39) | 1 | 19 | 0 | 696.19 | 5.00 | 5/25 (20%, CI 9–39) | 217.30 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 15 | 5/15 (33%, CI 15–58) | 3/15 (20%, CI 7–45) | 2 | 8 | 0 | 1.47 | 7.00 | 6/15 (40%, CI 20–64) | 2317.60 |
| M1_disk_lightglue | test | 10 | 4/10 (40%, CI 17–69) | 3/10 (30%, CI 11–60) | 1 | 5 | 0 | 1.21 | 12.50 | 4/10 (40%, CI 17–69) | 2300.55 |
| M2_sift_flann | dev | 15 | 3/15 (20%, CI 7–45) | 3/15 (20%, CI 7–45) | 1 | 11 | 0 | 573.15 | 5.00 | 3/15 (20%, CI 7–45) | 217.30 |
| M2_sift_flann | test | 10 | 2/10 (20%, CI 6–51) | 2/10 (20%, CI 6–51) | 0 | 8 | 0 | 937.14 | 5.50 | 2/10 (20%, CI 6–51) | 216.95 |

**By sweep level**

| arm | lvl | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | delta_azimuth_deg=0.0 | 5 | 5/5 (100%, CI 57–100) | 5/5 (100%, CI 57–100) | 0 | 0 | 0 | 0.06 | 1505.00 | 5/5 (100%, CI 57–100) | 2115.00 |
| M1_disk_lightglue | delta_azimuth_deg=135.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 131.41 | 0.00 | 0/5 (0%, CI 0–43) | 2269.90 |
| M1_disk_lightglue | delta_azimuth_deg=180.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 773.70 | 4.00 | 0/5 (0%, CI 0–43) | 2343.60 |
| M1_disk_lightglue | delta_azimuth_deg=45.0 | 5 | 4/5 (80%, CI 38–96) | 1/5 (20%, CI 4–62) | 1 | 0 | 0 | 1.41 | 578.00 | 5/5 (100%, CI 57–100) | 3756.70 |
| M1_disk_lightglue | delta_azimuth_deg=90.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 2 | 3 | 0 | 3.74 | 0.00 | 0/5 (0%, CI 0–43) | 2391.80 |
| M2_sift_flann | delta_azimuth_deg=0.0 | 5 | 5/5 (100%, CI 57–100) | 5/5 (100%, CI 57–100) | 0 | 0 | 0 | 0.26 | 1048.00 | 5/5 (100%, CI 57–100) | 213.80 |
| M2_sift_flann | delta_azimuth_deg=135.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 749.79 | 4.00 | 0/5 (0%, CI 0–43) | 219.90 |
| M2_sift_flann | delta_azimuth_deg=180.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 1056.07 | 5.00 | 0/5 (0%, CI 0–43) | 217.90 |
| M2_sift_flann | delta_azimuth_deg=45.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 1 | 4 | 0 | 696.19 | 6.00 | 0/5 (0%, CI 0–43) | 215.60 |
| M2_sift_flann | delta_azimuth_deg=90.0 | 5 | 0/5 (0%, CI 0–43) | 0/5 (0%, CI 0–43) | 0 | 5 | 0 | 1872.60 | 5.00 | 0/5 (0%, CI 0–43) | 223.90 |

FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): F4_illum_azimuth_L0_daz90 [M2_sift_flann] rmse 0.30 / true 1872.5986, F4_illum_azimuth_L0_daz135 [M2_sift_flann] rmse 0.00 / true 436.3154, F4_illum_azimuth_L0_daz180 [M2_sift_flann] rmse 1.21 / true 520.3606, F4_illum_azimuth_L1_daz45 [M2_sift_flann] rmse 0.04 / true 736.1909, F4_illum_azimuth_L1_daz90 [M2_sift_flann] rmse 0.00 / true 1421.3863, F4_illum_azimuth_L1_daz135 [M2_sift_flann] rmse 0.00 / true 749.7874, F4_illum_azimuth_L1_daz180 [M2_sift_flann] rmse 0.00 / true 12662.3159, F4_illum_azimuth_L2_daz45 [M2_sift_flann] rmse 0.00 / true 185.536, F4_illum_azimuth_L2_daz90 [M2_sift_flann] rmse 0.00 / true 597.2354, F4_illum_azimuth_L2_daz135 [M2_sift_flann] rmse 0.00 / true 1722.2907, F4_illum_azimuth_L2_daz180 [M1_disk_lightglue] rmse 0.77 / true 41.8489, F4_illum_azimuth_L2_daz180 [M2_sift_flann] rmse 1.04 / true 1056.0745, F4_illum_azimuth_L3_daz45 [M2_sift_flann] rmse 0.11 / true 1123.871, F4_illum_azimuth_L3_daz90 [M2_sift_flann] rmse 0.00 / true 5146.8041, F4_illum_azimuth_L3_daz135 [M1_disk_lightglue] rmse 1.25 / true 131.4114, F4_illum_azimuth_L3_daz135 [M2_sift_flann] rmse 0.01 / true 750.4084, F4_illum_azimuth_L3_daz180 [M1_disk_lightglue] rmse 1.40 / true 5851.6445, F4_illum_azimuth_L3_daz180 [M2_sift_flann] rmse 0.00 / true 2963.3602, F4_illum_azimuth_L4_daz45 [M2_sift_flann] rmse 1.06 / true 696.1895, F4_illum_azimuth_L4_daz90 [M2_sift_flann] rmse 0.00 / true 16065.2959, F4_illum_azimuth_L4_daz135 [M2_sift_flann] rmse 1.29 / true 651.7165, F4_illum_azimuth_L4_daz180 [M1_disk_lightglue] rmse 0.00 / true 773.7001, F4_illum_azimuth_L4_daz180 [M2_sift_flann] rmse 0.00 / true 573.1507

## F5_iirs_bands (DERIVED)

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 14 | 14/14 (100%, CI 78–100) | 13/14 (93%, CI 69–99) | 0 | 0 | 0 | 0.71 | 1224.00 | 14/14 (100%, CI 78–100) | 1911.60 |
| M2_sift_flann | 14 | 8/14 (57%, CI 33–79) | 4/14 (29%, CI 12–55) | 2 | 4 | 0 | 1.72 | 22.00 | 6/14 (43%, CI 21–67) | 94.00 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 7 | 7/7 (100%, CI 65–100) | 6/7 (86%, CI 49–97) | 0 | 0 | 0 | 0.77 | 1241.00 | 7/7 (100%, CI 65–100) | 1919.60 |
| M1_disk_lightglue | test | 7 | 7/7 (100%, CI 65–100) | 7/7 (100%, CI 65–100) | 0 | 0 | 0 | 0.65 | 1216.00 | 7/7 (100%, CI 65–100) | 1821.10 |
| M2_sift_flann | dev | 7 | 3/7 (43%, CI 16–75) | 2/7 (29%, CI 8–64) | 2 | 2 | 0 | 1.80 | 24.00 | 3/7 (43%, CI 16–75) | 94.10 |
| M2_sift_flann | test | 7 | 5/7 (71%, CI 36–92) | 2/7 (29%, CI 8–64) | 0 | 2 | 0 | 1.63 | 20.00 | 3/7 (43%, CI 16–75) | 93.90 |

FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): F5_iirs_bands_L09 [M2_sift_flann] rmse 0.23 / true 447.7624, F5_iirs_bands_L10 [M2_sift_flann] rmse 0.01 / true 393.6179, F5_iirs_bands_L11 [M2_sift_flann] rmse 0.21 / true 344.2571

## F6_viewpoint (DERIVED)

**All**

| arm | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | 32 | 24/32 (75%, CI 58–87) | 24/32 (75%, CI 58–87) | 1 | 7 | 0 | 0.20 | 755.00 | 20/32 (62%, CI 45–77) | 2199.95 |
| M2_sift_flann | 32 | 32/32 (100%, CI 89–100) | 32/32 (100%, CI 89–100) | 0 | 0 | 0 | 0.15 | 974.50 | 28/32 (88%, CI 72–95) | 225.80 |

**By split**

| arm | split | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | dev | 16 | 12/16 (75%, CI 51–90) | 12/16 (75%, CI 51–90) | 0 | 4 | 0 | 0.22 | 710.00 | 10/16 (62%, CI 39–82) | 2199.95 |
| M1_disk_lightglue | test | 16 | 12/16 (75%, CI 51–90) | 12/16 (75%, CI 51–90) | 1 | 3 | 0 | 0.15 | 825.00 | 10/16 (62%, CI 39–82) | 2206.90 |
| M2_sift_flann | dev | 16 | 16/16 (100%, CI 81–100) | 16/16 (100%, CI 81–100) | 0 | 0 | 0 | 0.17 | 1090.00 | 14/16 (88%, CI 64–97) | 225.75 |
| M2_sift_flann | test | 16 | 16/16 (100%, CI 81–100) | 16/16 (100%, CI 81–100) | 0 | 0 | 0 | 0.13 | 959.50 | 14/16 (88%, CI 64–97) | 226.70 |

**By sweep level**

| arm | lvl | N | SUCCESS | SUBPIXEL | MARGINAL | FAILURE | NO_LOCK | median grid_err_px | median inliers | UNIFORM | median ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1_disk_lightglue | rot=0.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.06 | 1442.00 | 4/4 (100%, CI 51–100) | 2207.20 |
| M1_disk_lightglue | rot=10.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.11 | 1291.50 | 4/4 (100%, CI 51–100) | 2162.55 |
| M1_disk_lightglue | rot=180.0 | 4 | 0/4 (0%, CI 0–49) | 0/4 (0%, CI 0–49) | 0 | 4 | 0 | 1222.45 | 0.00 | 0/4 (0%, CI 0–49) | 2304.80 |
| M1_disk_lightglue | rot=30.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.38 | 824.00 | 4/4 (100%, CI 51–100) | 3032.10 |
| M1_disk_lightglue | rot=90.0 | 4 | 0/4 (0%, CI 0–49) | 0/4 (0%, CI 0–49) | 1 | 3 | 0 | 808.98 | 2.00 | 0/4 (0%, CI 0–49) | 2428.60 |
| M1_disk_lightglue | zoom=1.25 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.14 | 1034.50 | 4/4 (100%, CI 51–100) | 2148.20 |
| M1_disk_lightglue | zoom=1.5 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.20 | 696.00 | 4/4 (100%, CI 51–100) | 2143.85 |
| M1_disk_lightglue | zoom=2.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.30 | 322.00 | 0/4 (0%, CI 0–49) | 2270.35 |
| M2_sift_flann | rot=0.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.06 | 1145.00 | 4/4 (100%, CI 51–100) | 229.05 |
| M2_sift_flann | rot=10.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.10 | 1072.50 | 4/4 (100%, CI 51–100) | 223.65 |
| M2_sift_flann | rot=180.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.71 | 1144.00 | 4/4 (100%, CI 51–100) | 230.75 |
| M2_sift_flann | rot=30.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.23 | 958.50 | 4/4 (100%, CI 51–100) | 225.75 |
| M2_sift_flann | rot=90.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.53 | 1150.50 | 4/4 (100%, CI 51–100) | 234.30 |
| M2_sift_flann | zoom=1.25 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.10 | 816.00 | 4/4 (100%, CI 51–100) | 223.30 |
| M2_sift_flann | zoom=1.5 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.13 | 594.50 | 4/4 (100%, CI 51–100) | 227.65 |
| M2_sift_flann | zoom=2.0 | 4 | 4/4 (100%, CI 51–100) | 4/4 (100%, CI 51–100) | 0 | 0 | 0 | 0.18 | 321.00 | 0/4 (0%, CI 0–49) | 219.05 |

FALSE_CONFIDENCE rows (RMSE < 1.5 px, true error > 10 px): F6_viewpoint_L2_rot90 [M1_disk_lightglue] rmse 0.00 / true 1614.8046, F6_viewpoint_L2_rot180 [M1_disk_lightglue] rmse 0.00 / true 1222.4498
