"""Reading `--mode route-details` output, and the residential/service RUNS measured from it (T-0209).

ScenicRouterMain prints, per routed profile/model:

    ROUTE profile=car_scenic model=lambda-8.json time_ms=1234567 distance_m=23456.7
    EDGE model=lambda-8.json seq=0 road_class=primary osm_way_id=74344132 distance_m=123.456
    ...

A RUN is a maximal sequence of CONSECUTIVE edges whose road_class is in a given set (T-0224's definition:
"consecutive edges of one class"). One OSM way is usually several edges, so a run is reported in metres with
the distinct way ids it crossed, in route order. Pure functions: test_route_details.py parses the image's
real output with `parse`, and tools/route_la_pairs.py measures LA with `longest_run`.
"""

MINOR_CLASSES = ("residential", "living_street", "service")


def _fields(tokens):
    return dict(token.split("=", 1) for token in tokens)


def parse(stdout):
    """-> [{profile, model, time_ms, distance_m, edges: [{seq, road_class, way, m}]}] in output order."""
    routes = []
    for line in stdout.splitlines():
        tokens = line.strip().split()
        if not tokens:
            continue
        if tokens[0] == "ROUTE":
            kv = _fields(tokens[1:])
            routes.append({
                "profile": kv["profile"],
                "model": kv["model"],
                "time_ms": int(kv["time_ms"]),
                "distance_m": float(kv["distance_m"]),
                "edges": [],
            })
        elif tokens[0] == "EDGE":
            kv = _fields(tokens[1:])
            if not routes or routes[-1]["model"] != kv["model"]:
                raise ValueError(f"EDGE row for model={kv['model']} does not follow its ROUTE line: {line!r}")
            routes[-1]["edges"].append({
                "seq": int(kv["seq"]),
                "road_class": kv["road_class"].lower(),
                "way": int(kv["osm_way_id"]),
                "m": float(kv["distance_m"]),
            })
    return routes


def runs(edges, classes):
    """Every maximal run of consecutive edges with road_class in `classes`:
    [{"m": metres, "ways": [distinct way ids in route order], "classes": sorted classes seen, "edges": n}]."""
    wanted = set(classes)
    found = []
    current = None
    for edge in edges:
        if edge["road_class"] in wanted:
            if current is None:
                current = {"m": 0.0, "ways": [], "classes": set(), "edges": 0}
            current["m"] += edge["m"]
            current["edges"] += 1
            current["classes"].add(edge["road_class"])
            if not current["ways"] or current["ways"][-1] != edge["way"]:
                if edge["way"] not in current["ways"]:
                    current["ways"].append(edge["way"])
        elif current is not None:
            found.append(current)
            current = None
    if current is not None:
        found.append(current)
    for run in found:
        run["classes"] = sorted(run["classes"])
    return found


def longest_run(edges, classes):
    """The longest run (ties: the first), or an empty run of 0 m when the route never enters `classes`."""
    best = {"m": 0.0, "ways": [], "classes": [], "edges": 0}
    for run in runs(edges, classes):
        if run["m"] > best["m"]:
            best = run
    return best


def class_metres(edges):
    """{road_class: metres} over one route."""
    totals = {}
    for edge in edges:
        totals[edge["road_class"]] = totals.get(edge["road_class"], 0.0) + edge["m"]
    return totals
