---
id: T-0137
title: "pre-commit checks nothing when a git command errors: an empty MERGE_HEAD disables the touches gate"
state: done
owner: agent/claude-opus-5
owner_session: 012vL7Yk1ov7eNxoFD9U6Pfm
claimed_at: 2026-09-16T02:45:00Z
lease_expires_at: 2026-09-16T06:45:00Z
worktree: .worktrees/T-0137
branch: task/T-0137
exclusive: []
touches: [.githooks/pre-commit, ops/lib/check-touches-merge.py]
pins_affected: [P-GIT-01, P-GIT-02]
reviewer: agent/rv-pr84
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python ops/lib/check-touches-merge.py -> TOUCHES-MERGE OK (10 cases), exit 0"
  - "python ops/lib/check-touches-merge.py --variants -> TOUCHES-MERGE VARIANTS OK (3), each breaking exactly one case: --no-renames->5, error fallback->8, literal .git/MERGE_HEAD->9, exit 0"
  - "RED: git show 43f4f6f:.githooks/pre-commit > .artifacts/prefix-hook (hash ffc8d05d7f7f7f986a1f3b763a302c6d94caf730 == git rev-parse 43f4f6f:.githooks/pre-commit); python ops/lib/check-touches-merge.py --hook .artifacts/prefix-hook -> FAIL 8/empty-MERGE_HEAD must REFUSE (exit 0), TOUCHES-MERGE FAIL (10 cases), exit 1"
  - "bash ops/check-pins -> PINS ok=14 skipped=0 pending=3 expired=0 failed=0 tier=linux, exit 0"
  - "bash ops/check-pins --source-only -> PINS ok=6 skipped=10 pending=1 expired=0 failed=0 tier=linux source-only, exit 0"
  - "bash ops/lib/check-line-cap -> P-SRC-02: 25 Swift files tracked, none over 300 lines, exit 0"
---
## Brief

