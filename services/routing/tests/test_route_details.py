"""T-0209 clause 1: `--mode route-details` prints road_class / osm_way_id / distance for every routed edge.

T-0224 could not measure a single residential or service run: the image's ScenicRouterMain printed
`ROUTE ... time_ms distance_m` and nothing else, and `--mode details` exited 0 printing nothing. This test runs
the SHIPPING entry point - the image's ENTRYPOINT main(), through docker - and requires, for every ROUTE it
prints, the EDGE rows the run measurement (tools/route_la_pairs.py) reads.

The graph is imported by the image under test into a fresh temp directory (T-0213 S1: a pre-built graph binds
the assertions to nothing), from the canyon window test_scenic_score_readback.py already pins by sha256, and
the pair is T-0224's TYPED pair 34.0387,-118.5836 -> 34.0938,-118.6045.

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

# GraphHopper 11's RoadClass constants, lower-cased as its path details print them.
ROAD_CLASSES = {
    "other", "motorway", "trunk", "primary", "secondary", "tertiary", "residential", "unclassified",
    "service", "road", "track", "bridleway", "steps", "cycleway", "path", "living_street", "footway",
    "pedestrian", "platform", "corridor", "construction", "busway",
}


def _lambda_8_model(directory):
    """profiles/car_scenic_request.json with lambda 8's bands substituted - the committed request template."""
    template = (ROUTING / "profiles" / "car_scenic_request.json").read_text(encoding="utf-8")
    bands = json.loads((ROUTING / "profiles" / "scenic_lambda_bands.json").read_text(encoding="utf-8"))["8"]
    for name, value in bands.items():
        template = template.replace("${" + name + "}", value)
    assert "${" not in template
    (directory / "lambda-8.json").write_text(template, encoding="utf-8", newline="\n")


@pytest.fixture(scope="module")
def routed():
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
        _lambda_8_model(models)
        imported = _shell(
            f"bash {_wsl_path(ROUTING / 'import-graph.sh')} {_wsl_path(pbf)} {_wsl_path(graph)} {IMAGE}"
        )
        assert imported.returncode == 0, f"import with {IMAGE} failed:\n{imported.stdout[-3000:]}\n{imported.stderr[-3000:]}"
        result = _shell(
            f"docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx2g -v {_wsl_path(graph)}:/graph "
            f"-v {_wsl_path(models)}:/models:ro {IMAGE} --config /app/config.yml --graph /graph "
            f"--mode route-details --from {FROM} --to {TO} "
            f"--fast-profile car_fast --scenic-profile car_scenic --models /models"
        )
        print(result.stdout[-6000:])
        yield result, parse(result.stdout)
    finally:
        shutil.rmtree(graph, ignore_errors=True)
        shutil.rmtree(models, ignore_errors=True)


def test_route_details_mode_exists_and_prints_both_routes(routed):
    result, routes = routed
    assert result.returncode == 0, (
        f"{IMAGE} --mode route-details exited {result.returncode}:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}"
    )
    assert [(r["profile"], r["model"]) for r in routes] == [("car_fast", "-"), ("car_scenic", "lambda-8.json")], (
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
