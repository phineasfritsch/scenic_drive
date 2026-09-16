#!/usr/bin/env python3
"""Prove `ops/queue-sweep` cannot throw away finished work, on a queue built for it.

The sweeper exists to release a lease whose owner has gone away. On 2026-09-15 **67 of 67** tasks in
`queue/claimed/` had an expired lease and **39 of them had an open PR** - finished, pushed, green work. A
sweeper that reads only a timestamp would have set `owner: null` on all 39 (the state T-0068 exists to
reject), left `main` saying `ready/<id>` while each branch says `review/`, and produced the add/add
divergence eleven branches were already repaired for by hand.

`cmd_sweep` was hardened for that (T-0131's first item, landed before this file). **Nothing asserted it.**
A check that has never been seen red is untested, and the guard protecting 39 branches was one careless
edit from being a comment. This is the assertion.

Six cases, each on a throwaway repo with the real `ops/lib/queue.py` copied in:

  1. expired lease, branch pushed (origin/<branch> exists)       must KEEP
  2. expired lease, branch DECLARED but no ref anywhere          must KEEP
  3. expired lease, no branch declared at all                    must SWEEP to ready/
  4. lease still valid, branch pushed                            must not be touched
  5. not a git repository at all                                 must REFUSE, exit 2, move nothing
  6. expired lease, LOCAL branch only, never pushed              must KEEP

Case 2 is the one that changed the code. `_branch_exists` does no fetch - deliberately, a sweeper that
reaches the network is a sweeper nobody runs - so a branch pushed by another agent since this checkout last
fetched reads as ABSENT, and the old code swept it. The docstring called that direction safe; it is the
unsafe one, and it is the exact failure this task was filed about. A DECLARED branch is now evidence that
work was started somewhere, and the sweeper says it cannot prove otherwise without a fetch.

Case 5 is the control. Without it, a sweeper that refused everything - or one that died on a syntax error -
would pass cases 1, 2, 4 and 6 by doing nothing at all.

EVERY CASE ASSERTS WHAT THE SWEEPER SAID, not only where the file ended up. A run that moves nothing looks
identical whether the guard fired or the loop never ran, and "the loop never ran" is how the mutation
harnesses in this repository learned to report a clean sheet over an empty population.

`--variants` regenerates variants of the real `queue.py` and requires each to break EXACTLY the cases named
against it. That is what makes six cases discriminating rather than decorative.
"""
from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
QUEUE_PY = ROOT / "ops" / "lib" / "queue.py"

for _i, _a in enumerate(sys.argv):
    if _a == "--queue" and _i + 1 < len(sys.argv):
        QUEUE_PY = pathlib.Path(sys.argv[_i + 1]).resolve()

PAST = "2020-01-01T00:00:00Z"
FUTURE = "2099-01-01T00:00:00Z"

TASK = """---
id: {tid}
title: probe {tid}
state: claimed
owner: agent/probe
owner_session: probe
claimed_at: 2020-01-01T00:00:00Z
lease_expires_at: {expires}
worktree: null
branch: {branch}
exclusive: []
touches: [allowed/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test]
acceptance: []
---
## Brief

probe

## Log
"""


def git(repo, *args, check=True):
    p = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.strip()[:300]))
    return p.returncode, p.stdout + p.stderr


def build(tmp: pathlib.Path, queue_override: pathlib.Path | None = None,
          init_git: bool = True) -> pathlib.Path:
    """A repo shaped like this one: <root>/ops/lib/queue.py and <root>/queue/<state>/.

    queue.py finds its root with `Path(__file__).resolve().parents[2]`, so the copy has to sit at that
    depth or every path it computes belongs to the REAL repository - which would make these cases edit
    the queue they are meant to be testing.
    """
    repo = tmp / "repo"
    (repo / "ops" / "lib").mkdir(parents=True)
    shutil.copy(queue_override or QUEUE_PY, repo / "ops" / "lib" / "queue.py")
    for state in ("backlog", "ready", "claimed", "review", "blocked", "done"):
        (repo / "queue" / state).mkdir(parents=True)
    (repo / "queue" / "LOCKS").mkdir()

    if init_git:
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "probe@example.invalid")
        git(repo, "config", "user.name", "probe")
        git(repo, "config", "commit.gpgsign", "false")
        (repo / "README.md").write_text("probe\n", encoding="utf-8", newline="\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base", "--no-verify")
    return repo


