"""KMZ and osmium-export builders that can write a MALFORMED block, which is the point of them.

`test_oracle_build.py` carries its own pair of builders and they stay there: those produce only well-formed
input, and that is precisely why four parser guards in `etl/oracle.py` survived `ops/etl-mutation` (T-0088).
Nothing in the suite could write a Placemark with no `<description>`, no constituent-way rows or no
`<coordinates>`, so turning any of those `continue`s into `pass` was green. Here each Placemark is assembled
from parts, so a test can leave one of them out.

The shapes these emit are the ones `etl.oracle`'s regexes read, and no more: a `<Placemark>` holding a
`<name>`, a CDATA `<description>` carrying `Curvature: N` and a table of constituent-way rows, and a
`<LineString><coordinates>`. Every value is small and synthetic - no 2.5 MB oracle, no osmium - so these run
everywhere the suite runs.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

# A fixed zip timestamp, so the same arguments produce the same bytes and a digest can be compared across
# two builds rather than merely being non-empty.
STAMP = (2026, 9, 8, 0, 0, 0)

# Three collinear nodes: enough to clear `len(ours) < 3` in eligible().
COORDS = [(44.0, -72.8), (44.001, -72.8), (44.002, -72.8)]

# One row of the constituent-ways table. WAY_ROW anchors on the openstreetmap.org/way/N link and requires the
# anchor TEXT to be digits too, so the id appears twice on purpose.
_ROW = ('<tr><td><a href="https://www.openstreetmap.org/way/{way}">{way}</a></td>'
        "<td>{surface}</td><td>{curv}</td></tr>")

_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
{placemarks}
</Document></kml>
"""


def placemark(name: str = "Probe Road", ways=(), coords=COORDS, *,
              description: bool = True, curvature: float = 500.0, surface: str = "asphalt") -> str:
    """One `<Placemark>`, with any part of it left out.

    `description=False` omits the `<description>` element entirely - `DESCRIPTION.search` then returns None.
    `coords=None` omits the `<LineString>` - `PLACEMARK_COORDS.search` then returns None.
    `ways=()` writes a description whose table holds no rows - `WAY_ROW.findall` then returns [].
    """
    parts = [f"  <name>{name}</name>"]
    if description:
        rows = "\n    ".join(_ROW.format(way=w, surface=surface, curv=curvature) for w in ways)
        parts.append(f"  <description><![CDATA[Curvature: {curvature}\n"
                     f"    <table>\n    {rows}\n    </table>]]></description>")
    if coords is not None:
        joined = " ".join(f"{lon},{lat}" for lat, lon in coords)
        parts.append(f"  <LineString><coordinates>{joined}</coordinates></LineString>")
    return "<Placemark>\n" + "\n".join(parts) + "\n</Placemark>"


def write_kmz(path: Path, *blocks: str) -> Path:
    """A KMZ holding one doc.kml made of `blocks`, in the order given."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("doc.kml", STAMP), _KML.format(placemarks="\n".join(blocks)))
    return path


def collection(way_id: int, coords=None, name: str | None = None, curvature: float = 500.0) -> str:
    """The ordinary case: a single-way collection whose KML geometry is `coords`."""
    return placemark(name or f"Road {way_id}", ways=(way_id,),
                     coords=COORDS if coords is None else coords, curvature=curvature)


def write_export(path: Path, ways=(), nodes=()) -> Path:
    """`osmium export -f geojsonseq --add-unique-id=type_id` output.

    `ways` are `(id, coords, properties)` and `nodes` are `(id, properties, (lat, lon))`. Coordinates are
    given here as (lat, lon) and written as [lon, lat], which is the order osmium writes and the order
    `load_export` exists to reverse - mixing them silently halves every distance at this latitude.
    """
    lines = [json.dumps({
        "type": "Feature", "id": f"w{way_id}",
        "geometry": {"type": "LineString", "coordinates": [[lon, lat] for lat, lon in coords]},
        "properties": props,
    }) for way_id, coords, props in ways]
    lines += [json.dumps({
        "type": "Feature", "id": f"n{node_id}",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }) for node_id, props, (lat, lon) in nodes]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def road(way_id: int, coords=None, **props) -> tuple:
    """An export way entry for `write_export`, tagged as an ordinary road unless told otherwise."""
    return (way_id, COORDS if coords is None else coords, {"highway": "residential", **props})
