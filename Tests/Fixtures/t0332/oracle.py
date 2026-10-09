"""T-0332's independent reading of RouteScore over every recorded router body that carries scenic_score.

Run from the repository root: python Tests/Fixtures/t0332/oracle.py > Tests/Fixtures/t0332/route-scores.json

Written from the plan's formula and RouteScore.swift's stated constants, NOT from either port, so the TS suite
(services/api/test/routeScoreParity.test.ts) and the Swift suite (RouteScoreParityTests) are each held to a third
reading. Rows are cut as PlanTable cuts them (every osm_way_id / road_class / scenic_score boundary, neighbours with
the same three values merged), metres are the haversine over the row's points on the IUGG mean radius, and each row
of positive metres with a scenic_score becomes one edge of score / 10; unscored metres are left out.
"""
import glob
import json
import math
import os
import sys

RADIUS = 6_371_008.8
MEAN, P90, DUD, EPISODE = 0.60, 0.25, 0.15, 0.10
EPISODE_THRESHOLD, EPISODE_MIN, EPISODE_TARGET = 0.6, 800.0, 3.0
DUD_THRESHOLD, TOLERANCE = 0.25, 1e-9


def haversine(a, b):
    lat1, lat2 = math.radians(a[1]), math.radians(b[1])
    d_lat, d_lon = math.radians(b[1] - a[1]), math.radians(b[0] - a[0])
    h = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    return 2 * RADIUS * math.asin(min(1.0, math.sqrt(h)))


def covering(runs, index):
    for start, end, value in runs:
        if start <= index < end:
            return value
    return None


def whole(value):
    return math.trunc(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def edges_of(path):
    points = path["points"]["coordinates"]
    last = len(points) - 1
    details = path.get("details", {})
    ways, classes, scores = (details.get(k, []) for k in ("osm_way_id", "road_class", "scenic_score"))
    cuts = {0, last}
    for start, end, _ in ways + classes + scores:
        cuts.add(min(max(start, 0), last))
        cuts.add(min(max(end, 0), last))
    bounds = sorted(cuts)
    rows = []
    for i in range(len(bounds) - 1):
        start, end = bounds[i], bounds[i + 1]
        key = (whole(covering(ways, start)), covering(classes, start), whole(covering(scores, start)))
        metres = sum(haversine(points[k], points[k + 1]) for k in range(start, end))
        if rows and rows[-1][0] == key:
            rows[-1][1] += metres
        else:
            rows.append([key, metres])
    return [(metres, key[2] / 10) for key, metres in rows if metres > 0 and key[2] is not None]


def route_score(edges):
    total = sum(length for length, _ in edges)
    mean = sum(length * score for length, score in edges) / total
    ordered = sorted(edges, key=lambda edge: edge[1])
    running, p90 = 0.0, ordered[-1][1]
    for length, score in ordered:
        running += length
        if running >= total * 0.9 - total * TOLERANCE:
            p90 = score
            break
    dud = sum(length for length, score in edges if score <= DUD_THRESHOLD) / total
    episodes, run = 0, 0.0
    for length, score in edges:
        if score > EPISODE_THRESHOLD:
            run += length
        else:
            episodes += run >= EPISODE_MIN - total * TOLERANCE
            run = 0.0
    episodes += run >= EPISODE_MIN - total * TOLERANCE
    raw = MEAN * mean + P90 * p90 - DUD * dud + EPISODE * min(1.0, episodes / EPISODE_TARGET)
    return {"value": min(1.0, max(0.0, raw)), "mean": mean, "p90": p90, "dudFraction": dud,
            "episodeCount": int(episodes), "totalLength": total}


def main():
    rows = []
    for name in sorted(glob.glob("Tests/Fixtures/**/*.json", recursive=True)):
        try:
            with open(name, encoding="utf-8") as handle:
                path = json.load(handle)["paths"][0]
        except (ValueError, KeyError, IndexError, TypeError):
            continue
        if "scenic_score" not in path.get("details", {}):
            continue
        rows.append({"file": os.path.relpath(name, "Tests/Fixtures").replace(os.sep, "/"), **route_score(edges_of(path))})
    json.dump({"threshold": 0.45, "scores": rows}, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
