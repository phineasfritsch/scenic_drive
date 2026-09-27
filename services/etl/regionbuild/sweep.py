"""Run one command per tile, N tiles at a time, resuming by file presence.

T-0208's pass1*.sh and pass2.sh were `xargs -P N` over a tile list with a `[ -s out ] && SKIP` guard: a
session that restarts keeps the work store, and every tile whose output is already non-empty is kept. The
tiles are independent, so the parallelism changes no number - only which line is printed first.
"""
from __future__ import annotations

import concurrent.futures
import pathlib
import subprocess
import sys
import time

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]


def python_module(module: str, *args) -> list:
    """`python -m <module> <args>` with the interpreter running this build."""
    return [sys.executable, "-m", module] + [str(arg) for arg in args]


def count_line(command: list, prefix: str) -> tuple:
    """Run one command from the package root; return (its `prefix` line or None, its combined output)."""
    proc = subprocess.run(command, cwd=PACKAGE_ROOT, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    line = next((text for text in output.splitlines() if text.startswith(prefix)), None)
    if proc.returncode != 0:
        line = None
    return line, output


def run(names, output_of, work, jobs: int, label: str) -> list:
    """`work(name) -> (ok, line)` for each name whose `output_of(name)` is missing or empty.

    Returns the names that FAILED. A failed tile's partial output is the worker's to delete, so the next
    run retries it rather than skipping it.
    """
    todo = []
    for name in names:
        out = output_of(name)
        if out.exists() and out.stat().st_size > 0:
            print("SKIP %s (%s present)" % (name, out.name), flush=True)
        else:
            todo.append(name)
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        started = {pool.submit(_timed, work, name): name for name in todo}
        for future in concurrent.futures.as_completed(started):
            name = started[future]
            ok, line, elapsed = future.result()
            if ok:
                print("%s %s %s elapsed=%ds" % (label, name, line, elapsed), flush=True)
            else:
                failed.append(name)
                print("FAIL %s %s" % (name, line), flush=True)
    return sorted(failed)


def _timed(work, name: str) -> tuple:
    begun = time.monotonic()
    ok, line = work(name)
    return ok, line, int(time.monotonic() - begun)
