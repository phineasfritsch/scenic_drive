---
id: T-0097
title: ops/merge refuses a green PR because it reads every rollup entry, not the latest run per check
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T07:22:44Z
lease_expires_at: 2026-09-08T10:22:44Z
worktree: null
branch: task/T-0097
exclusive: []
touches: [ops/merge, ops/merge-selftest]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins, ops/merge-selftest]
acceptance: []
---
## Brief

**The one command this whole backlog is waiting on refuses a PR whose CI is green.**

`ops/merge` reads `statusCheckRollup` and treats *every* entry as current:

    rollup="$(gh pr view "$pr" --json statusCheckRollup -q '[.statusCheckRollup[]? | {name: ..., c: ...}]')"
    failed="$(... ",".join(x["name"] for x in d if x["c"] in ("FAILURE","CANCELLED",...)) ...)"
    [[ -n "$failed" ]] && { echo "MERGE REFUSED: failing checks: $failed"; exit 1; }

The rollup contains one entry **per check run**, not per check. A PR that failed, was fixed, and was re-run
carries both. PR #26 (`task/T-0024`) has four entries from two runs:

    2026-09-08T01:25:59Z  SUCCESS   pins-source-only
    2026-09-08T01:26:00Z  FAILURE   core          <- superseded
    2026-09-08T01:50:30Z  SUCCESS   pins-source-only
    2026-09-08T01:50:30Z  SUCCESS   core          <- current

    $ gh pr checks 26
    core              pass
    pins-source-only  pass

    $ ops/merge 26 --dry-run
    task     T-0024 is in queue/done/ on task/T-0024
    checks   total=4 pending=0 failed=[core] mergeState=DIRTY
    MERGE REFUSED: failing checks: core
    exit=1

`gh pr checks` reports both checks passing. `ops/merge` refuses on a run that was superseded 24 minutes
later. **`total=4` for a repository with two checks is the tell, and it was printed on every merge this tool
has ever gated without anyone reading it.**

**Why this is not "safe because it fails closed".** It is the wrong answer in the direction that blocks, on
the command the human operator has to run 41 times, and it gets *more* likely the more a branch is fixed —
so it punishes exactly the branches that were repaired after review. A gate that becomes stricter the more
work you do to satisfy it will be worked around, and the workaround is `gh pr merge`, which
`queue/README.md` step 7 forbids for reasons that cost this repo a broken `main` on 2026-09-07.

It also inflates `total`, which the next line uses:

    [[ "$total" -gt 0 ]] || { echo "MERGE REFUSED: no checks reported at all - CI did not run"; exit 1; }

That guard exists because a PR with zero checks once merged. Counting runs instead of checks does not break
it today, but it means the number it reasons about is not the number it names.

Do:

1. Reduce the rollup to the **latest run per check name** before classifying — `startedAt` (or
   `completedAt`) descending, first entry wins per name. Do not switch to `gh pr checks` text output: it is
   for humans, has no stable machine contract, and this tool already has a JSON seam.
2. Keep the failure classes as they are (`FAILURE`, `CANCELLED`, `TIMED_OUT`, `ACTION_REQUIRED`, `ERROR`) —
   the defect is *which runs* are classified, not how.
3. Print both numbers, because the discrepancy is the diagnostic that was sitting in plain sight:
   `checks   checks=2 runs=4 pending=0 failed=[none]`.
4. A check whose latest run is `PENDING` must still block, as now. A check with **no** completed run must
   not read as passing.

**Red/green, on real data, no fixture needed:**

    RED    ops/merge 26 --dry-run  ->  MERGE REFUSED: failing checks: core       (exit 1)
    GREEN  ops/merge 26 --dry-run  ->  gets past the checks gate

Note PR #26 is separately `mergeStateStatus=DIRTY`, so the green run must be shown reaching and failing the
*mergeState* gate rather than the checks gate — that is the correct refusal and proves the checks gate
stopped firing without pretending the PR is mergeable. Pick a second PR that is CLEAN to show a full pass.

## Log
- 2026-09-08T07:22:44Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:22:44Z

