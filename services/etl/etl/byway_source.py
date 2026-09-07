"""The two byway pulls, turned into the entry shape `byways.match` consumes.

Both files are pinned in `inputs/manifest.yaml` and fetched by `ops/etl-fetch-inputs`. Everything asserted
below was measured from those exact bytes, not assumed:

CALTRANS `byways-caltrans.geojson` - 273 features, `Status` {E: 207, OD: 66}. 154 of the 273 are
MultiLineString. Those parts are DISJOINT, so they are exploded into one entry each: concatenating them
would put a phantom straight segment between two real pieces of road, and any way lying under that phantom
would snap to a corridor it is nowhere near. Inter-vertex spacing on the Caltrans lines is median 29.5 m,
p99 410 m, max 5643 m - coarser than OSM, which is why the snap tolerance cannot be tight.

Each Caltrans row is a postmiled segment of a numbered state route, so `RTE` becomes the entry's route key.
That key is what tells a byway apart from the frontage road beside it; see `byways.route_matches`.

FHWA `byways-fhwa.geojson` - layer 107, 648 features, fields FID/Admin_Org/Type/Trail_Name only.

  `Type` is 'National Scenic Byway' on all 648 rows - it does NOT separate All-American Roads, whatever the
  field name suggests, so nothing here reads it.

  `Admin_Org` names the designating authority and IS load-bearing. It has 22 distinct values, each a
  comma-separated set of tokens - STATE 363, 'NSB, STATE' 62, 'USFS, STATE' 52, USFS 44, BLM 39, NSB 23,
  'USFS, NSB, STATE' 20 and fourteen more - so it is read as a token SET, not string-matched. 127 of the 648
  rows name NSB. Only those are ones FHWA itself designated; the rest are a state's or a land agency's own
  byway republished federally. We keep only the NSB rows, for two reasons that are the same reason:
    - 87 rows touch California and all 13 that touch the sfbay region are Admin_Org=STATE, with names like
      'Route 35--Skyline Boulevard' and 'Route 280--Father Junipero Serra Freeway'. Those ARE the Caltrans
      rows, re-published. Taking them would double-count every Bay Area designation.
    - a STATE row outside California is some other state's programme, whose meaning we have not read and
      whose licence we have not checked. Scoring it would be asserting we understand it.
  Measured consequence for M2: the 127 NSB rows explode to 793 entries and NOT ONE of them touches the
  sfbay region, against 248 Caltrans entries that do. The FHWA layer is pinned because the task's charter is
  Caltrans + FHWA and because the national build needs it, not because it changes a Bay Area score today.

  An NSB row carries no route number, so its entries have no route key and can only be matched on geometry -
  the weaker mode, named in `byways.route_matches`. A National Scenic Byway is designated by FHWA on a
  corridor management plan, which is the same two-gate shape as Caltrans OD, so NSB is mapped to OD's status
  rather than given a third weight. THAT IS A JUDGEMENT about two programmes' comparability, not a fact.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import byways as bw

CALTRANS_FILE = "byways-caltrans.geojson"
FHWA_FILE = "byways-fhwa.geojson"

CALTRANS_SOURCE = "caltrans"
FHWA_SOURCE = "fhwa"

# The Admin_Org token that means FHWA designated this one, as opposed to republishing someone else's.
FHWA_OWN_DESIGNATION = "NSB"

_RTE = re.compile(r"^\s*0*(\d{1,3})\s*$")


def _parts(geometry: dict | None) -> list[list[tuple[float, float]]]:
    """GeoJSON geometry to a list of (lat, lon) polylines. MultiLineString parts stay separate."""
    if not geometry:
        return []
    kind = geometry.get("type")
    if kind == "LineString":
        raw = [geometry.get("coordinates") or []]
    elif kind == "MultiLineString":
        raw = geometry.get("coordinates") or []
    else:
        return []
    out = []
    for part in raw:
        line = [(float(c[1]), float(c[0])) for c in part if c and len(c) >= 2]
        if len(line) >= 2:
            out.append(line)
    return out


def route_key(rte: object) -> set[str]:
    """Caltrans `RTE` as a route key. '280' and '0280' both give {'280'}; anything else gives nothing."""
    m = _RTE.match(str(rte or ""))
    return {m.group(1)} if m else set()


def admin_orgs(value: object) -> set[str]:
    """`Admin_Org` split into its tokens: 'NSB, STATE' -> {'NSB', 'STATE'}."""
    return {t.strip().upper() for t in str(value or "").split(",") if t.strip()}


def parse_caltrans(doc: dict) -> list[dict]:
    """Caltrans features to entries, one per disjoint geometry part."""
    out = []
    for f in doc.get("features") or []:
        p = f.get("properties") or {}
        status = (str(p.get("Status") or "")).strip().upper() or None
        routes = route_key(p.get("RTE"))
        label = f"CA {p.get('CO')} route {p.get('RTE')}"
        for line in _parts(f.get("geometry")):
            out.append({"name": label, "status": status, "source": CALTRANS_SOURCE,
                        "routes": routes, "geometry": line})
    return out


def parse_fhwa(doc: dict) -> list[dict]:
    """FHWA layer-107 features to entries, keeping only the ones FHWA itself designated.

    A dropped row is not a loss of coverage in California - it is the Caltrans row we already have, arriving
    a second time under a federal FID.
    """
    out = []
    for f in doc.get("features") or []:
        p = f.get("properties") or {}
        if FHWA_OWN_DESIGNATION not in admin_orgs(p.get("Admin_Org")):
            continue
        for line in _parts(f.get("geometry")):
            out.append({"name": p.get("Trail_Name"), "status": bw.DESIGNATED, "source": FHWA_SOURCE,
                        "routes": set(), "geometry": line})
    return out


def load(inputs_dir: str | Path) -> list[dict]:
    """Both pulls, parsed and concatenated. Missing files raise - a silently empty overlay flags nothing."""
    d = Path(inputs_dir)
    caltrans = json.loads((d / CALTRANS_FILE).read_text(encoding="utf-8"))
    fhwa = json.loads((d / FHWA_FILE).read_text(encoding="utf-8"))
    return parse_caltrans(caltrans) + parse_fhwa(fhwa)


def source_problems(entries: list[dict]) -> list[str]:
    """Checks on the PARSE, on top of `byways.problems`'s checks on the data.

    These catch a filter that silently stopped filtering, which is the failure that looks most like success:
    more rows, all of them wrong.
    """
    out = []
    fhwa = [e for e in entries if e.get("source") == FHWA_SOURCE]
    if any(e.get("routes") for e in fhwa):
        out.append("an FHWA entry has a route key - layer 107 carries no route number, so this came from "
                   "somewhere unexpected")
    caltrans = [e for e in entries if e.get("source") == CALTRANS_SOURCE]
    if entries and not caltrans:
        out.append("no Caltrans entries at all - California's designations come from Caltrans, not FHWA")
    return out
