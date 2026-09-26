"""T-0209/T-0244 MEASUREMENT: T(lambda) and the residential/service RUNS over the whole-LA graph, three typed pairs.

    python services/routing/tools/route_la_pairs.py            # route (docker through WSL), save, report
    python services/routing/tools/route_la_pairs.py --reuse    # re-report from the saved raw output only

Defaults point at the MAIN checkout's gitignored services/routing/work/t0209/ (a worktree removal deletes
gitignored files, so the graph never lives in a worktree): graph-la/ (import-graph.sh, image
scenic-routing:t0209), models/lambda-{0,1,2,4,8}.json (each `ops/plan --emit-model <lambda>` byte for byte) and
routes/<pair>.txt (the raw `--mode route-details` stdout, one container run per pair, so a reviewer can
re-report without docker and re-route with it).

T-0244: the models dir may hold any number of FAMILIES, each file named <family>-<lambda>.json (lambda-0.5.json,
cand-2.json); one container run per pair routes every file, and each family is reported as its own table
(`PAIR <pair>/<family>`) over its lambdas in numeric order. W0 uses the model file's own distance_influence
when it sets one (a request model overrides the base profile's). --fixture PAIR:FILE writes that route's edges
with the probed scenic_score of every minor-class edge, plus the model's bytes, under --fixture-dir.

Prints, in order: GRAPH_DIGEST (sha256 of the `sha256sum`-style manifest of every file in the graph dir, sorted
by name - the graph's identity in place of an /info hash this slice does not serve); per pair and family the
ROUTE durations (car_fast, then the lambdas), whether T is non-decreasing over lambda, the lowest -> highest
lambda spread (the bite); per route the longest run of each minor class and the longest mixed minor run
(tools/route_details.py defines a run), with metres, way ids and classes. It asserts nothing: the Log rules.
"""

import argparse
import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.route_details import MINOR_CLASSES, class_metres, longest_run, parse  # noqa: E402

ROUTING = Path(__file__).resolve().parents[1]
REPO = ROUTING.parents[1]
MAIN = REPO.parents[1] if REPO.parent.name == ".worktrees" else REPO
WORK = MAIN / "services" / "routing" / "work" / "t0209"

# Typed from the T-0209 Log's Nominatim geocode (tools/geocode_la_places.py), 4 decimals.
WESTWOOD = "34.0669,-118.4399"
MALIBU = "34.0356,-118.6894"
WOODLAND_HILLS = "34.1684,-118.6058"
SANTA_MONICA = "34.0195,-118.4912"
TOPANGA = "34.0676,-118.5957"
PAIRS = (
    ("westwood-malibu", WESTWOOD, MALIBU),
    ("westwood-woodland-hills", WESTWOOD, WOODLAND_HILLS),
    ("santa-monica-topanga", SANTA_MONICA, TOPANGA),
)
LAMBDAS = ("lambda-0.json", "lambda-1.json", "lambda-2.json", "lambda-4.json", "lambda-8.json")


def wsl_path(path):
    text = str(Path(path).resolve())
    if len(text) > 1 and text[1] == ":":
        return "/mnt/" + text[0].lower() + text[2:].replace("\\", "/")
    return text


def shell(command):
    argv = ["wsl", "-e", "bash", "-lc", command] if shutil.which("wsl") else ["bash", "-lc", command]
    return subprocess.run(argv, capture_output=True, text=True, timeout=3600)


def graph_digest(graph):
    manifest = ""
    for path in sorted(p for p in graph.iterdir() if p.is_file()):
        manifest += f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest(), manifest


def family_of(label):
    """"cand-0.5.json" -> ("cand", 0.5). The lambda is the text after the LAST hyphen."""
    stem = label[:-len(".json")] if label.endswith(".json") else label
    family, _, lam = stem.rpartition("-")
    return family, float(lam)


def families(models_dir):
    """{family: [labels in numeric lambda order]} over every *.json in the models dir."""
    grouped = {}
    for path in sorted(models_dir.glob("*.json")):
        family, lam = family_of(path.name)
        grouped.setdefault(family, []).append((lam, path.name))
    return {family: tuple(label for _, label in sorted(rows)) for family, rows in grouped.items()}


