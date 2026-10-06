"""T-0276 oracle: an independent Python reading of the recorded Caltrans LCS D7 response under the Log's rulings
R1-R6, written to expected.json. services/api/test/closuresFeed.test.ts holds parseLcsFeed + capClosures +
closuresVersion to this file by FULL equality. Only + - * / and sqrt touch a coordinate, so IEEE doubles agree
with the TypeScript bit for bit.

    python Tests/Fixtures/t0276/oracle.py      (rewrites Tests/Fixtures/t0276/expected.json)
"""
import hashlib
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NOW_S = 1791273972  # the response's own Date header, 2026-10-06T08:06:12Z
B = 30.0
LONG = 500.0
M_LAT = 110946.0
M_LON = 91961.0
LON = (-119.5, -117.6)
LAT = (33.7, 34.9)
CAP = 2000  # T-0282 N1: the stored cap; each request sends its own nearest 50
RANK = ["Conventional Hwy", "Mainline", "HOV", "Collector", "Connector", "HOV Connector", "On Ramp", "Off Ramp",
        "Rest Area"]
EPOCH = re.compile(r"[0-9]{1,10}")
DECIMAL = re.compile(r"-?[0-9]{1,3}(\.[0-9]{1,8})?")


def flag(v):
    return v if v in ("true", "false") else None


def get(obj, *path):
    for key in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def position(lon_s, lat_s):
    for s in (lon_s, lat_s):
        if not isinstance(s, str) or not DECIMAL.fullmatch(s):
            return "position_not_decimal"
    lon, lat = float(lon_s), float(lat_s)
    if not (LON[0] <= lon <= LON[1]) or not (LAT[0] <= lat <= LAT[1]):
        return "position_outside_d7"
    return (lon, lat)


def rings(blon, blat, elon, elat):
    dx = (elon - blon) * M_LON
    dy = (elat - blat) * M_LAT
    length = math.sqrt(dx * dx + dy * dy)
    pt = lambda x, y: [blon + x / M_LON, blat + y / M_LAT]
    square = lambda cx, cy: [pt(cx - B, cy - B), pt(cx + B, cy - B), pt(cx + B, cy + B), pt(cx - B, cy + B),
                             pt(cx - B, cy - B)]
    if length == 0:
        return [square(0.0, 0.0)]
    if length > LONG:
        return [square(0.0, 0.0), square(dx, dy)]
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    p0x, p0y = -ux * B, -uy * B
    p1x, p1y = dx + ux * B, dy + uy * B
    a = pt(p0x - nx * B, p0y - ny * B)
    return [[a, pt(p1x - nx * B, p1y - ny * B), pt(p1x + nx * B, p1y + ny * B), pt(p0x + nx * B, p0y + ny * B), a]]


def parse(data, now):
    out = {"rows": len(data), "full": 0, "active": 0, "refused": [], "closures": []}
    for row in data:
        lcs = get(row, "lcs")
        if not isinstance(lcs, dict):
            out["refused"].append({"index": None, "reason": "row_not_object"})
            continue
        kind = get(lcs, "closure", "typeOfClosure")
        idx = lcs.get("index") if isinstance(lcs.get("index"), str) else None
        if not isinstance(kind, str):
            out["refused"].append({"index": idx, "reason": "type_missing"})
            continue
        if kind != "Full":
            continue
        out["full"] += 1
        c = lcs["closure"]
        ts = get(c, "closureTimestamp")
        reason = None
        codes = [flag(get(c, f"code{n}", f"isCode{n}")) for n in ("1097", "1098", "1022")]
        start, ind, end = get(ts, "closureStartEpoch"), flag(get(ts, "isClosureEndIndefinite")), get(ts, "closureEndEpoch")
        fac = get(c, "facility")
        if not idx:
            reason = "index_missing"
        elif None in codes:
            reason = "code_not_boolean"
        elif not isinstance(start, str) or not EPOCH.fullmatch(start):
            reason = "start_not_epoch"
        elif ind is None:
            reason = "indefinite_not_boolean"
        elif ind == "false" and (not isinstance(end, str) or not EPOCH.fullmatch(end)):
            reason = "end_not_epoch"
        elif ind == "false" and int(end) < int(start):
            reason = "window_inverted"
        elif not isinstance(fac, str) or fac == "":
            reason = "facility_missing"
        if reason is None:
            b = position(get(lcs, "location", "begin", "beginLongitude"), get(lcs, "location", "begin", "beginLatitude"))
            e = position(get(lcs, "location", "end", "endLongitude"), get(lcs, "location", "end", "endLatitude"))
            reason = b if isinstance(b, str) else e if isinstance(e, str) else None
        if reason is not None:
            out["refused"].append({"index": idx, "reason": reason})
            continue
        c97, c98, c22 = (v == "true" for v in codes)
        s = int(start)
        live = c97 or (s <= now and (ind == "true" or now <= int(end)))
        if c22 or c98 or not live:
            continue
        out["active"] += 1
        out["closures"].append({"index": idx, "confirmed": c97, "facility": fac, "rings": rings(*b, *e)})
    rank = lambda f: RANK.index(f) if f in RANK else len(RANK)
    out["closures"].sort(key=lambda x: (not x["confirmed"], rank(x["facility"]), x["index"]))
    return out


def cap(closures):
    total, kept, dropped, features = 0, 0, 0, []
    for c in closures:
        if total + len(c["rings"]) > CAP:
            dropped += 1
            continue
        total += len(c["rings"])
        kept += 1
        for ring in c["rings"]:
            features.append({"type": "Feature", "properties": {"lcs_index": c["index"]},
                             "geometry": {"type": "Polygon", "coordinates": [ring]}})
    return {"geojson": {"type": "FeatureCollection", "features": features}, "kept": kept, "dropped": dropped}


def main():
    with open(os.path.join(HERE, "lcsStatusD07.json"), encoding="utf-8") as f:
        data = json.load(f)["data"]
    parsed = parse(data, NOW_S)
    capped = cap(parsed["closures"])
    digest = hashlib.sha256(json.dumps(capped["geojson"], separators=(",", ":")).encode()).hexdigest()
    expected = {"now_s": NOW_S, "parse": parsed, "cap": capped, "version": "lcs-d7-" + digest[:16]}
    with open(os.path.join(HERE, "expected.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(expected, f, indent=1)
        f.write("\n")
    print(f"rows={parsed['rows']} full={parsed['full']} active={parsed['active']} refused={len(parsed['refused'])} "
          f"kept={capped['kept']} dropped={capped['dropped']} polygons={len(capped['geojson']['features'])} "
          f"version={expected['version']}")


if __name__ == "__main__":
    main()
