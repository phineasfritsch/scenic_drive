#!/usr/bin/env python3
"""Prove the pre-commit touches gate handles a merge, in BOTH directions, on a repository built for it.

Four cases, each on a throwaway repo with the real hook installed:

  1. a merge that only brings in the other side's files            must COMMIT
  2. a merge whose conflict resolution is inside touches:          must COMMIT
  3. a merge whose resolution edits a file OUTSIDE touches:        must REFUSE
  4. an ordinary (non-merge) commit outside touches:               must REFUSE

Case 3 is the one that matters. The naive fix - skip the check whenever MERGE_HEAD exists - passes cases 1,
2 and 4 and fails only this one, which is exactly why it is here: it would turn "merge main" into a way to
smuggle any file into any branch, and nothing else in the suite would notice.

Case 4 is the control. Without it, a hook that had lost the touches check entirely would pass 1, 2 and 3.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOOK = ROOT / ".githooks" / "pre-commit"
# `--hook <path>` points the cases at a VARIANT of the hook. That is how this check is
# demonstrated red: against the pre-fix hook (cases 1 and 2 must fail) and against the naive
# "skip whenever MERGE_HEAD exists" fix (case 3 must fail). A check only ever run against the
# implementation it ships with has never been seen red.
for _i, _a in enumerate(sys.argv):
    if _a == "--hook" and _i + 1 < len(sys.argv):
        HOOK = pathlib.Path(sys.argv[_i + 1]).resolve()

TASK = """---
id: T-9999
title: probe
state: claimed
owner: agent/probe
owner_session: probe
claimed_at: 2026-01-01T00:00:00Z
lease_expires_at: 2026-12-31T00:00:00Z
worktree: null
branch: task/T-9999
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


def build(tmp: pathlib.Path) -> pathlib.Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "probe@example.invalid")
    git(repo, "config", "user.name", "probe")
    git(repo, "config", "commit.gpgsign", "false")

    hooks = repo / ".githooks"
    hooks.mkdir()
    shutil.copy(HOOK, hooks / "pre-commit")
    os.chmod(hooks / "pre-commit", 0o755)
    git(repo, "config", "core.hooksPath", ".githooks")

    (repo / "allowed").mkdir()
    (repo / "other").mkdir()
    (repo / "allowed" / "a.txt").write_text("base\n", encoding="utf-8", newline="\n")
    (repo / "other" / "b.txt").write_text("base\n", encoding="utf-8", newline="\n")
    (repo / "queue" / "claimed").mkdir(parents=True)
    (repo / "queue" / "claimed" / "T-9999-probe.md").write_text(TASK, encoding="utf-8", newline="\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base", "--no-verify")

    # main moves a file the branch never touches.
    git(repo, "checkout", "-q", "-b", "task/T-9999")
    git(repo, "checkout", "-q", "main")
    (repo / "other" / "b.txt").write_text("from main\n", encoding="utf-8", newline="\n")
    (repo / "other" / "c.txt").write_text("new on main\n", encoding="utf-8", newline="\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "main moves on", "--no-verify")

    # the branch edits only what it is allowed to.
    git(repo, "checkout", "-q", "task/T-9999")
    (repo / "allowed" / "a.txt").write_text("from branch\n", encoding="utf-8", newline="\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "branch work", "--no-verify")
    return repo


def case_merge_clean(repo):
    """1. Only the other side's files arrive. Must commit."""
    git(repo, "merge", "--no-commit", "--no-ff", "main", check=False)
    return git(repo, "commit", "-m", "merge main", check=False)


def case_resolution_inside(repo):
    """2. A conflict resolved inside touches:. Must commit."""
    git(repo, "checkout", "-q", "main")
    (repo / "allowed" / "a.txt").write_text("main also edits allowed\n", encoding="utf-8", newline="\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "main edits allowed", "--no-verify")
    git(repo, "checkout", "-q", "task/T-9999")
    git(repo, "merge", "--no-commit", "--no-ff", "main", check=False)
    (repo / "allowed" / "a.txt").write_text("resolved\n", encoding="utf-8", newline="\n")
    git(repo, "add", "allowed/a.txt")
    return git(repo, "commit", "-m", "merge main, resolve inside touches", check=False)


def case_resolution_outside(repo):
    """3. The author edits a file OUTSIDE touches: during the merge. Must be REFUSED."""
    git(repo, "merge", "--no-commit", "--no-ff", "main", check=False)
    (repo / "other" / "b.txt").write_text("author edited this during the merge\n",
                                          encoding="utf-8", newline="\n")
    git(repo, "add", "other/b.txt")
    return git(repo, "commit", "-m", "merge main and sneak a file in", check=False)


def case_plain_outside(repo):
    """4. Control: an ordinary commit outside touches:. Must be REFUSED."""
    (repo / "other" / "b.txt").write_text("plain edit\n", encoding="utf-8", newline="\n")
    git(repo, "add", "other/b.txt")
    return git(repo, "commit", "-m", "plain commit outside touches", check=False)


CASES = [
    ("1/merge-brings-other-side   must COMMIT", case_merge_clean, True),
    ("2/resolution-inside-touches must COMMIT", case_resolution_inside, True),
    ("3/resolution-outside        must REFUSE", case_resolution_outside, False),
    ("4/plain-commit-outside      must REFUSE", case_plain_outside, False),
]


def main() -> int:
    if not HOOK.is_file():
        sys.stdout.write("TOUCHES-MERGE FAIL: %s not found\n" % HOOK)
        return 2

    ok = True
    for name, fn, must_commit in CASES:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="touches-merge-"))
        try:
            repo = build(tmp)
            code, out = fn(repo)
            committed = code == 0
            if committed == must_commit:
                sys.stdout.write("ok      %s\n" % name)
            else:
                ok = False
                sys.stdout.write("FAIL    %s  (exit %d)\n" % (name, code))
                for line in out.strip().splitlines()[:4]:
                    sys.stdout.write("            %s\n" % line)
        except Exception as e:                                    # noqa: BLE001
            ok = False
            sys.stdout.write("ERROR   %s  %s\n" % (name, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    sys.stdout.write("\nTOUCHES-MERGE %s (%d cases)\n" % ("OK" if ok else "FAIL", len(CASES)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
