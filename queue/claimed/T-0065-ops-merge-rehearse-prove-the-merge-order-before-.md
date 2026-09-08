---
id: T-0065
title: ops/merge-rehearse: prove the merge order before the window opens
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T00:11:07Z
lease_expires_at: 2026-09-08T02:11:07Z
worktree: null
branch: task/T-0065
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
- 2026-09-08T00:11:07Z claimed by agent/unknown; lease until 2026-09-08T02:11:07Z

- 2026-09-08 agent/claude-opus-5 — `ops/merge-rehearse` built, and its brief's instruction followed: running
  it against the current backlog IS the red demonstration, so the output is here verbatim rather than
  summarised.

  **Red #1 — the tool's own first bug, which is the exact failure the tool exists to catch.** The first run
  against thirty-one branches printed:

        REHEARSAL: 0 conflicts, 0 gate failures

  having merged **one** branch. The order comes from a python heredoc; on git-bash its stdout carries CRLF,
  so every entry arrived as `task/T-0014\r`, `git rev-parse --verify origin/task/T-0014\r` failed, and the
  loop `continue`d **silently**. A clean bill of health from a run that did almost nothing — a check whose
  evidence that it ran came from the same place as its result. Fixed three ways, because fixing only the CR
  would have left the shape: strip the CR; make an unresolvable branch print a line and increment a counter
  instead of a silent `continue`; and assert completeness at the end —

        if [[ $merged -eq 0 || $((merged + conflicts + unresolved)) -lt $want ]]; then
          echo "  INCOMPLETE: $want branches were requested and only ... were accounted for."; exit 2

  Green: `REHEARSAL: 27 of 31 merged, 3 conflicts, 25 gate failures, 0 unresolvable`.

  **What the first honest run found** — four defects, none of which any per-branch CI could ever see, because
  every branch passes its own gates and only the merged tree fails:

  1. `ops/lib/gh-stub-for-merge-tests` ADD/ADD across T-0022, T-0044 and T-0049.
  2. All thirty branches duplicated their own task file: `main` says `claimed/`, the branch says `review/`.
  3. `check-line-cap` fails on `services/etl/tests/test_dockerfile.py` (436 lines) where the Dockerfile chain
     meets T-0058 — a file no single branch can see.
  4. `check-exec-bits` fails once T-0036 lands.

  It also nearly caught a fifth: a rename/delete conflict where git paired a deleted task file with T-0034 by
  content similarity, so the suggested resolution would have silently dropped a filed task. Hence the task-id
  census, which is now in the tool.

  **Red #2 — nine of those gate failures were one ordering constraint, mis-read as a mode error.** Executed
  both ways in a throwaway worktree:

        merging task/T-0021 first:
          P-OPS-01: wrong git file mode:
            ops/lib/classify-checks.py (script, should be 100755, is 100644)

        merging task/T-0036 first, then task/T-0021:
          P-OPS-01: 25 files, 20 required present, all modes correct

  T-0036 changes the RULE (`ops/lib/*.py` are data, since they are only ever invoked as `"$PY" ops/lib/x.py`);
  T-0021 adds a file the rule covers. No mode for that file is correct in both orders. Both branches are based
  on `main`, so the PR graph does not order them and the topological sort fell back to alphabetical — the
  wrong one. A constraint written in a document is one that gets forgotten, so it is an extra edge instead,
  which needs no special case in the sort because "X after Y" and "X is based on Y" are the same shape:

        EDGES+=("task/T-0021 task/T-0036")

  Green: `REHEARSAL: 28 of 31 merged, 3 conflicts, 4 gate failures, 0 unresolvable`.

  **Red #3 — and this is the finding worth more than the tool.** The four remaining failures were all
  `duplicate id`. Checking them by merging each branch into `main` ALONE gave a different, larger answer:

        task/T-0023        T-0032 T-0033 T-0038 T-0039
        task/T-0024        T-0032 T-0033
        task/T-0038        T-0032 T-0033
        task/T-0042        T-0032 T-0033
        task/T-0046        T-0032 T-0033
        task/T-0049        T-0049
        (T-0025, T-0027, T-0028, T-0029, T-0030, T-0040, T-0069: clean)

  **Six branches break `main` on their own; the cumulative run named four, two of them wrongly.** It missed
  T-0042 and T-0046 because T-0032 and T-0033 had already merged and taken the colliding paths with them, so
  the duplicate never appeared and both printed *"merged, gates clean"*. And it blamed T-0025 for a duplicate
  T-0024 introduced, because a failure nothing repairs is still there at the next step and every step after.

  Same root cause in both directions: in cumulative mode the state under test is *everything merged so far*,
  and a per-branch verdict read off that is not a per-branch verdict. So the tool grew a second mode, and
  both are needed — each is blind exactly where the other sees. Cumulative finds collisions BETWEEN branches
  (the ADD/ADD, the line-cap failure) that no single branch can produce; `--pairwise` answers "does this
  branch alone break main", the question a reviewer is actually asking, and is the only answer that does not
  depend on what merged first.

  Two guards came with it, both because the same vacuity would otherwise reappear inside the new mode:
  `--pairwise` refuses to run at all if `main`'s own gates are red (every row would inherit main's failure and
  the run would say nothing), and cumulative mode now prints `(INHERITED, unchanged by this branch)` rather
  than counting a repeat.

  **Green for `--pairwise`**, after repairing the six branches (merge `origin/main` first so the branch knows
  about the move, THEN remove the copy at the path main no longer uses — deleting without merging just
  re-creates the divergence):

        REHEARSAL (pairwise): 31 of 31 merged, 0 conflicts, 2 gate failures, 0 unresolvable

  Set against the cumulative run of the same backlog at the same moment, which is the whole argument for
  having both:

        cumulative   28 of 31 merged,  3 conflicts,  0 gate failures
        pairwise     31 of 31 merged,  0 conflicts,  2 gate failures

  Exactly opposite. Every conflict is invisible to pairwise, because a conflict needs two branches in the
  tree at once and pairwise never has that. Every remaining gate failure is invisible to cumulative, because
  by the time those branches merge, the branch that fixes the rule has already landed.

  The one row that is not clean is correct and is the constraint from red #2: T-0021 merged into `main` alone
  puts `classify-checks.py` at 100644 while `main`'s rule still calls `ops/lib/*.py` scripts. It cannot merge
  before T-0036, which is exactly what the edge says. Note also that `task/T-0022` and `task/T-0044` are clean
  here while conflicting in cumulative mode — the `gh-stub` ADD/ADD needs two branches in the tree at once,
  and pairwise never has that. That is the documented blindness, observed.

  Not run by this tool, deliberately: `ops/test`. The swift, vitest and pytest tiers dominate the runtime by
  an order of magnitude and this tool is about structural collisions between diffs. Run `ops/test` once on the
  merged result at the end if you want that too.

  **Red #4 — the constraint from red #2, written down, was already incomplete when it was written.** The
  first version of the ordering edge was the hard-coded pair `EDGES+=("task/T-0021 task/T-0036")`, because
  T-0021 was the branch that had been measured. `--pairwise` then reported:

        task/T-0049   merged, GATES FAIL | exec-bits: P-OPS-01: wrong git file mode:
                        ops/lib/merge_reason_cap_assert.py (script, should be 100755, is 100644)

  The same constraint, on a branch the hard-coded pair said nothing about. So the edges are derived instead —
  ask git which branches ADD an `ops/lib/*.py` and make each of them follow T-0036:

        ordering: task/T-0049 adds an ops/lib/*.py, so it must follow task/T-0036
        ordering: task/T-0021 adds an ops/lib/*.py, so it must follow task/T-0036

  It is self-limiting on purpose: once T-0036 merges, no open PR head is T-0036 and the block adds nothing,
  so it cannot rot into a permanent special case for a branch that no longer exists.

  Deriving them exposed a second bug, in the sort. `base = {h: b for h, b in pairs}` keeps **one** base per
  head, so adding "T-0049 after T-0036" silently discarded T-0049's real base, `task/T-0044`, and the stack
  it stands on. Now a list per head. A one-line dict comprehension quietly dropping a dependency is the same
  shape as everything else in this log: the data structure could not represent the thing being asserted.

  **Two more corrections, both found by using the tool rather than reading it:**

  - `| exec-bits: P-OPS-01: wrong git file mode:` named no file. `wrong git file mode:` is a header and the
    path is on the NEXT line, so `grep -m1` reported a failure a reviewer could do nothing with. `-A1` now.
  - Pairwise did `git reset --hard main` every iteration, re-reading the ref. `main` moves — a queue claim
    pushes straight to it, and it moved twice during the run that produced the numbers above. The first rows
    were measured against one base and the last against another, which is not a comparable set of results,
    and nothing in the output showed it. The base is now resolved to one SHA at the start and printed.

  **A process finding, recorded because it cost a run.** The first `--pairwise` invocation died at the end
  with `ops/merge-rehearse: line 236: unexpected EOF while looking for matching '`. The file was
  syntactically valid — `bash -n` passed before and after. Bash reads a script incrementally from a byte
  offset as it executes, so editing a running script corrupts the running process. The edit was mine, made
  while the run was in flight. Do not edit a script that is executing; the failure looks exactly like a
  syntax error in a file that does not have one.

  Handing to review. The reviewer should run BOTH modes rather than reading the numbers here — this tool has
  now been wrong four times in ways only execution caught, twice inside itself, and once in the sentence that
  recorded the previous fix.
