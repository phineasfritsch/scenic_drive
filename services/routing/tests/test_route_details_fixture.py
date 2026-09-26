"""rv1-t0209 B1 and B2, rv2-t0209 B1-r2: the EDGE rows against an oracle that is not the path details, and an
unknown --mode.

test_route_details.py checks the EDGE rows against the path details they were printed from, so a printer that
aligns road_class and osm_way_id to the NEIGHBOURING edge (rv1's MA: `getLast() < point` for `<= point` in
RouteDetailsPrinter.covering) moves both together and passes every one of its tests. Here the oracle is typed by
hand: tests/fixtures/two-ways.osm has way A (900001, secondary) split into two edges by a spur at its middle node,
way B (900002, tertiary) as one edge, and way C (900004, tertiary - B's class) as one edge continuing from B's
last node, each edge with a pillar node. A's first node to C's last node has exactly one simple path, so every
route prints A, A, B, C - and each way's EDGE metres are that way's own length, measured here from the file's
coordinates, never from a route. B and C share one road_class interval, so a printer that reads the way id
through the road_class cursor (rv2's MC: `ways.get(classIndex)` for `ways.get(wayIndex)`) prints B on C's row.

The rest of the file is a 15 x 15 residential lattice reached only through the spur: GraphHopper 11 marks every
component under prepare.min_network_size (200, which config.yml does not override) as a subnetwork nothing
snaps to, and the config under test is the config that ships (T-0209 Log, ruling on rv1 B1/B2).

The graph is imported by the image under test into a fresh temp directory, and every run goes through the
image's ENTRYPOINT main(). RED (T-0209 Log): MA, MB and MC, built through the shipping Dockerfile.
"""

import math
import os
import shutil
import tempfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest

from test_route_details import MODELS, _lambda_model
from test_scenic_score_readback import _shell, _wsl_path
from tools.route_details import parse

IMAGE = os.environ.get("SCENIC_ROUTING_IMAGE", "scenic-routing:t0209")
ROUTING = Path(__file__).resolve().parents[1]
FIXTURE = ROUTING / "tests" / "fixtures" / "two-ways.osm"
WAY_A = 900001
WAY_B = 900002
WAY_C = 900004
# The edges of the one path from A's first node to C's last, in order - typed, not read from any output.
EXPECTED_WAYS = [WAY_A, WAY_A, WAY_B, WAY_C]
EARTH_RADIUS_M = 6371000.0  # GraphHopper's DistanceCalcEarth.R


