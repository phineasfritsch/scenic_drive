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
touches: [ops/merge]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
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
