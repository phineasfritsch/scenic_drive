"""`ops/publish-tiles` refuses without the human's credentials, and that refusal comes FIRST.

T-0165 demonstrated this by pasting three runs into a task file. Prose in a Log is not a check: the day
somebody moves the credential gate below the artifact or lock gates, a run with no credentials reaches
code that resolves paths, reads a sidecar and shells out to docker before it refuses - and the refusal a
human sees stops naming the thing they can fix. This runs the script bare and reads the FIRST line.

Nothing here can publish: the script is invoked with the four variables stripped out of the environment,
so the only branch reachable is the refusal.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ops" / "publish-tiles"
CREDENTIALS = ("CLOUDFLARE_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")


def run_publish(**credentials: str) -> subprocess.CompletedProcess:
    """The script, bare, with every credential variable removed unless this call names it."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.fail("no bash on PATH: ops/publish-tiles cannot be exercised, so it is not verified")
    env = {k: v for k, v in os.environ.items() if k not in CREDENTIALS}
    env.update(credentials)
    return subprocess.run([bash, str(SCRIPT)], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=180)


def first_line(completed: subprocess.CompletedProcess) -> str:
    out = (completed.stdout or "").strip()
    assert out, f"no output at all; stderr={completed.stderr!r}"
    return out.splitlines()[0].strip()


def test_the_credential_refusal_is_the_first_thing_a_bare_run_says() -> None:
    completed = run_publish()
    line = first_line(completed)
    assert completed.returncode == 1, completed.stdout
    assert line.startswith("PUBLISH REFUSED:"), line
    assert "credential(s) not set" in line, line
    for name in CREDENTIALS:
        assert name in line, f"{name} is not named in the refusal: {line}"
    assert "PUBLISHED" not in completed.stdout


def test_the_refusal_names_the_one_variable_that_is_missing() -> None:
    """A human with three of four set is told which one, not told 'credentials'."""
    completed = run_publish(CLOUDFLARE_ACCOUNT_ID="x", R2_ACCESS_KEY_ID="x", R2_BUCKET="x")
    line = first_line(completed)
    assert completed.returncode == 1
    assert line == ("PUBLISH REFUSED: 1 credential(s) not set: R2_SECRET_ACCESS_KEY"), line


def test_the_credential_gate_runs_before_every_other_gate() -> None:
    """With all four present the script still refuses - on the lock, or the missing artifact - which is
    what makes the bare run's first line evidence of ORDER rather than of there being one gate."""
    completed = run_publish(**{name: "x" for name in CREDENTIALS})
    line = first_line(completed)
    assert completed.returncode != 0, completed.stdout
    assert line.startswith("PUBLISH REFUSED:"), line
    assert "credential(s) not set" not in line, line
    assert "PUBLISHED" not in completed.stdout
