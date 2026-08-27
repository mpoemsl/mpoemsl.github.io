#!/usr/bin/env python3
"""Sanitize Swisstopo GPX files: strip metadata, waypoints, timestamps,
extensions. Adds a type attribute to <trk> based on parent folder name."""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

GPX_NS = "http://www.topografix.com/GPX/1/1"
ET.register_namespace("", GPX_NS)

FOLDER_TO_TYPE = {
    "hiking_tours": "hiking",
    "snowshoe_tours": "snowshoe",
}

UMLAUT_MAP = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }
)


def web_filename(stem: str) -> str:
    """Convert a human-readable tour name to a web-safe filename stem."""
    name = stem.translate(UMLAUT_MAP)
    name = re.sub(r"[\s\.\-_]+", "_", name)
    return name.lower()


def sanitize(path: Path, tour_type: str, meta_name: str) -> str:
    tree = ET.parse(path)
    root = tree.getroot()

    # Build clean <gpx> root with only standard attributes
    gpx = ET.Element(
        "gpx",
        {
            "version": root.get("version", "1.1"),
            "xmlns": GPX_NS,
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": (
                "http://www.topografix.com/GPX/1/1 "
                "http://www.topografix.com/GPX/1/1/gpx.xsd"
            ),
        },
    )

    # Use filename stem as the canonical display name
    if meta_name:
        metadata = ET.SubElement(gpx, "metadata")
        name_el = ET.SubElement(metadata, "name")
        words = meta_name.split("_")
        plain_name = " ".join(word.capitalize() for word in words)
        name_el.text = plain_name

    def copy_points(new_seg, points):
        for pt in points:
            new_pt = ET.SubElement(
                new_seg,
                "trkpt",
                {
                    "lat": pt.get("lat", ""),
                    "lon": pt.get("lon", ""),
                },
            )
            ele = pt.findtext(f"{{{GPX_NS}}}ele")
            if ele is not None:
                ele_el = ET.SubElement(new_pt, "ele")
                ele_el.text = ele

    # Process tracks — strip <time>, <extensions>, waypoints; add type attr
    trks = root.findall(f"{{{GPX_NS}}}trk")
    for trk in trks:
        new_trk = ET.SubElement(gpx, "trk", {"type": tour_type})
        for trkseg in trk.findall(f"{{{GPX_NS}}}trkseg"):
            new_seg = ET.SubElement(new_trk, "trkseg")
            copy_points(new_seg, trkseg.findall(f"{{{GPX_NS}}}trkpt"))

    # Fall back to <rte><rtept> (e.g. AllTrails exports) when no track present
    if not trks:
        for rte in root.findall(f"{{{GPX_NS}}}rte"):
            new_trk = ET.SubElement(gpx, "trk", {"type": tour_type})
            new_seg = ET.SubElement(new_trk, "trkseg")
            copy_points(new_seg, rte.findall(f"{{{GPX_NS}}}rtept"))

    # Pretty-print via re-serialization
    ET.indent(gpx, space="\t")
    raw = ET.tostring(gpx, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0"?>\n' + raw + "\n"


def main():
    gpx_root = Path(__file__).parent

    files = list(gpx_root.glob("**/*.gpx"))
    if not files:
        print("No GPX files found.", file=sys.stderr)
        sys.exit(1)

    for path in sorted(files):
        folder = path.parent.name
        tour_type = FOLDER_TO_TYPE.get(folder)
        if tour_type is None:
            print(
                f"Skipping {path} (unknown folder '{folder}')",
                file=sys.stderr,
            )
            continue

        stem = path.stem
        new_name = web_filename(stem) + ".gpx"
        new_path = path.parent / new_name

        sanitized = sanitize(path, tour_type, stem)
        path.write_text(sanitized, encoding="utf-8")

        if new_path != path:
            path.rename(new_path)
            rel_path = path.relative_to(gpx_root)
            print(f"Renamed & sanitized: {rel_path} -> {new_name}")
        else:
            print(f"Sanitized: {path.relative_to(gpx_root)}")


if __name__ == "__main__":
    main()
