---
id: T-0056
title: ops/claim must refuse a task whose brief is still the placeholder
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T21:56:22Z
lease_expires_at: 2026-09-07T23:56:22Z
worktree: null
branch: task/T-0056
exclusive: []
touches: [ops/lib/queue.py, ops/claim, ops/lib/check-brief-required]
pins_affected: []
reviewer: agent/reviewer-41
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

- 2026-09-08T03:50Z filed, claimed and implemented by agent/claude-opus-5. Stacked on task/T-0039 (done),
  which owns ops/lib/queue.py.

  **How this was found.** I hit it twice in one session - T-0033 and T-0032 both turned out to have nothing
  but the placeholder when I went to claim them - and then swept the tree: TEN task files carry
  `ops/new-task`'s placeholder verbatim, and T-0011 is in `queue/done/` still carrying it. A reviewer signed
  that one off against acceptance criteria nobody had written.

  **`ops/claim` now refuses.** `brief_is_unwritten()` in ops/lib/queue.py, called from `cmd_claim` before
  anything is mutated.

  **Matched on SHAPE, never on the placeholder's wording**, and that is the whole design. A check anchored on
  that literal sentence would stop firing the moment somebody rephrased it and would then report every task
  as fine - which is the defect this repo keeps finding, most recently in T-0051 where the CRLF check could
  not fire at all, and in the four decorative tests before it. The property is "somebody wrote prose here";
  a lone parenthetical instruction is not prose, and a missing `## Brief` heading is worse than an empty one.
  The reworded-placeholder case is in the check specifically to prove the wording is not what is matched.

  **Claim time, not `ops/queue-check`.** Eight of the ten placeholders are stale copies on `main` whose real
  briefs were written on task branches and will not reach main until those branches merge - which is blocked
  on billing (T-0053). A queue-check rule would fail the gate for everyone until an unrelated problem is
  fixed. Claim time is the last moment the failure can still be prevented and cannot be tripped by somebody
  else's in-flight work.

  **New `ops/lib/check-brief-required`**, in the style of `ops/lib/check-failure-naming` (P-OPS-02), because
  `ops/lib/*.py` HAS NO TEST TIER - `ops/test` runs swift, vitest and `services/etl` pytest, and nothing
  covers ops/lib except pin assertion scripts. It builds a throwaway repo, runs the real `queue.py claim`
  end to end against generated task fixtures, and asserts both directions:

      ok: the current placeholder -> refuse
      ok: a reworded placeholder -> refuse
      ok: an empty Brief section -> refuse
      ok: no Brief heading at all -> refuse
      ok: one real sentence -> accept
      ok: prose followed by a parenthetical -> accept
      BRIEF CHECK OK

  The last two matter as much as the first four. A check that only ever refuses is not a check, it is an
  outage, and "brief is long enough" is the obvious wrong implementation.

  It also asserts that a REFUSAL does not half-claim: the task stays in `ready/`, does not appear in
  `claimed/`, and the message says why.

  **RED demonstrated** by deleting the guard from `queue.py` and re-running the check - all four refuse-cases
  flip to `accept`, `BRIEF CHECK FAIL`, exit 1 - then restored, with sha256 confirmed identical. And on a
  REAL task rather than a fixture: `python ops/lib/queue.py claim T-0045`, which still carries the
  placeholder on this branch ->

      T-0045 has no brief - the ## Brief section is empty or still the placeholder.
      Write it, commit it, then claim. ...
      still in ready/: yes

  **`ops/new-task` keeps writing the placeholder.** The brief asked me to decide whether an empty section
  would be more honest. I kept it: the sentence is genuinely useful guidance about what a brief must contain,
  and now that claiming enforces it, it can no longer be mistaken for content that satisfies anything.

  **Verification:** `ops/lib/check-brief-required` -> `BRIEF CHECK OK`; `ops/test` -> `TESTS linux=50/50
  ios=skipped failed=0 skipped=0` / `OK`; `ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0
  failed=0 tier=linux` (9 not 10 because this branch is based on task/T-0039, which predates a later pin on
  main); `ops/queue-check` -> `QUEUE OK (41 tasks)`. `ops/lib/check-brief-required` is committed 100755, as
  P-OPS-01 requires for a bash script. GitHub Actions is DISABLED repo-wide (T-0053), so there is no CI
  signal at all.

  **What to attack.** The new check is not wired into any pin, so nothing runs it - `pins/PINS.yaml` is
  outside this task's `touches:` and adding a pin entry deserves its own review. That leaves it in the same
  position as the fixture guard in T-0025: correct, and invoked by nobody. Second: `brief_is_unwritten`
  accepts any single line of prose, so `## Brief

fix the thing` claims fine - it enforces that somebody
  wrote something, not that what they wrote is a brief, and I do not think a script can tell the difference.
  Third: this does nothing about the ten existing placeholders, including the one in `done/`; whether T-0011's
  brief is worth reconstructing after the fact is argued in this task's own brief and I came down against it.
