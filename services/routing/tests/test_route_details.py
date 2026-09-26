"""T-0209 clause 1: `--mode route-details` prints road_class / osm_way_id / distance for every routed edge.

T-0224 could not measure a single residential or service run: the image's ScenicRouterMain printed
`ROUTE ... time_ms distance_m` and nothing else, and `--mode details` exited 0 printing nothing. This test runs
the SHIPPING entry point - the image's ENTRYPOINT main(), through docker - and requires, for every ROUTE it
prints, the EDGE rows the run measurement (tools/route_la_pairs.py) reads.

The graph is imported by the image under test into a fresh temp directory (T-0213 S1: a pre-built graph binds
the assertions to nothing), from the canyon window test_scenic_score_readback.py already pins by sha256, and
the pair is T-0224's TYPED pair 34.0387,-118.5836 -> 34.0938,-118.6045.

The models directory holds lambda-0 AND lambda-8 (the committed T-0213 template), so main()'s model loop routes
two files: a loop that routes one file's model under every file's label moves no ROUTE on the typed pair (all
three are 526739 ms / 8230.4 m there, measured), so the loop is checked on a second pair of the same window whose
lambda-8 route was measured to move (T-0209 Log, survivor pass).

RED (T-0209 Log): SCENIC_ROUTING_IMAGE=scenic-routing:t0213 - main's jar, which has no route-details mode.
Prerequisites as test_scenic_score_readback.py: docker (through WSL on this box), the image, the input PBF.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from test_scenic_score_readback import PBF_RELATIVE, PBF_SHA256, _pbf, _sha256, _shell, _wsl_path
from tools.route_details import parse

IMAGE = os.environ.get("SCENIC_ROUTING_IMAGE", "scenic-routing:t0209")
ROUTING = Path(__file__).resolve().parents[1]
FROM = "34.0387,-118.5836"
TO = "34.0938,-118.6045"
# The loop pair: a 3x3 grid inside the window's import bounds, 28 of 36 pairs routed, every one with lambda-0 ==
# car_fast and 20 with lambda-8 slower. This one: car_fast 1449345 ms / 23971.0 m, lambda-8 2515815 ms (+73.58 %).
LOOP_FROM = "34.0366,-118.7401"
LOOP_TO = "34.0875,-118.6044"
MODELS = ("lambda-0.json", "lambda-8.json")

# GraphHopper 11's RoadClass constants, lower-cased as its path details print them.
ROAD_CLASSES = {
    "other", "motorway", "trunk", "primary", "secondary", "tertiary", "residential", "unclassified",
    "service", "road", "track", "bridleway", "steps", "cycleway", "path", "living_street", "footway",
    "pedestrian", "platform", "corridor", "construction", "busway",
}


def _lambda_model(directory, value):
    """profiles/car_scenic_request.json with one lambda's bands substituted - the committed request template."""
    template = (ROUTING / "profiles" / "car_scenic_request.json").read_text(encoding="utf-8")
    bands = json.loads((ROUTING / "profiles" / "scenic_lambda_bands.json").read_text(encoding="utf-8"))[str(value)]
    for name, band in bands.items():
        template = template.replace("${" + name + "}", band)
    assert "${" not in template
    (directory / f"lambda-{value}.json").write_text(template, encoding="utf-8", newline="\n")


@pytest.fixture(scope="module")
def window():
    """(route-details runner) over one window graph the image under test imported itself, both models loaded."""
    pbf = _pbf()
    if not pbf.exists():
        pytest.skip(f"the read-only input {PBF_RELATIVE} is not in this checkout (looked at {pbf})")
    assert _sha256(pbf) == PBF_SHA256, f"{pbf} is not the canyon window this test's pair was typed against"
    if _shell(f"docker image inspect --format ok {IMAGE}", timeout=180).returncode != 0:
        pytest.skip(f"docker image {IMAGE} is not built; see services/routing/README.md")

    work = ROUTING / "work"
    work.mkdir(parents=True, exist_ok=True)
    graph = Path(tempfile.mkdtemp(prefix="graph-details-", dir=str(work)))
    models = Path(tempfile.mkdtemp(prefix="models-details-", dir=str(work)))
    try:
        _lambda_model(models, 0)
        _lambda_model(models, 8)
        imported = _shell(
            f"bash {_wsl_path(ROUTING / 'import-graph.sh')} {_wsl_path(pbf)} {_wsl_path(graph)} {IMAGE}"
        )
        assert imported.returncode == 0, f"import with {IMAGE} failed:\n{imported.stdout[-3000:]}\n{imported.stderr[-3000:]}"

        def route_details(origin, destination):
            result = _shell(
                f"docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx2g -v {_wsl_path(graph)}:/graph "
                f"-v {_wsl_path(models)}:/models:ro {IMAGE} --config /app/config.yml --graph /graph "
                f"--mode route-details --from {origin} --to {destination} "
                f"--fast-profile car_fast --scenic-profile car_scenic --models /models"
            )
            print("\n".join(line for line in result.stdout.splitlines() if line.startswith("ROUTE")))
            return result, parse(result.stdout)

        yield route_details
    finally:
        shutil.rmtree(graph, ignore_errors=True)
        shutil.rmtree(models, ignore_errors=True)


