#!/usr/bin/env python3
"""Prove the pre-commit hook refuses a commit whose staged content is not what is on disk.

T-0047 built this check and reviewer-28 hardened it; PR #30 was merged into the STACKED branch
task/T-0039 a day after that branch had already landed on main, so the child never followed and none of it
reached main. T-0160 re-lands it on the hook as it exists now (rewritten since by T-0137, T-0139, T-0140)
and adds the second half the same review found: the touches: gate read the WORKING-TREE task file, so an
unstaged widening of touches: let a forbidden path land.

The defect, live on main until this lands, is the shape six agents shipped in one session:

    git mv queue/review/T-9990-x.md queue/done/T-9990-x.md   # stages the rename against the PRE-edit blob
    # rewrite the file: state: done, append the verdict
    git commit                                               # exit 0, "1 file changed, 0 insertions(+)"

`git status` shows a clean rename and says nothing is wrong. `git show HEAD:queue/done/T-9990-x.md` still
reads `state: review`: the verdict and the whole review log are absent from the commit.

Fourteen cases, each on a throwaway repo with the real hook installed. Eight of them are red on the hook at
origin/main (1, 2, 4, 5, 6, 8, 10, 13); the other six are the false-positive controls - a check that
refuses a legitimate commit is worse than the bug, so each of them must COMMIT (or refuse for a reason that
is not this check) on both hooks:

  1. `git mv` then edit, never re-added                   must REFUSE, naming the path and the git add
  2. staged, then deleted from disk                       must REFUSE, and say so DISTINCTLY
  3. a fully staged commit                                must COMMIT, and land the edit
  4. ALLOW_PARTIAL_STAGE=1 over a stale path              must COMMIT and SAY SO ON STDERR
  5. ALLOW_PARTIAL_STAGE=yes (not the value 1)            must REFUSE - the waiver is one exact value
  6. touches: widened in the working tree only            must REFUSE the out-of-touches path
  7. touches: widened AND staged                          must COMMIT (the control for 6: a gate that only
                                                          ever read HEAD would pass 6 and fail this)
  8. a non-ASCII path, fully staged                       must COMMIT (`--name-only` without -z C-quotes it
                                                          and T-0140's fail-closed branch then refuses it)
  9. a merge that only brings in the other side's files   must COMMIT
 10. a merge, then a merged file edited and not re-added  must REFUSE - check 4 reads the FULL staged set,
                                                          not the merge-narrowed set touches: uses; the case
                                                          asserts its own premise, that the path is absent
                                                          from the MERGE_HEAD diff and so would be invisible
                                                          to a narrowed check
 11. an empty commit                                      must COMMIT
 12. a pure rename with no content edit                   must COMMIT - 0 insertions is not itself the bug
 13. a task file on disk, in neither the index nor HEAD   must REFUSE - "could not read the touches: being
                                                          committed" must never read as "nothing to check"
 14. the task file removed from the index but in HEAD     must REFUSE the out-of-touches path - the HEAD
                                                          fallback, which nothing else exercises

EVERY REFUSING CASE NAMES THE REASON IT MUST GIVE, and the two must-COMMIT cases that can, assert what
landed. Asserting only on the exit code lets a hook that refuses everything - or one that dies on a syntax
error - pass every negative case.

EVERY CASE ASSERTS ITS OWN PREMISE and returns 99 when it does not hold, because a case whose setup
silently failed still produces an exit code: `git mv` not moving, a platform that does not C-quote, a merge
that staged nothing. check-touches-merge.py's case 6 passed that way for a while.

`--hook <path>` points the cases at another hook - that is how this is run red:

    git show origin/main:.githooks/pre-commit > /tmp/main-hook
    python ops/lib/check-stale-stage.py --hook /tmp/main-hook
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
for _i, _a in enumerate(sys.argv):
    if _a == "--hook" and _i + 1 < len(sys.argv):
        HOOK = pathlib.Path(sys.argv[_i + 1]).resolve()

# EQUAL to the case count, not a floor. `STALE-STAGE OK (0 cases)` must not be reachable by deleting the
# list, and "at least" lets cases be removed one at a time with a clean sheet printed each time.
EXPECTED_CASES = 14

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
WIDE_TASK = TASK.replace("touches: [allowed/]", "touches: [allowed/, other/]")
REVIEW_FILE = "---\nid: T-9990\nstate: review\n---\n## Log\n- opened\n"
DONE_FILE = "---\nid: T-9990\nstate: done\n---\n## Log\n- opened\n- PASS, signed off\n"


def git(repo, *args, env=None):
    p = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env=None if env is None else {**os.environ, **env})
    return p.returncode, p.stdout + p.stderr


def git_split(repo, *args, env=None):
    p = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env=None if env is None else {**os.environ, **env})
    return p.returncode, p.stdout, p.stderr


def write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


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

    write(repo / "allowed" / "a.txt", "base\n")
    write(repo / "other" / "b.txt", "base\n")
    write(repo / "queue" / "review" / "T-9990-x.md", REVIEW_FILE)
    write(repo / "queue" / "claimed" / "T-9999-probe.md", TASK)
    (repo / "queue" / "done").mkdir(parents=True, exist_ok=True)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base", "--no-verify")

    git(repo, "checkout", "-q", "-b", "task/T-9999")
    git(repo, "checkout", "-q", "main")
    write(repo / "other" / "b.txt", "from main\n")
    write(repo / "other" / "c.txt", "new on main\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "main moves on", "--no-verify")
    git(repo, "checkout", "-q", "task/T-9999")
    write(repo / "allowed" / "a.txt", "from branch\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "branch work", "--no-verify")
    return repo


def case_git_mv_then_edit(repo):
    """1. The Brief's exact sequence. Must be REFUSED, naming the path."""
    rc, out = git(repo, "mv", "queue/review/T-9990-x.md", "queue/done/T-9990-x.md")
    if rc != 0:
        return 99, "git mv failed: %s" % out.strip()[:200]
    write(repo / "queue" / "done" / "T-9990-x.md", DONE_FILE)
    rc, blob = git(repo, "show", ":queue/done/T-9990-x.md")
    if rc != 0 or "state: done" in blob:
        return 99, "the staged blob already carries the edit, so this case would test nothing"
    return git(repo, "commit", "-m", "T-9990 review complete, mark done")