def _fixture_ways():
    """{way id: ([(lat, lon), ...], highway)} straight from the OSM XML."""
    root = ElementTree.parse(FIXTURE).getroot()
    nodes = {int(node.get("id")): (float(node.get("lat")), float(node.get("lon"))) for node in root.iter("node")}
    ways = {}
    for way in root.iter("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.iter("tag")}
        ways[int(way.get("id"))] = ([nodes[int(nd.get("ref"))] for nd in way.iter("nd")], tags["highway"])
    return ways


def _haversine(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def _length(points):
    return sum(_haversine(a, b) for a, b in zip(points, points[1:]))


def _point(lat_lon):
    return f"{lat_lon[0]:.7f},{lat_lon[1]:.7f}"


@pytest.fixture(scope="module")
def fixture_graph():
    """A runner for any --mode over the fixture graph the image under test imported itself."""
    if _shell(f"docker image inspect --format ok {IMAGE}", timeout=180).returncode != 0:
        pytest.skip(f"docker image {IMAGE} is not built; see services/routing/README.md")
    work = ROUTING / "work"
    work.mkdir(parents=True, exist_ok=True)
    graph = Path(tempfile.mkdtemp(prefix="graph-two-ways-", dir=str(work)))
    models = Path(tempfile.mkdtemp(prefix="models-two-ways-", dir=str(work)))
    try:
        for value in (0, 8):
            _lambda_model(models, value)
        imported = _shell(
            f"bash {_wsl_path(ROUTING / 'import-graph.sh')} {_wsl_path(FIXTURE)} {_wsl_path(graph)} {IMAGE}"
        )
        assert imported.returncode == 0, f"import with {IMAGE} failed:\n{imported.stdout[-3000:]}\n{imported.stderr[-3000:]}"
        ways = _fixture_ways()

        def run(mode):
            return _shell(
                f"docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx1g -v {_wsl_path(graph)}:/graph "
                f"-v {_wsl_path(models)}:/models:ro {IMAGE} --config /app/config.yml --graph /graph "
                f"--mode {mode} --from {_point(ways[WAY_A][0][0])} --to {_point(ways[WAY_C][0][-1])} "
                f"--fast-profile car_fast --scenic-profile car_scenic --models /models"
            )

        yield run
    finally:
        shutil.rmtree(graph, ignore_errors=True)
        shutil.rmtree(models, ignore_errors=True)


@pytest.fixture(scope="module")
def routed(fixture_graph):
    result = fixture_graph("route-details")
    print("\n".join(line for line in result.stdout.splitlines() if line.startswith(("ROUTE", "EDGE"))))
    assert result.returncode == 0, (
        f"{IMAGE} --mode route-details exited {result.returncode}:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}"
    )
    routes = parse(result.stdout)
    assert [(r["profile"], r["model"]) for r in routes] == [("car_fast", "-")] + [("car_scenic", m) for m in MODELS], (
        f"{IMAGE} printed routes {[(r['profile'], r['model']) for r in routes]}"
    )
    return routes


def test_the_fixture_is_the_oracle_this_file_types():
    """A and B are distinct classes, B and C one class, and each way starts where the one before it ends, so a row
    credited to the wrong way shows - across a class boundary (MA) and inside one class interval (MC)."""
    ways = _fixture_ways()
    assert (ways[WAY_A][1], ways[WAY_B][1], ways[WAY_C][1]) == ("secondary", "tertiary", "tertiary")
    assert ways[WAY_A][0][-1] == ways[WAY_B][0][0], "B must start where A ends"
    assert ways[WAY_B][0][-1] == ways[WAY_C][0][0], "C must start where B ends"
    assert len(ways[WAY_A][0]) == 5 and len(ways[WAY_B][0]) == 3 and len(ways[WAY_C][0]) == 3, (
        "A is two edges with pillars, B and C one edge with one each"
    )


def test_edge_rows_name_the_way_and_class_of_each_fixture_edge_in_order(routed):
    ways = _fixture_ways()
    expected = [(way, ways[way][1]) for way in EXPECTED_WAYS]
    for route in routed:
        printed = [(edge["way"], edge["road_class"]) for edge in route["edges"]]
        assert printed == expected, (
            f"model={route['model']}: EDGE rows {printed}, the fixture's one path is {expected} - a row carries "
            f"a neighbouring edge's osm_way_id / road_class"
        )


def test_each_fixture_way_prints_its_own_length_in_metres(routed):
    ways = _fixture_ways()
    for route in routed:
        for way in (WAY_A, WAY_B, WAY_C):
            printed = sum(edge["m"] for edge in route["edges"] if edge["way"] == way)
            own = _length(ways[way][0])
            assert abs(printed - own) <= 0.5, (
                f"model={route['model']}: way {way}'s EDGE rows sum to {printed:.3f} m, its own length is "
                f"{own:.3f} m - its rows carry another way's metres, or miss its own"
            )


def test_an_unknown_mode_exits_non_zero_and_names_the_mode(fixture_graph):
    """T-0224's `--mode details` exited 0 printing nothing, which read as a route with no rows (rv1 B2)."""
    result = fixture_graph("details")
    assert result.returncode != 0, f"{IMAGE} --mode details exited 0:\n{result.stdout[-2000:]}"
    assert "unknown --mode details" in result.stderr, f"{IMAGE} --mode details stderr:\n{result.stderr[-2000:]}"
    assert not [line for line in result.stdout.splitlines() if line.startswith(("ROUTE", "EDGE"))]
