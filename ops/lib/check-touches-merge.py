#!/usr/bin/env python3
"""Prove the pre-commit touches gate handles a merge, in BOTH directions, on a repository built for it.

Eleven cases, each on a throwaway repo with the real hook installed:

  1. a merge that only brings in the other side's files            must COMMIT
  2. a merge whose conflict resolution is inside touches:          must COMMIT
  3. a merge whose resolution edits a file OUTSIDE touches:        must REFUSE
  4. an ordinary (non-merge) commit outside touches:               must REFUSE
  5. `git mv` from outside touches: to inside it, during a merge   must REFUSE
  6. a delete outside touches:, during a merge                     must REFUSE
  7. a secret arriving from the other side of a merge              must REFUSE
  8. a MERGE_HEAD that names no commit, so a diff errors           must REFUSE
  9. a merge inside a LINKED WORKTREE, resolution INSIDE touches:  must COMMIT
 10. the same, resolution OUTSIDE touches:                         must REFUSE
 11. `git mv` a file main NEVER CHANGED into touches:, in a merge  must REFUSE

Case 8 is T-0137: an intersection is empty as soon as either side is, so one failing `git diff --cached`
leaves the gate with nothing to check - the fail-open that arrived with the merge case. (Measured:
`head_rc=0 merge_rc=128`. The docstring here said "both diffs error" until T-0139 instrumented the hook and
found that only the MERGE_HEAD one does.)

Cases 9 and 10 pin the `--git-dir` handling every task in this fleet depends on and that cases 1-8 cannot
see, because they build plain `git init` checkouts where `--git-dir` is `.git`. The pair is deliberate: 9
is the direction that DEPENDS on the narrowing, and is therefore the only one that can see a hook whose
`--git-dir` lookup was "simplified" to a literal `.git/MERGE_HEAD` - in a linked worktree `.git` is a FILE,
so the narrowing never applies, the full staged set is checked, and a must-REFUSE case passes for a reason
unrelated to what it claims to pin. That was case 9's first version, and it could not fail.

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

`--variants` regenerates variants of the real hook and requires each to break exactly the set of cases named
against it. That is tracked here rather than in a scratch directory, because a demonstration living in a gitignored path ships
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
    (repo / "other" / "d.txt").write_text("nobody changes this\n", encoding="utf-8", newline="\n")
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


def case_empty_merge_head(repo):
    """8. A MERGE_HEAD that does not name a commit must not switch the gate off. Must be REFUSED.

    The merge case intersects two `git diff --cached` outputs, and an intersection is empty as soon as
    EITHER side is. So one failing git call empties it, the `while` loop iterates over nothing, and the gate
    checks nothing - silently, with no warning, producing an ordinary single-parent commit that looks normal
    afterwards. An empty `.git/MERGE_HEAD` is enough to produce it:

        printf 'x\\n' >> other/b.txt && git add other/b.txt
        : > "$(git rev-parse --git-dir)/MERGE_HEAD"
        git commit                      # exit 0 before the fix
        git log -1 --pretty=%P          # ONE sha - not a merge

    Found by agent/rv-keystone while passing PR #78, filed as T-0137. It needs a deliberate write into
    `.git/`, so it is not an attack anyone stumbles into - it is here because the SHAPE is the one this
    repository keeps finding: a check that silently passes when its own machinery fails. `check-exec-bits`
    refuses on an empty file set, the mutation harnesses refuse on an empty population, `--prove-vacuity`
    requires MISSED to be complete. The gate that runs on every commit by every agent should not be the one
    place where "the command errored" reads as "nothing to check".

    The fix is to fall back to the FULL staged set: a gate that cannot compute the narrower set must check
    the wider one. So this case must be refused for the ORDINARY touches reason, which is what the expected
    message asserts - a hook that died on a syntax error would also refuse, and must not pass here.
    """
    (repo / "other" / "b.txt").write_text("edited outside touches\n", encoding="utf-8", newline="\n")
    git(repo, "add", "other/b.txt")
    _, gitdir = git(repo, "rev-parse", "--git-dir")
    mh = (repo / gitdir.strip()) if not os.path.isabs(gitdir.strip()) else pathlib.Path(gitdir.strip())
    (mh / "MERGE_HEAD").write_text("", encoding="utf-8", newline="\n")
    if not (mh / "MERGE_HEAD").is_file():
        return 99, "setup failed: MERGE_HEAD was not created, so this case tested nothing"
    code, out = git(repo, "commit", "-m", "commit with an empty MERGE_HEAD", check=False)
    (mh / "MERGE_HEAD").unlink(missing_ok=True)
    return code, out


def _linked_worktree(repo):
    """A linked checkout of task/T-9999, mid-merge with main. Returns (path, None) or (None, why)."""
    wt = repo.parent / "linked"
    git(repo, "checkout", "-q", "--detach")          # free task/T-9999 for the linked worktree
    rc, out = git(repo, "worktree", "add", "-q", str(wt), "task/T-9999", check=False)
    if rc != 0 or not (wt / ".git").exists():
        return None, "git worktree add did not produce a linked checkout (%s)" % out.strip()[:120]
    if (wt / ".git").is_dir():
        return None, ".git is a directory, so this is not a linked worktree"
    _, gd = git(wt, "rev-parse", "--git-dir")
    if pathlib.Path(gd.strip()).name == ".git":
        return None, "--git-dir is %r, so this case cannot tell a linked worktree from a plain one" % gd.strip()
    git(wt, "merge", "--no-commit", "--no-ff", "main", check=False)
    if not (wt / "other" / "c.txt").is_file():
        return None, "the merge did not run in the linked worktree"
    return wt, None


def case_merge_inside_linked_worktree(repo):
    """9. A legitimate merge run inside a LINKED WORKTREE still commits. Must COMMIT.

    Every task in this fleet runs in a `git worktree add`ed checkout, where `--git-dir` is
    `.git/worktrees/<name>` and `.git` is a FILE, not a directory. The hook is correct there today - a
    reviewer verified it by hand - but nothing pinned it, and cases 1-8 all build plain `git init`
    checkouts where `--git-dir` is `.git`. A "simplification" to a literal `.git/MERGE_HEAD` would leave
    every one of them green and refuse every real merge in this repository.

    THIS CASE MUST COMMIT, and that is the whole point. The first version of it was a REFUSE case, which
    proved nothing: with `--git-dir` broken the narrowing never applies, the hook checks the full staged
    set, and a REFUSE case passes for the wrong reason. Only the direction that DEPENDS on the narrowing
    can discriminate. Case 10 guards the other direction.
    """
    wt, why = _linked_worktree(repo)
    if wt is None:
        return 99, "setup failed: " + why
    (wt / "allowed" / "a.txt").write_text("resolved in the linked worktree\n",
                                          encoding="utf-8", newline="\n")
    git(wt, "add", "allowed/a.txt")
    return git(wt, "commit", "-m", "merge main in a linked worktree, resolve inside touches", check=False)


def case_linked_worktree_resolution_outside(repo):
    """10. ...and the narrowing is not a blanket skip there either. Must be REFUSED.

    Case 9 alone is satisfied by a hook that skips the check whenever MERGE_HEAD exists - the same naive
    fix case 3 exists to catch, which would reappear in the one environment cases 1-8 never enter.
    """
    wt, why = _linked_worktree(repo)
    if wt is None:
        return 99, "setup failed: " + why
    (wt / "other" / "b.txt").write_text("author edited this during the merge\n",
                                        encoding="utf-8", newline="\n")
    git(wt, "add", "other/b.txt")
    return git(wt, "commit", "-m", "merge main in a linked worktree, sneak a file in", check=False)


def case_rename_of_an_untouched_file(repo):
    """11. `git mv` a file that main NEVER CHANGED into touches:, during a merge. Must be REFUSED.

    Case 5 moves a file main did change, so its moved copy differs from HEAD's and HEAD-side rename
    detection never fires - only the MERGE_HEAD side's `--no-renames` was ever exercised, and the one
    variant removed both flags at once (agent/rv-pr86, N2). This file is byte-identical in both parents, so
    with rename detection on the HEAD side the source path vanishes from THAT diff and the intersection is
    just the destination, inside touches:. One variant per flag, below, so each occurrence is pinned alone.
    """
    git(repo, "merge", "--no-commit", "--no-ff", "main", check=False)
    git(repo, "mv", "other/d.txt", "allowed/d.txt", check=False)
    return git(repo, "commit", "-m", "merge main and relocate an untouched file into touches", check=False)


CASES = [
    ("1/merge-brings-other-side   must COMMIT", case_merge_clean, True, None),
    # The narrowing announces itself, and case 2 is where it has exactly one path to announce. Without this
    # phrase the case passes on a hook that skipped the check entirely - the naive fix case 3 exists for.
    ("2/resolution-inside-touches must COMMIT", case_resolution_inside, True,
     "checking touches: against the 1 path(s) that differ from both parents"),
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
    # Two phrases: the refusal itself, AND the operator message. The fallback is invisible without it -
    # an author whose commit was checked against the wide set instead of the narrow one has to be told why.
    ("8/empty-MERGE_HEAD          must REFUSE", case_empty_merge_head, False,
     ("other/b.txt is outside T-9999 touches",
      "checking touches: against the FULL staged set instead")),
    ("9/linked-worktree-resolve   must COMMIT", case_merge_inside_linked_worktree, True, None),
    ("10/linked-worktree-outside  must REFUSE", case_linked_worktree_resolution_outside, False,
     "other/b.txt is outside T-9999 touches"),
    ("11/rename-untouched-file    must REFUSE", case_rename_of_an_untouched_file, False,
     "other/d.txt is outside T-9999 touches"),
]


def variant_without(marker: str, replacement: str, tmp: pathlib.Path) -> pathlib.Path:
    """A copy of the real hook with one thing removed, written where the cases can point at it."""
    text = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
    if marker not in text:
        raise RuntimeError("variant marker not present in the hook: %r" % marker)
    out = tmp / "variant-hook"
    out.write_text(text.replace(marker, replacement), encoding="utf-8", newline="\n")
    return out


# (label, what to remove, its replacement, the SET of cases that must break - and no others). That is the
# whole rule, and it is the rule `run_variants` enforces; nothing here requires two variants to target
# different cases, and two of them legitimately target case 8 (one removes the fallback, one removes its
# message). An earlier version of this comment said "each variant must fail a DIFFERENT case" and
# "the seven" - a rule the code never had and a count two rounds stale, in the task filed to remove exactly
# that (agent/rv-pr86, BLOCKING 1). Generated from the real hook at run time and tracked here, because a
# demonstration in a gitignored scratch directory ships nowhere and cannot be re-run.
VARIANTS = [
    # One entry per OCCURRENCE of --no-renames. The single "without --no-renames" variant removed both and
    # could not tell which side a case was watching; case 5 sees only the MERGE_HEAD side, case 11 only HEAD.
    ("without --no-renames on the HEAD side", "--no-renames HEAD |", "HEAD |", {"11"}),
    ("without --no-renames on the MERGE_HEAD side", "--no-renames MERGE_HEAD |", "MERGE_HEAD |", {"5", "11"}),
    # T-0137. The fallback itself, removed: the error path computes an empty set instead of the wide one,
    # which is the fail-open exactly as it shipped. Only case 8 enters that path.
    ("without the error fallback", '    to_check="$staged"\n  else', '    to_check=""\n  else', {"8"}),
    # The `--git-dir` lookup, "simplified" to the literal every plain checkout has. `.git` is a FILE in a
    # linked worktree, so the narrowing never applies there and a real merge is refused - which only case 9
    # can see, because it is the only case that must COMMIT in that environment.
    ('literal ".git/MERGE_HEAD"', '"$(git rev-parse --git-dir)/MERGE_HEAD"', '".git/MERGE_HEAD"', {"9"}),
    # T-0139. The operator message the fallback prints was advertised in a PR and asserted by nothing:
    # deleting the echo left all ten cases green. Case 8 reads it now, so it cannot quietly stop existing.
    # The marker is the phrase itself rather than the whole echo, because the statement spans a line
    # continuation and a marker carrying one is a marker nobody can keep correct.
    ("without the fallback message", "checking touches: against the FULL staged set instead", "", {"8"}),
    # N5: case 2's narrowing-line assertion was never shown red. This is the variant that shows it.
    ("without the narrowing message", "pre-commit: merge in progress; checking touches: against the",
     "pre-commit: merge in progress; touches narrowed to", {"2"}),
]


def case_verdict(name, fn, must_commit, must_say, hook_override=None):
    """Run one case. Returns (ok, lines_to_print).

    THE ONE PLACE A CASE IS JUDGED, and it exists because there were two (T-0139). `run_variants` had its
    own weaker rule - it compared only the exit code - so a variant that silenced an asserted MESSAGE broke
    nothing in its eyes while breaking a case in `main`'s. A variant sweep whose idea of "broken" is
    narrower than the suite's reports a guard as unpinned when it is pinned, or worse, blesses a marker that
    no longer discriminates. Both callers now ask the same question and get the same answer.
    """
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="touches-merge-"))
    try:
        repo = build(tmp, hook_override=hook_override)
        code, out = fn(repo)
        # 99 is a case reporting that its own SETUP did not happen. A case whose premise silently fails
        # still produces an exit code, and case 6 passed that way until a probe showed the file it
        # claimed to delete was never deleted.
        if code == 99:
            return None, ["SETUP   %s  %s" % (name, out)]
        committed = code == 0
        # A refusal must be for the RIGHT REASON. Asserting only on the exit code lets a hook that refuses
        # everything - or one that dies on a syntax error - pass every negative case, which is how case 5's
        # defect stayed invisible. Checked in BOTH directions since T-0139, and `must_say` may be several
        # phrases: what the hook SAYS is part of what it does, and the fallback's operator message was
        # advertised in a PR while nothing would have noticed it disappearing.
        missing = [s for s in ((must_say,) if isinstance(must_say, str) else (must_say or ()))
                   if s not in out]
        if missing:
            lines = ["FAIL    %s  %s, but never said what it should"
                     % (name, "committed" if committed else "refused")]
            lines += ["            expected to see: %s" % s for s in missing]
            lines += ["            %s" % l for l in out.strip().splitlines()[:3]]
            return False, lines
        if committed == must_commit:
            return True, ["ok      %s" % name]
        return False, (["FAIL    %s  (exit %d)" % (name, code)]
                       + ["            %s" % l for l in out.strip().splitlines()[:4]])
    except Exception as e:                                        # noqa: BLE001
        return False, ["ERROR   %s  %s: %s" % (name, type(e).__name__, e)]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_variants() -> int:
    ok = True
    for label, marker, replacement, must_fail in VARIANTS:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="touches-variant-"))
        try:
            hook = variant_without(marker, replacement, tmp)
            failed, setup_failed = set(), []
            for name, fn, must_commit, must_say in CASES:
                ok_case, _lines = case_verdict(name, fn, must_commit, must_say, hook_override=hook)
                if ok_case is None:
                    # A case whose SETUP died ran nothing, and a sweep that counts it as "not broken" is
                    # judging over fewer cases than it prints (agent/rv-pr86, N3). Fatal, not neutral.
                    setup_failed.append(name.split("/")[0])
                elif ok_case is False:
                    failed.add(name.split("/")[0])
            if setup_failed:
                ok = False
                sys.stdout.write("FAIL    variant %-44s case setup died for %s; nothing was judged\n"
                                 % (label, ",".join(setup_failed)))
            elif failed == must_fail:
                sys.stdout.write("ok      variant %-44s breaks exactly %s\n"
                                 % (label, ",".join(sorted(must_fail, key=int))))
            else:
                ok = False
                sys.stdout.write("FAIL    variant %-44s expected %s to break, got %s\n"
                                 % (label, ",".join(sorted(must_fail, key=int)),
                                    ",".join(sorted(failed, key=int)) or "nothing"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    sys.stdout.write("\nTOUCHES-MERGE VARIANTS %s (%d)\n" % ("OK" if ok else "FAIL", len(VARIANTS)))
    return 0 if ok else 1


# The populations this file is allowed to shrink to: EQUAL, not "at least", and stated here rather than
# implied by whatever the lists happen to hold (T-0139).
#
# `TOUCHES-MERGE OK (0 cases)` and `TOUCHES-MERGE VARIANTS OK (0)` were both reachable - emptying either
# list printed OK and exited 0, and P-GIT-02 reads only the exit code, so the pin stayed green over a
# fixture measuring nothing. This file's own case-8 docstring cites "the mutation harnesses refuse on an
# empty population" as the standard everything here is held to; it was not holding itself to it. Inherited
# from PR #78 and found by agent/rv-pr84 while passing PR #84.
#
# EQUAL is the load-bearing word. A floor of "at least" lets cases be deleted one at a time down to the
# floor with a clean sheet printed each time, which is exactly how MIN_MUTATIONS failed in ops/mutate.
# Adding a case means changing this number, on purpose, in the same commit.
MIN_CASES = 11
MIN_VARIANTS = 6


def _population_ok() -> bool:
    ok = True
    if len(CASES) != MIN_CASES:
        sys.stdout.write("TOUCHES-MERGE REFUSING: %d cases defined, MIN_CASES says %d. A case list that "
                         "does not match its own floor cannot be trusted to have run anything.\n"
                         % (len(CASES), MIN_CASES))
        ok = False
    if len(VARIANTS) != MIN_VARIANTS:
        sys.stdout.write("TOUCHES-MERGE REFUSING: %d variants defined, MIN_VARIANTS says %d.\n"
                         % (len(VARIANTS), MIN_VARIANTS))
        ok = False
    # Two cases carrying the same label (or the same builder) would report the full count over one fewer
    # distinct check.
    labels = [c[0] for c in CASES]
    builders = [c[1] for c in CASES]
    if len(set(labels)) != len(labels) or len(set(builders)) != len(builders):
        sys.stdout.write("TOUCHES-MERGE REFUSING: duplicate case labels or builders\n")
        ok = False
    edits = [(v[1], v[2]) for v in VARIANTS]
    if len(set(edits)) != len(edits):
        sys.stdout.write("TOUCHES-MERGE REFUSING: duplicate variant edits\n")
        ok = False
    # A variant whose replacement equals its marker changes nothing, and one expecting NO case to break
    # is satisfied by that; together they are a variant that proves nothing and counts as one. The sweep
    # blessed exactly that - ("decorative", "#!/", "#!/", set()) printed ok (agent/rv2-pr86, NB2).
    for v in VARIANTS:
        if v[1] == v[2] or not v[3]:
            sys.stdout.write("TOUCHES-MERGE REFUSING: variant %r changes nothing or expects nothing to break\n" % v[0])
            ok = False
    return ok


def main() -> int:
    if not HOOK.is_file():
        sys.stdout.write("TOUCHES-MERGE FAIL: %s not found\n" % HOOK)
        return 2
    if not _population_ok():
        return 2
    if "--variants" in sys.argv:
        return run_variants()

    ok = True
    for name, fn, must_commit, must_say in CASES:
        ok_case, lines = case_verdict(name, fn, must_commit, must_say)
        if ok_case is not True:
            ok = False
        for line in lines:
            sys.stdout.write(line + "\n")

    sys.stdout.write("\nTOUCHES-MERGE %s (%d cases)\n" % ("OK" if ok else "FAIL", len(CASES)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
