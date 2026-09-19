"""ops/deploy-routing, exercised: three refusals by their text, the atomic flip, and N-1 retention.

T-0213's Log rehearsed this script by hand and never bound the rehearsal to anything a later change would
have to keep true (CLAUDE.md: a check that has never been seen red is untested, and a script with no test is
not a check at all). deploy_rehearsal_driver.sh does what that hand rehearsal did - a throwaway git
repository under mktemp, a fake built graph, a local directory standing in for the box - and this file makes
the assertions over its transcript.

It runs through WSL because the flip is a real symbolic link plus `mv -T`, and the Windows checkout cannot
create a symbolic link at all (`ln: failed to create symbolic link: Operation not permitted`), so rehearsing
the flip in git-bash would rehearse nothing. On a box with no WSL this FAILS BY NAME rather than skipping
into a green run; SCENIC_DEPLOY_REHEARSAL_SKIP=1 is the explicit opt-out and says so in its reason.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROUTING = Path(__file__).resolve().parents[1]
REPO = ROUTING.parents[1]
DEPLOY = REPO / "ops" / "deploy-routing"
DRIVER = ROUTING / "tests" / "deploy_rehearsal_driver.sh"

KEEP = 2  # ops/deploy-routing's KEEP: N-1 means the previous release is always there to flip back to
RELEASE = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{7}$")


def _wsl_path(path):
    text = str(Path(path).resolve())
    if len(text) > 1 and text[1] == ":":
        return "/mnt/" + text[0].lower() + text[2:].replace("\\", "/")
    return text


@pytest.fixture(scope="session")
def transcript():
    """One driver run: the refusals, three rehearsed deploys, and what the box directory looks like after."""
    if os.environ.get("SCENIC_DEPLOY_REHEARSAL_SKIP"):
        pytest.skip(
            "SCENIC_DEPLOY_REHEARSAL_SKIP is set: ops/deploy-routing's flip is a real symlink plus mv -T, "
            "so this test needs a POSIX filesystem (WSL on the Windows dev box) - it is NOT being checked here"
        )
    assert DEPLOY.exists(), f"ops/deploy-routing is missing at {DEPLOY}"
    assert shutil.which("wsl") or os.name != "nt", (
        "ops/deploy-routing's atomic flip cannot be rehearsed without a POSIX filesystem and there is no "
        "wsl on PATH. This test refuses to pass silently: install WSL, run it on Linux, or set "
        "SCENIC_DEPLOY_REHEARSAL_SKIP=1 to record deliberately that the deploy script is unchecked here."
    )
    command = f"bash {_wsl_path(DRIVER)} {_wsl_path(DEPLOY)}"
    argv = ["wsl", "-e", "bash", "-lc", command] if shutil.which("wsl") else ["bash", "-lc", command]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=900)
    print(result.stdout)
    assert result.returncode == 0, f"the driver failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
    assert "=== driver done ===" in result.stdout, f"the driver did not finish:\n{result.stdout}"
    return result.stdout


def _section(transcript, heading):
    """The lines between `=== heading ===` and the next `=== ... ===`."""
    lines = transcript.splitlines()
    start = lines.index(f"=== {heading} ===") + 1
    for index in range(start, len(lines)):
        if lines[index].startswith("=== "):
            return lines[start:index]
    return lines[start:]


def test_refuses_a_directory_that_is_not_a_built_graph(transcript):
    section = _section(transcript, "refusal 1: not a built graph")
    assert any("DEPLOY-ROUTING REFUSED" in line and "is not a built graph" in line for line in section), section
    assert "exit=1" in section


def test_refuses_without_credentials_and_names_all_four(transcript):
    """The refusal has to say WHICH variables are missing: 'set the credentials' sends nobody anywhere."""
    section = _section(transcript, "refusal 2: credentials missing (HEAD is on origin)")
    refusal = [line for line in section if "DEPLOY-ROUTING REFUSED" in line]
    assert refusal, section
    for name in ("SCENIC_ROUTING_HOST", "SCENIC_ROUTING_USER", "SCENIC_ROUTING_KEY", "SCENIC_ROUTING_ROOT"):
        assert name in refusal[0], f"the credentials refusal does not name {name}: {refusal[0]}"
    assert "exit=1" in section


def test_refuses_when_head_is_not_on_origin(transcript):
    """A deploy of unpushed code has no version anyone else can check out."""
    section = _section(transcript, "refusal 3: HEAD not on origin")
    assert any("is not on origin - push first" in line for line in section), section
    assert "exit=1" in section


def test_a_rehearsed_deploy_uploads_restarts_and_reports_what_is_live(transcript):
    section = _section(transcript, "rehearsed deploy 1")
    assert any(line.startswith("DEPLOY-ROUTING OK sha=") for line in section), section
    assert "[stub] systemctl restart scenic-routing" in section, "the restart step did not run"
    assert "exit=0" in section, section


def test_the_flip_is_a_symlink_that_points_at_the_newest_release(transcript):
    """`current` is a symbolic link (the flip is ln -sfn beside + mv -T over, atomic on one filesystem), and
    after three deploys it points at the third release, with the uploaded graph reachable through it."""
    assert _section(transcript, "current is a symlink") == ["SYMLINK yes"]
    current = _section(transcript, "current resolves to")[0]
    assert RELEASE.match(current), f"'{current}' is not a <utc>-<sha7> release directory"
    releases = sorted(_section(transcript, "releases on disk"))
    assert current == releases[-1], f"current is {current} but the newest release is {releases[-1]}"
    assert sorted(_section(transcript, "the graph under current")) == ["edges", "nodes"], (
        "the graph did not arrive under current/graph"
    )


def test_three_deploys_keep_exactly_the_two_newest_releases(transcript):
    """N-1: the oldest of three is pruned and the previous one stays on disk to flip back to."""
    first = [line for line in _section(transcript, "rehearsed deploy 1") if line.startswith("DEPLOY-ROUTING OK")]
    oldest = first[0].rsplit("/", 1)[-1]
    releases = sorted(_section(transcript, "releases on disk"))
    assert len(releases) == KEEP, f"after three deploys {len(releases)} releases are on disk, not {KEEP}: {releases}"
    assert oldest not in releases, f"the oldest release {oldest} was not pruned: {releases}"
