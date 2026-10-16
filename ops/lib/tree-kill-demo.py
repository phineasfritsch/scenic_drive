"""T-0354: run check-mutate-only.py's run_tree() on a parent with a sleeping grandchild, past its timeout, on POSIX.

    python3 ops/lib/tree-kill-demo.py [--mutant direct-child|no-session]

check-mutate-only.py kills a timed-out probe's whole tree (a driver that ignored --only has swift build
grandchildren). Its Windows branch was seen red/green on the Windows box; its POSIX branch - start_new_session=True
plus os.killpg(SIGKILL) - only runs on Linux/macOS, so this demo is how it is seen at all. It loads the SHIPPED
file's text, optionally applies one mutant to it (each anchor must occur exactly once, or the demo refuses), and
calls that module's run_tree() with a 3 s timeout on a child that starts a 60 s grandchild sharing its stdout pipe
and then sleeps 60 s itself. After run_tree() returns, the grandchild must be gone (no /proc entry, or a zombie).

  direct-child  os.killpg(p.pid, ...) -> os.kill(p.pid, ...): only the direct child dies.
  no-session    start_new_session dropped: the child shares this process's group, so killpg names no group of p.pid.

Exit 0 the grandchild was killed; 1 it survived; 2 the demo could not run (not POSIX, an anchor missing or
repeated, the timeout never fired, the grandchild never reported its pid).
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import time
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SHIPPED = ROOT / "ops/lib/check-mutate-only.py"
MUTANTS = {
    "direct-child": ("os.killpg(p.pid, signal.SIGKILL)", "os.kill(p.pid, signal.SIGKILL)"),
    "no-session": ('{"start_new_session": True}', "{}"),
}
TIMEOUT_S = 3
CHILD = """
import subprocess, sys, time
g = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
with open(sys.argv[1], "w") as f:
    f.write(str(g.pid))
print("child %d started grandchild %d" % (__import__("os").getpid(), g.pid), flush=True)
time.sleep(60)
"""


def load(mutant: str | None) -> types.ModuleType:
    src = SHIPPED.read_text(encoding="utf-8")
    if mutant is not None:
        old, new = MUTANTS[mutant]
        if src.count(old) != 1:
            raise SystemExit("tree-kill-demo: anchor %r occurs %d times in %s, need 1: REFUSING"
                             % (old, src.count(old), SHIPPED.name))
        src = src.replace(old, new)
    mod = types.ModuleType("check_mutate_only_demo")
    mod.__file__ = str(SHIPPED)
    exec(compile(src, str(SHIPPED), "exec"), mod.__dict__)
    return mod


def alive(pid: int) -> str | None:
    """The /proc state letter of a live process, None when it is gone or a zombie (dead, not yet reaped)."""
    try:
        stat = pathlib.Path("/proc/%d/stat" % pid).read_text()
    except OSError:
        return None
    state = stat.rsplit(")", 1)[1].split()[0]
    return None if state in ("Z", "X") else state


def main(argv: list) -> int:
    if os.name == "nt" or not pathlib.Path("/proc/self/stat").exists():
        print("tree-kill-demo: needs POSIX with /proc (run it in Linux): REFUSING")
        return 2
    mutant = None
    if argv[:1] == ["--mutant"] and len(argv) == 2 and argv[1] in MUTANTS:
        mutant = argv[1]
    elif argv:
        print("usage: tree-kill-demo.py [--mutant %s]" % "|".join(MUTANTS))
        return 2
    mod = load(mutant)
    with tempfile.TemporaryDirectory() as tmp:
        pidfile = pathlib.Path(tmp) / "grandchild.pid"
        t0 = time.monotonic()
        code, out, how = mod.run_tree([sys.executable, "-c", CHILD, str(pidfile)], TIMEOUT_S)
        took = time.monotonic() - t0
        time.sleep(0.5)
        gpid = int(pidfile.read_text()) if pidfile.exists() and pidfile.read_text().strip() else None
    label = "mutant " + mutant if mutant else "shipped"
    print("%s run_tree: exit %s after %.1fs, kill: %s" % (label, code, took, how))
    print("%s output: %s" % (label, out.strip().replace("\n", " | ") or "(none)"))
    if how is None or gpid is None:
        print("%s: the timeout never fired or the grandchild never reported its pid: CANNOT JUDGE" % label)
        return 2
    state = alive(gpid)
    if state is not None:
        print("GRANDCHILD SURVIVED (%s): pid %d is still running (state %s)" % (label, gpid, state))
        os.kill(gpid, 9)
        return 1
    print("GRANDCHILD KILLED (%s): pid %d is gone" % (label, gpid))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
