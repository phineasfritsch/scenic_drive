"""What a run of ops/mutate/geometry.py does to the filesystem: the copy, the mutant, pytest, the probe.

Split out of the runner at the 300-line cap, along the boundary budget_tree.py draws for budget.py - that
file is "what the run does to the working tree" and the runner is the protocol. The boundary is meaning and
not a line number: every function here touches the disk or a subprocess, and nothing here decides whether a
verdict is a pass.

NEVER THE WORKTREE. `services/etl` is copied into .build-mutate-geometry/ - the gitignored scratch
convention (`.build-*/`) every harness in this repository uses - ONE textual mutation is written into the
COPY, and pytest runs there with that directory as its cwd. There is no restore step, and that is the point:
budget.py has to write the mutation into `Sources/` and put the pristine bytes back in a `finally`, which is
why it also needs a sentinel file and a `git show HEAD:` comparison to notice a restore that never happened.
Here `git status` over services/etl is untouched by a full sweep, so the failure those two mechanisms exist
to catch cannot arise. What replaces the sleep-before-restore a hand-run demo needs is `purge_pycache`.

THE .pyc HAZARD, which is the one thing this file does that budget.py's Swift equivalent does not have to.
CPython keys a cached .pyc on the source's mtime and size at ONE-SECOND granularity. A sweep writes several
mutants of the same file inside the same second, and two mutants of the same size - `<= 1` for `< 1`, say -
would be byte-for-byte indistinguishable to that cache, so the second could be measured through the first's
bytecode. Every `__pycache__` under the copy is removed before every pytest run, which is cheap and, unlike
a sleep, does not depend on a clock.
"""
from __future__ import annotations

import hashlib
import pathlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from geometry_mutations import ETL, ROOT, TEST_FILES

SCRATCH = ROOT / ".build-mutate-geometry"
COPY = SCRATCH / "etl"
PROBE = pathlib.Path(__file__).resolve().parent / "geometry_probe.py"
PYTEST = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-p", "no:randomly", "--tb=no", "-q"]


def fresh_copy() -> None:
    """A copy of services/etl under the scratch path, minus the `inputs` no test here reads."""
    if COPY.exists():
        shutil.rmtree(COPY)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ETL, COPY, ignore=shutil.ignore_patterns(
        "__pycache__", ".pytest_cache", "work", "inputs"))


def purge_pycache(root: pathlib.Path) -> int:
    """Every __pycache__ under the copy, before every pytest run. See the module docstring."""
    gone = 0
    for cache in sorted(root.rglob("__pycache__")):
        shutil.rmtree(cache, ignore_errors=True)
        gone += 1
    return gone


def apply(rel: str, old: str, new: str) -> bool:
    """Write one mutant into the COPY. False when the anchor is not there exactly once, or when the
    replacement leaves the file unchanged: either one is a stale harness, never a pass."""
    fresh_copy()
    target = COPY / rel
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        sys.stdout.write("    DID NOT APPLY - anchor appears %d times in %s, not once\n"
                         % (text.count(old), rel))
        return False
    mutated = text.replace(old, new, 1)
    if mutated == text:
        sys.stdout.write("    DID NOT APPLY - the replacement left %s unchanged\n" % rel)
        return False
    target.write_text(mutated, encoding="utf-8", newline="\n")
    return True


def failures(xml: pathlib.Path) -> list[str]:
    """The test NAMES that failed or errored, read from the JUnit XML and never grepped from stdout."""
    if not xml.exists():
        return []
    return [tc.get("name") for tc in ET.parse(xml).getroot().iter("testcase")
            if tc.find("failure") is not None or tc.find("error") is not None]


def run_tests(cwd: pathlib.Path, tag: str) -> tuple[int, list[str]]:
    """pytest over TEST_FILES inside the copy: `(exit code, the names that went red)`."""
    xml = SCRATCH / ("%s.xml" % tag)
    if xml.exists():
        xml.unlink()
    purge_pycache(cwd)
    p = subprocess.run([*PYTEST, "--junitxml=%s" % xml, *TEST_FILES], cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, failures(xml)


def fingerprint(cwd: pathlib.Path) -> tuple[str, int, str]:
    """`(digest, values measured, raw output)` - geometry_probe.py's answers over every fixture case.

    A probe that crashes is a fingerprint too, and a DIFFERENT one: its output carries the exit code and the
    traceback, so a mutation that makes the module unimportable can never read as equivalent.
    """
    p = subprocess.run([sys.executable, str(PROBE), str(cwd)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = p.stdout if p.returncode == 0 else "PROBE FAILED exit=%d\n%s%s" % (p.returncode, p.stdout, p.stderr)
    return hashlib.sha256(out.encode("utf-8")).hexdigest()[:16], len(out.splitlines()), out


def fingerprint_of_pristine() -> tuple[str, int, str]:
    """The baseline witness, over a copy with no mutation in it."""
    fresh_copy()
    return fingerprint(COPY)