def case_staged_then_deleted(repo):
    """2. Staged content that no longer exists on disk. Must be REFUSED, distinctly."""
    write(repo / "allowed" / "gone.txt", "staged, then removed\n")
    git(repo, "add", "allowed/gone.txt")
    (repo / "allowed" / "gone.txt").unlink()
    if (repo / "allowed" / "gone.txt").exists():
        return 99, "the file is still on disk, so this case would test nothing"
    return git(repo, "commit", "-m", "add a file that is no longer on disk")


def case_fully_staged(repo):
    """3. The ordinary commit. Must COMMIT, and the edit must land."""
    write(repo / "allowed" / "a.txt", "fully staged edit\n")
    git(repo, "add", "allowed/a.txt")
    rc, out = git(repo, "commit", "-m", "an ordinary, fully staged commit")
    if rc == 0:
        _, landed = git(repo, "show", "HEAD:allowed/a.txt")
        if "fully staged edit" not in landed:
            return 99, "the commit succeeded but did not carry the edit"
    return rc, out


def case_waiver_one(repo):
    """4. A deliberate partial stage. Must COMMIT and say so ON STDERR - judged on stderr alone."""
    write(repo / "allowed" / "a.txt", "the staged version\n")
    git(repo, "add", "allowed/a.txt")
    write(repo / "allowed" / "a.txt", "a further edit, deliberately not staged\n")
    rc, out, err = git_split(repo, "commit", "-m", "deliberate partial stage",
                             env={"ALLOW_PARTIAL_STAGE": "1"})
    if rc == 0:
        _, landed = git(repo, "show", "HEAD:allowed/a.txt")
        if "the staged version" not in landed:
            return 99, "the waived commit did not land the staged version: %r" % landed[:80]
    return rc, err


def case_waiver_not_one(repo):
    """5. ALLOW_PARTIAL_STAGE=yes is not the waiver. Must be REFUSED."""
    write(repo / "allowed" / "a.txt", "the staged version\n")
    git(repo, "add", "allowed/a.txt")
    write(repo / "allowed" / "a.txt", "a further edit, deliberately not staged\n")
    return git(repo, "commit", "-m", "partial stage with a value that is not 1",
               env={"ALLOW_PARTIAL_STAGE": "yes"})


def case_unstaged_widening(repo):
    """6. touches: widened in the working tree only. Must REFUSE the out-of-touches path."""
    write(repo / "queue" / "claimed" / "T-9999-probe.md", WIDE_TASK)
    write(repo / "other" / "b.txt", "the branch takes this file over\n")
    git(repo, "add", "other/b.txt")
    rc, blob = git(repo, "show", ":queue/claimed/T-9999-probe.md")
    if rc != 0 or "other/" in blob:
        return 99, "the staged task file already carries the widening, so this case would test nothing"
    return git(repo, "commit", "-m", "widen touches: without staging it")


