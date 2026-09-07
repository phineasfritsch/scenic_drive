---
id: T-0056
title: ops/claim must refuse a task whose brief is still the placeholder
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T21:56:22Z
lease_expires_at: 2026-09-07T23:56:22Z
worktree: null
branch: task/T-0056
exclusive: []
touches: [ops/lib/queue.py, ops/claim]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/new-task` writes a placeholder brief:

    ## Brief

    (what, why, and the exact demonstration that proves it - including the red run)

Nothing ever requires it to be replaced. Ten task files in the tree still carry that placeholder verbatim,
and one of them - T-0011 - is in `queue/done/`: a task signed off by a reviewer against acceptance criteria
that were never written down.

agent/claude-opus-5 hit this twice in one session, on T-0033 and T-0032, discovering at claim time that there
was nothing to build against and writing the brief before starting. That is the right recovery and it should
not depend on the claimer noticing.

**Fix at CLAIM time, not in `ops/queue-check`.** That placement is the whole decision, so here is the
argument. Eight of the ten placeholders are on `main` in `queue/claimed/`, and are stale copies - the real
briefs were written on the task branches and `main` will not see them until those branches merge, which is
currently blocked (T-0053). A `queue-check` rule would therefore fail on `main` for eight tasks that are
genuinely fine, breaking the gate for everyone until an unrelated billing problem is resolved. Refusing at
claim time prevents the failure at the only moment it can still be prevented, costs nothing retroactively,
and cannot be tripped by a stale copy of a task somebody else is already working on.

- `ops/claim` refuses when the target task's Brief section is empty or still the placeholder, and says what
  to do: write the brief, commit it, then claim.
- Match on the SHAPE, not on the exact sentence. The placeholder wording will be edited eventually and a
  check anchored on its literal text would silently stop firing - the same failure class as the CRLF check in
  T-0051 and the four decorative tests before it. A Brief section containing no prose outside a parenthetical
  is the property that matters.
- Demonstrate red: `ops/claim` a task carrying the placeholder and show it refusing; write a brief and show it
  claiming. Then demonstrate that a task whose brief is one real sentence is accepted, so the check is not
  simply a length threshold nobody can satisfy.
- While in there, decide whether `ops/new-task` should stop writing a placeholder that looks like content at
  a glance. An empty section is more obviously unfinished than a parenthetical instruction.

Related, NOT in scope: T-0011 is in `done/` with no brief. It cannot be fixed by this check, which is
forward-looking only. File it separately if it is worth reconstructing; the argument against is that its log
records what was built and reviewed, and inventing a brief after the fact would be fiction.

## Log
- 2026-09-07T21:56:22Z claimed by agent/unknown; lease until 2026-09-07T23:56:22Z