Found by `agent/rv-keystone` while reviewing PR #78, which it passed. This is a **new fail-open introduced by
that PR's merge case**, reported as non-blocking with the reasoning recorded, and it was right that it should
not block the keystone - but it should not sit unfiled either, and the reviewer said so ("worth a follow-up
task; I did not file one", because a sign-off commits the task file alone).

`.githooks/pre-commit:76-78`. The merge case intersects two `git diff --cached` outputs to find the author's
own changes. If **both git calls fail**, their outputs are empty, the intersection is empty, and the `while`
loop iterates over nothing - so the gate checks nothing and the commit is allowed. An empty
`.git/MERGE_HEAD` is enough to produce that, and the commit that results is an **ordinary single-parent
commit**, not a merge:

```
printf 'x\n' >> other/b.txt && git add other/b.txt
: > "$(git rev-parse --git-dir)/MERGE_HEAD"
git commit -m whatever          # exit 0
git log -1 --pretty=%P          # ONE sha - not a merge
```

CONTROL, from the same reviewer: `main`'s pre-fix hook refuses the identical sequence with
`other/b.txt is outside T-9999 touches`, exit 1.

### Why it is worth fixing even though it needs a deliberate write into `.git/`

The shape is the one this repository keeps finding: **a check that silently passes when its own machinery
fails.** Everything else here has been hardened against exactly this - `ops/lib/check-exec-bits` refuses on an
empty file set, the mutation harnesses refuse on an empty population, `--prove-vacuity` requires MISSED to be
complete. The gate that runs on *every commit by every agent* should not be the one place where "the command
errored" reads as "nothing to check".

It is also invisible when it happens. There is no output, no warning, and the commit looks normal afterwards.

### Do

1. Make the merge case fail CLOSED: if either `git diff --cached` exits non-zero, fall back to checking the
   full staged set (`"$staged"`) rather than the intersection. A gate that cannot compute the narrower set
   must check the wider one.
2. **Demonstrate red then green**, with the reproduction above as the red case and a normal merge as the
   green one, so the fix does not re-break what PR #78 just unblocked.
3. Add the case to `ops/lib/check-touches-merge.py`, whose seven cases all build plain `git init` checkouts.

### Two related findings from the same review, recorded so they are not rediscovered

* **F-B, permissive by design.** The merge case trusts *any* merge parent, not `main`. A forbidden file
  committed on a branch whose name does not match `^task/(T-[0-9]+)` - where the gate does not apply at all,
  which is pre-existing - and then merged in, is byte-identical to `MERGE_HEAD`, drops out of the
  intersection, and is never checked. The reviewer weighed this non-blocking after measuring that
  `git cherry-pick` and `git rebase` **never run `pre-commit` at all**, so a forbidden file reaches a task
  branch today in fewer steps with the hook never firing. Tightening the exemption to a `MERGE_HEAD` that is
  an ancestor of `origin/main` would close the merge route. Worth doing *with* item 1, not instead of it.
* **F-E, coverage.** The fixture only builds plain `git init` checkouts, where `--git-dir` is `.git`. The hook
  is correct today inside a **linked worktree** - which is where every task in this fleet actually runs, and
  the reviewer verified it - but nothing pins that. A later "simplification" to a literal `.git/MERGE_HEAD`
  would leave all seven cases green and break every real merge. An eighth case using `git worktree add`
  anchors it.

## Log
- 2026-09-15T23:30:00Z filed by agent/claude-opus-5 from agent/rv-keystone's review of PR #78. That PR is
  merged: the merge case is on `main`, and task branches can take an update from `main` for the first time.
  This is the debt that came with it.
- 2026-09-16T03:10:00Z claimed by agent/claude-opus-5; lease until 2026-09-16T06:45:00Z. Worktree
  `.worktrees/T-0137`, branch `task/T-0137`, off `43f4f6f`.
- 2026-09-16T03:40:00Z **Item 1 fixed, and one thing this task asked for turned out to be the defect it
  warns about.** Both git calls now run into variables so their exit codes can be read - process
  substitution throws the status away, which is the whole reason the fail-open existed - and if either is
  non-zero the gate checks `$staged`, the FULL staged set, and says so on stdout.

  **RED, reproducible from git rather than from a scratch directory:**

      $ git show 43f4f6f:.githooks/pre-commit > .artifacts/prefix-hook
      $ git hash-object .artifacts/prefix-hook          -> ffc8d05d7f7f7f986a1f3b763a302c6d94caf730
      $ git rev-parse 43f4f6f:.githooks/pre-commit      -> ffc8d05d7f7f7f986a1f3b763a302c6d94caf730
      $ python ops/lib/check-touches-merge.py --hook .artifacts/prefix-hook
        FAIL    8/empty-MERGE_HEAD          must REFUSE  (exit 0)
                    [task/T-9999 3054c54] commit with an empty MERGE_HEAD
                    fatal: ambiguous argument 'MERGE_HEAD': unknown revision or path not in the working tree.
        TOUCHES-MERGE FAIL (10 cases)                                                            exit 1

  The `fatal:` line is the point: git said it could not do the thing, and the gate read that as nothing to
  check. GREEN after the fix: `TOUCHES-MERGE OK (10 cases)`, exit 0.

  **F-E (the worktree coverage gap) was going to ship as exactly the defect this repository keeps finding.**
  My first version of case 9 was *"the same merge inside a linked worktree, resolution OUTSIDE touches:,
  must REFUSE"*. It passed - against the pre-fix hook, against the fixed hook, and against a hook with the
  `--git-dir` lookup replaced by the literal `.git/MERGE_HEAD`. It could not fail. In a linked worktree
  `.git` is a FILE, so a literal `.git/MERGE_HEAD` finds no merge, the narrowing never applies, the hook
  checks the full staged set - and a REFUSE case passes for a reason that has nothing to do with what it
  claims to pin. Only the direction that DEPENDS on the narrowing can see it. So case 9 is now
  *"resolution INSIDE touches:, must COMMIT"* - the merge every task in this fleet actually makes, the one
  PR #36 needed - and case 10 keeps the REFUSE direction so the narrowing cannot become a blanket skip in
  the one environment cases 1-8 never enter. `_linked_worktree` returns 99 (setup-failed) if `.git` is a
  directory or `--git-dir` ends in `.git`, so the pair cannot silently degrade into two more plain-repo
  cases.

  **Each variant breaks exactly one case**, which is what makes ten cases discriminating rather than
  decorative. Generated from the real hook at run time:

      $ python ops/lib/check-touches-merge.py --variants
      ok      variant without --no-renames       breaks exactly 5/rename-into-touches
      ok      variant without the error fallback breaks exactly 8/empty-MERGE_HEAD
      ok      variant literal ".git/MERGE_HEAD"  breaks exactly 9/linked-worktree-resolve
      TOUCHES-MERGE VARIANTS OK (3)                                                               exit 0

  The second variant is the fail-open exactly as it shipped: the error path computing an empty set instead
  of the wide one. The third is the "simplification" F-E predicted, and case 9 is the only case that sees
  it.

  **VERIFICATION.** `bash ops/check-pins` -> `PINS ok=14 skipped=0 pending=3 expired=0 failed=0 tier=linux`,
  exit 0 (P-GIT-02 is this fixture). `bash ops/check-pins --source-only` -> `PINS ok=6 skipped=10 pending=1
  expired=0 failed=0 tier=linux source-only`, exit 0. `bash ops/lib/check-line-cap` -> `P-SRC-02: 25 Swift
  files tracked, none over 300 lines`, exit 0 - the 300-line cap is Swift-only and this fixture is 440
  lines, which is stated here rather than discovered by a reviewer.

  **F-B is NOT fixed, and the reason is a measurement, not an opinion.** Tightening the merge exemption to a
  `MERGE_HEAD` that is an ancestor of `origin/main` closes the route where a forbidden file committed on a
  non-`task/` branch is merged in and drops out of the intersection. But every case in this fixture builds
  a repo with no remote, so the rule would have to answer "what if `origin/main` does not resolve" - and
  both answers are bad in the shape this task is about: trusting the merge is the same fail-open one level
  up, and refusing it breaks cases 1, 2 and 9. Doing it properly means giving `build()` a real bare origin
  and adding a case for a merge parent that is NOT an ancestor of it. That is a second task, not a rider on
  this one, and the reviewer who found F-B already weighed it non-blocking after measuring that
  `git cherry-pick` and `git rebase` never run `pre-commit` at all - a forbidden file reaches a task branch
  today in fewer steps with the hook never firing. Filed as a follow-up rather than half-done here.
- 2026-09-16T05:10:00Z **review PASS** by `agent/rv-pr84` (reviewer != owner `agent/claude-opus-5`), on PR #84
  head `7db9428`. Measured in a throwaway worktree `.worktrees/rv-pr84` detached at that commit, after
  confirming `git rev-parse origin/task/T-0137` == `7db9428` and, for both subjects,
  `git hash-object` == `git rev-parse 7db9428:<path>`: hook `03b1ac2`, fixture `f6bbb81`. Modes as required -
  `.githooks/pre-commit` 100755, `ops/lib/check-touches-merge.py` 100644.

  **All six acceptance lines reproduced character for character, counts included**, exit codes read from the
  process and never from a grep: `TOUCHES-MERGE OK (10 cases)` exit 0; `TOUCHES-MERGE VARIANTS OK (3)` exit 0
  with the 5/8/9 mapping intact; the RED line with `git hash-object .artifacts/prefix-hook` and
  `git rev-parse 43f4f6f:.githooks/pre-commit` both `ffc8d05d7f7f7f986a1f3b763a302c6d94caf730`, producing
  `FAIL 8/empty-MERGE_HEAD` and only 8, `TOUCHES-MERGE FAIL (10 cases)` exit 1;
  `PINS ok=14 skipped=0 pending=3 expired=0 failed=0 tier=linux` exit 0; `PINS ok=6 skipped=10 pending=1
  expired=0 failed=0 tier=linux source-only` exit 0; `P-SRC-02: 25 Swift files tracked, none over 300 lines`
  exit 0. `bash ops/queue-check` -> `QUEUE OK (130 tasks)` exit 0.

  **RE-BROKEN BY HAND, red by NAME.** A hand revert of the fallback to the original process-substitution
  intersection (`.artifacts/hook-M1-revert-fallback`) -> `FAIL 8/empty-MERGE_HEAD` and nothing else. Keeping
  the `$?` reads but letting the error branch narrow anyway (M2) -> the same single red, which locates the
  fix in the *fallback*, not in the exit-code plumbing. The pre-fix hook from `git show 43f4f6f` fails case 8
  and ONLY case 8.

  **ATTACKS, each with a control.** Only ONE diff fails, not both: an instrumented copy of the shipped hook
  prints `PROBE head_rc=0 merge_rc=128` in the case-8 scenario, and a mutant that replaces `||` with `&&`
  turns case 8 red - so `||` is load-bearing and strictly more general than the prose. Dropping
  `set -o pipefail` also turns case 8 red, so `$?` really is the pipeline's status and case 8 pins it.
  `MERGE_HEAD` naming a valid non-parent: both diffs succeed, the resolution differs from both, REFUSED for
  the right reason. Octopus `MERGE_HEAD` (two hand-written shas): `git rev-parse MERGE_HEAD` resolves to the
  first, the diff succeeds, a file arriving from parent 2 reads as an author edit and is REFUSED - the
  comment's "fails CLOSED" claim is true, and identical on the pre-fix hook. A legitimately empty
  intersection still COMMITs (`head_rc=0 merge_rc=0`, no message, exit 0), so the fallback has not made
  case 1 stricter. The echo condition cannot hide a merge: `rc != 0` prints the fallback line, `rc == 0` with
  a non-empty intersection prints the narrowing line, and `rc == 0` with an empty one is silent exactly as
  before - the added `rc` guards prevent the fallback path from printing the pre-fix line, which would have
  claimed an intersection while checking the full staged set.

  **FIXTURE ATTACKS.** `git worktree add` sabotaged -> `SETUP 9/...` and `SETUP 10/...`, exit 1, not a pass.
  The linked worktree replaced by a plain clone -> both report `setup failed: .git is a directory, so this is
  not a linked worktree`, exit 1. `--hook` at a missing path -> exit 2, with and without `--variants`. A
  variant that breaks zero cases -> `expected only ... to break, got nothing`, exit 1. A stale variant marker
  -> `RuntimeError: variant marker not present in the hook`, exit 1. A hook that refuses everything -> every
  REFUSING case reports "refused, but not for the stated reason", so the reason assertions are real.

  **The owner's claim about his own first case 9 is true.** That first version is what shipped as case 10,
  and case 10 passes against the pre-fix hook, the fixed hook AND the literal `.git/MERGE_HEAD` variant - it
  could not discriminate. Case 9 as shipped is broken by the literal variant and by nothing else.

  **Record.** T-0138 exists on `main` in `queue/backlog/` and says what the PR says it says. The F-B
  deferral is honest and measured, not asserted: `build()` adds no remote, and a hook whose narrowing never
  applies turns cases 1, 2 and 9 red (5 and 6 too, on the reason assertion) - exactly the breakage the Log
  predicts. The fixture is 440 lines and `ops/lib/check-line-cap` globs only `Sources/**/*.swift` and
  `Tests/**/*.swift`, so the statement that the cap is Swift-only is correct; T-0058 is the filed debt.

  **NON-BLOCKING FINDINGS, for a follow-up rather than this PR.**
  1. *"when both git calls fail"* is the wrong mechanism. Measured: `head_rc=0 merge_rc=128`. Only the
     `MERGE_HEAD` diff fails; either one failing empties the intersection. The wording is in the hook comment,
     the fixture module and case-8 docstrings, the Brief and the Log. The code is right; the prose is not.
  2. `ops/lib/check-touches-merge.py`'s module docstring still says "Nine cases" and lists case 9 as
     "must REFUSE" with no case 10 - it preserves precisely the version the Log says was rewritten, and
     `VARIANTS`' comment still says "the seven". A later agent reading only the header would flip case 9 back.
     The per-case docstrings and the `CASES` table are correct, and variant 3 would go red, so nothing
     load-bearing depends on it.
  3. Vacuity surface, pre-existing (identical in `43f4f6f`): `CASES = []` prints `TOUCHES-MERGE OK (0 cases)`
     exit 0 and `VARIANTS = []` prints `TOUCHES-MERGE VARIANTS OK (0)` exit 0. P-GIT-02 asserts only the exit
     code, so an emptied case list keeps the pin green - the one empty-population guard this file preaches
     about in its own case-8 docstring and does not apply to itself.
  4. Nothing automated runs `--variants`: `pins/PINS.yaml` is the only reference to the fixture and it invokes
     the plain form. Pre-existing from PR #78.
  5. No case asserts either operator message; removing both echoes leaves all ten green, though the PR
     advertises "and says so on stdout".
  6. F-B is live and correctly deferred: a hand-written `MERGE_HEAD` naming any valid commit lets staged paths
     byte-identical to that commit drop out of the intersection and commit, exit 0. CONTROL: identical on the
     pre-fix hook, so this PR neither introduces nor worsens it. That is T-0138.

  Nothing was changed in `.worktrees/T-0137` except this file; every mutant and probe lived in
  `.worktrees/rv-pr84/.artifacts/`, and that worktree has been removed.