def route_pair(args, name, origin, destination):
    raw = args.out / f"{name}.txt"
    if not args.reuse:
        result = shell(
            f"docker run --rm -e JAVA_TOOL_OPTIONS={args.heap} -v {wsl_path(args.graph)}:/graph "
            f"-v {wsl_path(args.models)}:/models:ro {args.image} --config /app/config.yml --graph /graph "
            f"--mode route-details --from {origin} --to {destination} "
            f"--fast-profile car_fast --scenic-profile car_scenic --models /models"
        )
        if result.returncode != 0:
            raise SystemExit(f"{name}: route-details exited {result.returncode}\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")
        raw.write_text(result.stdout, encoding="utf-8", newline="\n")
    return parse(raw.read_text(encoding="utf-8"))


RUN_WAYS = set()  # every way id of every longest run reported (and of a --fixture route), probed at the end


def probe_run_ways(args):
    """One `--mode probe` over the ways of the reported runs: the score the GRAPH encoded for each.
    -> {way id: scenic_score}."""
    raw = args.out / "probe-run-ways.txt"
    probed = set()
    if raw.is_file():
        probed = {int(line.split()[1][len("way="):]) for line in raw.read_text(encoding="utf-8").splitlines()
                  if line.startswith("PROBE ")}
    # --reuse re-reads a probe only when it covers every way asked for now (a --fixture asks for more ways).
    if not args.reuse or not RUN_WAYS <= probed:
        ways = ",".join(str(way) for way in sorted(RUN_WAYS))
        result = shell(
            f"docker run --rm -e JAVA_TOOL_OPTIONS={args.heap} -v {wsl_path(args.graph)}:/graph {args.image} "
            f"--config /app/config.yml --graph /graph --mode probe --probe-ways {ways}"
        )
        if result.returncode != 0:
            raise SystemExit(f"probe exited {result.returncode}\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")
        raw.write_text(result.stdout, encoding="utf-8", newline="\n")
    scores = {}
    for line in raw.read_text(encoding="utf-8").splitlines():
        if line.startswith("PROBE "):
            print("RUN_WAY_SCORE " + line[len("PROBE "):])
            kv = dict(token.split("=", 1) for token in line.split()[1:])
            scores[int(kv["way"])] = int(kv["scenic_score"])
    return scores


def ways_text(ways, limit=12):
    shown = ",".join(str(way) for way in ways[:limit])
    return shown + (f",+{len(ways) - limit} more" if len(ways) > limit else "")


def influence_of(models_dir, label, base):
    """The distance_influence the router used for `label`: the request model's own if it sets one."""
    path = None if models_dir is None else Path(models_dir) / label
    if path is not None and path.is_file():
        model = json.loads(path.read_text(encoding="utf-8"))
        if "distance_influence" in model:
            return model["distance_influence"]
    return base


def report_pair(name, origin, destination, routes, labels=LAMBDAS, models_dir=None):
    by_model = {route["model"]: route for route in routes}
    missing = [label for label in ("-",) + tuple(labels) if label not in by_model]
    if missing:
        raise SystemExit(f"{name}: no ROUTE for {missing} - were all the models in the models dir?")
    print(f"PAIR {name} from={origin} to={destination}")
    for label in ("-",) + tuple(labels):
        route = by_model[label]
        print(f"  ROUTE {label:<14} time_ms={route['time_ms']:>8} min={route['time_ms'] / 60000:7.2f} "
              f"distance_m={route['distance_m']:9.1f} edges={len(route['edges'])}")
    times = [by_model[label]["time_ms"] for label in labels]
    monotone = all(a <= b for a, b in zip(times, times[1:]))
    spread = (times[-1] - times[0]) / times[0]
    print(f"  T_NONDECREASING {name} {monotone} T={times}")
    # What the weighting minimises at lambda 0 when every edge's priority is 1: seconds plus distance_influence
    # per km (the model's own, else profiles/car_scenic_base.json's). Exact for a route with no RESIDENTIAL edge
    # (T-0209's model halves a low-score residential edge's priority at every lambda); marked otherwise.
    base_influence = json.loads((ROUTING / "profiles" / "car_scenic_base.json").read_text(encoding="utf-8"))["distance_influence"]
    base = []
    for label in labels:
        route = by_model[label]
        influence = influence_of(models_dir, label, base_influence)
        exact = not any(edge["road_class"] == "residential" for edge in route["edges"])
        base.append(f"{route['time_ms'] / 1000 + influence * route['distance_m'] / 1000:.2f}"
                    f"{'' if exact else '(+res)'}@{influence}")
    print(f"  W0 {name} seconds+influence/km=[{', '.join(base)}]")
    print(f"  BITE {name} T0={times[0]} T8={times[-1]} spread={spread * 100:+.2f}%")
    worst = []
    for label in ("-",) + tuple(labels):
        edges = by_model[label]["edges"]
        metres = class_metres(edges)
        parts = []
        for road_class in MINOR_CLASSES:
            run = longest_run(edges, (road_class,))
            RUN_WAYS.update(run["ways"])
            parts.append(f"{road_class}={run['m']:.1f}m[{ways_text(run['ways'])}]")
        mixed = longest_run(edges, MINOR_CLASSES)
        RUN_WAYS.update(mixed["ways"])
        total = sum(metres.get(c, 0.0) for c in MINOR_CLASSES)
        print(f"  RUNS {label:<14} " + " ".join(parts)
              + f" mixed={mixed['m']:.1f}m{mixed['classes']}[{ways_text(mixed['ways'])}] minor_total={total:.1f}m")
        worst.append((mixed["m"], label, mixed))
    return monotone, spread, max(worst, key=lambda item: item[0])


