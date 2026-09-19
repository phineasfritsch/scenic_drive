"""T-0224 MEASUREMENT: T-0213's routed pair at lambda 0 and lambda 8, and what the router will say about it.

NUMBERS ONLY, and an honest boundary. This script asserts nothing (it is not a `test_*.py`, so `ops/test`
does not collect it); T-0209's anti-rat-run ruling is written AFTER reading what it prints.

WHAT WAS ASKED FOR: the longest run of consecutive residential/service edges on T-0213's window route, per
lambda, in metres and way ids - which needs GraphHopper PATH DETAILS (road_class, osm_way_id, distance).

WHAT THIS HARNESS CAN ANSWER: `ROUTE profile=<p> model=<m> time_ms=<t> distance_m=<d>` and nothing else.
The image under test is built from services/routing/plugins/scenic-score-parser/pom.xml, whose only
GraphHopper dependency is `graphhopper-core`: there is no graphhopper-web / graphhopper-application in the
jar, so the image serves no HTTP `/route` and the `details=` query parameter has nowhere to arrive.
Its ENTRYPOINT is ScenicRouterMain, whose `route()` prints exactly the one ROUTE line above from
`ResponsePath.getTime()` and `getDistance()` and never touches `getPathDetails()`, and whose mode dispatch
is `probe` / `route` / silent return. Reaching per-edge details means editing
services/routing/plugins/... - which T-0224 forbids (acceptance 3: nothing under services/routing/ changes).
So this script ROUTES the pair, quotes the lines it gets, and DEMONSTRATES the boundary rather than
asserting it: it runs the same container with an unknown `--mode` and quotes the empty answer, and it reads
the pom's dependency list back out.

EXACT COMMANDS (repo root; docker lives inside WSL on this box). The graph is T-0213's imported window
graph; a worktree does not carry gitignored work/, so it is copied in first and the copy is what runs:

    cp -r ../../services/routing/work/t0213/graph-la-window services/routing/work/t0224/graph-la-window
    python services/routing/tests/measure_runs.py

    # which runs, after substituting profiles/scenic_lambda_bands.json into profiles/car_scenic_request.json:
    docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx4g -v <graph>:/graph -v <models>:/models:ro scenic-routing:t0213 \
      --config /app/config.yml --graph /graph --mode route --from 34.0387,-118.5836 --to 34.0938,-118.6045 \
      --fast-profile car_fast --scenic-profile car_scenic --models /models

THE PAIR: PCH at Topanga -> Topanga Canyon Boulevard near Old Topanga, the one T-0213 routed (its Log,
2026-09-19T12:00:10Z: car_fast 507242 ms / 8121.6 m). T-0213 recorded the pair in prose and not as
coordinates, so the binding back to it is the DISTANCE: these endpoints must reproduce 8121.6 m, and this
script prints T-0213's number beside its own for the reader to compare.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE = "scenic-routing:t0213"
LAMBDAS = (0, 8)

# PCH at Topanga -> Topanga Canyon Boulevard near Old Topanga Canyon Road.
FROM_POINT = "34.0387,-118.5836"
TO_POINT = "34.0938,-118.6045"
T0213_DISTANCE_M = 8121.6  # T-0213 Log, 2026-09-19T12:00:10Z - quoted, never asserted
T0213_TIME_MS = 507242

ROUTING = Path(__file__).resolve().parents[1]
REPO = ROUTING.parents[1]
POM = ROUTING / "plugins" / "scenic-score-parser" / "pom.xml"
TEMPLATE = ROUTING / "profiles" / "car_scenic_request.json"
BANDS = ROUTING / "profiles" / "scenic_lambda_bands.json"
WORK = ROUTING / "work" / "t0224"
MODELS = WORK / "models"
GRAPH_CANDIDATES = (
    WORK / "graph-la-window",
    REPO / "services" / "routing" / "work" / "t0213" / "graph-la-window",
    REPO.parents[1] / "services" / "routing" / "work" / "t0213" / "graph-la-window"
    if len(REPO.parents) > 1
    else WORK / "graph-la-window",
)

ROUTE_LINE = re.compile(
    r"^ROUTE profile=(?P<profile>\S+) model=(?P<model>\S+) time_ms=(?P<time_ms>\d+) "
    r"distance_m=(?P<distance_m>[0-9.]+)$"
)


def shell(command: str, timeout: int = 1800):
    """Run where docker is: inside WSL on the Windows box, directly on Linux - T-0213's harness shape."""
    if shutil.which("wsl"):
        argv = ["wsl", "-e", "bash", "-lc", command]
    elif shutil.which("bash"):
        argv = ["bash", "-lc", command]
    else:
        raise SystemExit("neither wsl nor bash on PATH, so there is no docker to reach")
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def wsl_path(path: Path) -> str:
    """C:\\Users\\x -> /mnt/c/Users/x, the only spelling docker inside WSL understands."""
    text = str(Path(path).resolve())
    if len(text) > 1 and text[1] == ":":
        return "/mnt/" + text[0].lower() + text[2:].replace("\\", "/")
    return text


