# Problem statement — SIH26166

**Title:** Multi-modal, Sun angle and scale invariant image correspondence using
Chandrayaan-2 optical images (OHRC, TMC and IIRS)
**Theme:** Space Technology · **Category:** Software

Verbatim text as supplied by the team (2026-09-18):

> **Background:** Image Registration is the process of aligning two or more images
> of the same scene taken at different times, from different viewpoints, or by
> different sensors into a common coordinate system.
>
> It has two main components:
> - Source Image (Moving): The image that is to be geometrically transformed
>   to align with the reference image.
> - Reference Image (Fixed): The target image about which source image is to
>   be geometrically transformed.
>
> **Description:** The process of lunar images registration involves finding match
> points between source and reference image and then aligning the source image
> with the reference image. The key challenges involved in this process are as
> follows:
> - Illumination variation: Illumination variation refers to changes in sun
>   azimuth and elevation effect on the surface lighting conditions that affect
>   the appearance of the lunar surface features which is hard to correlate.
> - Viewpoint variation: It refers to geometric distortions caused by different
>   camera positions/orientations capturing the same scene. Objects appear
>   shifted, scaled, rotated, or perspective-distorted depending on observing
>   angle.
> - Scale Variation: Lunar imaging missions operate at vastly different
>   altitudes and at different spatial resolutions. This creates scale ratios.
>
> **Expected Solution:** Generic software solution for finding correspondence
> between Chandrayaan-2 acquired optical images and Lunar reference images with
> a sub-pixel accuracy of source image maintaining uniform distribution across
> the images.
> - Software and registered product with corresponding match points.
> - Evaluation metric (e.g. RMSE, inlier match count, inlier ratio, etc.)

## Requirements extracted (numbered for the scorecard)

| ID | Requirement | Source phrase |
|---|---|---|
| R1 | Correspondence across **illumination** change (sun azimuth and elevation) | "Illumination variation" |
| R2 | Correspondence across **viewpoint** change (shift, rotation, scale, perspective) | "Viewpoint variation" |
| R3 | Correspondence across **scale / resolution** ratios between missions | "Scale Variation" |
| R4 | **Multi-modal**: OHRC, TMC and IIRS | title |
| R5 | Across **time** (different dates) | "taken at different times" |
| R6 | **Sub-pixel accuracy** in the source image | "sub-pixel accuracy of source image" |
| R7 | **Uniform distribution** of match points across the images | "maintaining uniform distribution across the images" |
| R8 | Registered product **plus the match points** as output | "Software and registered product with corresponding match points" |
| R9 | **Evaluation metrics** (RMSE, inlier count, inlier ratio, ...) | "Evaluation metric" |
| R10 | **Generic** — works across sensors and scenes without per-case tuning | "Generic software solution" |
| R11 | Chandrayaan-2 images against **lunar reference images** (other missions) | "Lunar reference images" |

R11 note: the PS pairs Chandrayaan-2 images with "Lunar reference images", which
may mean another mission's basemap (e.g. LRO). This dataset has no non-Chandrayaan
product, so R11 can only be addressed by Chandrayaan-2 ↔ Chandrayaan-2 pairs
(different sensor / date) unless external reference data is added.
