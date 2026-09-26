"""T-0209 MEASUREMENT: T(lambda) and the residential/service RUNS over the whole-LA graph, three typed pairs.

    python services/routing/tools/route_la_pairs.py            # route (docker through WSL), save, report
    python services/routing/tools/route_la_pairs.py --reuse    # re-report from the saved raw output only

Defaults point at the MAIN checkout's gitignored services/routing/work/t0209/ (a worktree removal deletes
gitignored files, so the graph never lives in a worktree): graph-la/ (import-graph.sh, image
scenic-routing:t0209), models/lambda-{0,1,2,4,8}.json (each `ops/plan --emit-model <lambda>` byte for byte) and
routes/<pair>.txt (the raw `--mode route-details` stdout, one container run per pair, so a reviewer can
re-report without docker and re-route with it).

Prints, in order: GRAPH_DIGEST (sha256 of the `sha256sum`-style manifest of every file in the graph dir, sorted
by name - the graph's identity in place of an /info hash this slice does not serve); per pair the six ROUTE
durations (car_fast, then the five lambdas), whether T is non-decreasing over lambda, the lambda 0 -> 8 spread
(the bite); per route the longest run of each minor class and the longest mixed minor run (tools/route_details.py
defines a run), with metres, way ids and classes. It asserts nothing: the Log rules on the numbers.
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


RUN_WAYS = set()  # every way id of every longest run reported, probed for its encoded scenic_score at the end


def probe_run_ways(args):
    """One `--mode probe` over the ways of the reported runs: the score the GRAPH encoded for each (the
    emitted model's anti-rat-run clause multiplies RESIDENTIAL by 0.5 only when scenic_score < 7)."""
    raw = args.out / "probe-run-ways.txt"
    if not args.reuse:
        ways = ",".join(str(way) for way in sorted(RUN_WAYS))
        result = shell(
            f"docker run --rm -e JAVA_TOOL_OPTIONS={args.heap} -v {wsl_path(args.graph)}:/graph {args.image} "
            f"--config /app/config.yml --graph /graph --mode probe --probe-ways {ways}"
        )
        if result.returncode != 0:
            raise SystemExit(f"probe exited {result.returncode}\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")
        raw.write_text(result.stdout, encoding="utf-8", newline="\n")
    for line in raw.read_text(encoding="utf-8").splitlines():
        if line.startswith("PROBE "):
            print("RUN_WAY_SCORE " + line[len("PROBE "):])


def ways_text(ways, limit=12):
    shown = ",".join(str(way) for way in ways[:limit])
    return shown + (f",+{len(ways) - limit} more" if len(ways) > limit else "")


def report_pair(name, origin, destination, routes):
    by_model = {route["model"]: route for route in routes}
    missing = [label for label in ("-",) + LAMBDAS if label not in by_model]
    if missing:
        raise SystemExit(f"{name}: no ROUTE for {missing} - were all five models in the models dir?")
    print(f"PAIR {name} from={origin} to={destination}")
    for label in ("-",) + LAMBDAS:
        route = by_model[label]
        print(f"  ROUTE {label:<14} time_ms={route['time_ms']:>8} min={route['time_ms'] / 60000:7.2f} "
              f"distance_m={route['distance_m']:9.1f} edges={len(route['edges'])}")
    times = [by_model[label]["time_ms"] for label in LAMBDAS]
    monotone = all(a <= b for a, b in zip(times, times[1:]))
    spread = (times[-1] - times[0]) / times[0]
    print(f"  T_NONDECREASING {name} {monotone} T={times}")
    # What the weighting actually minimises at lambda 0 when every edge's priority is 1: seconds plus
    # distance_influence (profiles/car_scenic_base.json) per km. Exact for a route with no RESIDENTIAL edge
    # (the emitted model halves a low-score residential edge's priority at every lambda); marked otherwise.
    influence = json.loads((ROUTING / "profiles" / "car_scenic_base.json").read_text(encoding="utf-8"))["distance_influence"]
    base = []
    for label in LAMBDAS:
        route = by_model[label]
        exact = not any(edge["road_class"] == "residential" for edge in route["edges"])
        base.append(f"{route['time_ms'] / 1000 + influence * route['distance_m'] / 1000:.2f}{'' if exact else '(+res)'}")
    print(f"  W0 {name} seconds+{influence}/km=[{', '.join(base)}]")
    print(f"  BITE {name} T0={times[0]} T8={times[-1]} spread={spread * 100:+.2f}%")
    worst = []
    for label in ("-",) + LAMBDAS:
        edges = by_model[label]["edges"]
        metres = class_metres(edges)
        parts = []
        for road_class in MINOR_CLASSES:
            run = longest_run(edges, (road_class,))
            RUN_WAYS.update(run["ways"])
            parts.append(f"{road_class}={run['m']:.1f}m[{ways_text(run['ways'])}]")
        mixed = longest_run(edges, MINOR_CLASSES)
        total = sum(metres.get(c, 0.0) for c in MINOR_CLASSES)
        print(f"  RUNS {label:<14} " + " ".join(parts)
              + f" mixed={mixed['m']:.1f}m{mixed['classes']}[{ways_text(mixed['ways'])}] minor_total={total:.1f}m")
        worst.append((mixed["m"], label, mixed))
    return monotone, spread, max(worst, key=lambda item: item[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, default=WORK / "graph-la")
    parser.add_argument("--models", type=Path, default=WORK / "models")
    parser.add_argument("--out", type=Path, default=WORK / "routes")
    parser.add_argument("--image", default="scenic-routing:t0209")
    parser.add_argument("--heap", default="-Xmx6g")
    parser.add_argument("--reuse", action="store_true", help="re-report from --out without running docker")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    digest, manifest = graph_digest(args.graph)
    print(f"GRAPH_DIGEST sha256={digest} dir={args.graph}")
    print("".join("  " + line for line in manifest.splitlines(keepends=True)), end="")
    summary = []
    for name, origin, destination in PAIRS:
        summary.append((name,) + report_pair(name, origin, destination, route_pair(args, name, origin, destination)))
    print(f"SUMMARY monotone={sum(1 for s in summary if s[1])}/{len(summary)} "
          f"bites={','.join(f'{s[0]}:{s[2] * 100:+.2f}%' for s in summary)}")
    for name, _, _, (metres, label, run) in summary:
        print(f"SUMMARY longest_mixed_minor_run {name} {metres:.1f}m model={label} classes={run['classes']} "
              f"ways=[{ways_text(run['ways'], 40)}]")
    if RUN_WAYS:
        probe_run_ways(args)


if __name__ == "__main__":
    main()
