"""The joint T-0031 never exercised: REAL tagwriter bytes -> GraphHopper's TagParser -> the built graph.

T-0031 imported synthetic `way_id % 11` tags, so "scenic_score survives the import" was true of a value no
scoring model had ever produced. This file IMPORTS the real canyon window
(services/etl/work/la/window-tagged-1.osm.pbf, sha256 06046be0...0090, 12,402 ways, 11,740 scored) with the
image under test into a fresh temp graph directory, and only then reads NAMED OSM ways back out of it. The
import is part of the test: a pre-built graph directory proves nothing about the image being tested - the
author's own misspelled-key image passes every assertion when it is only allowed to probe someone else's
graph (T-0213 Log, S1).

The binding is way id -> score, not point -> score: config.yml carries GraphHopper's `osm_way_id` encoded
value and ScenicRouterMain - the shipping entry point, the same main() the import runs through - answers
`--mode probe --probe-ways <ids>` by walking every edge. A snapped short route would only prove "some edge
near this coordinate", which the neighbouring way satisfies just as well.

Every expected value below is a typed literal read out of the tagged artifact's own osmium read-back
(services/etl/work/la/window-readback.osm.xml), never recomputed from the scorer. One named, routable way
per score 1..8, so that a parser which merely maps 0->0 and 8->8 (the shape the old two-point probe could
not tell from the real one) fails: the interior of the range is pinned way by way.

RED demonstration (T-0213 Log, S1): with `way.getTag(KEY, "")` misspelled in a COPY of ScenicScoreParser.java
(services/routing/work/red-build.sh), the encoded value still exists and the import still succeeds, but every
way reads 0 - and eight of these tests fail. SCENIC_ROUTING_IMAGE points this same file at that red build.

Prerequisites (skipped without them, like test_lambda_monotone.py - docker lives inside WSL on this box):
docker with the image built (`docker build -t scenic-routing:t0213 services/routing`) and the read-only
input PBF in the main checkout. The import itself takes about a minute and runs once per session.
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

IMAGE = os.environ.get("SCENIC_ROUTING_IMAGE", "scenic-routing:t0213")

ROUTING = Path(__file__).resolve().parents[1]
REPO = ROUTING.parents[1]
PBF_SHA256 = "06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090"
PBF_RELATIVE = "services/etl/work/la/window-tagged-1.osm.pbf"

# score -> (way id, the road's name in the read-back). One named way per score, ids and scores typed from
# services/etl/work/la/window-readback.osm.xml (histogram 1:758 2:1677 3:1397 4:926 5:693 6:245 7:65 8:4).
SCORED_WAYS = (
    (1, 1073769540, "Civic Center Way"),
    (2, 13452810, "Malibu Road"),
    (3, 13418694, "Rambla Vista"),
    (4, 13295089, "Encinal Canyon Road"),
    (5, 149210418, "Corral Canyon Road"),
    (6, 246767080, "Mulholland Highway"),
    (7, 221164472, "Latigo Canyon Road"),
    (8, 74344132, "Topanga Canyon Boulevard"),
)
GATED_TRACK = 10715427  # highway=track, scenic_gate=track, scenic_score=0 - gated by the PROFILE, imported
NOT_A_ROAD = 4883641  # natural=..., no highway tag, no scenic_score - never a routable edge

PROBE_WAYS = tuple(way for _, way, _ in SCORED_WAYS) + (GATED_TRACK, NOT_A_ROAD)


def _pbf():
    """The read-only input, wherever this checkout can see it (worktrees do not carry gitignored work/)."""
    override = os.environ.get("SCENIC_ROUTING_PBF")
    if override:
        return Path(override)
    for root in (REPO, REPO.parents[1] if len(REPO.parents) > 1 else REPO):
        candidate = root / PBF_RELATIVE
        if candidate.exists():
            return candidate
    return REPO / PBF_RELATIVE


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


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_probe(stdout):
    """PROBE way=<id> edges=<n> scenic_score=<csv|-> -> {way id: (edges, [scores])}."""
    parsed = {}
    for line in stdout.splitlines():
        fields = line.strip().split()
        if len(fields) != 4 or fields[0] != "PROBE":
            continue
        way = int(fields[1].split("=", 1)[1])
        edges = int(fields[2].split("=", 1)[1])
        scores = fields[3].split("=", 1)[1]
        parsed[way] = (edges, [] if scores == "-" else [int(value) for value in scores.split(",")])
    return parsed


@pytest.fixture(scope="session")
def probed():
    """Import the real PBF with the image under test, then probe it. {way id -> (edges, [scores])}.

    The import is the point: it binds these assertions to IMAGE. Probing a graph someone else built binds
    them to nothing."""
    pbf = _pbf()
    if not pbf.exists():
        pytest.skip(f"the read-only input {PBF_RELATIVE} is not in this checkout (looked at {pbf})")
    actual = _sha256(pbf)
    assert actual == PBF_SHA256, (
        f"{pbf} is sha256 {actual}, not the artifact these literals were read out of ({PBF_SHA256}); every "
        f"expected score below comes from window-readback.osm.xml, which describes THAT file"
    )
    if _shell(f"docker image inspect --format ok {IMAGE}", timeout=180).returncode != 0:
        pytest.skip(f"docker image {IMAGE} is not built; see services/routing/README.md")

    work = ROUTING / "work"
    work.mkdir(parents=True, exist_ok=True)
    graph = Path(tempfile.mkdtemp(prefix="graph-readback-", dir=str(work)))
    try:
        imported = _shell(
            f"bash {_wsl_path(ROUTING / 'import-graph.sh')} {_wsl_path(pbf)} {_wsl_path(graph)} {IMAGE}"
        )
        print(imported.stdout[-4000:])
        assert imported.returncode == 0, (
            f"import of {pbf.name} with {IMAGE} failed ({imported.returncode}):\n"
            f"{imported.stdout[-4000:]}\n{imported.stderr[-4000:]}"
        )
        assert "SCENIC_EV present=true" in imported.stdout, (
            f"the graph just imported with {IMAGE} carries no scenic_score encoded value:\n{imported.stdout}"
        )
        ways = ",".join(str(way) for way in PROBE_WAYS)
        result = _shell(
            f"docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx2g -v {_wsl_path(graph)}:/graph {IMAGE} "
            f"--config /app/config.yml --graph /graph --mode probe --probe-ways {ways}"
        )
        assert result.returncode == 0, f"probe failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
        print(result.stdout)
        parsed = _parse_probe(result.stdout)
        assert set(parsed) == set(PROBE_WAYS), (
            f"probe answered {sorted(parsed)}, expected {sorted(PROBE_WAYS)}"
        )
        yield parsed
    finally:
        shutil.rmtree(graph, ignore_errors=True)


@pytest.mark.parametrize("score,way,name", SCORED_WAYS, ids=[f"score{s}" for s, _, _ in SCORED_WAYS])
def test_named_way_carries_its_real_scenic_score(probed, score, way, name):
    """Each score 1..8 is pinned on a way that actually carries it in the tagged PBF.

    This is the assertion T-0031 could not make (its tags were way_id % 11) and the one two probe points
    could not make either: with only 0 and the window's maximum 8 probed, any parser with f(0)=0 and f(8)=8
    - `value >= 5 ? 8 : 0`, say - reads back green."""
    edges, scores = probed[way]
    assert edges > 0, (
        f"way {way} ({name}) produced no edge in the graph just imported with {IMAGE} - the probe cannot "
        f"see a score for a way the import dropped"
    )
    assert scores == [score], (
        f"way {way} ({name}) carries scenic_score={score} in {PBF_RELATIVE} but the graph imported with "
        f"{IMAGE} encoded {scores} over its {edges} edge(s)"
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
    and the importer never gives them an edge. The no-tag default itself (0) is pinned by
    ScenicScoreParserTest.java, which runs inside the image build."""
    edges, scores = probed[NOT_A_ROAD]
    assert (edges, scores) == (0, []), (
        f"way {NOT_A_ROAD} has no highway tag and no scenic_score, yet the graph has {edges} edge(s) for it "
        f"carrying {scores}"
    )
