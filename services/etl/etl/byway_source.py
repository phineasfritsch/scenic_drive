"""The two byway pulls, turned into the entry shape `byways.match` consumes.

Both files are pinned in `inputs/manifest.yaml` and fetched by `ops/etl-fetch-inputs`. Everything asserted
below was measured from those exact bytes, not assumed:

CALTRANS `byways-caltrans.geojson` - 273 features, `Status` {E: 207, OD: 66}. 154 of the 273 are
MultiLineString. Those parts are DISJOINT, so they are exploded into one entry each: concatenating them
would put a phantom straight segment between two real pieces of road, and any way lying under that phantom
would snap to a corridor it is nowhere near. Inter-vertex spacing on the Caltrans lines is median 29.5 m,
p99 410 m, max 5643 m - coarser than OSM, which is why the snap tolerance cannot be tight.

Each Caltrans row is a postmiled segment of a numbered state route, so `RTE` becomes the entry's route key.
That key is what tells a byway apart from the frontage road beside it; see `byways.route_matches`. `RTE` is
also WRONG on real rows - FID 181 is 27.9 km of State Route 236 filed as RTE=221 - and a wrong key rejects
its whole corridor in silence, so an entry is not trustworthy until `byway_route_key.reconcile` has checked
it against the ways that lie along it. This module does not do that: it has no way corpus. It parses.

FHWA `byways-fhwa.geojson` - layer 107, 648 features, fields FID/Admin_Org/Type/Trail_Name only.

  `Type` is 'National Scenic Byway' on all 648 rows - it does NOT separate All-American Roads, whatever the
  field name suggests, so nothing here reads it.

  `Admin_Org` names the designating authority and IS load-bearing. It has 22 distinct values, each a
  comma-separated set of tokens, so it is read as a token SET and never string-matched. By token: STATE 525,
  USFS 130, NSB 127, BLM 54, NPS 9, OTHER 7. 127 of the 648 rows name NSB and only those were designated by
  FHWA itself; the other 521 are somebody else's byway republished federally. We keep only the NSB rows.

  What that drops, and why each kind. The five bullets PARTITION the 521 dropped rows - 364 + 96 + 53 + 2
  + 6 - so the arithmetic is checkable rather than impressionistic; an earlier version said "15 more
  carrying STATE", which is no reading of the data at all.
    - 364 rows whose only token is STATE. (65 more carry STATE beside USFS, BLM or OTHER and are counted
      in the bullets below, not here.) 87 rows touch California and all 12 that touch the
      sfbay region are Admin_Org=STATE, with names like 'Route 35--Skyline Boulevard' and 'Route 280--
      Father Junipero Serra Freeway'. Those ARE the Caltrans rows, re-published, so taking them would
      double-count every Bay Area designation. Outside California a STATE row is another state's programme,
      whose criteria we have not read and whose licence we have not checked; scoring it would assert we
      understand it. Neither of those is an argument about quality - it is an argument about provenance.
    - 96 dropped rows carry USFS (44 USFS-only) and 53 carry BLM (42 BLM-only): Forest Service Scenic Byways
      and BLM Back Country Byways. These are REAL federal designations and dropping them is a real loss of
      national coverage - Angeles Crest, Feather River, Lassen, Yuba-Donner, Kings Canyon. They go for the
      same provenance reason and no other: they are separate programmes with their own criteria, awarded by
      land-management agencies rather than by FHWA, and we have read neither set of criteria. Mapping them
      onto OD's weight would be a guess about comparability dressed as a fact, and mapping them onto E's
      would be worse. ZERO of them touch the sfbay region, so nothing in M2 moves either way - which is
      exactly why this is recorded as an unresolved question rather than settled: the national build has to
      answer it, and until then the module is not pretending the answer is "they do not count".
      (The layer holds 130 rows carrying USFS and 54 carrying BLM; the other 34 and 1 name NSB as well and
      are kept, which is why the drop counts are smaller than the token counts.)
    - 2 NPS-only and 6 rows carrying OTHER, same reason.
  Measured consequence for M2: the 127 NSB rows explode to 793 entries and NOT ONE of them touches the
  sfbay region, against 229 Caltrans entries that do. The FHWA layer is pinned because the task's charter is
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
# Designating authorities whose rows this filter therefore drops. Real federal designations under separate
# programmes with their own criteria, which we have not read - dropped for provenance, not for quality, and
# none of them reaches sfbay. Named so the decision is an identifier a test can pin rather than a paragraph.
OTHER_FEDERAL_PROGRAMMES = frozenset({"USFS", "BLM", "NPS"})

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
