---
id: T-0160
title: re-land T-0047 - the hook still commits stale staged content after a git mv, its fix never reached main, and the touches gate reads the working tree instead of what is being committed
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T19:13:11Z
lease_expires_at: 2026-09-19T03:13:11Z
worktree: .worktrees/T-0160
branch: task/T-0160
exclusive: []
touches: [.githooks/pre-commit, ops/lib/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "RED, the whole point: python ops/lib/check-stale-stage.py --hook .artifacts/T-0160/main-pre-commit (origin/main's hook, saved with git show) -> STALE-STAGE FAIL (14 cases, hook main-pre-commit), exit 1, FAIL by name on 1/git-mv-then-edit, 2/staged-then-deleted, 4/ALLOW_PARTIAL_STAGE=1, 5/ALLOW_PARTIAL_STAGE=yes, 6/unstaged-widening, 8/non-ASCII-path, 10/merge-then-stale-edit, 13/task-file-untracked, and ok on the six false-positive controls 3, 7, 9, 11, 12, 14"
  - "python ops/lib/check-stale-stage.py -> ok on all fourteen cases, STALE-STAGE OK (14 cases, hook pre-commit), exit 0"
  - "python ops/lib/check-stale-stage.py --variants -> ok variant touches: read from HEAD, not the index breaks exactly 7 / a hook that refuses everything breaks exactly 3,4,7,8,9,12 / without the HEAD fallback breaks exactly 14 / without the empty-staging early exit breaks exactly 11, STALE-STAGE VARIANTS OK (4), exit 0. With the RED run above, every one of the fourteen cases has been seen red by name"
  - "python .artifacts/T-0160/probe_commit_modes.py (gitignored scratch) -> git commit --amend --no-edit exit=0 COMMITTED, git commit -a exit=0 COMMITTED, git commit -m x -- a.txt exit=0 COMMITTED with landed: 'working-tree version', PROBE EXIT=0"
  - "python .artifacts/T-0160/probe_hook_latency.py 50 (gitignored scratch) -> two lines, 'this branch 50 staged paths exit=0' and 'origin/main 50 staged paths exit=0' - both hooks commit - carrying a per-path timing that varies run to run and is the only number here that cannot be re-run identically: 1458 vs 717 ms/path on an idle box, 3100 vs 942 ms/path when three other fixtures were running on the same box. The measurement is the ratio, roughly 2x, and the three extra git spawns per staged path behind it"
  - "python ops/lib/check-touches-merge.py -> ok on 11 cases, TOUCHES-MERGE OK (11 cases), exit 0"
  - "python ops/lib/check-touches-merge.py --variants -> six ok lines, breaks exactly 11 / 5,11 / 8 / 9 / 8 / 2, TOUCHES-MERGE VARIANTS OK (6), exit 0"
  - "python ops/lib/check-secret-scan.py -> ok on 7 cases, SECRET-SCAN OK (7 cases), exit 0"
  - "bash ops/lib/check-pipe-consumers -> PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (62 scanned, 63 tracked, floor 42), exit 0"
  - "bash ops/lib/check-exec-bits -> P-OPS-01: 62 files, 23 required present, all modes correct, exit 0"
  - "bash ops/check-pins --source-only -> PINS ok=10 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only, exit 0"
  - "bash ops/queue-check -> QUEUE OK (164 tasks), exit 0"
  - "git ls-files -s .githooks/pre-commit ops/lib/check-stale-stage.py -> 100755 .githooks/pre-commit and 100644 ops/lib/check-stale-stage.py (P-OPS-01: a script keeps its exec bit, a .py under ops/ does not get one)"
  - "the check run on itself: git show HEAD:.githooks/pre-commit into a file, diff that file .githooks/pre-commit -> no output, COMMITTED == WORKING TREE"
---
## Brief

Filed from agent/rv-t0047's sign-off review of T-0047 on 2026-09-18 (FAIL; its entry is appended verbatim to
`queue/claimed/T-0047-*.md`). The finding is not about T-0047's code. It is that **none of it is on main.**

`gh pr view 30 --json baseRefName` -> `task/T-0039`: PR #30 was merged on 2026-09-08 into the STACKED branch
`task/T-0039`, a day after that branch had already landed on main as `186d612`, so the child never followed.
`git merge-base --is-ancestor <c> origin/main` says NO for `a137685` (the fix), `41f59ee` (the reviewer-28
symlink fix) and `24a46ec` (the PR #30 merge). `grep -rn ALLOW_PARTIAL_STAGE` over main hits one line: the
task's own Brief. Three more commits of hook work in the same stack are non-ancestors by the same test -
`4314bd4` (T-0048), `2f5d64d` (T-0051), `3854128`, `732cebe` - and T-0048 and T-0051 still sit in
`queue/claimed/`.

**The bug is live on main today** (the reviewer's ATTACK 1, in a throwaway repository with `core.hooksPath` on
the head hook): commit `queue/review/T-9990-x.md`; `git mv` it to `queue/done/`; rewrite it with `state: done`
and a verdict; `git commit` without re-adding -> rc=0, the hook prints nothing, `1 file changed, 0
insertions(+), 0 deletions(-)`, and `git show HEAD:queue/done/T-9990-x.md` still reads `state: review` with
no verdict. That is the defect that turned PR #69's CI red on 2026-09-18 (`71c6450` carried `id: T-0117`
inside a file renamed to T-0148) and that the orchestrator's memory has recorded twice in one day.

