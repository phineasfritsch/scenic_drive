---
id: T-0130
title: A reviewer's red-demo rewrote a tracked file inside another agent's worktree
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/, queue/README.md]
pins_affected: [P-PROC-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Two agents were working at the same time. One was fixing PR #78 in `.worktrees/T-0122`. The other was
reviewing the same task and, to demonstrate a pin going red, ran `.artifacts/rvw2/pinred.sh`, which:

* **overwrites the tracked file** `ops/lib/check-touches-merge.py` with a deliberately-failing stub (line 9),
* runs the check,
* restores it (line 16),

**inside the first agent's worktree.**

The fixer noticed only because their own verification produced an impossible result - `TOUCHES-MERGE FAIL
(stubbed by reviewer)` in the middle of a run that should have been green. They re-ran with a guard that
hashed the subject against `HEAD` before and after, confirmed both matched, and correctly concluded the false
red was not theirs. It restored byte-identically that time.

### Why this is a real hazard and not a near-miss story

The window between the stub being written and restored is a window in which **any commit by the other agent
would have committed the stub**. What kept it out was one habit: CLAUDE.md's *"Never `git add -A`. Stage
explicit paths"*. That is a good rule and it held, but the fleet should not depend on every agent, in every
worktree, remembering it during someone else's unannounced write.

It also silently corrupts evidence. The fixer's first GREEN run reported a failure that had nothing to do with
their change. Had they been less careful, the plausible conclusions were both wrong: "my fix does not work" or
"the check is flaky". Either would have produced a task log describing something that never happened - which
is precisely the failure mode `ops/`, `pins/` and `queue/` exist to prevent.

### The general shape

`queue/LOCKS` and `exclusive:` protect **serial files**. Nothing currently states that a **worktree** is owned
by the agent that claimed its task, and that another agent may read it but must not write in it. Reviewers
legitimately need to mutate files to demonstrate red - CLAUDE.md requires it: *"A check that has never been
seen red is untested"* - so the answer is not "reviewers must not mutate", it is "reviewers mutate in a
worktree of their own".

Note the reviewers who did this correctly today did exactly that: PR #70's reviewer worked in
`.worktrees/rvw3-T0114` with its own `--scratch-path`, and said so in their report.

### Do

1. State the rule where an agent will actually meet it - `CLAUDE.md` and `queue/README.md`: **a worktree
   belongs to the task that claimed it. Create your own (`git worktree add`) to run any demonstration that
   writes to a tracked file.** A reviewer reads the owner's worktree; it never writes there.
2. Make it mechanical rather than remembered. Options worth weighing in the task log before choosing:
   * a `.githooks/pre-commit` refusal when the worktree's checked-out branch does not match the `branch:` of
     any task naming this worktree - cheap, and it fires at the moment damage would be committed;
   * `ops/agent-preflight` printing the worktree's owning task and warning when the current session is not
     that owner;
   * an `ops/` helper that makes "give me a scratch worktree at this ref" a one-liner, so the correct thing is
     also the easy thing. The absence of that helper is probably why the shortcut was taken.
3. Whichever is built: **demonstrate it red then green.** The red case is a write to a tracked file inside a
   worktree the session does not own; the green case is the same write inside its own.
4. Do not weaken anything to accommodate this. `git add -A` stays banned, and reviewers still have to show red.

## Log
- 2026-09-08T20:40:00Z filed by agent/claude-opus-5 from the PR #78 fixer's own report, which flagged it as
  "worth escalating, not mine to fix". Their guard - hashing the subject blob against HEAD before and after a
  verification run - is worth keeping as a technique regardless of what this task builds.
