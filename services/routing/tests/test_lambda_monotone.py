"""T(lambda) is non-decreasing over {0, 1, 2, 4, 8} - the property the whole budget search rests on.

The plan's property table (line 215) reads "`T(lambda)` non-decreasing over {0,1,2,4,8} on every fixture".
Problem A bisects on lambda for `T(lambda) ~ T_fast + B`; a bisection on a non-monotone function returns a
number that means nothing, so this is checked the moment a graph exists rather than after the search is built.

One fixed Vermont pair, five per-request custom models, one loaded graph. The expected values are not
computed from anything the router says: the lambdas and the band multipliers are typed literals in
profiles/scenic_lambda_bands.json, the assertion is an order property, and the one equality is against the
car_fast baseline (lambda=0 must be the fastest route - that is what makes the bisection always feasible).

Prerequisites, all built by `bash services/routing/build-slice.sh` in WSL; the routed tests SKIP without them
because docker exists only inside WSL on this box. test_band_multipliers_match_the_plan needs neither.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

LAMBDAS = (0, 1, 2, 4, 8)

# How much more lambda=8 must cost than lambda=0 for the penalty to count as biting. See
# test_lambda_penalty_bites for how the number is ruled.
BITE_FLOOR = 0.05

# Typed literals, both in Vermont: Burlington City Hall Park to downtown Rutland, about 100 km apart on the
# Vermont extract, with US 7 and the quieter roads on either side of it available between them.
FROM_POINT = "44.4759,-73.2121"
TO_POINT = "43.6106,-72.9726"

IMAGE = "scenic-routing:t0213"
REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTING = REPO_ROOT / "services" / "routing"
WORK = ROUTING / "work"
GRAPH = WORK / "graph-cache"
MODELS = WORK / "models"
TEMPLATE = ROUTING / "profiles" / "car_scenic_request.json"
BANDS = ROUTING / "profiles" / "scenic_lambda_bands.json"

ROUTE_LINE = re.compile(
    r"^ROUTE profile=(?P<profile>\S+) model=(?P<model>\S+) time_ms=(?P<time_ms>\d+) distance_m=(?P<distance_m>[0-9.]+)$"
)


def _shell(command, timeout=1800):
    """Run a shell command where docker lives: inside WSL on the Windows box, directly on Linux."""
    if shutil.which("wsl"):
        argv = ["wsl", "-e", "bash", "-lc", command]
    elif shutil.which("bash"):
        argv = ["bash", "-lc", command]
    else:
        pytest.skip("neither wsl nor bash on PATH, so there is no docker to reach")
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def _wsl_path(path):
    """C:\\Users\\x -> /mnt/c/Users/x, which is the only spelling docker inside WSL understands."""
    text = str(Path(path).resolve())
    if len(text) > 1 and text[1] == ":":
        return "/mnt/" + text[0].lower() + text[2:].replace("\\", "/")
    return text


def _write_request_models():
    """Substitute each lambda's band multipliers into the shipped per-request model. Both files are committed
    profiles, so the red demonstration edits data and never this test."""
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
        assert "${" not in model, f"unsubstituted placeholder left in the model for lambda={value}"
        json.loads(model)  # a malformed model must fail here, not a minute later inside the container
        (MODELS / f"lambda-{value}.json").write_text(model, encoding="utf-8")


def test_band_multipliers_match_the_plan():
    """The table is the plan's three bands (:105-107), the same numbers services/api/src/customModel.ts
    computes: high 1, mid 1/(1+0.5*lambda), low 1/(1+lambda), six decimals, trailing zeros dropped.
    GraphHopper's expression compiler refuses '/' inside multiply_by, so the arithmetic cannot live in the
    profile and the numbers are typed out here instead."""
    bands = json.loads(BANDS.read_text(encoding="utf-8"))
    assert sorted(int(key) for key in bands) == sorted(LAMBDAS)
    for value in LAMBDAS:
        band = bands[str(value)]
        assert band["high"] == "1", f"lambda={value}: the scenic_score >= 7 band is never penalized"
        assert float(band["mid"]) == pytest.approx(1 / (1 + 0.5 * value), abs=5e-7), f"mid band at lambda={value}"
        assert float(band["low"]) == pytest.approx(1 / (1 + value), abs=5e-7), f"low band at lambda={value}"


@pytest.fixture(scope="module")
def routes():
    """{model name -> (time_ms, distance_m)} from one container run over the imported Vermont graph."""
    if not (GRAPH / "edges").exists():
        pytest.skip(f"no graph at {GRAPH}; build it with: bash services/routing/build-slice.sh")
    if _shell(f"docker image inspect --format ok {IMAGE}", timeout=120).returncode != 0:
        pytest.skip(f"docker image {IMAGE} is not built; build it with: bash services/routing/build-slice.sh")
    _write_request_models()
    command = (
        f"docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx4g "
        f"-v {_wsl_path(GRAPH)}:/graph -v {_wsl_path(MODELS)}:/models:ro {IMAGE} "
        f"--config /app/config.yml --graph /graph --mode route "
        f"--from {FROM_POINT} --to {TO_POINT} "
        f"--fast-profile car_fast --scenic-profile car_scenic --models /models"
    )
    result = _shell(command)
    assert result.returncode == 0, f"router run failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
    parsed = {}
    for line in result.stdout.splitlines():
        match = ROUTE_LINE.match(line.strip())
        if match:
            parsed[match.group("model")] = (int(match.group("time_ms")), float(match.group("distance_m")))
    expected = {"-"} | {f"lambda-{value}.json" for value in LAMBDAS}
    assert set(parsed) == expected, f"router answered {sorted(parsed)}, expected {sorted(expected)}"
    return parsed


def test_lambda_monotone_non_decreasing(routes):
    durations = [routes[f"lambda-{value}.json"][0] for value in LAMBDAS]
    print("T(lambda) ms: " + ", ".join(f"lambda={v}: {t}" for v, t in zip(LAMBDAS, durations)))
    for index in range(len(LAMBDAS) - 1):
        low, high = LAMBDAS[index], LAMBDAS[index + 1]
        assert durations[index + 1] >= durations[index], (
            f"T(lambda) DECREASED at step lambda={low} -> lambda={high}: "
            f"{durations[index]} ms -> {durations[index + 1]} ms"
        )


def test_lambda_penalty_bites(routes):
    """Non-decreasing is true of a CONSTANT, and lambda=0 == car_fast is trivially true when every lambda is
    the car_fast route, so both assertions above survive a per-request model that does nothing at all - drop
    the first band's threshold to `scenic_score >= 0` and every edge lands in the never-penalized `high`
    band. This asserts the model bites: lambda=8 costs strictly more than lambda=0 by a stated margin, and at
    least one step of the five strictly rises.

    The margin is ruled from the five measured durations on this fixture (5945246 -> 8491177 ms, +43%): a 5%
    floor is an order of magnitude below what the model delivers, and the router is deterministic over a
    fixed graph, so it leaves room for another region's numbers without leaving room for a dead model."""
    durations = [routes[f"lambda-{value}.json"][0] for value in LAMBDAS]
    at_zero, at_eight = durations[0], durations[-1]
    floor = at_zero * (1 + BITE_FLOOR)
    assert at_eight > floor, (
        f"the scenic penalty does not BITE: lambda=8 is {at_eight} ms against lambda=0 at {at_zero} ms, "
        f"short of the +{BITE_FLOOR:.0%} ({floor:.0f} ms) this asserts. A per-request model that matches "
        f"every edge at multiplier 1 gives a constant T(lambda) and passes every other check in this file."
    )
    rising = [
        (LAMBDAS[index], LAMBDAS[index + 1])
        for index in range(len(LAMBDAS) - 1)
        if durations[index + 1] > durations[index]
    ]
    assert rising, (
        f"no step of T(lambda) over {list(LAMBDAS)} strictly increased: {durations} ms - the per-request "
        f"model moves the route at no lambda between 0 and 8"
    )


def test_lambda_zero_is_the_car_fast_route(routes):
    fast_ms, fast_m = routes["-"]
    zero_ms, zero_m = routes["lambda-0.json"]
    print(f"car_fast: {fast_ms} ms / {fast_m} m   lambda=0: {zero_ms} ms / {zero_m} m")
    assert zero_ms == fast_ms, (
        f"lambda=0 must be the car_fast route - the bisection's feasibility end - "
        f"but car_fast is {fast_ms} ms and lambda=0 is {zero_ms} ms"
    )
