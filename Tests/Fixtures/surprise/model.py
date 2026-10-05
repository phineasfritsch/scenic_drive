#!/usr/bin/env python3
"""T-0253's synthetic Surprise fixture and its INDEPENDENT oracle (a Python model of the ruled selector).

    python Tests/Fixtures/surprise/model.py          # rewrites candidates.tsv + sequences.tsv, prints counts

The candidates are synthetic: twelve LA-area centres (4 dp), ten generated places each, plus ruled witness
rows that each fail exactly one hard filter. No raw OSM geometry, no personal data. The model re-implements
the ruled selector (T-0253 Log, R1-R8) from the ruling text, not from the Swift, and writes the whole pick
permutation per scenario; the Swift tests compare Surprise.pick to it by exact equality.
"""
from __future__ import annotations

import datetime as dt
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
M64 = (1 << 64) - 1

AREAS = [("Malibu", "malibu", 34.0259, -118.7798, "pch"), ("Topanga", "topanga", 34.0934, -118.6012, "topanga"),
         ("Mulholland", "mulholland", 34.1305, -118.5010, "mulholland"),
         ("Griffith", "griffith", 34.1366, -118.2942, "griffith"),
         ("Angeles Crest", "crest", 34.2600, -118.1000, "acrest"),
         ("Palos Verdes", "pv", 33.7450, -118.3870, "pv"), ("Santa Clarita", "clarita", 34.3917, -118.5426, "sclarita"),
         ("Ojai", "ojai", 34.4480, -119.2429, "ojai"), ("Arroyo Seco", "arroyo", 34.1478, -118.1445, "arroyo"),
         ("Long Beach", "lbc", 33.7701, -118.1937, "lbc"), ("Simi Hills", "simi", 34.2700, -118.7000, "simi"),
         ("San Gabriel Canyon", "sgc", 34.2200, -117.8600, "sgcanyon")]
CATS = ["park", "trailhead", "viewpoint", "beach", "garden", "cafe", "museum", "town"]
WORD = {"park": "Park", "trailhead": "Trailhead", "viewpoint": "Overlook", "beach": "Cove", "garden": "Garden",
        "cafe": "Cafe", "museum": "Museum", "town": "Main Street"}
HOOK = {"park": "Oak shade and a creek path", "trailhead": "A short climb to a long view",
        "viewpoint": "The whole basin below you", "beach": "Tide pools at the end of a quiet road",
        "garden": "Roses and a koi pond", "cafe": "Coffee at the top of a canyon road",
        "museum": "A small museum worth the drive", "town": "An old main street to wander"}
EXEMPT = {"park", "trailhead", "viewpoint", "beach"}
HOURS = {"garden": (540, 1110), "cafe": (420, 1140), "museum": (600, 1080), "town": (480, 1260)}
BLOCKED = {"Starbucks", "McDonald's", "In-N-Out Burger", "Denny's", "7-Eleven", "Chevron", "Walmart", "Target"}
FIRE = {"park", "trailhead", "viewpoint"}
COLS = ["id", "name", "category", "corridor", "brand", "lat", "lon", "quality", "approach", "dwell", "opens",
        "closes", "exempt", "lit", "unpaved", "private", "roundtrip", "hook"]


