#!/usr/bin/env python3
"""Prove the pre-commit touches gate handles a merge, in BOTH directions, on a repository built for it.

Seven cases, each on a throwaway repo with the real hook installed:

  1. a merge that only brings in the other side's files            must COMMIT
  2. a merge whose conflict resolution is inside touches:          must COMMIT
  3. a merge whose resolution edits a file OUTSIDE touches:        must REFUSE
  4. an ordinary (non-merge) commit outside touches:               must REFUSE
  5. `git mv` from outside touches: to inside it, during a merge   must REFUSE
  6. a delete outside touches:, during a merge                     must REFUSE
  7. a secret arriving from the other side of a merge              must REFUSE

Case 3 is the one that matters most. The naive fix - skip the check whenever MERGE_HEAD exists - passes
cases 1, 2 and 4 and fails only this one: it would turn "merge main" into a way to smuggle any file into
any branch, and nothing else in the suite would notice.

Case 4 is the control. Without it, a hook that had lost the touches check entirely would pass 1, 2 and 3.

Case 5 is a reviewer's attack that DEFEATED the first version of this gate. `git diff --name-only` has
rename detection on by default and prints only a rename's destination, so the source path vanished from the
MERGE_HEAD side and dropped out of the intersection - letting a branch relocate any file in the repository
into its own touches: prefix. Case 7 exists because the Log claimed the secret scan still guards a merge and
nothing asserted it.

EVERY REFUSING CASE NAMES THE REASON IT MUST GIVE. Asserting only on the exit code lets a hook that refuses
everything - or one that dies on a syntax error - pass every negative case, which is how case 5's defect
stayed invisible.

`--variants` regenerates variants of the real hook and requires each to break exactly one case. That is
tracked here rather than in a scratch directory, because a demonstration living in a gitignored path ships
nowhere and cannot be re-run.
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


def build(tmp: pathlib.Path, hook_override: pathlib.Path | None = None) -> pathlib.Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "probe@example.invalid")
    git(repo, "config", "user.name", "probe")
    git(repo, "config", "commit.gpgsign", "false")

    hooks = repo / ".githooks"
    hooks.mkdir()
    shutil.copy(hook_override or HOOK, hooks / "pre-commit")
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


def case_rename_into_touches(repo):
    """5. `git mv` a file from OUTSIDE touches: to INSIDE it, during a merge. Must be REFUSED.

    This is the attack that defeated the first version of the gate, found by a reviewer:

        git merge --no-commit --no-ff main
        git mv other/b.txt allowed/b.txt      # touches: [allowed/]
        git commit                            # exit 0

    `git diff --name-only` has rename detection on by default and prints only the DESTINATION, so
    `other/b.txt` vanished from the MERGE_HEAD side and dropped out of the intersection - letting a branch
    relocate any file in the repository into its own prefix and then own it. `--no-renames` closes it.
    """
    git(repo, "merge", "--no-commit", "--no-ff", "main", check=False)
    git(repo, "mv", "other/b.txt", "allowed/b.txt", check=False)
    return git(repo, "commit", "-m", "merge main and relocate a file into touches", check=False)


def case_delete_outside(repo):
    """6. Delete a file outside touches: during a merge. Must be REFUSED.

    The staged list is built with `--diff-filter=ACMR`, which omits deletes, while the merge intersection
    has no filter. A reviewer pointed out the asymmetry: a delete outside touches: is refused inside a merge
    and allowed on an ordinary commit. Refusing inside the merge is the safe direction, and this pins it so
    the behaviour is deliberate rather than incidental.
    """
    git(repo, "merge", "--no-commit", "--no-ff", "main", check=False)
    # `-f` is required: during a merge `git rm` refuses a path with changes staged in the index. Without it
    # the removal SILENTLY FAILED and this case quietly became a duplicate of case 1 - it passed, for a
    # reason that had nothing to do with deletes. Caught by probing what the hook actually saw
    # (`status` reported `M other/b.txt`, not a deletion) rather than by reading the case.
    rc, _ = git(repo, "rm", "-q", "-f", "other/b.txt", check=False)
    if rc != 0:
        return 99, "setup failed: git rm did not remove the file, so this case tested nothing"
    return git(repo, "commit", "-m", "merge main and delete a file outside touches", check=False)


def case_secret_across_merge(repo):
    """7. A secret arriving from the other side of a merge is still refused.

    The merge case narrowed `touches:` only. The secret scan and the CRLF check above it keep reading the
    raw staged list on purpose - a secret arriving from the other side is still a secret in this branch's
    history - and this is the assertion that says so.
    """
    git(repo, "checkout", "-q", "main")
    (repo / "allowed" / "leak.txt").write_text(
        "sk.%s\n" % ("A1b2C3d4E5f6G7h8I9j0"), encoding="utf-8", newline="\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "main adds a secret", "--no-verify")
    git(repo, "checkout", "-q", "task/T-9999")
    git(repo, "merge", "--no-commit", "--no-ff", "main", check=False)
    return git(repo, "commit", "-m", "merge main carrying a secret", check=False)


CASES = [
    ("1/merge-brings-other-side   must COMMIT", case_merge_clean, True, None),
    ("2/resolution-inside-touches must COMMIT", case_resolution_inside, True, None),
    ("3/resolution-outside        must REFUSE", case_resolution_outside, False,
     "other/b.txt is outside T-9999 touches"),
    ("4/plain-commit-outside      must REFUSE", case_plain_outside, False,
     "other/b.txt is outside T-9999 touches"),
    ("5/rename-into-touches       must REFUSE", case_rename_into_touches, False,
     "other/b.txt is outside T-9999 touches"),
    ("6/delete-outside-in-merge   must REFUSE", case_delete_outside, False,
     "other/b.txt is outside T-9999 touches"),
    ("7/secret-across-a-merge     must REFUSE", case_secret_across_merge, False,
     "secret-looking content"),
]


def variant_without(marker: str, replacement: str, tmp: pathlib.Path) -> pathlib.Path:
    """A copy of the real hook with one thing removed, written where the cases can point at it."""
    text = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
    if marker not in text:
        raise RuntimeError("variant marker not present in the hook: %r" % marker)
    out = tmp / "variant-hook"
    out.write_text(text.replace(marker, replacement), encoding="utf-8", newline="\n")
    return out


# (label, what to remove, what must break). Each variant must fail a DIFFERENT case, which is what makes the
# seven discriminating rather than decorative. Generated from the real hook at run time and tracked here,
# because a demonstration that lives in a gitignored scratch directory ships nowhere and cannot be re-run -
# a defect a reviewer already found in the sibling check's history demo.
VARIANTS = [
    ("without --no-renames", " --no-renames", "", "5/rename-into-touches"),
]


def run_variants() -> int:
    ok = True
    for label, marker, replacement, must_fail in VARIANTS:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="touches-variant-"))
        try:
            hook = variant_without(marker, replacement, tmp)
            failed = []
            for name, fn, must_commit, must_say in CASES:
                t2 = pathlib.Path(tempfile.mkdtemp(prefix="touches-merge-"))
                try:
                    repo = build(t2, hook_override=hook)
                    code, _ = fn(repo)
                    if code != 99 and (code == 0) != must_commit:
                        failed.append(name.split()[0])
                finally:
                    shutil.rmtree(t2, ignore_errors=True)
            if must_fail.split("/")[0] in [f.split("/")[0] for f in failed] and len(failed) == 1:
                sys.stdout.write("ok      variant %-22s breaks exactly %s\n" % (label, failed[0]))
            else:
                ok = False
                sys.stdout.write("FAIL    variant %-22s expected only %s to break, got %s\n"
                                 % (label, must_fail, failed or "nothing"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    sys.stdout.write("\nTOUCHES-MERGE VARIANTS %s (%d)\n" % ("OK" if ok else "FAIL", len(VARIANTS)))
    return 0 if ok else 1


def main() -> int:
    if not HOOK.is_file():
        sys.stdout.write("TOUCHES-MERGE FAIL: %s not found\n" % HOOK)
        return 2
    if "--variants" in sys.argv:
        return run_variants()

    ok = True
    for name, fn, must_commit, must_say in CASES:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="touches-merge-"))
        try:
            repo = build(tmp)
            code, out = fn(repo)
            # 99 is a case reporting that its own SETUP did not happen. A case whose premise silently fails
            # still produces an exit code, and case 6 passed that way until a probe showed the file it
            # claimed to delete was never deleted.
            if code == 99:
                ok = False
                sys.stdout.write("SETUP   %s  %s\n" % (name, out))
                continue
            committed = code == 0
            # A refusal must be for the RIGHT REASON. Asserting only on the exit code lets a hook that
            # refuses everything - or one that dies on a syntax error - pass every negative case, which a
            # reviewer flagged as the gap that made F1 possible to miss.
            if not must_commit and not committed and must_say and must_say not in out:
                ok = False
                sys.stdout.write("FAIL    %s  refused, but not for the stated reason\n"
                                 "            expected to see: %s\n" % (name, must_say))
                for line in out.strip().splitlines()[:3]:
                    sys.stdout.write("            %s\n" % line)
                continue
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
