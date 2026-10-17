"""The per-request custom models the routing oracle sends: the Worker's own bytes, never a template.

T-0190. Tests/Fixtures/custom-model/lambda-<l>.json is the ONE record of what services/api/src/customModel.ts's
buildCustomModel(l, null) sends. services/api/test/customModelGolden.test.ts holds every file byte-equal to the
shipped builder (ops/test runs it in CI), and the Swift port is held to the same bytes. This module hands those
bytes to GraphHopper unchanged: no placeholder, no substitution, no second copy of a band table, so a clause the
Worker adds, drops or re-weights reaches the routed tests the moment the record is re-recorded - and the vitest
refuses a record that is not re-recorded.
"""

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RECORD = REPO_ROOT / "Tests" / "Fixtures" / "custom-model"

# The plan's oracle lambdas (property table: T(lambda) non-decreasing over {0,1,2,4,8}).
ORACLE_LAMBDAS = (0, 1, 2, 4, 8)


def recorded(value):
    """The recorded model file for one lambda; a lambda nobody recorded is an error, never a fallback."""
    path = RECORD / f"lambda-{value}.json"
    assert path.is_file(), f"no recorded Worker model for lambda={value} at {path}"
    return path


def write_models(directory, lambdas=ORACLE_LAMBDAS):
    """Copy the recorded models for `lambdas` into a fresh `directory` as lambda-<l>.json, bytes unchanged."""
    directory = Path(directory)
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    for value in lambdas:
        (directory / f"lambda-{value}.json").write_bytes(recorded(value).read_bytes())
    return directory
