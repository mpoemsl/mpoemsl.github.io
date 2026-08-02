#!/usr/bin/env python3
"""Invert GPX routes by reversing track segment and point order.
Writes each input file to a sibling file with the source/target swapped
in the name, e.g. 'A_B_official.gpx' -> 'B_A_official.gpx'."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

GPX_NS = "http://www.topografix.com/GPX/1/1"
ET.register_namespace("", GPX_NS)


def swapped_name(stem: str) -> str:
    """Swap the source/target fields in 'A_B[_suffix]' -> 'B_A[_suffix]'."""
    first, second, *rest = stem.split("_")
    parts = [second, first, *rest]
    return "_".join(parts)


def invert(path: Path) -> Path:
    tree = ET.parse(path)
    root = tree.getroot()

    for trk in root.findall(f"{{{GPX_NS}}}trk"):
        trksegs = trk.findall(f"{{{GPX_NS}}}trkseg")

        for trkseg in trksegs:
            trkpts = trkseg.findall(f"{{{GPX_NS}}}trkpt")
            trkpts.reverse()
            for trkpt in list(trkseg):
                trkseg.remove(trkpt)
            for trkpt in trkpts:
                trkseg.append(trkpt)

        trksegs_reversed = list(reversed(trksegs))
        for trkseg in list(trk.findall(f"{{{GPX_NS}}}trkseg")):
            trk.remove(trkseg)
        for trkseg in trksegs_reversed:
            trk.append(trkseg)

    out_path = path.with_name(f"{swapped_name(path.stem)}{path.suffix}")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path


def main():
    args = sys.argv[1:]
    if args:
        files = [Path(a) for a in args]
    else:
        files = sorted(Path.cwd().glob("*.gpx"))

    if not files:
        print("No GPX files found.", file=sys.stderr)
        sys.exit(1)

    for path in files:
        out_path = invert(path)
        print(f"Inverted: {path.name} -> {out_path.name}")


if __name__ == "__main__":
    main()