@pytest.fixture(scope="module")
def routed(window):
    return window(FROM, TO)


@pytest.fixture(scope="module")
def loop_routed(window):
    return window(LOOP_FROM, LOOP_TO)


def test_route_details_mode_exists_and_prints_every_route(routed):
    result, routes = routed
    assert result.returncode == 0, (
        f"{IMAGE} --mode route-details exited {result.returncode}:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}"
    )
    assert [(r["profile"], r["model"]) for r in routes] == [("car_fast", "-")] + [("car_scenic", m) for m in MODELS], (
        f"{IMAGE} --mode route-details printed routes {[(r['profile'], r['model']) for r in routes]}"
    )


def test_every_route_carries_one_edge_row_per_edge_in_order(routed):
    _, routes = routed
    assert routes, f"{IMAGE} printed no ROUTE line for --mode route-details"
    for route in routes:
        edges = route["edges"]
        assert edges, (
            f"model={route['model']}: ROUTE printed but no EDGE rows - the residential/service runs of this "
            f"route cannot be measured (T-0224's blocker)"
        )
        assert [edge["seq"] for edge in edges] == list(range(len(edges))), f"model={route['model']}: seq out of order"


def test_edge_distances_sum_to_the_route_distance(routed):
    _, routes = routed
    assert routes, f"{IMAGE} printed no ROUTE line for --mode route-details"
    for route in routes:
        total = sum(edge["m"] for edge in route["edges"])
        assert abs(total - route["distance_m"]) <= 0.5, (
            f"model={route['model']}: EDGE rows sum to {total:.3f} m, ROUTE says {route['distance_m']} m - "
            f"a row is missing, doubled or misaligned"
        )


def test_every_edge_names_a_road_class_and_an_osm_way(routed):
    _, routes = routed
    assert routes, f"{IMAGE} printed no ROUTE line for --mode route-details"
    for route in routes:
        for edge in route["edges"]:
            assert edge["road_class"] in ROAD_CLASSES, f"model={route['model']} seq={edge['seq']}: {edge}"
            assert edge["way"] > 0, f"model={route['model']} seq={edge['seq']}: no OSM way id: {edge}"


def test_each_osm_way_prints_one_road_class_in_one_unbroken_stretch(routed):
    """One OSM way is one highway= tag, so its edges share one road_class, and none of the measured routes
    leaves a way and comes back to it (0 of 21: the 3 here and the 18 saved LA routes). An osm_way_id aligned to
    a neighbouring edge credits a way with the next way's class - `way > 0` cannot see that."""
    _, routes = routed
    assert routes, f"{IMAGE} printed no ROUTE line for --mode route-details"
    for route in routes:
        classes = {}
        stretches = []
        for edge in route["edges"]:
            classes.setdefault(edge["way"], set()).add(edge["road_class"])
            if not stretches or stretches[-1] != edge["way"]:
                stretches.append(edge["way"])
        mixed = {way: sorted(seen) for way, seen in classes.items() if len(seen) > 1}
        assert not mixed, f"model={route['model']}: osm_way_id printed with more than one road_class: {mixed}"
        broken = sorted({way for way in stretches if stretches.count(way) > 1})
        assert not broken, f"model={route['model']}: the edges of these ways are not consecutive: {broken}"


def test_every_model_file_routes_its_own_model(loop_routed):
    """lambda-0 (every band 1) must be car_fast, and lambda-8 must not be: a model loop that routes one file's
    model, or none, under every file's label makes the two equal and T(lambda) flat - clause 4's bite reads 0."""
    result, routes = loop_routed
    assert result.returncode == 0, f"{IMAGE} exited {result.returncode}:\n{result.stderr[-3000:]}"
    by_model = {route["model"]: route for route in routes}
    assert sorted(by_model) == sorted(("-",) + MODELS), f"{IMAGE} printed routes {sorted(by_model)}"
    fast, zero, eight = by_model["-"], by_model["lambda-0.json"], by_model["lambda-8.json"]
    assert (zero["time_ms"], zero["distance_m"]) == (fast["time_ms"], fast["distance_m"]), (
        f"lambda-0 routed {zero['time_ms']} ms / {zero['distance_m']} m, car_fast {fast['time_ms']} ms / "
        f"{fast['distance_m']} m - lambda-0.json was not the model routed under its label"
    )
    assert eight["time_ms"] > fast["time_ms"], (
        f"lambda-8 routed {eight['time_ms']} ms / {eight['distance_m']} m, car_fast {fast['time_ms']} ms - "
        f"measured 2515815 ms against 1449345 ms; lambda-8.json was not the model routed under its label"
    )