def case_staged_widening(repo):
    """7. The control for 6: a widening that IS staged must be honoured. Must COMMIT."""
    write(repo / "queue" / "claimed" / "T-9999-probe.md", WIDE_TASK)
    write(repo / "other" / "b.txt", "the branch takes this file over\n")
    git(repo, "add", "other/b.txt", "queue/claimed/T-9999-probe.md")
    rc, blob = git(repo, "show", ":queue/claimed/T-9999-probe.md")
    if rc != 0 or "other/" not in blob:
        return 99, "the widening did not reach the index, so this case would test nothing"
    return git(repo, "commit", "-m", "widen touches: and stage it")


def case_non_ascii_path(repo):
    """8. A non-ASCII path, fully staged. Must COMMIT."""
    write(repo / "allowed" / "café-note.txt", "ordinary content\n")
    git(repo, "add", "allowed/café-note.txt")
    rc, quoted = git(repo, "diff", "--cached", "--name-only")
    if rc != 0 or "caf\\303" not in quoted:
        return 99, "git does not C-quote this path here (%r), so this case would test nothing" % quoted.strip()
    return git(repo, "commit", "-m", "add a file with a non-ASCII name")


def case_merge_brings_other_side(repo):
    """9. A merge that only brings in the other side's files. Must COMMIT."""
    git(repo, "merge", "--no-commit", "--no-ff", "main")
    rc, staged = git(repo, "diff", "--cached", "--name-only", "HEAD")
    if rc != 0 or "other/b.txt" not in staged:
        return 99, "the merge staged nothing from the other side (%r)" % staged.strip()[:120]
    return git(repo, "commit", "-m", "merge main")


def case_merge_then_stale_edit(repo):
    """10. A merged file edited after the merge staged it, never re-added. Must be REFUSED.

    The premise is the point: `other/b.txt` is in the staged set but NOT in the diff against MERGE_HEAD, so
    it drops out of the intersection the touches: gate narrows to. A check 4 that reused that narrowed set
    would not look at it, and this commit would land content the author is not looking at.
    """
    git(repo, "merge", "--no-commit", "--no-ff", "main")
    write(repo / "other" / "b.txt", "edited during the merge, never re-added\n")
    rc, mh = git(repo, "diff", "--cached", "--name-only", "--no-renames", "MERGE_HEAD")
    if rc != 0 or "other/b.txt" in mh:
        return 99, "other/b.txt differs from MERGE_HEAD, so this case no longer proves check 4 reads the full staged set"
    return git(repo, "commit", "-m", "merge main, then edit a merged file without re-adding")


def case_empty_commit(repo):
    """11. An empty commit. Must COMMIT."""
    rc, staged = git(repo, "diff", "--cached", "--name-only")
    if rc != 0 or staged.strip():
        return 99, "something is staged, so this is not an empty commit"
    return git(repo, "commit", "--allow-empty", "-m", "an empty commit")


def case_pure_rename(repo):
    """12. A rename with no content edit. Must COMMIT - 0 insertions is not itself the defect."""
    rc, out = git(repo, "mv", "allowed/a.txt", "allowed/renamed.txt")
    if rc != 0:
        return 99, "git mv failed: %s" % out.strip()[:200]
    rc, status = git(repo, "status", "--short")
    if rc != 0 or not status.lstrip().startswith("R"):
        return 99, "the rename is not staged as a rename (%r)" % status.strip()[:120]
    return git(repo, "commit", "-m", "a pure rename")


def case_task_file_untracked(repo):
    """13. A task file that exists only on disk. Must be REFUSED.

    On a branch whose task file was never committed, the gate cannot read the touches: that is being
    committed. It refuses instead of switching itself off - the path staged here is INSIDE the touches: on
    disk, so a hook that reads the working tree commits it and a hook that reads nothing commits it too.
    """
    git(repo, "checkout", "-q", "-b", "task/T-9988")
    write(repo / "queue" / "claimed" / "T-9988-probe.md", TASK.replace("T-9999", "T-9988"))
    write(repo / "allowed" / "a.txt", "inside touches: on disk\n")
    git(repo, "add", "allowed/a.txt")
    rc, tracked = git(repo, "ls-files", "--", "queue/claimed/T-9988-probe.md")
    if rc != 0 or tracked.strip():
        return 99, "the task file is tracked, so this case would test nothing"
    if not (repo / "queue" / "claimed" / "T-9988-probe.md").is_file():
        return 99, "the task file is not on disk, so the gate would not find it at all"
    return git(repo, "commit", "-m", "commit on a branch whose task file was never staged")


