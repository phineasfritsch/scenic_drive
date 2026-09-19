"""Surface coverage per highway class: the corpus meta key, and the check that refuses a collapse.

WHAT IT MEASURES AND WHY (plan:283's M2 exit row, and the plan's "Absent surface" rule in Score per way).
The scorer assumes an untagged primary/secondary/tertiary is paved and penalises an untagged residential by
x0.8 with a `surface_unknown` flag. Both halves are claims about roads NOBODY SURVEYED, and they are only
honest while somebody watches how many roads that is. So every corpus records, per highway class, how many of
its ways carry a real surface tag - and a check refuses a build whose coverage has collapsed.

THE THREE BUCKETS ARE OFF THE RAW TAG, NOT OFF THE CORPUS COLUMN (T-0205 ruling R1b). `osm_features.surface`
is the three-state column T-0173 shipped, and surface.py's docstring says in those words that an absent tag on
primary/secondary/tertiary is PAVED(1) - indistinguishable there from `surface=asphalt`. That column would
therefore report motorway coverage as 100% where the LA canyon window's real number is 79%. Coverage asks
"was this road surveyed", so it is computed from `ExtractWay.surface`, the raw OSM value:

    known     a positive surface tag that is not an unpaved value
    unpaved   a positive tag in UNPAVED_SURFACES - the ways the safety gate refuses
    unknown   NO surface tag at all, on any class

The three partition a class, so known + unknown + unpaved == total, and `total` is stored rather than derived
so a reader never has to know that.

ONE COMPUTATION (ruling R1). `coverage` is invoked once, by `corpus.build`, and the result is written to
meta under META_KEY. `refusals` below RE-READS that table; it never recounts a way. A check that recomputed
the quantity it checks is a check that agrees with itself.

THE BASELINES ARE MEASURED, NOT INVENTED (ruling R3). They are the LA canyon window's real per-class
fractions (11,740 ways, quoted in T-0205's Log) times 0.75, truncated to three decimals. The margin is
deliberate: the defect this watches - the tag lost in the pipeline, an extract rebuilt against the retired
`paved` key, a class relabelled - sends a fraction to ~0, an order of magnitude under any literal here, while
ordinary OSM editing between two rebuilds of one region moves it by a point or two. MIN_CLASS_WAYS is the
other half: under 25 ways one way moves the fraction by over four points, so a small class is printed and
never refused on.

THE REQUIRED CLASSES ARE A WHITELIST (ruling S3). Comparing only the classes that happen to be present is a
check that passes over `{}`, over a table whose classes were all relabelled upstream, and over a table of
nothing but four-way classes - three tables where nothing was judged at all. So every key of BASELINES must
be PRESENT with at least MIN_CLASS_WAYS ways or the check refuses BY NAME, and a large class no baseline
names is reported on stderr rather than refused (it is a relabel or a class worth measuring; either wants a
human). A genuinely small region is therefore REFUSED and there is no flag to lower this: these baselines
are one region's measurement, so a region without the classes they name is not a region they can speak
about, and its recourse is its own measured baseline set, not an escape hatch.

THE BOUNDARY (ruling S4). A class whose fraction is EXACTLY its baseline PASSES: the baseline is a floor and
a floor is an allowed value, the margin is 25% so nothing real sits on it, and `fraction < baseline` reads
the way the refusal is worded.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys

from .surface import UNPAVED_SURFACES

META_KEY = "surface_coverage"

KNOWN = "known"
UNKNOWN = "unknown"
UNPAVED = "unpaved"
TOTAL = "total"
BUCKETS = (KNOWN, UNKNOWN, UNPAVED, TOTAL)

# T-0205's measurement of the LA canyon window x 0.75, truncated to three decimals. A class is refused on
# only if it is HERE and has at least MIN_CLASS_WAYS ways in the table being checked.
BASELINES = {
    "motorway": 0.593,
    "motorway_link": 0.318,
    "primary": 0.377,
    "residential": 0.091,
    "secondary": 0.287,
    "service": 0.029,
    "tertiary": 0.219,
    "track": 0.013,
    "trunk": 0.245,
    "unclassified": 0.103,
}
MIN_CLASS_WAYS = 25
# R3's margin, named so the test that recomputes BASELINES from the measurement reads the RULE from here
# and only the NUMBERS from the fixture.
BASELINE_MARGIN = 0.75

REFUSAL_EXIT = 1


def bucket(surface: str | None) -> str:
    """Which of the three a way falls in, from its RAW surface tag value (None = no tag).

    Positive evidence first, exactly as `surface.surface_state` orders it: a tagged `surface=gravel` is
    unpaved, not unknown. The tag is there; it says something; it is believed.
    """
    if surface is None:
        return UNKNOWN
    if surface in UNPAVED_SURFACES:
        return UNPAVED
    return KNOWN


def coverage(ways) -> dict:
    """The per-class table, from the ways the corpus is built from (`ExtractWay`: .highway, .surface)."""
    table: dict = {}
    for way in ways:
        row = table.setdefault(way.highway, {KNOWN: 0, UNKNOWN: 0, UNPAVED: 0, TOTAL: 0})
        row[bucket(way.surface)] += 1
        row[TOTAL] += 1
    return table


def encode(table: dict) -> str:
    """The meta value. Sorted keys and compact separators: two builds of one extract agree byte for byte."""
    return json.dumps(table, sort_keys=True, separators=(",", ":"))


def decode(value: str) -> dict:
    """The meta value back to a table, validated. A malformed table is a refusal, never an empty verdict."""
    table = json.loads(value)
    if not isinstance(table, dict):
        raise ValueError("%s is not an object" % META_KEY)
    for cls, row in sorted(table.items()):
        if not isinstance(row, dict) or set(row) != set(BUCKETS):
            raise ValueError("%s[%s]: expected exactly the keys %s" % (META_KEY, cls, ", ".join(BUCKETS)))
        if row[KNOWN] + row[UNKNOWN] + row[UNPAVED] != row[TOTAL]:
            raise ValueError("%s[%s]: known+unknown+unpaved != total - the three buckets partition a class"
                             % (META_KEY, cls))
    return table


def known_fraction(row: dict) -> float:
    """The number the baseline is about: surveyed ways over all ways of the class. An empty class is 0.0."""
    return 0.0 if row[TOTAL] == 0 else row[KNOWN] / row[TOTAL]


def refusals(table: dict) -> list:
    """Every class that is below its baseline, BY NAME. Reads the table; recounts nothing (ruling R1)."""
    out = []
    for cls in sorted(table):
        baseline = BASELINES.get(cls)
        row = table[cls]
        if baseline is None or row[TOTAL] < MIN_CLASS_WAYS:
            continue
        fraction = known_fraction(row)
        if fraction < baseline:
            out.append("%s: surface coverage %.4f is below the baseline %.3f (%d known of %d ways)"
                       % (cls, fraction, baseline, row[KNOWN], row[TOTAL]))
    return out


def required_missing(table: dict) -> list:
    """The WHITELIST (ruling S3): every baselined class must be in the table, big enough to be judged.

    Named one by one, because "3 classes missing" tells an operator nothing about which pipeline stage ate
    them. This is what makes an empty or relabelled table a refusal rather than a clean sheet.
    """
    out = []
    for cls in sorted(BASELINES):
        row = table.get(cls)
        if row is None:
            out.append("class %s is missing from the table - every baselined class must be measured" % cls)
        elif row[TOTAL] < MIN_CLASS_WAYS:
            out.append("class %s has only %d ways, under MIN_CLASS_WAYS=%d - too few to judge"
                       % (cls, row[TOTAL], MIN_CLASS_WAYS))
    return out


def unknown_classes(table: dict) -> list:
    """Large classes no baseline names: reported, never refused. A relabel, or a class worth measuring."""
    return [cls for cls in sorted(table)
            if cls not in BASELINES and table[cls][TOTAL] >= MIN_CLASS_WAYS]


def verdict(table: dict) -> list:
    """Everything that refuses this table: the missing classes first, then the collapsed ones."""
    return required_missing(table) + refusals(table)


def report_lines(table: dict) -> list:
    """The numbers, printed. Every class, whether or not it has a baseline - the ones with none say so."""
    lines = []
    for cls in sorted(table, key=lambda c: (-table[c][TOTAL], c)):
        row = table[cls]
        baseline = BASELINES.get(cls)
        if baseline is None:
            note = "no baseline (class is not in BASELINES)"
        elif row[TOTAL] < MIN_CLASS_WAYS:
            note = "no baseline (%d ways, under MIN_CLASS_WAYS=%d)" % (row[TOTAL], MIN_CLASS_WAYS)
        else:
            note = "baseline %.3f" % baseline
        lines.append("SURFACE %-15s known=%-6d unknown=%-6d unpaved=%-5d total=%-6d known_frac=%.4f  %s"
                     % (cls, row[KNOWN], row[UNKNOWN], row[UNPAVED], row[TOTAL],
                        known_fraction(row), note))
    return lines


def from_corpus(path) -> dict:
    """The table a built corpus carries in meta. Absent key -> refusal: a corpus without it is not checked."""
    conn = sqlite3.connect(str(path))
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (META_KEY,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise ValueError("%s: meta carries no %s" % (path, META_KEY))
    return decode(row[0])


def from_table_file(path) -> dict:
    return decode(pathlib.Path(path).read_text(encoding="utf-8"))


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.surfacecoverage",
                                     description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--corpus", help="a built corpus.sqlite; its meta.%s is read" % META_KEY)
    source.add_argument("--table", help="a JSON file holding the same table, as committed fixtures do")
    args = parser.parse_args(argv)
    table = from_corpus(args.corpus) if args.corpus else from_table_file(args.table)
    for line in report_lines(table):
        print(line)
    for cls in unknown_classes(table):
        print("SURFACE UNKNOWN CLASS %s (%d ways, no baseline)" % (cls, table[cls][TOTAL]), file=sys.stderr)
    bad = verdict(table)
    for line in bad:
        print("SURFACE REFUSED %s" % line, file=sys.stderr)
    print("SURFACE classes=%d refused=%d" % (len(table), len(bad)))
    return REFUSAL_EXIT if bad else 0


if __name__ == "__main__":
    sys.exit(main())