**Do, on the CURRENT hook** - it cannot be a cherry-pick: `.githooks/pre-commit` was rewritten since by T-0137,
T-0139 and T-0140 (one temp-file blob loop with a fail-closed read; merge-aware `touches:` with
`--no-renames`). Read `git show origin/task/T-0047:queue/done/T-0047-*.md` first - the design argument, the
red/green log and reviewer-28's FAIL-then-fix are all there and are the specification:

1. **Check 4 - refuse a commit whose staged content is stale relative to the working tree**, for every staged
   path (added, modified, renamed), naming the path and the `git add <path>` that fixes it; a path staged and
   then deleted from disk flagged distinctly (the reviewer's ATTACK 2 lands today: rc=0 for a file `ls` cannot
   find). The escape hatch for a deliberate partial stage stays an explicit environment variable, named in
   the refusal. Enumerate staged paths with `-z` - today a non-ASCII path arrives C-quoted from `git diff
   --cached --name-only` and T-0140's fail-closed branch then refuses a legitimate commit (ATTACK 4).
2. **The `touches:` gate must read what is being COMMITTED.** Today it greps the WORKING-TREE task file, so an
   unstaged widening of `touches:` lets a forbidden path land while `git show HEAD:<task file>` still forbids
   it (ATTACK 3, control proven alive). Read the staged blob (`git show :<task file>`), falling back to HEAD.
3. A fixture in the style of `ops/lib/check-touches-merge.py` (cases with a single judge, a population floor,
   variants proving each case can fail), each case demonstrated RED on the current main hook by name, then
   GREEN; a pin under a P-GIT id that is free on main AND on open PRs (#74 and the T-0024 fix PR #26 each claim
   one - check `gh pr list` heads before choosing).
4. Decide, in the Log, what of T-0048 / T-0051 / `3854128` / `732cebe` is still wanted on the current hook.
   PR #39 (T-0048) is OPEN against a base that no longer exists in that shape; do not re-land it blind.

`.githooks/pre-commit` is the serial chokepoint: T-0143, T-0150 and T-0138 also edit it. This goes first;
they rebase onto it. The carried-forward LOW from the branch-only Log: a symlink target ending in a newline,
and symlinks verified on WSL2 only, not on Windows.

## Log
- 2026-09-18T19:40:00Z filed by agent/claude-fable-5-1 from agent/rv-t0047's FAIL. Not started.
- 2026-09-18T19:13:11Z claimed by agent/claude-opus-5; lease until 2026-09-19T03:13:11Z
- 2026-09-18T19:47:17Z agent/claude-opus-5: check 4 and the staged `touches:` read are landed in `e23547d`
  with `ops/lib/check-stale-stage.py` (14 cases) and pin P-GIT-04. Red run verbatim below, then the rulings,
  then Brief item 4, then what I am leaving open.

### Read first, in this order

- `git show origin/task/T-0047:queue/done/T-0047-pre-commit-should-refuse-a-commit-whose-staged-c.md` - the
  design argument (refusal not warning, and why), the original red/green log, reviewer-28's FAIL on the
  symlink false positive, builder-8's confirmation of it in WSL2, and reviewer-28's re-review PASS carrying
  FINDING 2 (LOW): a symlink whose stored target text itself ends in a newline is still a false positive,
  because `$(readlink -- "$f")` strips ALL trailing newlines rather than only the one readlink adds.
- `git show a137685` (the check, 80 insertions) and `git show 41f59ee` (the symlink fix, 21 lines of the
  hook plus the log). Neither is an ancestor of origin/main.
- `.githooks/pre-commit` end to end at origin/main: 144 lines, one temp-file blob loop with T-0140's
  fail-closed read, T-0137/T-0139's merge-aware `touches:` with `--no-renames` on both diffs.
- `ops/lib/check-touches-merge.py` (11 cases, 6 variants, MIN_CASES/MIN_VARIANTS as equalities, one judge in
  `case_verdict`, `--hook`) and `ops/lib/check-secret-scan.py` (7 cases, EXPECTED_CASES, `--hook`, a secret
  assembled at run time so the fixture can pass through the hook it tests). That is the house style this
  fixture copies: throwaway repos, one judge, a population equality, `--hook` so a case can be pointed at an
  old hook and seen red.
- `ops/lib/check-exec-bits` (a `.py` under `ops/` must be 100644, not 100755) and `ops/lib/check-pipe-consumers`.

### RED - the current hook on origin/main, verbatim

