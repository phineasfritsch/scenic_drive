"""T-0282: measure the stored set and the per-request nearest-first selection over the recorded D7 response.

Independent of services/api: reads expected.json (the oracle's 163 active Full closures in R5 order) and the raw
feed, and recomputes in the local plane of R4 (110946 m/deg lat, 91961 m/deg lon) with + - * / only.

  python Tests/Fixtures/t0276/nearest.py            -> the measurement lines quoted in the T-0282 Log
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PER_REQUEST = 50


def xy(p):
    return (p[0] * oracle.M_LON, p[1] * oracle.M_LAT)


def point_seg2(p, a, b):
    """Squared distance from p to segment ab (a == b: to the point)."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    vv = vx * vx + vy * vy
    t = 0.0 if vv == 0 else (wx * vx + wy * vy) / vv
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    dx, dy = a[0] + t * vx - p[0], a[1] + t * vy - p[1]
    return dx * dx + dy * dy


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def crosses(a, b, c, d):
    d1, d2, d3, d4 = cross(c, d, a), cross(c, d, b), cross(a, b, c), cross(a, b, d)
    return ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0))


def inside(p, ring):
    hit = False
    for i in range(len(ring) - 1):
        a, b = ring[i], ring[i + 1]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if p[0] < x:
                hit = not hit
    return hit


def ring_dist2(o, d, ring):
    pts = [xy(p) for p in ring]
    if inside(o, pts):
        return 0.0
    best = None
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if crosses(o, d, a, b):
            return 0.0
        for v in (point_seg2(o, a, b), point_seg2(d, a, b), point_seg2(a, o, d), point_seg2(b, o, d)):
            best = v if best is None or v < best else best
    return best


def select(closures, origin, destination):
    """closures: [(index, rings)] in stored order. Nearest whole closures, stable on stored order; a prefix."""
    o, d = xy(origin), xy(destination)
    scored = [(min(ring_dist2(o, d, r) for r in rings), at, index, rings) for at, (index, rings) in enumerate(closures)]
    scored.sort(key=lambda s: (s[0], s[1]))
    kept, used = [], 0
    for at, s in enumerate(scored):
        if used + len(s[3]) > PER_REQUEST:
            return kept, len(scored) - at, scored
        kept.append(s)
        used += len(s[3])
    return kept, 0, scored


def record_bytes(closures):
    feats = [{"type": "Feature", "properties": {"lcs_index": i}, "geometry": {"type": "Polygon", "coordinates": [r]}}
             for i, rings in closures for r in rings]
    rec = {"version": "lcs-d7-0123456789abcdef", "fetched_at": "2026-10-06T08:04:20.000Z",
           "geojson": {"type": "FeatureCollection", "features": feats},
           "stats": {"rows": 2808, "full": 1708, "active": 163, "refused": 0, "kept": 163, "dropped": 0}}
    return len(feats), len(json.dumps(rec, separators=(",", ":")).encode())


def main():
    with open(os.path.join(HERE, "expected.json")) as f:
        active = [(c["index"], c["rings"]) for c in json.load(f)["parse"]["closures"]]
    n, b = record_bytes(active)
    print(f"active closures={len(active)} polygons={n} record_bytes={b} two_ring={sum(len(r) == 2 for _, r in active)}")
    with open(os.path.join(HERE, "lcsStatusD07.json")) as f:
        data = json.load(f)["data"]
    every_full = []
    for row in data:
        lcs = row["lcs"]
        if lcs["closure"]["typeOfClosure"] != "Full":
            continue
        bg, en = lcs["location"]["begin"], lcs["location"]["end"]
        b0 = oracle.position(bg["beginLongitude"], bg["beginLatitude"])
        e0 = oracle.position(en["endLongitude"], en["endLatitude"])
        every_full.append((lcs["index"], oracle.rings(b0[0], b0[1], e0[0], e0[1])))
    n, b = record_bytes(every_full)
    print(f"worst case every Full row active: closures={len(every_full)} polygons={n} record_bytes={b}")
    corridors = {
        "santa-monica->pasadena": ((-118.4912, 34.0195), (-118.1445, 34.1478)),
        "malibu->downtown": ((-118.7798, 34.0259), (-118.2437, 34.0522)),
        "lancaster->long-beach": ((-118.1542, 34.6868), (-118.1937, 33.7701)),
        "loop@topanga": ((-118.6012, 34.0937), (-118.6012, 34.0937)),
        "loop@newhall": ((-118.5301, 34.3847), (-118.5301, 34.3847)),
    }
    for name, (o, d) in corridors.items():
        kept, dropped, scored = select(active, o, d)
        on = sum(1 for s in scored if s[0] == 0.0)
        far = scored[len(kept) - 1][0] ** 0.5 if kept else 0
        nxt = scored[len(kept)][0] ** 0.5 if dropped else float("nan")
        within = [sum(1 for s in scored if s[0] <= (k * 1000.0) ** 2) for k in (1, 5, 20)]
        print(f"{name}: on_corridor={on} within_1/5/20km={within} kept={len(kept)} polygons={sum(len(s[3]) for s in kept)} "
              f"dropped={dropped} farthest_kept_m={far:.0f} nearest_dropped_m={nxt:.0f}")


if __name__ == "__main__":
    main()