def graph() -> Path:
    for candidate in GRAPH_CANDIDATES:
        if (candidate / "edges").exists():
            return candidate
    raise SystemExit(f"no imported graph found; looked at {[str(c) for c in GRAPH_CANDIDATES]}")


def write_models() -> Path:
    """Substitute each lambda's band multipliers into the shipped per-request model (committed profiles)."""
    template = TEMPLATE.read_text(encoding="utf-8")
    bands = json.loads(BANDS.read_text(encoding="utf-8"))
    if MODELS.exists():
        shutil.rmtree(MODELS)
    MODELS.mkdir(parents=True)
    for value in LAMBDAS:
        band = bands[str(value)]
        model = template
        for name in ("high", "mid", "low"):
            model = model.replace("${" + name + "}", band[name])
        if "${" in model:
            raise SystemExit(f"unsubstituted placeholder left in the model for lambda={value}")
        json.loads(model)
        (MODELS / f"lambda-{value}.json").write_text(model, encoding="utf-8")
        print(f"  lambda={value} model={json.dumps(json.loads(model)['priority'])}")
    return MODELS


def route(graph_dir: Path, models: Path) -> dict:
    command = (
        f"docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx4g "
        f"-v {wsl_path(graph_dir)}:/graph -v {wsl_path(models)}:/models:ro {IMAGE} "
        f"--config /app/config.yml --graph /graph --mode route "
        f"--from {FROM_POINT} --to {TO_POINT} "
        f"--fast-profile car_fast --scenic-profile car_scenic --models /models"
    )
    print(f"$ {command}")
    result = shell(command)
    if result.returncode != 0:
        print(result.stdout[-4000:])
        print(result.stderr[-4000:], file=sys.stderr)
        raise SystemExit(f"router run failed ({result.returncode})")
    parsed = {}
    for line in result.stdout.splitlines():
        match = ROUTE_LINE.match(line.strip())
        if match:
            print("  " + line.strip())
            parsed[match.group("model")] = (int(match.group("time_ms")), float(match.group("distance_m")))
    return parsed


def details_probe(graph_dir: Path) -> None:
    """The CLI surface, demonstrated rather than described: an unknown --mode answers with nothing at all."""
    command = (
        f"docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx4g -v {wsl_path(graph_dir)}:/graph {IMAGE} "
        f"--config /app/config.yml --graph /graph --mode details "
        f"--from {FROM_POINT} --to {TO_POINT}"
    )
    print(f"$ {command}")
    result = shell(command)
    body = "\n".join(
        line for line in result.stdout.splitlines() if line.strip() and not line.startswith("[main]")
    )
    print(f"  exit={result.returncode} stdout-without-log-lines={body!r}")


def pom_dependencies() -> None:
    text = POM.read_text(encoding="utf-8")
    artifacts = re.findall(r"<artifactId>([^<]+)</artifactId>", text)
    print(f"  {POM.relative_to(REPO).as_posix()} artifactIds: {', '.join(artifacts)}")
    web = [name for name in artifacts if name.startswith("graphhopper-") and name != "graphhopper-core"]
    print(f"  graphhopper modules other than graphhopper-core in the image: {web or 'NONE'}")


def main() -> int:
    graph_dir = graph()
    print(f"ROUTED PAIR from={FROM_POINT} to={TO_POINT}  graph={graph_dir}")
    print(f"T-0213 recorded car_fast time_ms={T0213_TIME_MS} distance_m={T0213_DISTANCE_M} on this pair")
    print("PER-REQUEST MODELS (profiles/scenic_lambda_bands.json into profiles/car_scenic_request.json):")
    models = write_models()
    print("ROUTE:")
    parsed = route(graph_dir, models)
    print("PATH DETAILS PROBE (unknown --mode, to show the CLI surface):")
    details_probe(graph_dir)
    print("IMAGE DEPENDENCIES (why there is no HTTP /route to ask for details=):")
    pom_dependencies()
    print()
    print("LONGEST RESIDENTIAL/SERVICE RUN: NOT REACHABLE THROUGH THIS HARNESS.")
    print(
        "  Reachable: the ROUTE lines above (profile, model, time_ms, distance_m) and "
        "--mode probe's 'PROBE way=<id> edges=<n> scenic_score=<csv>' over way ids named on the command "
        "line. Neither carries road_class, per-edge distance, or the routed edge sequence."
    )
    for label, (time_ms, distance_m) in parsed.items():
        print(f"  got: model={label} time_ms={time_ms} distance_m={distance_m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
