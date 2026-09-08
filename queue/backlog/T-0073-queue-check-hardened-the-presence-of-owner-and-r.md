---
id: T-0073
title: queue-check hardened the presence of owner and reviewer, not the comparison between them
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Follow-up to [[T-0068]], which made `queue-check` and `ops/review` require an owner AND a reviewer before
comparing them. A second agent executed sixteen evasions against that fix. **Five went red. Eleven did not.**
Full report in T-0068's `## Log`. The fix hardened the **presence** of the two names; it did not harden the
**comparison**, and that is where every surviving route goes.

**1. A YAML block list defeats the equality, with no funny values.** The module's own front-matter reader
handles "scalars, [flow, lists], and `- ` block lists" — so

        reviewer:
          - agent/self

parses to `['agent/self']`. A list is truthy, so the new presence check passes. Then
`['agent/self'] == 'agent/self'` is **False**, so the inequality passes too. Executed end to end:
`ops/review T-9001` printed `reviewer=['agent/self']` beside an owner spelled identically, exited 0, and moved
the file; `queue-check` then printed `QUEUE OK` in `review/` and again in `done/`, and P-PROC-01's literal
assertion exited 0. The mirror image — owner as the block list, reviewer a plain scalar — is green too.

**2. `owner: "null"` — one pair of quotes.** `_scalar` strips the quotes and yields the *string* `'null'`,
which is truthy, so the presence check passes. Worse at the transition: `ops/review` accepted it, exited 0,
moved the file, and `dump()` rewrote it as `owner: null` — **the transition-time guard manufactured the exact
real null it exists to refuse.** `queue-check` catches the wreckage afterwards, which is the "report, not
prevention" T-0068's own comment argues against.

**3. `agent/self` vs `agent/Self`.** One capital letter, same worker, green. Nothing normalises agent names.

**4. No population floor — the ninth occurrence of this repo's signature bug.** The real module against an
empty `queue/` prints `QUEUE OK (0 tasks)` exit 0; with `queue/review` and `queue/done` deleted outright,
same. Two cheaper variants are also green: a fully self-graded `done/` task named outside `tasks()`'
`rglob("T-*.md")` (`queue/done/selfgraded-fixture.md` — not even counted), and one parked in
`queue/completed/`, a directory outside `STATES`. Already filed as part of [[T-0070]]; repeated here because
the fix for this task must not land without it.

**What the guard did catch**, and should keep catching: a field-name typo (`ownr:`), `owner: []`, and the
`--reviewer=agent/self` flag form. The presence check is not evadable by *absence*; it is evadable by the
*presence of a non-name*.

- Normalise both operands before comparing: require each to be a non-empty string of the `agent/<name>` shape,
  reject lists, reject the literals `null` / `none` / `~`, and casefold before `==`.
- Anything that is not a valid agent name is a failure, not a value to compare. That single rule closes 1, 2
  and 3 together, which is why it is worth doing once rather than three times.
- `tasks()` must not silently ignore files it cannot see: either widen the glob and fail on a task file whose
  name does not match, or assert that every `.md` under a state directory is a task.
- Add the population floor from [[T-0070]] in the same pass; without it the rest is decoration.
- `ops/lib/queue.py` is 515 lines, already over the 300-line cap before this change. [[T-0059]] owns the
  split. Do not split it here, but do not grow it much either.
- Demonstrate each route red then green, and re-run the end-to-end chain the verifier used: one task walked
  `claimed/ -> review/ -> done/` through the real tools with owner and reviewer naming the same worker.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the adversarial verification of T-0068. Every case above was
  executed by an agent that did not write the fix, against the real tools, and the fixtures were removed
  afterwards (`git status --short` empty).