def case_task_file_head_fallback(repo):
    """14. The task file removed from the index but present in HEAD. Must REFUSE the outside path."""
    rc, out = git(repo, "rm", "-q", "--cached", "queue/claimed/T-9999-probe.md")
    if rc != 0:
        return 99, "git rm --cached failed: %s" % out.strip()[:200]
    rc, _ = git(repo, "show", ":queue/claimed/T-9999-probe.md")
    if rc == 0:
        return 99, "the task file is still in the index, so the HEAD fallback would not be exercised"
    write(repo / "other" / "b.txt", "outside touches\n")
    git(repo, "add", "other/b.txt")
    return git(repo, "commit", "-m", "commit with the task file only in HEAD")


STALE_SAYS = ("staged content in queue/done/T-9990-x.md is stale",
              'git add -- "queue/done/T-9990-x.md"')
CASES = [
    ("1/git-mv-then-edit          must REFUSE", case_git_mv_then_edit, False, STALE_SAYS),
    ("2/staged-then-deleted       must REFUSE", case_staged_then_deleted, False,
     "allowed/gone.txt is staged but missing from the working tree"),
    ("3/fully-staged              must COMMIT", case_fully_staged, True, None),
    ("4/ALLOW_PARTIAL_STAGE=1     must COMMIT", case_waiver_one, True,
     "ALLOW_PARTIAL_STAGE=1 waives the stale-content check for: allowed/a.txt"),
    ("5/ALLOW_PARTIAL_STAGE=yes   must REFUSE", case_waiver_not_one, False,
     ("is not the value 1", "staged content in allowed/a.txt is stale")),
    ("6/unstaged-widening         must REFUSE", case_unstaged_widening, False,
     "other/b.txt is outside T-9999 touches"),
    ("7/staged-widening           must COMMIT", case_staged_widening, True, None),
    ("8/non-ASCII-path            must COMMIT", case_non_ascii_path, True, None),
    ("9/merge-brings-other-side   must COMMIT", case_merge_brings_other_side, True, None),
    ("10/merge-then-stale-edit    must REFUSE", case_merge_then_stale_edit, False,
     "staged content in other/b.txt is stale"),
    ("11/empty-commit             must COMMIT", case_empty_commit, True, None),
    ("12/pure-rename              must COMMIT", case_pure_rename, True, None),
    ("13/task-file-untracked      must REFUSE", case_task_file_untracked, False,
     "cannot read the touches: that is being committed"),
    ("14/task-file-HEAD-fallback  must REFUSE", case_task_file_head_fallback, False,
     "other/b.txt is outside T-9999 touches"),
]


def case_verdict(name, fn, must_commit, must_say):
    """The one place a case is judged. Both callers must ask the same question (T-0139)."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="stale-stage-"))
    try:
        repo = build(tmp)
        code, out = fn(repo)
        if code == 99:
            return None, ["SETUP   %s  %s" % (name, out)]
        committed = code == 0
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
        return False, (["FAIL    %s  %s (exit %d)"
                        % (name, "COMMITTED - failed open" if committed else "refused", code)]
                       + ["            %s" % l for l in out.strip().splitlines()[:4]])
    except Exception as e:                                        # noqa: BLE001
        return False, ["ERROR   %s  %s: %s" % (name, type(e).__name__, e)]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _population_ok() -> bool:
    ok = True
    if len(CASES) != EXPECTED_CASES:
        sys.stdout.write("STALE-STAGE REFUSING: %d cases defined, EXPECTED_CASES says %d. A case list that "
                         "does not match its own count cannot be trusted to have run anything.\n"
                         % (len(CASES), EXPECTED_CASES))
        ok = False
    labels = [c[0] for c in CASES]
    builders = [c[1] for c in CASES]
    if len(set(labels)) != len(labels) or len(set(builders)) != len(builders):
        sys.stdout.write("STALE-STAGE REFUSING: duplicate case labels or builders\n")
        ok = False
    return ok


def main() -> int:
    if not HOOK.is_file():
        sys.stdout.write("STALE-STAGE FAIL: %s not found\n" % HOOK)
        return 2
    if not _population_ok():
        return 2
    ok = True
    for name, fn, must_commit, must_say in CASES:
        ok_case, lines = case_verdict(name, fn, must_commit, must_say)
        if ok_case is not True:
            ok = False
        for line in lines:
            sys.stdout.write(line + "\n")
    sys.stdout.write("\nSTALE-STAGE %s (%d cases, hook %s)\n"
                     % ("OK" if ok else "FAIL", len(CASES), HOOK.name))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
