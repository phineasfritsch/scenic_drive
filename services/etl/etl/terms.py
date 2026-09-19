"""The term vocabulary: the ids the corpus carries, their ODbL family, and who produces each one.

This is the ON-DEVICE SCORE CONTRACT. schema.py rule 6 says the corpus stores no score and no score view -
the score is recomputed from `terms_osm` and `terms_raster` at query time - so a term the device cannot
spend is a term that does not exist, and a name here that `score.score` does not accept is exactly that.
`tests/test_corpus_schema.py` asserts every name in TERM_NAMES against `inspect.signature(score.score)`.

It lives in its own module because schema.py is the DDL and its 300-line cap is real (CLAUDE.md, file
discipline). schema.py re-exports the four names its callers already read through it, so nothing else moved.

THE IDS ARE PERMANENT. A term id is written into every device's corpus and read back by position and number
for as long as that corpus lives, so the whole range is allocated here, at once, rather than one id at a
time next to whichever producer lands next - which is how two producers pick the same number. The split is
arithmetic and load-bearing: < 100 is the ODbL family, >= 100 is ours.

FAMILY IS THE ODbL LINE AND NOTHING ELSE. `osm` means derived from OSM alone - geometry, or OSM tags.
`raster` is a historical name for the other half: it selects `terms_raster`, which carries OWN_LICENSE, and
it means "not derived from OSM" rather than "sampled from a GeoTIFF". `points_of_interest` is Wikimedia
Commons photo density (plan:89) - no raster anywhere in it, and emphatically not OSM, so it belongs on this
side of the line. `CorpusWriter.add_term` refuses a term written into the wrong table, which is the only
thing standing between the ODbL Collective-Database posture and a quiet lie.
"""
from __future__ import annotations

TERM_NAMES = {
    # --- osm: derived from OSM geometry or OSM tags alone -> terms_osm, ODbL --------------------------
    1: "curvature",
    2: "sinuosity",
    3: "speed_fit",
    4: "furniture",
    # --- raster: everything not derived from OSM -> terms_raster, OWN_LICENSE -------------------------
    101: "elevation_gain",
    102: "relief",
    103: "canopy",
    104: "impervious",
    105: "byway",
    106: "water",
    107: "points_of_interest",
}

# Who computes the value. Either a file that exists in this package, or the id of the task that will write
# one. `tests/test_corpus_schema.py` asserts both halves: a module entry must name a file that is really
# there, and a task entry must be in RESERVED and must look like a task id.
PRODUCERS = {
    1: "etl/curvature.py",
    2: "T-0161",
    3: "etl/speedfit.py",
    4: "etl/furniture.py",
    101: "etl/terrain.py",
    102: "etl/terrain.py",
    103: "etl/landcover.py",
    104: "etl/landcover.py",
    105: "etl/byways.py",
    106: "etl/landcover.py",
    107: "T-0164",
}

# The terms with no producer module in this package, and the task filed to write one. Typed out rather than
# derived from PRODUCERS, because the two lists are meant to be edited together and a derived one would
# agree with any mistake.
#
# "No producer" here means NO MODULE, not "no rows in a corpus yet". By the second reading all eleven would
# be reserved: T-0030 ships zero term rows and T-0146 is the assembler that first fills the two tables.
#
#   2   sinuosity          T-0161, PR #94 open on 2026-09-18
#   107 points_of_interest T-0164, filed, queue/backlog - way_record.py's DEFERRED_TERMS already says so
RESERVED = {2: "T-0161", 107: "T-0164"}

OSM_TERM_IDS = frozenset(k for k in TERM_NAMES if k < 100)
RASTER_TERM_IDS = frozenset(k for k in TERM_NAMES if k >= 100)
TERM_FAMILIES = {"osm": OSM_TERM_IDS, "raster": RASTER_TERM_IDS}
