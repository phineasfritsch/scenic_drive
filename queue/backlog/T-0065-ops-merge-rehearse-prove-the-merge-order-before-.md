---
id: T-0065
title: ops/merge-rehearse: prove the merge order before the window opens
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/merge-rehearse]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

A whole class of defect in this repo is invisible to per-branch CI by construction: every branch passes its own
gates and the MERGED tree fails. On 2026-09-08 a hand-rolled rehearsal - merge all thirty open branches into a
throwaway in dependency order, run the gates after each - found four of them in one pass:

    ADD/ADD conflict on ops/lib/gh-stub-for-merge-tests across T-0022, T-0044, T-0049
    all thirty branches duplicated their own task file (main says claimed/, branch says review/)
    check-line-cap fails on services/etl/tests/test_dockerfile.py (436 lines) where the Dockerfile
      chain meets T-0058 - a file no single branch could see
    check-exec-bits fails once T-0036 lands, exactly as T-0041 predicted

It also nearly caught a fifth: a rename/delete conflict where git paired a deleted task file with T-0034 by
content similarity, and taking git's suggested resolution would have silently dropped a filed task.

That script is currently `.artifacts/merge-rehearsal.sh`, which is gitignored - so the one tool that can see
this class of problem is not in the repository. Promote it to `ops/merge-rehearse`.

- Derive the merge order from the PRs rather than hard-coding it. `gh pr list --json number,headRefName,
  baseRefName` gives the dependency graph; topologically sort it. A hard-coded list is wrong the moment
  somebody opens a PR, which is exactly when a rehearsal is most needed.
- Never push, never touch an existing worktree, and clean up the scratch worktree on exit including on
  failure. The hand-rolled version used a trap; keep that.
- Run the FAST gates after each merge - queue-check, check-exec-bits, check-line-cap - and a task-id census
  before and after, so a dropped task file is reported rather than discovered later. `ops/test` would dominate
  the runtime and is not what this tool is for; say so in the header rather than leaving it to be asked.
- Report per-branch and summarise: merged, conflicts, gate failures. Distinguish a CONFLICT from a GATE
  FAILURE - they need different people.
- Demonstrate red: it must find a problem that exists. The four above are all still reproducible today, so
  running it against the current backlog IS the red demonstration, and its output belongs in the log verbatim.
- Consider whether `ops/merge` should refuse to merge when a rehearsal has not been run since the last push to
  any open PR. Probably too strict - argue it either way, but do not leave it unconsidered.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after the hand-rolled version paid for itself four times in one run.
