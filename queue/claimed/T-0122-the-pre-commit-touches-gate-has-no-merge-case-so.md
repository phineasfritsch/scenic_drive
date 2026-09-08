---
id: T-0122
title: the pre-commit touches gate has no merge case, so no task branch can merge main
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T16:55:41Z
lease_expires_at: 2026-09-08T18:55:41Z
worktree: .worktrees/T-0122
branch: task/T-0122
exclusive: []
touches: [.githooks/pre-commit, ops/lib/check-touches-merge.py, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "\"${PYTHON:-$(command -v python3 || command -v python)}\" ops/lib/check-touches-merge.py -> TOUCHES-MERGE OK (7 cases), exit 0"
  - "RED: --hook <pre-fix> fails cases 1 and 2; --hook <naive> fails case 3"
---
## Brief

**No task branch can merge `main`.** The pre-commit `touches:` gate has no case for a merge commit, so it
refuses every file the merge brings in.

Reproduced on `task/T-0097`, which needed `main` to resolve a real conflict:

    $ git merge origin/main          # one conflict, in ops/merge; resolved by hand
    $ git commit
    pre-commit: .githooks/pre-commit is outside T-0097 touches: [ops/merge ops/merge-selftest ]
    pre-commit: .github/workflows/linux-core.yml is outside T-0097 touches: [...]
    pre-commit: ops/agent-preflight is outside T-0097 touches: [...]
    ... 41 paths ...
    pre-commit: refusing commit

Every one of those is a file `main` changed and this branch did not touch. The author changed exactly one
file, `ops/merge`, which IS in `touches:`.

`.githooks/pre-commit:32-46` reads the staged path list and compares each entry against the task's
`touches:`. `git grep -n 'MERGE_HEAD' .githooks/` returns nothing: the hook cannot tell a merge from an
ordinary commit.

## Why this is worth a task rather than a `--no-verify`

**It is very likely the cause of the branch tower.** [[T-0113]] measured 31 open PRs, ten of them based on a
branch whose own PR had already merged, and a chain of task branches stacked on merged parents with no route
back to `main`. If merging `main` into a task branch is blocked by the hook, then the only way to get
current with `main` is to branch off another task branch - which is exactly the shape [[T-0113]] found and
could not explain.

It also blocks the honest resolution of a merge conflict. A conflict is where two branches disagree, and
resolving it is the moment the most careful work happens; a gate that refuses that commit pushes people to
`--no-verify`, which turns off the secret scan and the CRLF check as well.

## What the fix must and must not do

**Must not** simply skip the check when `MERGE_HEAD` exists. A merge commit legitimately carries the
author's own conflict resolutions - `ops/merge` in the case above - and those are exactly the changes
`touches:` should still govern. Skipping the whole check would make "merge main" a way to smuggle any file
into any branch.

**Must** check the paths the author actually changed. On a merge, that is the set of files differing from
BOTH parents: a file taken unmodified from either side is not the author's edit, and a file that differs
from both is a resolution the author wrote. `git diff-tree` against each parent, intersected.

Do:

1. Teach `.githooks/pre-commit` the merge case: when `MERGE_HEAD` exists, apply `touches:` to
   `staged ∩ (differs from HEAD) ∩ (differs from MERGE_HEAD)` rather than to every staged path.
2. **RED FIRST.** The reproduction above is the red run and it is already recorded: a resolved merge of
   `origin/main` into `task/T-0097` refused with 41 paths. After the fix the same merge must commit, and a
   merge that also modifies a file outside `touches:` must still be refused - both directions, because a
   gate that only ever passes is the defect this repository is built around.
3. A check under `ops/lib/` that exercises both directions on a constructed repository, so the property has
   a witness that is not a story in this Log.

**Note the ordering problem, and do not work around it.** Fixing the hook requires committing
`.githooks/pre-commit`, which this task declares in `touches:`, so this branch can be committed normally.
But `task/T-0097`'s merge stays blocked until this reaches `main`. Its resolved files are preserved at
`.worktrees/T-0097/.artifacts/resolution/` and the merge was aborted rather than forced, so nothing is lost
and nothing was smuggled past the gate.

## Log
- 2026-09-08T16:55:41Z claimed by agent/claude-opus-5; lease until 2026-09-08T18:55:41Z

## Log

    python ops/lib/check-touches-merge.py            TOUCHES-MERGE OK (4 cases)      exit 0
    bash -n .githooks/pre-commit                     syntax OK                       exit 0

### The fix

`.githooks/pre-commit` gains a merge case. On a merge it applies `touches:` to
`staged INTERSECT (differs from HEAD) INTERSECT (differs from MERGE_HEAD)` - the files that differ from BOTH
parents. A file identical to either side arrived from that side and is not an edit; a file differing from
both is a resolution the author wrote, and those are exactly what `touches:` should still govern.

The CRLF check and the secret scan above it keep reading the raw staged list on purpose: a secret arriving
from the other side of a merge is still a secret in this branch's history.

`git rev-parse --git-dir`, not `--show-toplevel` - the latter is banned in `ops/` and the hooks because from
WSL this checkout's `.git` file reads `gitdir: C:/...` which WSL's git cannot follow (T-0060, T-0093).

### RED, against two different wrong hooks, each failing a DIFFERENT case

`ops/lib/check-touches-merge.py --hook <path>` runs the four cases against a variant.

    hook                              1 merge   2 resolve-inside   3 resolve-outside   4 plain-outside
    origin/main (no merge case)       FAIL      FAIL               ok                  ok
    naive: skip on MERGE_HEAD         ok        ok                 FAIL                ok
    this branch                       ok        ok                 ok                  ok

**Case 3 is why the naive fix is not the fix.** Skipping the check whenever `MERGE_HEAD` exists passes three
of four cases and turns "merge main" into a way to stage any file into any branch - and nothing else in the
repository would notice. It is the obvious one-line change and it is wrong.

**Case 4 is the control.** A hook that had lost the touches check entirely passes 1, 2 and 3.

Each variant fails a different case, which is what makes the four discriminating rather than decorative.

### The variant builder had a defect of its own, and it is the kind that fakes a red

The first version sliced the hook on `src.index("fi\n", ...)` and cut at the INNER
`if [[ -n "$to_check" ]]` terminator, leaving a stray `fi`. The variant did not parse, so every case failed
with a bash syntax error - **which looks exactly like a successful red run** if you only read the verdict.
Rebuilt line-based, walking the block by nesting depth. Worth recording: a red for the wrong reason is
worse than a green, because it is evidence that will be cited later.

### What this unblocks

`task/T-0097` needs `main` to resolve a genuine semantic conflict in `ops/merge` (two fixes that compose;
taking either side drops the other). That merge was aborted rather than forced past the gate, and its
resolved files are preserved at `.worktrees/T-0097/.artifacts/resolution/`. It can be redone once this
reaches `main`.

More broadly, [[T-0113]] found ten open PRs based on a branch whose own PR had already merged, and could not
explain how the tower formed. This is a mechanism that would produce exactly that shape.

---

## Fix pass: a reviewer defeated the gate outright

### F1 (BLOCKING) - rename detection let a branch relocate any file into its own touches:

    git merge --no-commit --no-ff main
    git mv other/b.txt allowed/b.txt      # touches: [allowed/]
    git commit                            # exit 0, two parents

`git diff --name-only` has rename detection ON by default and prints only the DESTINATION of a rename. So
`other/b.txt` never appeared on the `MERGE_HEAD` side, dropped out of the intersection, and was never
checked - **the intersection was omitting a path that genuinely differs from both parents, which is exactly
the rule this hook claims to implement.**

The effect is a full bypass: a task branch could move ANY file in the repository into its own `touches:`
prefix inside a merge commit and then own it. A delete-plus-add variant committed too.

Fixed with `--no-renames` on both diffs, which the reviewer had already verified closes it. Case 5 in the
fixture is that exact attack, and it now refuses.

The reviewer scoped it honestly rather than maximally: the same `git mv` is allowed on an ORDINARY commit
too, because `staged` is built with `--diff-filter=ACMR` which drops the `D` side. So the defect is
pre-existing *in kind* and this PR did not invent it - but it is the rule the PR claims to implement, so it
is this PR's to close.

### The fixture asserted only on exit code, which is how F1 stayed invisible

A hook that refuses everything - or one that dies on a syntax error - passed every negative case. Each
refusing case now names the reason it must give, and a refusal for a different reason is a FAIL. That is the
hazard the original Log documented for the *variant* path and did not close in the fixture itself.

Three cases added: the rename attack, a delete outside `touches:` during a merge, and a secret arriving
across a merge - the last because the Log claimed the secret scan still guards a merge and nothing asserted
it. It does; now it is pinned.

### F5 - my own comment asserted something false

*"A file identical to either side arrived from that side and is not an edit."* True in the `MERGE_HEAD`
direction. **False in the HEAD direction:** `git merge -X ours`, or resolving by keeping this branch's
version, produces a file identical to HEAD while silently discarding main's change to it. No rule over
staged paths can see that, because nothing was staged.

Uncatchable by this gate, so the fix is to state the limit. The comment now does, instead of asserting the
opposite.

### F3 - octopus merges, stated rather than discovered later

`git rev-parse MERGE_HEAD` silently resolves a multi-sha `MERGE_HEAD` to its FIRST parent, so files from
parents 2..n look like author edits. That fails CLOSED - the octopus merge is refused - and is left that way
deliberately, now written down.

### F4 - an asymmetry, named

`to_check` has no `--diff-filter` while `staged` has `ACMR`, so a delete outside `touches:` is refused
inside a merge and allowed outside it. Refusing is the safe direction; case 6 pins it so the behaviour is
deliberate rather than incidental.

### F2 - not fixed here, filed instead

The CRLF check in the same hook **never fires on this checkout**: MSYS2 grep strips `\r` in text mode, so
`grep -qI` cannot match a carriage return that is genuinely in the blob. Pre-existing, a different layer,
and it deserves its own red demonstration - filed as T-0125 rather than folded in.

### What held under attack

The reviewer ran sixteen attacks. These survived unchanged: a genuine octopus merge; a new file
byte-identical to main's version of another path; a plain delete outside `touches:` inside a merge; an
exec-bit flip outside `touches:`; `--amend` onto a finished merge commit; a hand-written `MERGE_HEAD` with
no merge in progress; and a secret arriving from the other side of a merge.

### And their method note is worth keeping

Their first CRLF verdict was a false green - it matched the word "CRLF" in the commit MESSAGE. They caught
it, rewrote the probe binary-safe, and the result reversed. Their words: *"That is the same signature defect
I was sent to hunt, in my own harness."*

## CI fix: the pin's own assertion could not run on the Linux runner

P-GIT-02 shipped with `assertion: "python ops/lib/check-touches-merge.py"`. PR #78's `core` check went red:

    PINS ok=12 skipped=0 pending=2 expired=0 failed=1 tier=linux
     - P-GIT-02: ...
           assertion: python ops/lib/check-touches-merge.py
           output: bash: line 1: python: command not found

The runner installs `python3` (`.github/workflows/linux-core.yml:48`) and Debian ships no `python` alias, so
the pin could never have passed there. The pin was green on the authoring box only because Windows has a bare
`python` on PATH - the check was passing for a reason that had nothing to do with the property it asserts.

This repo already has one way to name an interpreter, used at 17 call sites
(`ops/check-pins:2`, `ops/claim`, `ops/lock`, `ops/new-task`, `ops/queue-*`, `ops/merge:23`, `ops/sane:17`,
`ops/test:15`, `ops/prod-read:10`, `ops/lib/check-*`):

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/x.py

`ops/lib/check-exec-bits:37-42` is explicit that this is the contract, and that it is *why* `ops/lib/*.py`
stays 100644: every call site passes the script as an argument to an interpreter, never `./ops/lib/x.py`.
So the fix is the shim, not `chmod +x` and not a hardcoded `python3` - hardcoding `python3` would break the
Windows box, where `python3` resolves to the App Execution Alias stub that `ops/test:47` documents.
`pins.py:86` runs assertions through `bash -o pipefail -c`, and does not export `PYTHON`, so the `${PYTHON:-...}`
default has to live in the assertion itself.

### RED then GREEN, against a PATH shaped like the runner's

A shim directory holding a real `python3` only, then `PATH=<shim>:/usr/bin:/mingw64/bin`, `PYTHON` unset:

    command -v python  -> []            (exit 1)
    command -v python3 -> <shim>        Python 3.10.11

    RED   (old assertion)  bash: line 1: python: command not found          exit 127
    GREEN (new assertion)  TOUCHES-MERGE OK (7 cases)                       exit 0

RED reproduces the CI output byte for byte. GREEN was run through `pins.load` + `pins.run` rather than by
hand, so it exercises the same code path CI does.

### One false red, worth recording

The first GREEN attempt reported `TOUCHES-MERGE FAIL (stubbed by reviewer)`. That was not this fix: a
reviewer's red-demo (`.artifacts/rvw2/pinred.sh:9`) overwrites `ops/lib/check-touches-merge.py` with a
failing stub and restores it at line 16, and it was running in this worktree at the same moment. The probe
now hashes the subject against `HEAD:` before and after the run and aborts if they differ. Both matched on
the recorded run. Note that the reviewer's own `pinred.out` already shows the fixed assertion resolving an
interpreter and executing the stub - the failure it captured is the stub's, not a `command not found`.

Staging explicit paths is what kept that stub out of this commit.