def rows():
    out = []
    for a, (area, slug, lat, lon, corridor) in enumerate(AREAS):
        for j in range(10):
            i = a * 10 + j
            cat = CATS[(a + j) % 8]
            opens, closes = HOURS.get(cat, (None, None))
            out.append({"id": "%s-%02d" % (slug, j), "name": "%s %s %d" % (area, WORD[cat], j + 1),
                        "category": cat, "corridor": corridor,
                        "brand": "Canyon Coffee Co." if cat == "cafe" and i % 2 == 0 else None,
                        "lat": round(lat + ((i * 7) % 13 - 6) * 0.004, 4),
                        "lon": round(lon + ((i * 5) % 11 - 5) * 0.004, 4),
                        "quality": (37 * i + 11) % 61 + 40, "approach": (53 * i + 7) % 71 + 30,
                        "dwell": [30, 45, 60, 75, 90][i % 5], "opens": opens, "closes": closes,
                        "exempt": cat in EXEMPT, "lit": cat == "viewpoint" and i % 3 == 0,
                        "unpaved": cat == "viewpoint" and i % 2 == 0, "private": False,
                        "roundtrip": 40 + (29 * i) % 141, "hook": "%s - %s" % (HOOK[cat], area)})
    base = dict(brand=None, lat=34.1, lon=-118.4, quality=70, approach=60, dwell=60, opens=None, closes=None,
                exempt=True, lit=False, unpaved=False, private=False, hook="A ruled witness")

    def w(id_, name, cat, corridor, **kw):
        r = dict(base, id=id_, name=name, category=cat, corridor=corridor, roundtrip=kw.pop("roundtrip", 120))
        r.update(kw)
        out.append(r)
    # Base context: 2026-06-20, depart 14:00 (840), budget 180. Arrival = 840 + roundtrip // 2.
    w("w-reach-over", "Witness Reach Over", "park", "wreach", roundtrip=181)
    w("w-reach-edge", "Witness Reach Edge", "park", "wreach", roundtrip=180)
    w("w-reach-none", "Witness Outside Polygon", "viewpoint", "wreach", roundtrip=None)
    w("w-brand-sbux", "Witness Starbucks", "cafe", "wbrand", brand="Starbucks", exempt=False, opens=420, closes=1260)
    w("w-brand-innout", "Witness In-N-Out", "cafe", "wbrand", brand="In-N-Out Burger", exempt=False, opens=420,
      closes=1260)
    # 120 -> arrival 900; dwell 60 + 45 -> needs closes >= 1005.
    w("w-hours-late", "Witness Closes 1004", "museum", "whours", exempt=False, opens=600, closes=1004)
    w("w-hours-edge", "Witness Closes 1005", "museum", "whours", exempt=False, opens=600, closes=1005)
    w("w-hours-open-edge", "Witness Opens 900", "cafe", "whours", exempt=False, opens=900, closes=1260)
    w("w-hours-opens", "Witness Opens 901", "cafe", "whours", exempt=False, opens=901, closes=1260)
    w("w-hours-none", "Witness No Hours", "cafe", "whours", exempt=False)
    w("w-private-1", "Witness Private Gate", "trailhead", "wprivate", private=True)
    w("w-private-2", "Witness Ranch Road", "viewpoint", "wprivate", private=True, lit=True)
    # Evening context: depart 19:30 (1170). Civil dusk ~20:37 PDT (1237) at 34.1 N on 2026-06-20.
    w("w-dark-late", "Witness Dark Dirt Overlook", "viewpoint", "wdark", unpaved=True, roundtrip=160)
    w("w-dark-lit", "Witness Lit Dirt Overlook", "viewpoint", "wdark", unpaved=True, lit=True, roundtrip=160)
    w("w-dark-paved", "Witness Paved Overlook", "viewpoint", "wdark", roundtrip=160)
    w("w-dark-early", "Witness Early Dirt Overlook", "viewpoint", "wdark", unpaved=True, roundtrip=30, dwell=45,
      hook="Sunset from a dirt turnout")
    return out


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)


def fnv_mix(text: str) -> int:
    h = 0xcbf29ce484222325
    for b in text.encode("utf-8"):
        h = ((h ^ b) * 0x100000001b3) & M64
    h = ((h ^ (h >> 30)) * 0xbf58476d1ce4e5b9) & M64
    h = ((h ^ (h >> 27)) * 0x94d049bb133111eb) & M64
    return h ^ (h >> 31)


def days(today, then):
    return (today - then).days


def eligible(cands, ctx, hist):
    today = ctx["date"]
    budget = ctx["budget"]
    for f in hist.get("feedback", []):
        if f["reason"] == "tooFar" and days(today, f["date"]) == 0:
            budget = min(budget, f["roundtrip"] - 1)
    out = []
    for c in cands:
        rt = c["roundtrip"]
        if rt is None or rt > budget:
            continue
        if any(s["id"] == c["id"] and days(today, s["date"]) < 90 for s in hist.get("shown", [])):
            continue
        if any(s["category"] == c["category"] and s["corridor"] == c["corridor"] and days(today, s["date"]) < 30
               for s in hist.get("shown", [])):
            continue
        if c["brand"] in BLOCKED:
            continue
        arrival = ctx["depart"] + rt // 2
        if not c["exempt"] and not (c["opens"] is not None and c["closes"] is not None and c["opens"] <= arrival
                                    and arrival + c["dwell"] + 45 <= c["closes"]):
            continue
        if c["category"] == "viewpoint" and not c["lit"] and c["unpaved"] and arrival > ctx.get("dusk", 99999):
            continue
        if ctx.get("redflag") and c["category"] in FIRE:
            continue
        if c["private"]:
            continue
        fb = hist.get("feedback", [])
        if any(f["reason"] == "beenThere" and f["id"] == c["id"] for f in fb):
            continue
        if any(f["reason"] == "notMyThing" and f["category"] == c["category"] and days(today, f["date"]) < 30
               for f in fb):
            continue
        if any(f["reason"] == "wrongTime" and f["id"] == c["id"] and days(today, f["date"]) == 0 for f in fb):
            continue
        novel = [days(today, s["date"]) for s in hist.get("shown", []) if s["category"] == c["category"]]
        novelty = 100 if not novel else min(100, max(0, min(novel)))
        score = c["quality"] + c["approach"] + novelty + rt * 100 // max(ctx["budget"], 1)
        out.append((score, c))
    return out