def write_fixture(args, route, pair, label, scores):
    """The recorded route a Linux test reads without a container: one row per edge, the minor-class edges
    carrying the graph's encoded scenic_score ("-" on every other class, which the rat-run rule never reads)."""
    args.fixture_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{pair}-lambda-{label[:-len('.json')].rpartition('-')[2]}"
    rows = ["seq\troad_class\tosm_way_id\tdistance_m\tscenic_score"]
    for edge in route["edges"]:
        score = scores[edge["way"]] if edge["road_class"] in MINOR_CLASSES else "-"
        rows.append(f"{edge['seq']}\t{edge['road_class']}\t{edge['way']}\t{edge['m']:.3f}\t{score}")
    (args.fixture_dir / f"{stem}.edges.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    shutil.copyfile(args.models / label, args.fixture_dir / f"{stem}.model.json")
    print(f"FIXTURE {stem} edges={len(route['edges'])} time_ms={route['time_ms']} distance_m={route['distance_m']:.1f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, default=WORK / "graph-la")
    parser.add_argument("--models", type=Path, default=WORK / "models")
    parser.add_argument("--out", type=Path, default=WORK / "routes")
    parser.add_argument("--image", default="scenic-routing:t0209")
    parser.add_argument("--heap", default="-Xmx6g")
    parser.add_argument("--reuse", action="store_true", help="re-report from --out without running docker")
    parser.add_argument("--fixture", action="append", default=[],
                        help="PAIR:MODELFILE (repeatable) - record that route's edges under --fixture-dir")
    parser.add_argument("--fixture-dir", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    digest, manifest = graph_digest(args.graph)
    print(f"GRAPH_DIGEST sha256={digest} dir={args.graph}")
    print("".join("  " + line for line in manifest.splitlines(keepends=True)), end="")
    grouped = families(args.models)
    summary = []
    fixture_routes = []
    for name, origin, destination in PAIRS:
        routes = route_pair(args, name, origin, destination)
        for family, labels in grouped.items():
            summary.append((f"{name}/{family}",) + report_pair(f"{name}/{family}", origin, destination, routes,
                                                               labels=labels, models_dir=args.models))
        for label in [f.split(":", 1)[1] for f in args.fixture if f.split(":", 1)[0] == name]:
            fixture_routes.append((name, label, next(r for r in routes if r["model"] == label)))
            RUN_WAYS.update(e["way"] for e in fixture_routes[-1][2]["edges"] if e["road_class"] in MINOR_CLASSES)
    print(f"SUMMARY monotone={sum(1 for s in summary if s[1])}/{len(summary)} "
          f"bites={','.join(f'{s[0]}:{s[2] * 100:+.2f}%' for s in summary)}")
    for name, _, _, (metres, label, run) in summary:
        print(f"SUMMARY longest_mixed_minor_run {name} {metres:.1f}m model={label} classes={run['classes']} "
              f"ways=[{ways_text(run['ways'], 40)}]")
    scores = probe_run_ways(args) if RUN_WAYS else {}
    for name, label, route in fixture_routes:
        write_fixture(args, route, name, label, scores)


if __name__ == "__main__":
    main()