`git show origin/main:.githooks/pre-commit > .artifacts/T-0160/main-pre-commit` (identical to this
worktree's HEAD hook before this task: `git diff origin/main -- .githooks/pre-commit` printed nothing).

    $ python ops/lib/check-stale-stage.py --hook .artifacts/T-0160/main-pre-commit
    FAIL    1/git-mv-then-edit          must REFUSE  committed, but never said what it should
                expected to see: staged content in queue/done/T-9990-x.md is stale
                expected to see: git add -- "queue/done/T-9990-x.md"
                [task/T-9999 7132637] T-9990 review complete, mark done
                 1 file changed, 0 insertions(+), 0 deletions(-)
                 rename queue/{review => done}/T-9990-x.md (100%)
    FAIL    2/staged-then-deleted       must REFUSE  committed, but never said what it should
                expected to see: allowed/gone.txt is staged but missing from the working tree
                [task/T-9999 ff96dde] add a file that is no longer on disk
                 1 file changed, 1 insertion(+)
                 create mode 100644 allowed/gone.txt
    ok      3/fully-staged              must COMMIT
    FAIL    4/ALLOW_PARTIAL_STAGE=1     must COMMIT  committed, but never said what it should
                expected to see: ALLOW_PARTIAL_STAGE=1 waives the stale-content check for: allowed/a.txt
    FAIL    5/ALLOW_PARTIAL_STAGE=yes   must REFUSE  committed, but never said what it should
                expected to see: is not the value 1
                expected to see: staged content in allowed/a.txt is stale
                [task/T-9999 3a01635] partial stage with a value that is not 1
                 1 file changed, 1 insertion(+), 1 deletion(-)
    FAIL    6/unstaged-widening         must REFUSE  committed, but never said what it should
                expected to see: other/b.txt is outside T-9999 touches
                [task/T-9999 3225a20] widen touches: without staging it
                 1 file changed, 1 insertion(+), 1 deletion(-)
    ok      7/staged-widening           must COMMIT
    FAIL    8/non-ASCII-path            must COMMIT  refused (exit 1)
                pre-commit: cannot read the staged blob for "allowed/caf\303\251-note.txt", so it cannot be scanned; refusing rather than assuming
                pre-commit: "allowed/caf\303\251-note.txt" is outside T-9999 touches: [allowed/ ]
                pre-commit: refusing commit
    ok      9/merge-brings-other-side   must COMMIT
    FAIL    10/merge-then-stale-edit    must REFUSE  committed, but never said what it should
                expected to see: staged content in other/b.txt is stale
                [task/T-9999 72892b8] merge main, then edit a merged file without re-adding
    ok      11/empty-commit             must COMMIT
    ok      12/pure-rename              must COMMIT
    FAIL    13/task-file-untracked      must REFUSE  committed, but never said what it should
                expected to see: cannot read the touches: that is being committed
                [task/T-9988 ef0e237] commit on a branch whose task file was never staged
                 1 file changed, 1 insertion(+), 1 deletion(-)
    ok      14/task-file-HEAD-fallback  must REFUSE

    STALE-STAGE FAIL (14 cases, hook main-pre-commit)
    EXIT=1

Case 1 is the Brief's own sequence and main lands it as `1 file changed, 0 insertions(+), 0 deletions(-)`.
Case 8 is ATTACK 4 with both halves visible in one run: the C-quoted literal defeats `git show ":$f"`, so
T-0140's fail-closed branch refuses, and the `touches:` loop then reports the same unusable spelling as
outside the list. The six `ok` lines are the false-positive controls; they must pass on both hooks, because a
hook that refuses a legitimate commit is worse than the bug it guards.

### GREEN - the same fourteen on the new hook

    $ python ops/lib/check-stale-stage.py
    ok      1/git-mv-then-edit          must REFUSE
    ok      2/staged-then-deleted       must REFUSE
    ok      3/fully-staged              must COMMIT
    ok      4/ALLOW_PARTIAL_STAGE=1     must COMMIT
    ok      5/ALLOW_PARTIAL_STAGE=yes   must REFUSE
    ok      6/unstaged-widening         must REFUSE
    ok      7/staged-widening           must COMMIT
    ok      8/non-ASCII-path            must COMMIT
    ok      9/merge-brings-other-side   must COMMIT
    ok      10/merge-then-stale-edit    must REFUSE
    ok      11/empty-commit             must COMMIT
    ok      12/pure-rename              must COMMIT
    ok      13/task-file-untracked      must REFUSE
    ok      14/task-file-HEAD-fallback  must REFUSE

    STALE-STAGE OK (14 cases, hook pre-commit)
    EXIT=0

The three existing hook fixtures, on the new hook: `TOUCHES-MERGE OK (11 cases)`,
`TOUCHES-MERGE VARIANTS OK (6)` (all six markers still present and still discriminating - the merge diffs
kept their exact spelling for that reason, see RULING 6), `SECRET-SCAN OK (7 cases)`,
`PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (58 scanned, 58 tracked, floor 42)`. Full
outputs in the acceptance block.

### RULINGS

1. **Refusal, not warning** - T-0047's argument stands and is not re-litigated: the cost is a silently
   deleted verdict, `git status` looks clean, and the *instruction* to check was in every prompt and was
   missed six times.
2. **One environment variable, one value.** `ALLOW_PARTIAL_STAGE=1` keeps T-0047's name. Its path-scoped
   form (`ALLOW_PARTIAL_STAGE=a,b`) is deliberately NOT re-landed: the Brief asks for one variable, and
   T-0047's own log records the parser bug that form cost (`read -r -d ''` silently drops an unterminated
   final record, so a single-path value parsed to zero entries). Any value other than `1` now refuses with
   its own line (case 5) instead of being ignored, which buys the property the scoped form existed for - a
   variable left exported in a shell from an earlier commit cannot quietly waive a later, unrelated stale
   file - without a parser to get wrong. The waiver prints on stderr, and the refusal names the variable.
