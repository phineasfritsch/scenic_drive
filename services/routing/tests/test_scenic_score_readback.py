"""The joint T-0031 never exercised: REAL tagwriter bytes -> GraphHopper's TagParser -> the built graph.

T-0031 imported synthetic `way_id % 11` tags, so "scenic_score survives the import" was true of a value no
scoring model had ever produced. This reads three NAMED OSM ways back out of a graph built from the real
canyon window (services/etl/work/la/window-tagged-1.osm.pbf, sha256 06046be0...0090, 12,402 ways, 11,740
scored) and compares the encoded value against what tagwriter actually wrote into that PBF.

The binding is way id -> score, not point -> score: config.yml carries GraphHopper's `osm_way_id` encoded
value and ScenicRouterMain - the shipping entry point, the same main() the import runs through - answers
`--mode probe --probe-ways <ids>` by walking every edge. A snapped short route would only prove "some edge
near this coordinate", which the neighbouring way satisfies just as well.

Expected values are typed literals read out of the tagged artifact's own osmium read-back
(services/etl/work/la/window-readback.osm.xml), never recomputed from the scorer:

    way 74344132  Topanga Canyon Boulevard, highway=primary  scenic_score=8   (4 ways in the window score 8)
    way 10715427  highway=track, scenic_gate=track           scenic_score=0   (gated, and still IMPORTED -
                  motorway/trunk/track are penalized or profile-gated, never dropped at import)
    way 4883641   natural=..., no highway tag, NO scenic_score  -> never reaches the routable graph at all

RED demonstration (T-0213 Log): with `way.getTag(KEY, "")` misspelled in a copy of ScenicScoreParser.java,
the encoded value exists and the import succeeds, but every way reads 0 - Topanga included - and
test_named_way_carries_its_real_scenic_score fails on the 8. SCENIC_ROUTING_IMAGE and SCENIC_ROUTING_GRAPH
point this same file at that red build; their defaults are what the green run uses.

Prerequisites (skipped without them, like test_lambda_monotone.py - docker lives inside WSL on this box):
  bash services/routing/import-graph.sh <the tagged pbf> services/routing/work/graph-la-window
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

IMAGE = os.environ.get("SCENIC_ROUTING_IMAGE", "scenic-routing:t0213")

ROUTING = Path(__file__).resolve().parents[1]
GRAPH = Path(os.environ.get("SCENIC_ROUTING_GRAPH", str(ROUTING / "work" / "graph-la-window")))

TOPANGA = 74344132
GATED_TRACK = 10715427
NOT_A_ROAD = 4883641

PROBE_WAYS = (TOPANGA, GATED_TRACK, NOT_A_ROAD)

PROBE_LINE = re.compile(
    r"^PROBE way=(?P<way>\d+) edges=(?P<edges>\d+) scenic_score=(?P<scores>\S+)$"
)


def _shell(command, timeout=1800):
    if shutil.which("wsl"):
        argv = ["wsl", "-e", "bash", "-lc", command]
    elif shutil.which("bash"):
        argv = ["bash", "-lc", command]
    else:
        pytest.skip("neither wsl nor bash on PATH, so there is no docker to reach")
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def _wsl_path(path):
    text = str(Path(path).resolve())
    if len(text) > 1 and text[1] == ":":
        return "/mnt/" + text[0].lower() + text[2:].replace("\\", "/")
    return text


@pytest.fixture(scope="module")
def probed():
    """{way id -> (edge count, [scenic_score, ...])} from one probe run over the imported window graph."""
    if not (GRAPH / "edges").exists():
        pytest.skip(
            f"no graph at {GRAPH}; build it with: bash services/routing/import-graph.sh "
            f"services/etl/work/la/window-tagged-1.osm.pbf services/routing/work/graph-la-window"
        )
    if _shell(f"docker image inspect --format ok {IMAGE}", timeout=120).returncode != 0:
        pytest.skip(f"docker image {IMAGE} is not built; see services/routing/README.md")
    ways = ",".join(str(way) for way in PROBE_WAYS)
    command = (
        f"docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx2g -v {_wsl_path(GRAPH)}:/graph {IMAGE} "
        f"--config /app/config.yml --graph /graph --mode probe --probe-ways {ways}"
    )
    result = _shell(command)
    assert result.returncode == 0, f"probe failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
    print(result.stdout)
    parsed = {}
    for line in result.stdout.splitlines():
        match = PROBE_LINE.match(line.strip())
        if match:
            scores = match.group("scores")
            parsed[int(match.group("way"))] = (
                int(match.group("edges")),
                [] if scores == "-" else [int(value) for value in scores.split(",")],
            )
    assert set(parsed) == set(PROBE_WAYS), f"probe answered {sorted(parsed)}, expected {sorted(PROBE_WAYS)}"
    assert "SCENIC_EV present=true" in result.stdout, (
        f"the graph at {GRAPH} carries no scenic_score encoded value:\n{result.stdout}"
    )
    return parsed


def test_named_way_carries_its_real_scenic_score(probed):
    """Topanga Canyon Boulevard scored 8 in the tagged PBF; the graph must say 8 on every edge of it.

    This is the assertion T-0031 could not make: its tags were way_id % 11, so any number read back was
    consistent with a parser that had never seen a real scoring model's output."""
    edges, scores = probed[TOPANGA]
    assert edges > 0, (
        f"way {TOPANGA} (Topanga Canyon Boulevard) produced no edge in the graph at {GRAPH} - the probe "
        f"cannot see a score for a way the import dropped"
    )
    assert scores == [8], (
        f"way {TOPANGA} carries scenic_score=8 in window-tagged-1.osm.pbf but the graph encoded {scores} "
        f"over its {edges} edge(s). A parser reading the wrong tag key encodes the no-tag default 0 here "
        f"while the import, the encoded value and every routed test stay green."
    )


def test_gated_way_is_imported_and_carries_zero(probed):
    """A gate is a PROFILE decision, never an import one: way 10715427 is scenic_gate=track, scored 0, and
    it must still be in the graph. CLAUDE.md's invariant lives on the same mechanism - motorway and trunk
    carry 0 and are penalized, and an edge that was never imported can never be penalized back in."""
    edges, scores = probed[GATED_TRACK]
    assert edges > 0, (
        f"gated way {GATED_TRACK} (highway=track, scenic_gate=track) is absent from the graph: gating is "
        f"the custom model's job, not the importer's"
    )
    assert scores == [0], f"gated way {GATED_TRACK} carries scenic_score=0 in the PBF, graph encoded {scores}"


def test_a_way_with_no_scenic_score_is_not_a_road_and_never_reaches_the_graph(probed):
    """Every one of the window's 11,740 scored ways is a road and every road is scored (refused=0 here), so
    the ruled no-tag default cannot be observed on a routable edge in this window. What IS observable: the
    662 unscored ways are not-a-road (way 4883641 is `natural`, nothing else - T-0168 leaves those untouched)
    and the importer never gives them an edge. The no-tag default itself (0, ScenicScoreParser.parse) is
    demonstrated by the RED run in T-0213's Log, where the misspelled key makes every way take it."""
    edges, scores = probed[NOT_A_ROAD]
    assert (edges, scores) == (0, []), (
        f"way {NOT_A_ROAD} has no highway tag and no scenic_score, yet the graph has {edges} edge(s) for it "
        f"carrying {scores}"
    )