def sequence(cands, ctx, hist, user, tally=None):
    ranked = [c for _s, c in sorted(eligible(cands, ctx, hist), key=lambda sc: (-sc[0], sc[1]["id"]))]
    seq = []
    for step in range(len(ranked)):
        h = fnv_mix("%s|%s|%d" % (user, ctx["date"].isoformat(), step))
        if tally is not None:
            tally[h % 100] = tally.get(h % 100, 0) + 1
        index = (h >> 32) % len(ranked) if h % 100 < 20 else 0
        seq.append(ranked.pop(index)["id"])
    return seq


D0 = dt.date(2026, 6, 20)
BASE = {"date": D0, "depart": 840, "budget": 180}
D1 = dt.date(2026, 6, 21)
B_CTX = {"date": D1, "depart": 600, "budget": 150}
B_HIST = {"shown": [{"id": "topanga-03", "category": "beach", "corridor": "topanga", "date": dt.date(2026, 3, 24)},
                    {"id": "malibu-02", "category": "viewpoint", "corridor": "pch", "date": dt.date(2026, 3, 23)},
                    {"id": "griffith-x", "category": "cafe", "corridor": "griffith", "date": dt.date(2026, 5, 23)},
                    {"id": "arroyo-x", "category": "museum", "corridor": "arroyo", "date": dt.date(2026, 5, 22)},
                    {"id": "ojai-x", "category": "garden", "corridor": "ojai", "date": dt.date(2025, 12, 3)}]}


def main():
    cands = rows()
    with open(HERE / "candidates.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("# " + "\t".join(COLS) + "\n")
        for r in cands:
            f.write("\t".join(fmt(r[c]) for c in COLS) + "\n")
    tally = {}
    a = sequence(cands, BASE, {}, "driver-a", tally)
    c = sequence(cands, BASE, {}, "driver-c", tally)
    b = sequence(cands, B_CTX, B_HIST, "driver-b", tally)
    r = sequence(cands, dict(BASE, redflag=True), {}, "driver-a")
    p0 = a[0]
    p0c = next(r for r in cands if r["id"] == p0)
    fb = {}
    for reason, fdate in (("tooFar", D0), ("notMyThing", D0), ("beenThere", dt.date(2025, 5, 16)),
                          ("wrongTime", D0)):
        hist = {"feedback": [{"id": p0, "category": p0c["category"], "roundtrip": p0c["roundtrip"], "reason": reason,
                              "date": fdate}]}
        fb[reason] = sequence(cands, BASE, hist, "driver-a")
    wrong_next = sequence(cands, dict(BASE, date=D1), {"feedback": [{"id": p0, "category": p0c["category"],
                          "roundtrip": p0c["roundtrip"], "reason": "wrongTime", "date": D0}]}, "driver-a")
    with open(HERE / "sequences.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("# scenario\tseed\tid\n")
        for name, seq in (("A", a), ("C", c), ("B", b), ("R", r)):
            for i, cid in enumerate(seq):
                f.write("%s\t%d\t%s\n" % (name, i, cid))
    print("candidates=%d  eligible A=%d B=%d  distinct over seeds 0..99: A=%d" % (
        len(cands), len(a), len(b), len(set(a[:100]))))
    print("R (red flag, driver-a): eligible=%d  fire picks=%d  A minus fire == R as a set: %s" % (
        len(r), sum(1 for x in r if next(q for q in cands if q["id"] == x)["category"] in FIRE),
        set(r) == {x for x in a if next(q for q in cands if q["id"] == x)["category"] not in FIRE}))
    print("A[0..5]=%s  C[0..5]=%s  B[0..3]=%s" % (a[:6], c[:6], b[:4]))
    print("P0=%s cat=%s rt=%d  next picks seed0: %s  wrongTime next day seed0=%s" % (
        p0, p0c["category"], p0c["roundtrip"], {k: v[0] for k, v in fb.items()}, wrong_next[0]))
    print("draws h%%100==19: %d, ==20: %d, <20: %d of %d" % (tally.get(19, 0), tally.get(20, 0),
                                                            sum(v for k, v in tally.items() if k < 20),
                                                            sum(tally.values())))
    absent = [w for w in ("w-reach-over", "w-reach-none", "w-brand-sbux", "w-brand-innout", "w-hours-late",
                          "w-hours-opens", "w-hours-none", "w-private-1", "w-private-2") if w in a]
    present = [w for w in ("w-reach-edge", "w-hours-edge", "w-hours-open-edge", "w-dark-late", "w-dark-early") if w in a]
    print("A: witnesses wrongly present=%s  boundary witnesses present=%s" % (absent, present))
    print("B: topanga-03 in=%s malibu-02 in=%s cafe@griffith=%s museum@arroyo=%s" % (
        "topanga-03" in b, "malibu-02" in b, [x for x in b if x.startswith("griffith") and
                                              next(r for r in cands if r["id"] == x)["category"] == "cafe"],
        [x for x in b if x.startswith("arroyo") and next(r for r in cands if r["id"] == x)["category"] == "museum"]))


if __name__ == "__main__":
    main()