3. **On a merge, check 4 reads the FULL staged set** - this deviates from the Brief's parenthetical ("the
   author's own staged changes, not every file the merge brings in"), and it is measured, not reasoned.
   Check 4's question is whether the staged bytes are the bytes on disk, which is not a question about who
   owns a path: a merged-in file's index and working-tree copies are both the merge result, so it compares
   EQUAL and nothing legitimate is refused - case 9 stages `other/b.txt` and `other/c.txt` from the other
   side and commits, on both hooks. Narrowing would lose the case a merge makes easiest: a file edited after
   `git merge --no-commit` has staged content identical to MERGE_HEAD, so it is absent from the MERGE_HEAD
   diff and drops out of the `touches:` intersection. Case 10 asserts exactly that premise (it returns a
   setup failure if `other/b.txt` ever appears in `git diff --cached --name-only --no-renames MERGE_HEAD`)
   before judging, so a future narrowing of check 4 turns it red rather than passing quietly. The `touches:`
   narrowing is untouched; the hook comment states which check uses which set and why.
4. **A `touches:` list the hook cannot read is a refusal, not an exemption** (case 13). The index is the
   source, HEAD is the fallback for a task file removed from the index or left unmerged (case 14 exercises
   it - nothing else did), and a file in neither refuses with the `git add` that fixes it. This is a
   deliberate behaviour change: main reads the working tree and commits in that situation.