def add_task(repo: pathlib.Path, tid: str, branch: str | None, expires: str) -> pathlib.Path:
    p = repo / "queue" / "claimed" / ("%s-probe.md" % tid)
    p.write_text(TASK.format(tid=tid, branch=branch or "null", expires=expires),
                 encoding="utf-8", newline="\n")
    return p


def make_branch(repo: pathlib.Path, name: str, pushed: bool) -> None:
    """A real branch, optionally also visible as a remote-tracking ref.

    `git update-ref` rather than a bare clone: the sweeper reads refs/remotes/origin/<name> directly and
    never touches the network, so the ref IS the whole of what it can see.
    """
    git(repo, "branch", name, "main")
    if pushed:
        _, sha = git(repo, "rev-parse", "main")
        git(repo, "update-ref", "refs/remotes/origin/%s" % name, sha.strip())


def sweep(repo: pathlib.Path):
    p = subprocess.run([sys.executable, str(repo / "ops" / "lib" / "queue.py"), "sweep"],
                       cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def where(repo: pathlib.Path, tid: str) -> str:
    for state in ("backlog", "ready", "claimed", "review", "blocked", "done"):
        if list((repo / "queue" / state).glob("%s-*.md" % tid)):
            return state
    return "GONE"


# (label, build the case -> (repo, tid), expected state afterwards, a phrase the output must contain)
def case_pushed_branch(tmp):
    repo = build(tmp)
    add_task(repo, "T-9001", "task/T-9001", PAST)
    make_branch(repo, "task/T-9001", pushed=True)
    return repo, "T-9001"


def case_declared_but_unfetched(tmp):
    repo = build(tmp)
    add_task(repo, "T-9002", "task/T-9002", PAST)
    # No branch is created at all: this is the checkout that has not fetched what another agent pushed.
    return repo, "T-9002"


def case_no_branch_declared(tmp):
    repo = build(tmp)
    add_task(repo, "T-9003", None, PAST)
    return repo, "T-9003"


def case_lease_still_valid(tmp):
    repo = build(tmp)
    add_task(repo, "T-9004", "task/T-9004", FUTURE)
    make_branch(repo, "task/T-9004", pushed=True)
    return repo, "T-9004"


def case_not_a_git_repo(tmp):
    repo = build(tmp, init_git=False)
    add_task(repo, "T-9005", None, PAST)     # no branch: without the guard this one WOULD be swept
    return repo, "T-9005"


def case_local_branch_only(tmp):
    repo = build(tmp)
    add_task(repo, "T-9006", "task/T-9006", PAST)
    make_branch(repo, "task/T-9006", pushed=False)
    return repo, "T-9006"


CASES = [
    ("1/pushed-branch          must KEEP",   case_pushed_branch,          "claimed", 0, "kept"),
    ("2/declared-not-fetched   must KEEP",   case_declared_but_unfetched, "claimed", 0, "kept"),
    ("3/no-branch-declared     must SWEEP",  case_no_branch_declared,     "ready",   0, "-> ready/"),
    ("4/lease-still-valid      must NOT move", case_lease_still_valid,    "claimed", 0, "SWEEP done (0 moved"),
    ("5/not-a-git-repo         must REFUSE", case_not_a_git_repo,         "claimed", 2, "SWEEP REFUSED"),
    ("6/local-branch-only      must KEEP",   case_local_branch_only,      "claimed", 0, "kept"),
]


def run_cases(queue_override=None, quiet=False):
    """Returns the list of failing case labels. Empty means every case held."""
    failed = []
    for name, fn, want_state, want_code, want_say in CASES:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="sweep-case-"))
        try:
            if queue_override is not None:
                # The case builders call build() with the real queue.py; patch it afterwards so a variant
                # does not have to be threaded through six functions.
                repo, tid = fn(tmp)
                shutil.copy(queue_override, repo / "ops" / "lib" / "queue.py")
            else:
                repo, tid = fn(tmp)
            code, out = sweep(repo)
            got_state = where(repo, tid)
            why = []
            if got_state != want_state:
                why.append("ended in %s/, expected %s/" % (got_state, want_state))
            if code != want_code:
                why.append("exit %d, expected %d" % (code, want_code))
            # A move is not the whole assertion. Asserting only on where the file ended up lets a sweeper
            # that does nothing at all - because it crashed, or because its loop never ran - pass every
            # must-KEEP case, which is four of the six.
            if want_say not in out:
                why.append("never said %r" % want_say)
            if why:
                failed.append(name.split("/")[0])
                if not quiet:
                    sys.stdout.write("FAIL    %s  %s\n" % (name, "; ".join(why)))
                    for line in out.strip().splitlines()[:4]:
                        sys.stdout.write("            %s\n" % line)
            elif not quiet:
                sys.stdout.write("ok      %s\n" % name)
        except Exception as e:                                    # noqa: BLE001
            failed.append(name.split("/")[0])
            if not quiet:
                sys.stdout.write("ERROR   %s  %s: %s\n" % (name, type(e).__name__, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return failed


# (label, marker to replace, replacement, the case numbers that MUST break and no others)
#
# A marker that no longer appears exactly once raises rather than being skipped. A variant sweep that
# quietly drops a stale variant reports OK while proving nothing, which is the shape this whole file is
# about - and it caught this file's own first draft, whose markers described code that was never written.
_KEEP_PUSHED = ('            if _branch_exists(branch):\n'
                '                held.append(f"{fm[\'id\']} (branch {branch} exists)")\n'
                '                continue\n')
_KEEP_DECLARED = ('            if _declares_branch(branch):\n'
                  '                held.append(f"{fm[\'id\']} (declares branch {branch}; no ref here'
                  ' - fetch to see it)")\n'
                  '                continue\n')

VARIANTS = [
    ("without the git-usable guard", "    if not _git_usable():", "    if False:", {"5"}),
    # T-0131 itself: the declared-branch fallback removed, i.e. the sweeper exactly as it shipped.
    ("declared-branch falls through", _KEEP_DECLARED, "", {"2"}),
    # Both branch questions answered "no", which is what a git that cannot read refs would produce.
    # The replacement needs a BODY: `if False:` with nothing under it is an IndentationError, and a variant
    # that dies on import breaks all six cases - which proves only that a broken file is broken, not that
    # any case is watching this guard.
    ("without any branch check", _KEEP_PUSHED + _KEEP_DECLARED,
     "            if False:\n                continue\n", {"1", "2", "6"}),
]


def variant(marker: str, replacement: str, tmp: pathlib.Path) -> pathlib.Path:
    text = QUEUE_PY.read_text(encoding="utf-8")
    if text.count(marker) != 1:
        raise RuntimeError("variant marker appears %d times, not once: %r" % (text.count(marker), marker))
    out = tmp / "variant-queue.py"
    out.write_text(text.replace(marker, replacement), encoding="utf-8", newline="\n")
    return out


def run_variants() -> int:
    ok = True
    for label, marker, replacement, must_break in VARIANTS:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="sweep-variant-"))
        try:
            v = variant(marker, replacement, tmp)
            broke = set(run_cases(queue_override=v, quiet=True))
            if broke == must_break:
                sys.stdout.write("ok      variant %-30s breaks exactly %s\n"
                                 % (label, ",".join(sorted(must_break))))
            else:
                ok = False
                sys.stdout.write("FAIL    variant %-30s expected %s, got %s\n"
                                 % (label, ",".join(sorted(must_break)) or "nothing",
                                    ",".join(sorted(broke)) or "nothing"))
        except Exception as e:                                    # noqa: BLE001
            ok = False
            sys.stdout.write("ERROR   variant %-30s %s: %s\n" % (label, type(e).__name__, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    sys.stdout.write("\nSWEEP VARIANTS %s (%d)\n" % ("OK" if ok else "FAIL", len(VARIANTS)))
    return 0 if ok else 1


def main() -> int:
    if not QUEUE_PY.is_file():
        sys.stdout.write("SWEEP-CHECK FAIL: %s not found\n" % QUEUE_PY)
        return 2
    if "--variants" in sys.argv:
        return run_variants()
    failed = run_cases()
    sys.stdout.write("\nSWEEP-CHECK %s (%d cases)\n" % ("FAIL" if failed else "OK", len(CASES)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
