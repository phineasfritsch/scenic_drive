"""regions/<region>/curated.yaml: the hand-curated seeds, held to the plan's Curation schema (T-0183).

THE SCHEMA is the plan's Curation row, field for field: id, name, hook (<= 90), lat/lon (5 dp),
join {gers_id | fsq_place_id | osm}, category, hours_exempt, dwell_min, approach_hint, verified_on,
curation_score (0.6-1.0), notes - under a top level of exactly `region` and `seeds`. `problems` names every
unknown or missing key and every out-of-range value; `load` refuses a file with any. Nothing is defaulted:
a seed the loader accepted is a seed somebody wrote out in full.

THE BOUNDS (T-0183 ruling R6). lat/lon must lie inside the region's own bbox, read from region.json and never
typed here. category is one of the shipped place allowlist's classes, so a seed cannot claim a kind of place
the corpus cannot hold. A number must be a number of the right type: a YAML `true` is a bool, which Python
calls an int, and is refused wherever a number is due.

THE JOIN (ruling R2). `joined` is True when the seed's join resolves to exactly ONE row of a places table
AND that row carries the seed's name and, rounded to 5 dp, its lat/lon - so an id typo that lands on another
place is refused rather than counted. Only `osm` can resolve against an OSM places table; a gers_id or
fsq_place_id resolves to nothing until a table keyed by them exists, and the plan lets such a seed through
only as hours-exempt (`joins_or_exempt`).

FRESHNESS (ruling R5). `fresh` is 0 <= (today - verified_on) <= FRESH_DAYS days. The caller passes `today`;
nothing here reads a clock.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

import yaml

from . import placeallow, region as region_mod

TOP_KEYS = ("region", "seeds")
FIELDS = ("id", "name", "hook", "lat", "lon", "join", "category", "hours_exempt", "dwell_min",
          "approach_hint", "verified_on", "curation_score", "notes")
JOIN_PATTERNS = {"gers_id": re.compile(r"[0-9a-f]{32}"),
                 "fsq_place_id": re.compile(r"[0-9a-f]{24}"),
                 "osm": re.compile(r"(node|way|relation)/[1-9][0-9]*")}
OSM_TYPE = {"node": "n", "way": "w", "relation": "r"}
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
TEXT_FIELDS = ("name", "approach_hint", "notes")
HOOK_MAX = 90
COORD_DP = 5
SCORE_MIN = 0.6
SCORE_MAX = 1.0
DWELL_MIN = 5
DWELL_MAX = 180
FRESH_DAYS = 365
FILENAME = "curated.yaml"


class CurationError(ValueError):
    """curated.yaml broke its schema; the message lists every problem."""


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_float(value) -> bool:
    return isinstance(value, float)


def _is_date(value) -> bool:
    return isinstance(value, datetime.date) and not isinstance(value, datetime.datetime)


def _text(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _coord(seed: dict, key: str, low: float, high: float) -> list:
    value = seed[key]
    if not _is_float(value):
        return ["%s is not a finite float: %r" % (key, value)]
    out = []
    if not low <= value <= high:
        out.append("%s %r is outside the region bbox [%r, %r]" % (key, value, low, high))
    if round(value, COORD_DP) != value:
        out.append("%s %r has more than %d decimal places" % (key, value, COORD_DP))
    return out


def _join(value) -> list:
    if not isinstance(value, dict) or len(value) != 1:
        return ["join must hold exactly one of %s: %r" % ("|".join(JOIN_PATTERNS), value)]
    (key, ref), = value.items()
    if key not in JOIN_PATTERNS:
        return ["join key %r is not one of %s" % (key, "|".join(JOIN_PATTERNS))]
    if not isinstance(ref, str) or JOIN_PATTERNS[key].fullmatch(ref) is None:
        return ["join %s %r is malformed" % (key, ref)]
    return []


def seed_problems(seed, bbox, today: datetime.date) -> list:
    """Every way one seed breaks the schema, as text naming the field."""
    if not isinstance(seed, dict):
        return ["a seed is not a mapping: %r" % (seed,)]
    missing = [k for k in FIELDS if k not in seed]
    unknown = sorted(str(k) for k in seed if k not in FIELDS)
    if missing or unknown:
        return ["missing field(s) %s" % missing] * bool(missing) + ["unknown field(s) %s" % unknown] * bool(unknown)
    out = []
    if not isinstance(seed["id"], str) or SLUG.fullmatch(seed["id"]) is None:
        out.append("id %r is not a lowercase slug" % (seed["id"],))
    out.extend("%s is empty or not text" % key for key in TEXT_FIELDS if not _text(seed[key]))
    hook = seed["hook"]
    if not _text(hook) or len(hook) > HOOK_MAX:
        out.append("hook must be 1..%d characters: %r" % (HOOK_MAX, hook))
    out.extend(_coord(seed, "lat", bbox.min_lat, bbox.max_lat))
    out.extend(_coord(seed, "lon", bbox.min_lon, bbox.max_lon))
    out.extend(_join(seed["join"]))
    if seed["category"] not in placeallow.CLASSES:
        out.append("category %r is not one of %s" % (seed["category"], placeallow.CLASSES))
    if not isinstance(seed["hours_exempt"], bool):
        out.append("hours_exempt is not a bool: %r" % (seed["hours_exempt"],))
    dwell = seed["dwell_min"]
    if not _is_int(dwell) or not DWELL_MIN <= dwell <= DWELL_MAX:
        out.append("dwell_min must be an int in [%d, %d]: %r" % (DWELL_MIN, DWELL_MAX, dwell))
    score = seed["curation_score"]
    if not _is_float(score) or not SCORE_MIN <= score <= SCORE_MAX:
        out.append("curation_score must be a float in [%r, %r]: %r" % (SCORE_MIN, SCORE_MAX, score))
    verified = seed["verified_on"]
    if not _is_date(verified):
        out.append("verified_on is not a date: %r" % (verified,))
    elif verified > today:
        out.append("verified_on %s is in the future" % verified)
    return out


def problems(doc, region_id: str, bbox, today: datetime.date) -> list:
    """Every way a parsed curated.yaml breaks the schema. Empty means the file is accepted."""
    if not isinstance(doc, dict):
        return ["curated.yaml is not a mapping"]
    out = []
    missing = [k for k in TOP_KEYS if k not in doc]
    unknown = sorted(str(k) for k in doc if k not in TOP_KEYS)
    if missing:
        out.append("missing top-level key(s) %s" % missing)
    if unknown:
        out.append("unknown top-level key(s) %s" % unknown)
    if "region" in doc and doc["region"] != region_id:
        out.append("region %r is not %r" % (doc["region"], region_id))
    seeds = doc.get("seeds")
    if "seeds" in doc and (not isinstance(seeds, list) or not seeds):
        out.append("seeds is not a non-empty list")
        seeds = []
    for index, seed in enumerate(seeds or []):
        out.extend("seed %d: %s" % (index, problem) for problem in seed_problems(seed, bbox, today))
    ids = [s.get("id") for s in seeds or [] if isinstance(s, dict)]
    out.extend("id %r appears more than once" % i for i in sorted({i for i in ids if ids.count(i) > 1}, key=str))
    return out


def load(region_id: str, today: datetime.date, root: Path | None = None) -> list:
    """The seeds of regions/<region_id>/curated.yaml, or CurationError naming every problem."""
    path = (root or region_mod.REGIONS) / region_id / FILENAME
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    bbox = region_mod.load(region_id, root).bbox
    found = problems(doc, region_id, bbox, today)
    if found:
        raise CurationError("%s:\n  %s" % (path, "\n  ".join(found)))
    return doc["seeds"]


def fresh(seed: dict, today: datetime.date) -> bool:
    """verified_on is no more than FRESH_DAYS before `today`, and not after it."""
    return 0 <= (today - seed["verified_on"]).days <= FRESH_DAYS


def join_rows(seed: dict, conn) -> list:
    """(name, lat_e7, lon_e7) of every places row the seed's join names; [] for a non-OSM join."""
    ref = seed["join"].get("osm")
    if ref is None:
        return []
    kind, osm_id = ref.split("/")
    return conn.execute("SELECT name, lat_e7, lon_e7 FROM places WHERE osm_type = ? AND osm_id = ?",
                        (OSM_TYPE[kind], int(osm_id))).fetchall()


def joined(seed: dict, conn) -> bool:
    """Exactly one place, carrying the seed's name and its 5 dp coordinates."""
    rows = join_rows(seed, conn)
    if len(rows) != 1:
        return False
    name, lat_e7, lon_e7 = rows[0]
    return (name == seed["name"] and round(lat_e7 / 1e7, COORD_DP) == seed["lat"]
            and round(lon_e7 / 1e7, COORD_DP) == seed["lon"])


def joins_or_exempt(seed: dict, conn) -> bool:
    """The plan's predicate: the seed joins exactly one place, or it is hours-exempt."""
    return joined(seed, conn) or seed["hours_exempt"] is True