5. **Symlinks ported verbatim from `41f59ee`**, `-L` branch and `readlink | git hash-object --stdin`
   included, with reviewer-28's LOW (a target text ending in a newline) copied into the hook comment rather
   than silently inherited. It is NOT covered by any case here: this Windows checkout cannot create a real
   symlink (`New-Item -ItemType SymbolicLink` needs Administrator, and git-bash's `ln -s` silently copies),
   so the branch is structurally unreachable in a fixture run on this box. Stated, not implied.
6. **No bash arrays** (T-0047 used them). The enumeration is `git diff --cached --name-only -z
   --diff-filter=ACMR | tr '\0' '\n'` into the same newline-delimited `$staged` the hook already read, for
   two reasons: `"${arr[@]}"` on an empty array errors under `set -u` on the bash 3.2 macOS ships, and `mac`
   is in this pin's `runs_on`; and `check-touches-merge.py`'s six variant markers are anchored on the exact
   text of the merge-diff lines, so those lines keep their spelling (`-z` and `tr` were inserted inside the
   marker, which is why the sweep still reports `breaks exactly 11 / 5,11 / 8 / 9 / 8 / 2`). The cost is
   that a path containing a literal newline still splits wrong; that is stated in the hook, and nothing in
   this repository creates one.

### Brief item 4 - the rest of the lost stack, one line each (NOT re-landed here)

- **T-0048, `4314bd4`** (`git show --stat`: `.githooks/pre-commit` +66/-7, task file +132) - five holes:
  staged deletions bypass every check (`--diff-filter=ACMR` omits `D`, so `git rm --cached` of another
  task's file exits 0), an empty or missing `touches:` fails OPEN, a bare prefix match (`touches: [ops/test]`
  licenses `ops/testing-decoy.md`), `ls a b c | head -1` picking alphabetically when the same id exists in
  two directories, and `queue/blocked/`+`queue/backlog/` unenforced. **None of the five is covered** by the
  current hook - all five lines are still exactly as they were, and this task did not change any of them.
  **Re-land as its own task** (T-0048 is still in `queue/claimed/`); PR #39 is open against a base that no
  longer exists in that shape, so it needs the same treatment this task gave T-0047, not a merge.
- **T-0051, `2f5d64d`** (`.githooks/pre-commit` +36/-2, task file +109) - the CRLF check greps the STAGED
  blob, which `* text=auto eol=lf` guarantees can never hold a CR, so it is named for a failure it cannot
  catch; the fix reads the WORKING TREE for files executed as shell, with `grep -U` because git-bash's grep
  opens in text mode and strips CRs. **Not covered**, and deliberately not covered by check 4: a file that
  is CRLF on disk and LF in the index hashes EQUAL there by design (that is the false positive T-0047 was
  built to avoid). **Re-land as its own task**; it edits check 1, which this task did not touch.
- **`3854128`, T-0078** (`.githooks/pre-commit` +128/-16, task file +225) - bind the allowlist to every task
  whose `branch:` names this branch (the union), instead of parsing `task/T-XXXX` out of the branch name, so
  a stacked follow-up's `touches:` stops being decorative; plus three properties that had to follow: task
  files read from the INDEX, `touches: []` as a real empty allowlist, and exact-or-directory matching.
  **Partly covered now**: the index read is landed here (it is the same defect as ATTACK 3, and case 6 pins
  it). The branch-name binding, the union over stacked tasks, `touches: []` and exact matching are **not**.
  **Re-land as its own task**, rebased on this hook and without reverting the index read.
- **`732cebe`** (`.githooks/commit-msg` +9, `.githooks/hook-guard.sh` +74 new, `.githooks/pre-commit` +10) -
  every hook prints `HOOK <name> <blob id> <dir>` and refuses if the file that ran is not this worktree's
  `.githooks`. **Not covered**: `ls .githooks/` is `commit-msg`, `pre-commit`. It is the mechanism that
  would make a red/green hook transcript self-evidencing, and worth its own task - **but it cannot be
  re-landed alone**: by its own design a missing `hook-guard.sh` next to a hook is a refusal, and all three
  hook fixtures (`check-stale-stage.py`, `check-touches-merge.py`, `check-secret-scan.py`) copy only
  `pre-commit` into their throwaway repos, so every case in all three would turn red. That task must change
  the three fixtures to install the whole `.githooks/` directory in the same commit.

### STILL OPEN

- Everything in item 4 above: T-0048's five holes, T-0051's dead CRLF check, T-0078's branch binding and
  `touches: []`, and `732cebe`'s hook provenance. Each is live on this hook today.
- The symlink branch is verified on WSL2/ext4 only (in T-0047's log, by two different agents), never on
  Windows, and the trailing-newline-target LOW is disclosed and unfixed. No case here exercises `-L`.
- Discovery of the task file is still `ls queue/{claimed,review,done}/<id>*.md | head -1`, so a duplicate id
  in two directories is still picked alphabetically. That is T-0048's hole 4; fixing it here would double
  this PR's surface on the repository's serial chokepoint.
- A path containing a literal newline is still split wrongly by every loop in the hook (RULING 6).
- `--no-verify` cannot be closed from a hook, and this changes nothing about that.
- `ops/test` was NOT run: this task touches no Swift, TypeScript or Python product code (`.githooks/`,
  `ops/lib/` and `pins/PINS.yaml` only), and the gates the Brief names are the four fixtures plus
  `check-pins --source-only`, `check-exec-bits` and `queue-check`, all of which are in the acceptance block.
  A reviewer who wants `TESTS linux=N/F` on this branch has to run it.

- 2026-09-18T20:35:08Z agent/claude-opus-5: every acceptance line re-run at `285587b`; **one number in the
  block was wrong and is corrected above**; a `--variants` layer added so the six cases that must COMMIT can
  also be seen red; two probes outside the fixture; full `ops/check-pins` green.

### The wrong number

`bash ops/lib/check-pipe-consumers` printed `(58 scanned, 58 tracked, floor 42)` when I ran it before
committing and `(58 scanned, 59 tracked, floor 42)` at the final commit: `tracked` counts the tracked files
in its pathspecs, and `ops/lib/check-stale-stage.py` was still untracked at the first run. The acceptance
block now quotes the second. Everything else re-ran identical, including the RED run's eight names and the
six `ok` controls.

### Full ops/check-pins, at `285587b`

    $ bash ops/check-pins
    PINS ok=20 skipped=0 pending=3 expired=0 failed=0 tier=linux
    EXIT=0

23 pins, P-GIT-04 among the 20 that ran - so the new pin's YAML parses and its assertion runs under the pin
runner, not only bare. It is not in the acceptance block because the Brief's gate list is
`--source-only`; a re-run of the full form after this entry's commit is left to the reviewer.

### The variants layer, and the prediction it corrected

Eight cases were seen red against origin/main's hook. The other six must COMMIT, so that run cannot show
them failing, and a control that has quietly stopped discriminating is exactly the defect this repository
keeps finding. `--variants` rewrites the hook four ways:

    $ python ops/lib/check-stale-stage.py --variants
    ok      variant touches: read from HEAD, not the index breaks exactly 7
    ok      variant a hook that refuses everything         breaks exactly 3,4,7,8,9,12
    ok      variant without the HEAD fallback              breaks exactly 14
    ok      variant without the empty-staging early exit   breaks exactly 11

    STALE-STAGE VARIANTS OK (4)
    EXIT=0

The second variant's set was written as `3,4,7,8,9,12,14` and the sweep said `expected 3,4,7,8,9,12,14 to
break, got 3,4,7,8,9,12`. Case 14 must REFUSE, so a hook that refuses everything passes it - my literal was
a prediction, not a measurement, and the sweep is what caught it. The fourth variant was added for case 14
instead: with the HEAD fallback removed, case 14 still refuses, on the "cannot read the touches:" branch, so
only the REASON it gives tells the two apart. That is the variant that proves the case asserts a message and
not just an exit code. Every one of the fourteen has now been seen red by name: 1, 2, 4, 5, 6, 8, 10, 13 on
main's hook, and 3, 4, 7, 8, 9, 11, 12, 14 on a variant. The correction is recorded in the VARIANTS comment
in the file, not just here.

### Two probes outside the fixture (`.artifacts/T-0160/`, gitignored)

- **Three commit modes no case covers**, against the new hook: `git commit --amend --no-edit` exit 0,
  `git commit -a` exit 0, and `git commit -m x -- a.txt` over a deliberately stale stage exit 0, landing
  `working-tree version`. The last is the one worth stating: a pathspec commit builds a temporary index from
  the WORKING TREE copy of that path, so the index and disk agree and check 4 correctly says nothing.
- **What check 4 costs**, on an idle box, 50 staged paths in one commit:

        this branch  50 staged paths  exit=0  72.9s  (1458 ms/path)
        origin/main  50 staged paths  exit=0  35.9s  (717 ms/path)

  Check 4 adds three git invocations per staged path (`ls-files -s` for the gitlink skip, `rev-parse ":$f"`,
  `hash-object`) on top of the blob loop's two, and on Windows every invocation is a process spawn. A first
  run at 200 paths (3100 vs 942 ms/path) was taken while three other fixtures were running on the same box
  and is not a fair number; the 50-path pair above is. For the 1-3 path commits this fleet actually makes it
  is a second or two. It is not free, and it is not optimised here.

### STILL OPEN, added by this entry

- Check 4's per-path cost, above. It can be cut to roughly one spawn per path by reading mode and staged oid
  for every path from a single `git diff --cached --raw -z` instead of `ls-files`+`rev-parse` per path, and
  by batching `git hash-object -- <many paths>`. Not done here: it is a rewrite of the loop this task exists
  to land, on the repository's serial chokepoint, and it would need the whole fixture set re-run behind it.
- No gate runs `ops/lib/check-stale-stage.py --variants`. P-GIT-04 pins the plain form only - exactly where
  P-GIT-02 stood until T-0139 filed the gap and pinned the sibling sweep as P-GIT-03. Same follow-up, named
  here rather than left for a reviewer to find.
- Full `bash ops/check-pins` was run at `285587b`, not at this entry's commit (it takes tens of minutes on
  this box). `--source-only`, and P-GIT-04's own assertion in both forms, were re-run at the final commit.

- 2026-09-18T20:55:57Z agent/claude-opus-5: one acceptance line rephrased, and why. The latency probe's line
  quoted `72.9s (1458 ms/path)` and `35.9s (717 ms/path)`, which is the one number in the block that cannot
  be re-run identically - a wall-clock timing is not a fact about a commit. It now quotes the two stable
  lines (`exit=0` for both hooks), states the ratio and the three extra git spawns per staged path that
  produce it, and records both measurements with the load conditions each was taken under. Every other line
  in the block is deterministic and was re-run verbatim at the final commit, including the RED run's eight
  names, `STALE-STAGE VARIANTS OK (4)` with its four `breaks exactly` sets, `TOUCHES-MERGE OK (11 cases)`,
  and the three `COMMITTED == WORKING TREE` diffs.

- 2026-09-18T21:28:56Z agent/claude-opus-5: a previous incarnation of this agent was killed by a session
  reset after the build landed, with the branch four commits ahead of the `91c78ef` it was cut from and never
  pushed. Nothing built above was redone and no dated entry above was edited. What this entry adds:
  origin/main merged in, every gate re-run on the merged tree, four counts in the acceptance block renumbered
  because the merge changed the population they count, and the branch pushed.

### The merge - `f4581dd`, not a rebase

`git rev-list --count HEAD..origin/main` said 63 and `origin/main..HEAD` said 4; the merge base was
`91c78ef`. A MERGE, deliberately, not a rebase: `e23547d` (check 4 and the staged `touches:` read),
`285587b` (the rulings and the RED run), `90b6627` (the variants layer) and `337dc69` are the shas this Log
names, and a rebase would have rewritten every one of them out from under the reviewer.

**One conflict, `pins/PINS.yaml`.** Both sides appended a pin at the end of the file, and because both
entries end with the identical `owner: agent/claude-opus-5` / `added: 2026-09-18` pair, git left those two
lines OUTSIDE the conflict as common context - so the naive resolution silently gives one entry both
`owner:` lines and the other none. Resolved keeping BOTH pins in full, origin/main's `P-OPS-05` (ops/sane's
exit-code precedence, `assertion: bash ops/lib/check-sane-exit-order`) first in main's position, then this
branch's `P-GIT-04`, each with its own `owner:` and `added:` lines restored. No assertion text on either
side was edited. The resolver asserted both ids were present before writing and `git diff --check` and the
marker grep both come back empty; the file now carries five `P-` ids after `P-OPS-03`: `P-GIT-03`,
`P-GIT-02`, `P-OPS-05`, `P-GIT-04`.

**`.githooks/pre-commit` did not conflict, and that is worth stating rather than assuming**: origin/main has
not touched the hook since `91c78ef` (`git diff --stat 91c78ef origin/main -- .githooks/` is empty), so
T-0140's fail-closed blob loop and T-0137/T-0139's merge-aware `touches:` arrived on this branch by way of
the base, not by way of the merge, and check 4 sits on top of them unchanged. `ops/lib/` merged cleanly -
origin/main added `check-ios-compile-guardrails.py` and `check-sane-exit-order`, this branch added
`check-stale-stage.py`, and no file was touched by both sides.

**The merge commit went through the hook it edits.** A known-good copy of `.githooks/pre-commit` was kept
outside the tree for the length of the merge and was not needed; `--no-verify` was not used. The hook
printed one line and committed: `pre-commit: merge in progress; checking touches: against the 1 path(s)
that differ from both parents` - that one path is `pins/PINS.yaml`, the conflict I resolved, which is the
T-0137/T-0139 behaviour the Brief asked check 4 not to break, observed on a real merge rather than on a
fixture.

**`P-GIT-04` is still free everywhere.** After the merge, `git show origin/main:pins/PINS.yaml` carries
`P-GIT-01`, `P-GIT-02` and `P-GIT-03` and no `P-GIT-04`; a loop over every head in
`gh pr list --state open --json number,headRefName` printed `P-GIT-04 count=0` for all thirty open PRs
(#97 down to #40 - PR #26 and PR #39, which the Brief named as claiming ids, are no longer open). The id
this task took is uncontested.

### Renumbered in the acceptance block, and why

A merge is a tree change, so the four gates that count a population all print different numbers than they
did at `337dc69`, and the acceptance block is required to quote the final commit. Only those four lines were
renumbered; no dated entry above was touched, and no assertion, case list or `breaks exactly` set moved.

- `check-exec-bits`: `58 files` -> `62 files` (the merge brought `ops/etl-curvature-fixture`,
  `ops/etl-oracle-report`, `ops/lib/check-sane-exit-order` and this branch's own new file into its scan).
  `23 required present, all modes correct` is unchanged.
- `check-pipe-consumers`: `(58 scanned, 58 tracked, floor 42)` at the first build run and
  `(58 scanned, 59 tracked, floor 42)` at `337dc69` -> the post-merge count below. The floor held.
- `check-pins --source-only` and `queue-check`: both changed with the merge - `P-OPS-05` is a new
  source-anchored pin, and the merge brought a dozen new task files into `queue/`. The post-merge outputs
  are quoted below and pasted into the block.
- The RED run, the GREEN run, the variants sweep, `check-touches-merge.py` (plain and `--variants`) and
  `check-secret-scan.py` are all unchanged by the merge, to the character, including the eight FAIL names
  and the four `breaks exactly` sets. That is the evidence that 63 commits of other people's work did not
  quietly move this fixture's ground.

### One mistake worth recording

The first sweep script redirected `git show origin/main:.githooks/pre-commit` into the saved main hook and
git-bash's MSYS path conversion rewrote the argument to `origin\main;.githooks\pre-commit`; git refused it
and the file was left EMPTY (`git hash-object` on it returned `e69de29`, the empty blob). A RED run against
an empty file is not a RED run against main's hook - it is a run against no hook at all, where every case
"commits". It was caught by hashing the saved file rather than by trusting the redirect, the sweep was
re-run with `MSYS_NO_PATHCONV=1`, and the saved hook's blob id is printed in the transcript below so a
reviewer can check it against `git rev-parse origin/main:.githooks/pre-commit` instead of taking my word.

### Every gate, bare, on the merged tree

Each command below was run bare - never piped into `tail`, `head` or `grep` before a `&&` - and the output
is pasted from that run at `f4581dd`, whose tree differs from the final commit only in this task file.

    $ bash ops/lib/check-exec-bits
    P-OPS-01: 62 files, 23 required present, all modes correct
    EXIT=0

    $ bash ops/lib/check-pipe-consumers
    PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (62 scanned, 63 tracked, floor 42)
    EXIT=0

    $ bash ops/check-pins --source-only
    PINS ok=10 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only
    EXIT=0

    $ bash ops/queue-check
    QUEUE OK (164 tasks)
    EXIT=0

    $ python ops/lib/check-touches-merge.py
    ok      1/merge-brings-other-side   must COMMIT
    ok      2/resolution-inside-touches must COMMIT
    ok      3/resolution-outside        must REFUSE
    ok      4/plain-commit-outside      must REFUSE
    ok      5/rename-into-touches       must REFUSE
    ok      6/delete-outside-in-merge   must REFUSE
    ok      7/secret-across-a-merge     must REFUSE
    ok      8/empty-MERGE_HEAD          must REFUSE
    ok      9/linked-worktree-resolve   must COMMIT
    ok      10/linked-worktree-outside  must REFUSE
    ok      11/rename-untouched-file    must REFUSE

    TOUCHES-MERGE OK (11 cases)
    EXIT=0

    $ python ops/lib/check-touches-merge.py --variants
    ok      variant without --no-renames on the HEAD side        breaks exactly 11
    ok      variant without --no-renames on the MERGE_HEAD side  breaks exactly 5,11
    ok      variant without the error fallback                   breaks exactly 8
    ok      variant literal ".git/MERGE_HEAD"                    breaks exactly 9
    ok      variant without the fallback message                 breaks exactly 8
    ok      variant without the narrowing message                breaks exactly 2

    TOUCHES-MERGE VARIANTS OK (6)
    EXIT=0

    $ python ops/lib/check-secret-scan.py
    ok          1 KB secret on line 1   must REFUSE  refused: secret-looking content in leak.txt
    ok         64 KB secret on line 1   must REFUSE  refused: secret-looking content in leak.txt
    ok        256 KB secret on line 1   must REFUSE  refused: secret-looking content in leak.txt
    ok       1024 KB secret on line 1   must REFUSE  refused: secret-looking content in leak.txt
    ok       4096 KB secret on line 1   must REFUSE  refused: secret-looking content in leak.txt
    ok       4096 KB clean               must COMMIT  committed
    ok      staged blob object deleted   must REFUSE  refused: cannot read the staged blob for leak.txt

    SECRET-SCAN OK (7 cases)
    EXIT=0

    $ python ops/lib/check-stale-stage.py
    ok      1/git-mv-then-edit          must REFUSE
    ok      2/staged-then-deleted       must REFUSE
    ok      3/fully-staged              must COMMIT
    ok      4/ALLOW_PARTIAL_STAGE=1     must COMMIT
    ok      5/ALLOW_PARTIAL_STAGE=yes   must REFUSE
    ok      6/unstaged-widening         must REFUSE
    ok      7/staged-widening           must COMMIT
    ok      8/non-ASCII-path            must COMMIT
    ok      9/merge-brings-other-side   must COMMIT
    ok      10/merge-then-stale-edit    must REFUSE
    ok      11/empty-commit             must COMMIT
    ok      12/pure-rename              must COMMIT
    ok      13/task-file-untracked      must REFUSE
    ok      14/task-file-HEAD-fallback  must REFUSE

    STALE-STAGE OK (14 cases, hook pre-commit)
    EXIT=0

    $ python ops/lib/check-stale-stage.py --variants
    ok      variant touches: read from HEAD, not the index breaks exactly 7
    ok      variant a hook that refuses everything         breaks exactly 3,4,7,8,9,12
    ok      variant without the HEAD fallback              breaks exactly 14
    ok      variant without the empty-staging early exit   breaks exactly 11

    STALE-STAGE VARIANTS OK (4)
    EXIT=0

    $ git show origin/main:.githooks/pre-commit > .artifacts/T-0160/main-pre-commit (MSYS_NO_PATHCONV=1)
    saved blob id:               3b0438944ce5c1daaeaa25a527abf407efcfede6
    origin/main:.githooks/pre-commit: 3b0438944ce5c1daaeaa25a527abf407efcfede6
    wc -l: 144
    EXIT=0

    $ python ops/lib/check-stale-stage.py --hook .artifacts/T-0160/main-pre-commit
    FAIL    1/git-mv-then-edit          must REFUSE  committed, but never said what it should
                expected to see: staged content in queue/done/T-9990-x.md is stale
                expected to see: git add -- "queue/done/T-9990-x.md"
                [task/T-9999 05ade2a] T-9990 review complete, mark done
                 1 file changed, 0 insertions(+), 0 deletions(-)
                 rename queue/{review => done}/T-9990-x.md (100%)
    FAIL    2/staged-then-deleted       must REFUSE  committed, but never said what it should
                expected to see: allowed/gone.txt is staged but missing from the working tree
                [task/T-9999 37a1755] add a file that is no longer on disk
                 1 file changed, 1 insertion(+)
                 create mode 100644 allowed/gone.txt
    ok      3/fully-staged              must COMMIT
    FAIL    4/ALLOW_PARTIAL_STAGE=1     must COMMIT  committed, but never said what it should
                expected to see: ALLOW_PARTIAL_STAGE=1 waives the stale-content check for: allowed/a.txt
    FAIL    5/ALLOW_PARTIAL_STAGE=yes   must REFUSE  committed, but never said what it should
                expected to see: is not the value 1
                expected to see: staged content in allowed/a.txt is stale
                [task/T-9999 b133281] partial stage with a value that is not 1
                 1 file changed, 1 insertion(+), 1 deletion(-)
    FAIL    6/unstaged-widening         must REFUSE  committed, but never said what it should
                expected to see: other/b.txt is outside T-9999 touches
                [task/T-9999 02c358f] widen touches: without staging it
                 1 file changed, 1 insertion(+), 1 deletion(-)
    ok      7/staged-widening           must COMMIT
    FAIL    8/non-ASCII-path            must COMMIT  refused (exit 1)
                pre-commit: cannot read the staged blob for "allowed/caf\303\251-note.txt", so it cannot be scanned; refusing rather than assuming
                pre-commit: "allowed/caf\303\251-note.txt" is outside T-9999 touches: [allowed/ ]
                pre-commit: refusing commit
    ok      9/merge-brings-other-side   must COMMIT
    FAIL    10/merge-then-stale-edit    must REFUSE  committed, but never said what it should
                expected to see: staged content in other/b.txt is stale
                [task/T-9999 1fd1f6c] merge main, then edit a merged file without re-adding
    ok      11/empty-commit             must COMMIT
    ok      12/pure-rename              must COMMIT
    FAIL    13/task-file-untracked      must REFUSE  committed, but never said what it should
                expected to see: cannot read the touches: that is being committed
                [task/T-9988 2b6ba08] commit on a branch whose task file was never staged
                 1 file changed, 1 insertion(+), 1 deletion(-)
    ok      14/task-file-HEAD-fallback  must REFUSE

    STALE-STAGE FAIL (14 cases, hook main-pre-commit)
    EXIT=1
- 2026-09-18T22:27:20Z **Record corrections from the read-only verification of this build, closed before review - agent/claude-fable-5-1
  (orchestrator), for the owner. The verifier saved origin/main's hook outside the tree (blob 3b04389, 144 lines)
  and re-ran the fixture bare (`STALE-STAGE OK (14 cases, hook pre-commit)`), with `--hook` on that old hook
  (`STALE-STAGE FAIL (14 cases, hook main-pre-commit)`, red by name on cases 1, 2, 4, 5, 6, 8, 10 and 13, twice,
  identical), `--variants` (`STALE-STAGE VARIANTS OK (4)`), `check-touches-merge.py` (`11 cases`) and
  `check-secret-scan.py` (`7 cases`); f4581dd is a true merge that changed neither the hook nor the fixture;
  these are text.** (a) The 21:28:56Z entry says "the file now carries five `P-` ids after `P-OPS-03`" and lists
  four (P-GIT-03, P-GIT-02, P-OPS-05, P-GIT-04); four is what the file has. (b) The build report's "4 files, 934
  insertions / 7 deletions ... task file +292" was measured before the final commit; at a5fd960 `git diff
  --stat 81f8483 HEAD` reads 4 files, 1144 insertions(+), 7 deletions(-) (hook 123+/7-, fixture +510, PINS +9,
  this file +502). (c) The 21:28:56Z stamp is the start of that entry, not the time of the gate runs it quotes:
  they take well over ten minutes on this box and the entry was committed at 21:57:12Z. (d) Not re-run by the
  verifier: `check-touches-merge.py --variants`, the full `bash ops/check-pins` (ok=20 at 285587b), the
  `P-GIT-04 count=0` loop over the open PR heads (origin/main and the merge base carry P-GIT-01/02/03 only),
  and acceptance lines 4-5 (the two probes live in the gitignored `.artifacts/T-0160/`; their timings are
  declared non-reproducible). (e) The symlink `-L` branch of check 4 is exercised by no case - this box cannot
  make a real symlink - as the build already discloses.
