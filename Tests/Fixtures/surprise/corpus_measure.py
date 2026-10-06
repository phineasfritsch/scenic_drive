#!/usr/bin/env python3
"""T-0283: where Surprise's picks land over the bundled LA corpus, read-only.

    python Tests/Fixtures/surprise/corpus_measure.py            # the shipped rule (model.py's oracle)
    python Tests/Fixtures/surprise/corpus_measure.py --before   # T-0253's rule: time-fit = minutes * 100 / budget

Every named place in apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite goes through the ruled mapping (T-0273 R3,
the prior from T-0283) and the offline reach from Westwood (T-0273 R2), then model.sequence - the same oracle the
Swift permutation tests are compared to. For each dial it prints the distribution of the picked round trip over the
budget for seeds 0..99 (the first 100 of the permutation) and the class mix of those picks.
"""
from __future__ import annotations

import datetime as dt
import math
import pathlib
import sqlite3
import sys

import model

ROOT = pathlib.Path(__file__).resolve().parents[3]
CORPUS = ROOT / "apps" / "ios" / "ScenicDrive" / "Corpus" / "corpus-fallback.sqlite"
ORIGIN = (34.0689, -118.4452)
RADIUS = 6_371_008.8
CATEGORY = {"viewpoint": "viewpoint", "peak": "viewpoint", "waterfall": "trailhead", "trailhead": "trailhead",
            "beach": "beach", "museum": "museum", "cafe": "cafe", "garden": "garden", "park": "park", "town": "town"}
DWELL = {"viewpoint": 20, "cafe": 30, "peak": 45, "park": 45, "waterfall": 60, "beach": 60, "trailhead": 60,
         "garden": 60, "town": 60, "museum": 90}
HOURS = {"museum": (600, 1020), "cafe": (420, 1080), "garden": (540, 1020)}
# T-0283 R2: the class prior, the quality a place carries while the corpus has no notability signal.
PRIOR = {"viewpoint": 70, "peak": 70, "waterfall": 70, "beach": 70, "trailhead": 70, "garden": 70,
         "park": 55, "museum": 55, "town": 55, "cafe": 40}
DIALS = (30, 60, 90, 120)
DATE = dt.date(2026, 10, 6)
DEPART = 600
USER = "on-device"


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) * math.sin(dlon / 2)
    return 2 * RADIUS * math.asin(min(1, math.sqrt(h)))


def corpus_rows():
    con = sqlite3.connect("file:%s?mode=ro" % CORPUS.as_posix(), uri=True)
    try:
        return con.execute("SELECT place_id, cls, name, lon_e7, lat_e7 FROM places ORDER BY place_id").fetchall()
    finally:
        con.close()


def round_trip(lat, lon):
    return math.ceil(2 * haversine(ORIGIN[0], ORIGIN[1], lat, lon) * 1.4 / 750.0)


def candidates(prior=True):
    out = []
    for pid, cls, name, lon_e7, lat_e7 in corpus_rows():
        if not name or cls not in CATEGORY:
            continue
        lat, lon = lat_e7 / 10_000_000, lon_e7 / 10_000_000
        opens, closes = HOURS.get(cls, (None, None))
        out.append({"id": str(pid), "cls": cls, "name": name, "category": CATEGORY[cls],
                    "corridor": "%d:%d" % (int(lat_e7 / 1_000_000), int(lon_e7 / 1_000_000)), "brand": None,
                    "quality": PRIOR[cls] if prior else 50, "approach": 0, "dwell": DWELL[cls], "opens": opens,
                    "closes": closes, "exempt": opens is None, "lit": False, "unpaved": False, "private": False,
                    "roundtrip": round_trip(lat, lon)})
    return out


def measure(cands, dial):
    seq = model.sequence(cands, {"date": DATE, "depart": DEPART, "budget": dial}, {}, USER)
    by_id = {c["id"]: c for c in cands}
    picks = [by_id[i] for i in seq[:100]]
    fr = sorted(p["roundtrip"] / dial for p in picks)
    bins = [0] * 5
    for f in fr:
        bins[min(4, int(f * 5))] += 1
    mix = {}
    for p in picks:
        mix[p["cls"]] = mix.get(p["cls"], 0) + 1
    print("dial=%3d eligible=%4d picks=%3d distinct=%3d  rt/budget min=%.2f p25=%.2f median=%.2f p75=%.2f max=%.2f"
          % (dial, len(seq), len(picks), len(set(seq[:100])), fr[0], fr[len(fr) // 4], fr[len(fr) // 2],
             fr[3 * len(fr) // 4], fr[-1]))
    print("          bins [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]: %s  at-exactly-budget=%d  seed0=%s %s %d min"
          % (bins, sum(1 for p in picks if p["roundtrip"] == dial), picks[0]["name"], picks[0]["cls"],
             picks[0]["roundtrip"]))
    print("          classes: %s" % ", ".join("%s %d" % kv for kv in sorted(mix.items(), key=lambda kv: -kv[1])))


def main():
    before = "--before" in sys.argv
    if before:
        model.time_fit = lambda rt, budget: rt * 100 // max(budget, 1)
    cands = candidates(prior=not before)
    print("%s rule: %d named places, user %s, %s depart %d" % ("T-0253" if before else "shipped", len(cands), USER,
                                                              DATE.isoformat(), DEPART))
    for dial in DIALS:
        measure(cands, dial)


if __name__ == "__main__":
    main()
