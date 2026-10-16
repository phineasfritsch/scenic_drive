"""Writes t1_landmarks.osm.xml: the LA viewpoint and peak NODES within 1000 m of any T1 recorded path (T-0241).

    python services/etl/tests/fixtures/generate_t1_landmarks.py <landmarks.osm.xml>

The input is `osmium tags-filter -R nwr/tourism=viewpoint nwr/natural=peak` over the LA region clip
(services/etl/work/la/la.osm.pbf, sha256 3bb2d4a8...8f4e, measured in T-0241's Log) then `osmium cat` to XML.
Data (c) OpenStreetMap contributors, ODbL. Every tag of a kept node is kept; nothing else is.
"""
from __future__ import annotations

import glob
import json
import pathlib
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "services" / "etl"))
from etl import geom  # noqa: E402

RADIUS_M = 1000.0
ROUTES = ROOT / "Tests" / "Fixtures" / "t0239" / "topanga-malibu"
OUT = HERE / "t1_landmarks.osm.xml"


def paths() -> list:
    lines = []
    for name in sorted(glob.glob(str(ROUTES / "*.json"))):
        for path in json.loads(pathlib.Path(name).read_text(encoding="utf-8"))["paths"]:
            lines.append([(lat, lon) for lon, lat in path["points"]["coordinates"]])
    return lines


def main(argv: list) -> int:
    lines = paths()
    out = ET.Element("osm", version="0.6", generator="generate_t1_landmarks.py")
    kept = 0
    for _, elem in ET.iterparse(argv[1]):
        if elem.tag != "node" or not elem.findall("tag"):
            continue
        point = (float(elem.get("lat")), float(elem.get("lon")))
        if min(geom.point_to_polyline_m(point, line) for line in lines) > RADIUS_M:
            continue
        node = ET.SubElement(out, "node", id=elem.get("id"), lat=elem.get("lat"), lon=elem.get("lon"))
        for tag in elem.findall("tag"):
            ET.SubElement(node, "tag", k=tag.get("k"), v=tag.get("v"))
        kept += 1
    ET.indent(out)
    OUT.write_text(ET.tostring(out, encoding="unicode") + "\n", encoding="utf-8", newline="\n")
    print("T1_LANDMARKS nodes=%d radius_m=%g" % (kept, RADIUS_M))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