- 2026-09-08 — **fixed.** (This entry's heading originally read *"and the fix uncovered a second defect that
  was latent in the code it replaced"*. It did not; see the CORRECTION below.)

  `ops/merge` now reduces the rollup to the LATEST run per check name before classifying anything, and
  prints both numbers so the discrepancy that caused this is visible rather than buried.

  **RED — the tool as it stands on `main`, on a PR whose CI is green:**

        $ ops/merge 26 --dry-run
        task     T-0024 is in queue/done/ on task/T-0024
        checks   total=4 pending=0 failed=[core] mergeState=DIRTY
        MERGE REFUSED: failing checks: core
        exit=1

        $ gh pr checks 26
        core              pass
        pins-source-only  pass

  **GREEN — same command, same PR:**

        $ ops/merge 26 --dry-run
        task     T-0024 is in queue/done/ on task/T-0024
        checks   checks=2 runs=4 pending=0 failed=[none] mergeState=DIRTY
        MERGE REFUSED: mergeStateStatus=DIRTY (want CLEAN)

  `runs=4 checks=2` is the whole bug in one line. The tool still refuses PR #26 — it has a real conflict —
  but it now refuses for the reason that is true, having stopped refusing for one that is not. That
  distinction is the point: a gate that blocks for the wrong reason teaches its operator to stop reading it.

  **CONTROL — a genuinely failing PR must still be refused, or this "fix" is just a way to merge red work:**

        $ ops/merge 17 --dry-run
        checks   checks=2 runs=2 pending=0 failed=[core] mergeState=UNKNOWN
        MERGE REFUSED: failing checks: core

  `runs=2` there: PR #17 has one run per check and its `core` is genuinely red, so the reduction changes
  nothing and the refusal stands. The two transcripts together are the claim — the gate stopped firing on
  superseded runs and did not stop firing on current ones.

  **A CR introduced by this change, and caught by it.** The first green run printed:

        checks   checks=2 runs=4 pending=0 failed=[-] mergeState=DIRTY
        MERGE REFUSED: failing checks: -

  `bash -x` showed `failed=[-\r]`. Python's text-mode stdout writes CRLF on Windows; `read` splits on LF, so
  the LAST field keeps the carriage return and `[[ "$failed" == "-" ]]` was false. Fixed with `| tr -d '\r'`
  inside the process substitution, with the reason written next to it. This is the CRLF family
  `CLAUDE.md` already warns about, met one layer further in.

  > **CORRECTION, 2026-09-08, after reviewer-pr57.** This entry originally claimed *"the code this replaces
  > had the same bug and nobody saw it: its `failed` was `core\r`, and every `MERGE REFUSED: failing checks:`
  > line this tool has ever printed carried a CR that the terminal quietly ate."* **That was false**, and the
  > reviewer was right to call it. `$( )` strips the trailing CRLF; `read` does not. Measured on this box:
  >
  >     $ "$PY" -c '...the pre-fix expression...' "$rollup" | od -c
  >     0000000   c   o   r   e  \r  \n              <- what python writes
  >     $ failed="$("$PY" -c '...same expression...' "$rollup")"; printf '%s' "$failed" | od -c
  >     0000000   c   o   r   e                      <- 4 bytes through command substitution, no CR
  >     $ read -r x < <("$PY" -c 'print("core")'); printf '%s' "$x" | od -c
  >     0000000   c   o   r   e  \r                  <- 5 bytes through `read`, CR present
  >
  > So the CR was **introduced** by moving from `$( )` to `read < <(...)` in this very commit, and `tr -d
  > '\r'` removes something this change created. It is still correct and still necessary; it is not a
  > pre-existing latent bug, and claiming a second find that was not there inflated this entry. The comment
  > in `ops/merge` that repeated the claim is corrected too.

  **What is NOT demonstrated here, said plainly:** a full pass through every gate. `mergeStateStatus` reads
  `UNKNOWN` on every candidate PR right now — GitHub computes it lazily and had not been asked — so there was
  no CLEAN PR to run a complete green against. The checks gate is demonstrated red-then-green with a
  control; the gates after it are unchanged by this diff and were not re-proven.

        $ bash -n ops/merge     # syntax
        $ ops/queue-check       # QUEUE OK

- 2026-09-08 — **a second refusal in the same gate, found by running the fixed tool across the backlog
  instead of stopping at one PR: `mergeStateStatus=UNKNOWN` is not a verdict.**

  Scope note first, because widening a task quietly is the thing this repository files tasks about: this is
  outside the brief above, which is only about the rollup. It is in the same `while` loop, in the same file,
  in this task's `touches:`, and it is the same defect class — **the gate refuses a branch that is fine** —
  so it is fixed here rather than filed and left blocking the merge it blocks. Said in the commit message
  too.

  GitHub computes `mergeStateStatus` **on demand**. The first query returns `UNKNOWN` and *triggers* the
  computation; a query moments later returns the real value. Sweeping the fifteen PRs whose task is already
  in `done/`, with only the rollup fix applied:

        PR#18  MERGE REFUSED: mergeStateStatus=UNKNOWN (want CLEAN)
        PR#19  MERGE REFUSED: mergeStateStatus=UNKNOWN (want CLEAN)
        ... UNKNOWN for every PR in the sweep

  Then asking the same three again, by hand, seconds later:

        PR#18  CLEAN      PR#19  CLEAN      PR#14  CLEAN

  So the tool refused **the entire signed-off backlog on first contact** — the command the operator has to
  run 41 times, failing the first time on every one of them. `--wait` does not help: it polls for CI that is
  still running, and nothing here is running.

  Fixed with a bounded re-ask (3 tries, 3 s apart), deliberately not behind `--wait`, and it prints what it
  is doing so nobody mistakes the pause for a hang.

  **GREEN — and this is the full pass the entry above had to say was not demonstrated:**

        $ ops/merge 30 --dry-run
        task     T-0047 is in queue/done/ on task/T-0047
        checks   checks=2 runs=2 pending=0 failed=[none] mergeState=CLEAN
        DRY RUN: every gate passed; would merge pr=30 task=T-0047 head=task/T-0047

  **The sweep with both fixes — 13 of 15 signed-off PRs now pass every gate:**

        PR#18  DRY RUN: every gate passed; would merge pr=18 task=T-0014 head=task/T-0014
        PR#19  DRY RUN: every gate passed; would merge pr=19 task=T-0035 head=task/T-0035
        PR#17  MERGE REFUSED: failing checks: core
        PR#14  DRY RUN: every gate passed; would merge pr=14 task=T-0023 head=task/T-0023
        PR#21  DRY RUN: every gate passed; would merge pr=21 task=T-0036 head=task/T-0036
        PR#22  DRY RUN: every gate passed; would merge pr=22 task=T-0022 head=task/T-0022
        PR#20  DRY RUN: every gate passed; would merge pr=20 task=T-0037 head=task/T-0037
        PR#23  DRY RUN: every gate passed; would merge pr=23 task=T-0038 head=task/T-0038
        PR#26  MERGE REFUSED: mergeStateStatus=DIRTY (want CLEAN)
        PR#24  DRY RUN: every gate passed; would merge pr=24 task=T-0039 head=task/T-0039
        PR#27  DRY RUN: every gate passed; would merge pr=27 task=T-0042 head=task/T-0042
        PR#25  DRY RUN: every gate passed; would merge pr=25 task=T-0044 head=task/T-0044
        PR#30  DRY RUN: every gate passed; would merge pr=30 task=T-0047 head=task/T-0047
        PR#32  DRY RUN: every gate passed; would merge pr=32 task=T-0026 head=task/T-0026
        PR#31  DRY RUN: every gate passed; would merge pr=31 task=T-0025 head=task/T-0025

  PR #17 is the known `ops/lib/*.py` exec-bit constraint that `task/T-0036` resolves; the refusals that
  remain are true ones.

- 2026-09-08 — **reviewer-pr57 FAIL closed. The reduction merged a PR with a check still running; it does
  not any more, and the shapes that prove it are now committed instead of narrated.**

  Three findings, three outcomes: the blocking one is **fixed**, the secondary one is **fixed by the same
  change**, and the false-claim one is **confirmed against me** and corrected above.

  **Reproduced first, all of it.** The reviewer's demo targets are gone — `gh pr view 26 --json
  statusCheckRollup` is `[]` today and PR #30 is merged — so the rollup shapes are replayed through a stub
  `gh` that answers the four calls `ops/merge` makes and serves the already-projected `{name,c,t}` array,
  exactly as the jq in `ops/merge` emits it. That harness is now `ops/merge-selftest`, in the tree.

  **BLOCKING (F2/F3) — reproduced.** `ops/merge` at `6db0597`, a `core` SUCCESS at 01:26:58 plus a re-run of
  `core` still in flight:

        F2  t="0001-01-01T00:00:00Z"   checks=2 runs=3 pending=0 failed=[none]
                                        DRY RUN: every gate passed          exit=0   <- MERGES
        F3  t=""                        checks=2 runs=3 pending=0 failed=[none]
                                        DRY RUN: every gate passed          exit=0   <- MERGES

  And the code this task replaced (`8632f4d:ops/merge`) refused both — `total=3 pending=1`, exit 1. So this
  was a regression I introduced, in the direction that merges, in the gate written after a merge broke main.

  **Cause.** `t: (.completedAt // .startedAt // "")`. An unfinished run has no `completedAt`; `gh` renders
  the absent value as null (so `//` falls through to `startedAt`, which a QUEUED run also lacks) or as the Go
  zero time. Both sort **below** every real 2026 timestamp, so `max(t)` kept the old completed run and threw
  the in-flight one away, and `pending` was summed over a set the running check was not in.

  **Fix.** The reduction key is now `(unfinished, t)`, not `t`: an in-flight run outranks every finished run
  of its name whatever its timestamp says, and `t` only breaks ties inside a class. Failure classes are
  untouched, as the brief asked — the defect was never *how* runs are classified.

  **GREEN — same shapes, same command, fixed `ops/merge`:**

        F2  checks=2 runs=3 pending=1 failed=[none]
            MERGE REFUSED: 1 check(s) still running (use --wait to poll)    exit=1
        F3  checks=2 runs=3 pending=1 failed=[none]
            MERGE REFUSED: 1 check(s) still running (use --wait to poll)    exit=1

  **SECONDARY (F5) — reproduced and fixed by the same key.** A `core` FAILURE plus an in-flight re-run
  printed `pending=0 failed=[core]` and refused on the superseded FAILURE — this task's original complaint,
  and it exited instead of polling under `--wait`. Now `pending=1 failed=[none]`, so `--wait` has something
  to poll for again. RED exit 1 with the wrong reason, GREEN exit 1 with the right one; the exit code is the
  same either way, which is exactly why a `checks` line assertion and not just an exit code is what the
  self-test compares.

  **THE FALSE CLAIM — the reviewer is right, and I ran it to be sure.** Transcript and correction are inline
  in the entry above; the `ops/merge` comment that repeated it is corrected in the same commit, and the PR
  body is edited. `$( )` strips the trailing CRLF, `read` does not: the CR arrived *with* this change. No
  second latent defect existed. Nothing about `tr -d '\r'` changes — it is still correct and necessary.

  **`ops/merge-selftest`, new, and the reason it is worth widening `touches:` for.** `touches:` goes from
  `[ops/merge]` to `[ops/merge, ops/merge-selftest]`, said here rather than done quietly. This gate has now
  been wrong twice in opposite directions, and **neither error was reachable from the repository** — you
  needed a live PR in a particular transient state to see it, and both live demonstrations in this log have
  since decayed to nothing. Ten rollup shapes are recorded instead, including both serializations of an
  in-flight re-run. Added to `verify:`.

  **RED — the self-test against the exact version the reviewer failed:**

        $ git show 6db0597:ops/merge > .artifacts/t0097fix/merge.6db0597.sh
        $ ops/merge-selftest .artifacts/t0097fix/merge.6db0597.sh
        ok   F1  ...
        FAIL F2  green run + in-flight re-run, zero-time: the re-run must WIN the reduction, not be dropped
               exit=0 want=1
               > checks   checks=2 runs=3 pending=0 failed=[none] mergeState=CLEAN
               > DRY RUN: every gate passed; would merge pr=99 task=T-0097 head=task/T-0097
        FAIL F3  same, empty-string serialization: the verdict must not depend on which one gh emits
        FAIL F5  red run + in-flight re-run: pending, not a refusal on the superseded FAILURE
        FAIL F10 a reducer that crashes must say so, not fall through to "CI did not run for this PR"
        MERGE-SELFTEST FAIL: 4 of 10 case(s) failed
        exit=1

  **GREEN — the same command against `ops/merge` as it now stands:**

        $ ops/merge-selftest
        ok   F1 F2 F3 F4 F5 F6 F7 F8 F9 F10
        MERGE-SELFTEST OK: 10 cases, 4 in-flight, script=ops/merge
        exit=0

  **The floors, and them going red.** A pass line that counts cases *listed* rather than cases *examined* is
  this repository's signature defect, so `asserted` is incremented only after a case has been run and its
  output compared, and there are two floors on that population — `MIN_CASES=10` and `MIN_PENDING_CASES=4`,
  the second on the in-flight window the blocking defect lived in. Deleting the four in-flight cases leaves
  every remaining case passing:

        $ sed '77,96d' ops/merge-selftest > /...none.sh && bash /...none.sh ops/merge
        ok   F1   ok   F6   ok   F7   ok   F8   ok   F9   ok   F10
        MERGE-SELFTEST FAIL: only 6 case(s) asserted (floor 10) - the table is short
        MERGE-SELFTEST FAIL: only 0 in-flight case(s) asserted (floor 4).
        exit=1

  Six `ok` lines and a FAIL verdict is the whole point: the cases that were run all passed, and the run still
  fails, because the population that was examined no longer contains the shape this defect lives in. With the
  table emptied entirely, `0 case(s) asserted` plus the both-directions floor (`pass=0 refuse=0`), exit 1.

  **One more thing the fix touches, small and said out loud.** If the reducer crashes, `read` sets every
  field empty and the old code fell through to `MERGE REFUSED: no checks reported at all - CI did not run for
  this PR` — fail-closed, but with a reason that is not true. Seen live in the F10 replay against `6db0597`:
  `checks   checks= runs= pending= failed=[none]` followed by that line. It now says
  `could not classify the check rollup (no verdict line from the reducer)`. Same direction, honest reason.

  **Controls — the gate must not have become permissive.**

        F8  core FAILURE, one run each, no re-run   failed=[core]   MERGE REFUSED: failing checks: core  exit=1
        F7  empty rollup                            checks=0        no checks reported at all           exit=1
        F9  all green, mergeState=DIRTY             pending=0       mergeStateStatus=DIRTY (want CLEAN)  exit=1
        F1  the original superseded-FAILURE shape   runs=4          DRY RUN: every gate passed           exit=0

        $ ops/merge 17 --dry-run          # real gh, live PR
        checks   checks=2 runs=2 pending=0 failed=[none] mergeState=UNKNOWN
        MERGE REFUSED: mergeStateStatus=UNKNOWN (want CLEAN)                                             exit=1

  **verify:**

        $ ops/check-pins        PINS ok=9 skipped=0 pending=3 expired=0 failed=0   exit=0
        $ ops/merge-selftest    MERGE-SELFTEST OK: 10 cases, 4 in-flight           exit=0
        $ ops/queue-check       QUEUE OK                                           exit=0
        $ bash -n ops/merge ; bash -n ops/merge-selftest                           exit=0
        $ ops/test              FAIL: services/api exists but vitest produced no report   exit=1

  `ops/test` is red on this box and **was red before this change** — `services/api/node_modules` does not
  exist here, so vitest cannot run; the Swift tier passes (16 tests, 3 suites). CI installs it (`npm ci` in
  `linux-core.yml`) and PR #57's `core` check is SUCCESS, so it is green where it counts. Not caused here,
  not fixed here, named because `verify:` lists it.

  **Not fixed, and not mine to fix here:** `ops/merge 17 --dry-run` returned `UNKNOWN` on all three re-asks
  above, so the bounded re-ask added in the previous entry does not always resolve it. That refusal is in the
  safe direction and is outside this review's findings; noting it rather than quietly widening the task
  again.
