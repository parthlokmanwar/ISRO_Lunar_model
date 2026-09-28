"""
PDS4 label parsing for Chandrayaan-2 products.

Replaces the ad-hoc parsing in the old data_ingest module. Two things it gets
right that the previous version did not:

  * `data_type` is read from the label instead of assumed. TMC-2 and IIRS are
    UnsignedLSB2 (16-bit), but the old reader hardcoded uint8, so every TMC image
    in the catalogue was decoded by reinterpreting byte pairs as pixels. The
    result was noise that still looked plausible enough at thumbnail size to go
    unnoticed.
  * All four ground corners are kept, not just two, so a real pixel-to-ground
    mapping can be fitted.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

NS = {
    "pds": "http://pds.nasa.gov/pds4/pds/v1",
    "isda": "https://isda.issdc.gov.in/pds4/isda/v1",
}

_CORNERS = (
    "upper_left_latitude", "upper_left_longitude",
    "upper_right_latitude", "upper_right_longitude",
    "lower_left_latitude", "lower_left_longitude",
    "lower_right_latitude", "lower_right_longitude",
)


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first_text(root: ET.Element, name: str) -> Optional[str]:
    """First element with this local name, ignoring namespace."""
    for el in root.iter():
        if _localname(el.tag) == name and el.text and el.text.strip():
            return el.text.strip()
    return None


def _first_float(root: ET.Element, name: str) -> Optional[float]:
    txt = _first_text(root, name)
    if txt is None:
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def _axes(root: ET.Element) -> Dict[str, int]:
    """Axis name -> element count, from every Axis_Array in the label."""
    out: Dict[str, int] = {}
    for el in root.iter():
        if not _localname(el.tag) == "Axis_Array":
            continue
        name = count = None
        for child in el:
            ln = _localname(child.tag)
            if ln == "axis_name" and child.text:
                name = child.text.strip().upper()
            elif ln == "elements" and child.text:
                try:
                    count = int(child.text.strip())
                except ValueError:
                    count = None
        if name and count:
            out[name] = count
    return out


def normalize_sensor(name: str) -> str:
    n = (name or "").lower()
    if "ohrc" in n or "high resolution" in n:
        return "OHRC"
    if "tmc" in n or "terrain mapping" in n:
        return "TMC-2"
    if "iirs" in n or "infrared" in n or "imaging infrared" in n:
        return "IIRS"
    return (name or "UNKNOWN").upper()


def parse_label(xml_path: Path) -> dict:
    """Parse a PDS4 label into a flat metadata dict."""
    root = ET.parse(xml_path).getroot()

    axes = _axes(root)
    lines = axes.get("LINE")
    samples = axes.get("SAMPLE")
    bands = axes.get("BAND")

    start = _first_text(root, "start_date_time") or ""
    instrument = ""
    for el in root.iter():
        if _localname(el.tag) == "Observing_System_Component":
            kind = name = None
            for child in el:
                ln = _localname(child.tag)
                if ln == "type" and child.text:
                    kind = child.text.strip().lower()
                elif ln == "name" and child.text:
                    name = child.text.strip()
            if kind == "instrument" and name:
                instrument = name
                break
    if not instrument:
        instrument = _first_text(root, "name") or ""

    meta: dict = {
        "product_id": xml_path.stem,
        "start_time": start,
        "date": start[:10] if start else "unknown",
        "sensor": normalize_sensor(instrument),
        "instrument_name": instrument,
        "data_type": _first_text(root, "data_type") or "UnsignedByte",
        "lines": lines,
        "samples": samples,
        "bands": bands,
        "sun_azimuth": _first_float(root, "sun_azimuth"),
        "sun_elevation": _first_float(root, "sun_elevation"),
        "solar_incidence": _first_float(root, "solar_incidence"),
        "pixel_resolution_m": _first_float(root, "pixel_resolution"),
        "spacecraft_altitude_km": _first_float(root, "spacecraft_altitude"),
    }

    for corner in _CORNERS:
        short = (
            corner.replace("latitude", "lat")
                  .replace("longitude", "lon")
        )
        meta[short] = _first_float(root, corner)

    lat_vals = [meta[k] for k in ("upper_left_lat", "upper_right_lat",
                                  "lower_left_lat", "lower_right_lat")
                if meta.get(k) is not None]
    lon_vals = [meta[k] for k in ("upper_left_lon", "upper_right_lon",
                                  "lower_left_lon", "lower_right_lon")
                if meta.get(k) is not None]
    meta["lat_center"] = sum(lat_vals) / len(lat_vals) if lat_vals else None
    meta["lon_center"] = sum(lon_vals) / len(lon_vals) if lon_vals else None

    return meta


def find_data_file(xml_path: Path) -> Optional[Path]:
    """The binary product that belongs to a label (.img or .qub, any case)."""
    for ext in (".img", ".IMG", ".qub", ".QUB"):
        candidate = xml_path.with_suffix(ext)
        if candidate.exists():
            return candidate
    return None


def discover_products(root_dir: Path) -> list:
    """
    Every observational PDS4 product under `root_dir`.

    Browse products (_b_brw) and the derived geometry grids (_g_grd) are skipped:
    the first are downsampled previews, the second carry no image data.
    """
    found = []
    for xml_path in sorted(root_dir.rglob("ch2_*.xml")):
        name = xml_path.name
        if "_b_brw" in name or "_g_grd" in name:
            continue
        data_file = find_data_file(xml_path)
        if data_file is None:
            continue
        try:
            meta = parse_label(xml_path)
        except ET.ParseError:
            continue
        if not meta.get("lines") or not meta.get("samples"):
            continue
        found.append({"xml": xml_path, "data": data_file, "meta": meta})
    return found
