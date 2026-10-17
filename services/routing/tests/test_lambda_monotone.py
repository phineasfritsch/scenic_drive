"""T(lambda) is non-decreasing over {0, 1, 2, 4, 8} - the property the whole budget search rests on.

The plan's property table (line 215) reads "`T(lambda)` non-decreasing over {0,1,2,4,8} on every fixture".
Problem A bisects on lambda for `T(lambda) ~ T_fast + B`; a bisection on a non-monotone function returns a
number that means nothing, so this is checked the moment a graph exists rather than after the search is built.

One fixed Vermont pair, five per-request custom models, one loaded graph. The models are the Worker's own
bytes: Tests/Fixtures/custom-model/lambda-<l>.json, held byte-equal to services/api/src/customModel.ts's
buildCustomModel by services/api/test/customModelGolden.test.ts (T-0190) and copied here unchanged by
request_models.py. The assertion is an order property, and the one equality is against the car_fast baseline
(lambda=0 must be the fastest route - that is what makes the bisection always feasible).

Prerequisites, all built by `bash services/routing/build-slice.sh` in WSL; the routed tests SKIP without them
because docker exists only inside WSL on this box.
"""

import math
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from request_models import ORACLE_LAMBDAS, write_models

LAMBDAS = ORACLE_LAMBDAS

# How much more lambda=8 must cost than lambda=0 for the penalty to count as biting. See
# test_lambda_penalty_bites for how the number is ruled.
BITE_FLOOR = 0.18

# T(lambda) in ms over LAMBDAS on this pair, as the router returns it with the recorded models (T-0386 stage 1).
# The router is deterministic over a fixed graph, image and model bytes: test_lambda_durations_are_the_measured_record
# holds every routed run to it, and test_bite_floor_is_ruled_from_the_measured_record derives BITE_FLOOR from it.
MEASURED_T_MS = (5945246, 6015807, 6785536, 7510022, 8122353)

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


@pytest.fixture(scope="module")
def routes():
    """{model name -> (time_ms, distance_m)} from one container run over the imported Vermont graph."""
    if not (GRAPH / "edges").exists():
        pytest.skip(f"no graph at {GRAPH}; build it with: bash services/routing/build-slice.sh")
    if _shell(f"docker image inspect --format ok {IMAGE}", timeout=120).returncode != 0:
        pytest.skip(f"docker image {IMAGE} is not built; build it with: bash services/routing/build-slice.sh")
    write_models(MODELS, LAMBDAS)
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

    The margin is ruled from the five durations measured on this fixture with the Worker's nine-clause models
    (T-0386 Log, 2026-10-17: 5945246, 6015807, 6785536, 7510022, 8122353 ms; lambda=8 is +36.62 %). The router is
    deterministic over a fixed graph and fixed model bytes, so the floor is half the measured bite, rounded down:
    18 %. It refuses a model whose penalty saturates early - lambda-2's model routed at lambda 4 and 8 is +14.13 %
    and passed the old 5 % floor - and leaves the real model 2x headroom."""
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


def test_lambda_durations_are_the_measured_record(routes):
    """Full equality: every routed T(lambda) is the measured one. A model written under the wrong label, a record
    re-recorded without re-measuring, or a changed image moves at least one duration off MEASURED_T_MS."""
    durations = tuple(routes[f"lambda-{value}.json"][0] for value in LAMBDAS)
    assert durations == MEASURED_T_MS, (
        f"T(lambda) over {list(LAMBDAS)} is {durations} ms, not the measured {MEASURED_T_MS}: re-measure and "
        f"re-rule BITE_FLOOR before changing either"
    )


def test_bite_floor_is_ruled_from_the_measured_record():
    """Docker-free. R3: BITE_FLOOR is half the measured lambda-8 bite, rounded down to two places - and so it sits
    above the bite of the penalty saturating at lambda 2 (lambda-2's T at the lambda-8 label), the mutant the old 5 %
    floor passed. A floor typed lower than the rule re-opens that gap; this fails it without a graph."""
    bite = MEASURED_T_MS[-1] / MEASURED_T_MS[0] - 1
    ruled = math.floor(bite * 100 / 2) / 100
    saturated = MEASURED_T_MS[LAMBDAS.index(2)] / MEASURED_T_MS[0] - 1
    assert BITE_FLOOR == ruled, (
        f"BITE_FLOOR {BITE_FLOOR} is not half the measured bite {bite:.4%} rounded down: {ruled}"
    )
    assert saturated < BITE_FLOOR < bite, (
        f"BITE_FLOOR {BITE_FLOOR} does not sit between the lambda-2 saturation bite {saturated:.4%} and the "
        f"measured bite {bite:.4%}"
    )
