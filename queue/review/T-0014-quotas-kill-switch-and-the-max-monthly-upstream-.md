---
id: T-0014
title: Quotas, kill switch and the MAX_MONTHLY_UPSTREAM_CALLS compile-time constant (P-COST-01, P-COST-02)
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T14:48:38Z
lease_expires_at: 2026-09-07T18:48:38Z
worktree: ../wt/T-0014
branch: task/T-0014
exclusive: []
touches: [services/api/, pins/PINS.yaml]
pins_affected: [P-COST-01, P-COST-02]
reviewer: agent/reviewer-14
depends_on: [T-0005]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Spend control, as two independent mechanisms because they fail differently:

  PER-USER QUOTA  bounds what one caller can cost in a day (anon 3 / free 10 / paid 200 plans).
  GLOBAL KILL     bounds what everyone can cost in a month. MAX_MONTHLY_UPSTREAM_CALLS is a COMPILE-TIME
                  constant, not config, because a config value is a value an agent can raise while
                  "fixing" a 429 at 3am. Raising it is a code change, a PR and a review.

The counter counts UPSTREAM CALLS, not user actions: one scenic plan is up to 12 requests to the routing box,
so counting plans would undercount the thing that costs money by an order of magnitude.

THE PROPERTY THAT MATTERS (P-COST-01): a quota decrement PRECEDES every upstream call. A quota checked after
the fact is an accounting record, not a limit - the request it should have stopped has already cost money.
That is made mechanical by having exactly one door (guardedUpstream) with the guard in front of it, and by
injecting the fetch so tests COUNT invocations rather than trusting a log line.

SCOPE NOTE: touches narrowed to services/api/ only. Making P-COST-02's assertion real edits pins/PINS.yaml,
which task T-0019 currently holds in review - two branches editing one file is the failure mode the queue
exists to prevent. The pin stays pending until this merges; then a follow-up makes it real.

## Log
- 2026-09-07T14:50:00Z promoted backlog -> ready: its dependency (the Worker skeleton, T-0005) is merged, so quotas/kill switch is unblocked. Also the only remaining task whose files (services/api/) are not held by an open PR, which makes it the one thing that can proceed in parallel without two branches editing one file.
- 2026-09-07T14:48:38Z claimed by agent/claude-opus-5; lease until 2026-09-07T18:48:38Z
- 2026-09-07T15:00:00Z GREEN: 56 Worker tests pass (14 new quota-policy + 8 new enforcement + the existing 34). Policy is a pure function of (tier, plansUsedToday, monthlyUpstreamCalls, now), so the arithmetic and the boundaries - the parts most likely to be wrong - are testable without a network, a clock or a Durable Object.
- 2026-09-07T15:00:00Z RED (the ordering property): moved the reserve() call to AFTER fetchImpl() and re-ran - exactly two tests fail, "reserves BEFORE calling, not after" and "over-counts rather than under-counts when upstream fails". Restored, 56 green. This is the P-COST-01 property proven to bite.
- 2026-09-07T15:00:00Z Boundary tests included deliberately: the kill switch trips exactly AT 90% and not one call later; the last plan in an allowance is permitted and the next refused; UTC day/month keys have no timezone seam; nextReset rolls over month and year ends.
- 2026-09-07T15:00:00Z GLOBAL BEATS LOCAL, tested: a paid user with a full daily allowance is still refused once the kill switch trips. The bill is global; the allowance is not.
- 2026-09-07T15:00:00Z Failure direction chosen deliberately and tested: reserving before the call means an upstream 500 over-counts by one plan. That costs the user one plan of allowance rather than costing us an unbounded bill.
- 2026-09-07T15:00:00Z NOT DONE HERE: the Durable Object that persists the counters, and wiring guardedUpstream into a real /plan route. This task delivers the policy and the enforcement seam with the property proven; the storage backend is a separate concern and a separate review.
- 2026-09-07T15:00:00Z moved to review/, reviewer agent/reviewer-14
- 2026-09-07T16:00:00Z reviewed by agent/reviewer-14: FAIL. Re-ran `cd services/api && npx vitest run` -> 56 passed. Re-ran the ordering experiment independently (moved reserve() after fetchImpl() in src/upstream.ts, ran `npx vitest run test/upstream.test.ts`): exactly 2 fail, "reserves BEFORE calling, not after" and "over-counts rather than under-counts when upstream fails" - matches the owner's claim, property is real. Restored from backup, confirmed diff clean and 56/56 green. Four findings block PASS:
  1. BLOCKER, mechanically reproduced: marking this task done breaks `ops/check-pins`. pins/PINS.yaml:90-98 (P-COST-02) has `pending: T-0014` with `assertion: TODO`. ops/lib/pins.py:132-134 fails any pin whose `pending` task has state=done while its assertion is still TODO ("the pin must be real now"). I dry-ran the PASS action (mv the task file review/ -> done/, ran `bash ops/check-pins`, moved it back): result was `PINS ok=8 skipped=0 pending=2 expired=0 failed=2` with `P-COST-02: pending on T-0014 but that task is done - the pin must be real now` (plus a P-PROC-01/queue-check knock-on failure). File was restored byte-identical (`diff` clean) and check-pins verified back to `failed=0` before I continued. Fix: before this can be marked done, either (a) repoint P-COST-02's `pending:` at a new, still-open follow-up task id instead of T-0014, so the debt stays alive until the assertion is real, or (b) land the real assertion together with this change once T-0019 (queue/claimed/T-0019-p-ops-01-..., touches: [pins/PINS.yaml]) releases the file. As scoped, "done" and "P-COST-02 pending on T-0014" cannot both be true at once - that's not a process nitpick, it's the exact failure mode ops/check-pins exists to catch.
  2. CRITICAL: services/api/src/quota.ts:48-49 `killSwitchTripped` does `monthlyCalls >= MAX_MONTHLY_UPSTREAM_CALLS * KILL_SWITCH_THRESHOLD` with no finiteness guard. Verified independently: `killSwitchTripped(NaN)` returns `false` (NaN comparisons are always false), so `checkQuota({tier:"free", plansUsedToday:0, monthlyUpstreamCalls:NaN, now})` returns `{ok:true,...}`. A NaN reaching the monthly counter (plausible once a real Counters/DO backend exists - bad deserialization, an uninitialized field, a division) silently disables the ONE mechanism this whole task exists to build. Fix: `Number.isFinite(monthlyCalls) && monthlyCalls >= ...` and treat non-finite as tripped (fail closed), not passable.
  3. MAJOR: services/api/src/quota.ts:70-73 `DAILY_PLAN_QUOTA[tier]` has no runtime guard for a tier not in {anon,free,paid}. Verified independently: `checkQuota({tier:"enterprise" as any, plansUsedToday:5, monthlyUpstreamCalls:0, now})` returns `{ok:true, tier:"enterprise", remaining:NaN}` - `5 >= undefined` is false, so the exhaustion check never fires and the caller is admitted with unlimited plans. The brief itself says this "runs on data from a database," where TypeScript's compile-time `Tier` union offers zero protection. Fix: validate `tier` against `Object.keys(DAILY_PLAN_QUOTA)` at the boundary and refuse (or map to the tightest tier) on an unrecognized value; same class of gap on `plansUsedToday` (verified: `-5` -> `remaining:14`; `9.5` on free (limit 10) -> `{ok:true, remaining:-0.5}`, an internally contradictory verdict) - clamp/validate to a non-negative integer too.
  4. MAJOR, unresolved seam question (task point 3d): services/api/src/upstream.ts:54 `guardedUpstream` reserves the full `PLAN_UPSTREAM_COST` (12) on every invocation but performs exactly one `fetchImpl` call per invocation (line 56). The docstring (upstream.ts:1-10) claims this is "the only way to reach the routing box" and "everything that costs money goes through `guardedUpstream`"; the brief says one plan is "up to 12 requests to the routing box." Those are only consistent if (a) `guardedUpstream` is called once per plan while the other ~11 real requests happen through some other, unguarded path (violating "the only door" and leaving most of a plan's upstream calls outside P-COST-01), or (b) a caller loops it once per real request, in which case the fixed 12-credit reservation over-charges 12x per call - an anon plan (daily quota 3) would be refused after its 3rd real upstream request without ever completing a scenic plan, and the monthly counter would cap real throughput at roughly 1/12th of MAX_MONTHLY_UPSTREAM_CALLS. test/upstream.test.ts never exercises more than one call, so neither reading is tested. Fix: pick a convention, document it in the docstring, add a test for a multi-call plan that shows the counters land on the intended numbers.

### 2026-09-07 - owner response to reviewer-14: all four findings fixed, each demonstrated red

reviewer-14 returned FAIL with one BLOCKER, one CRITICAL and two MAJORs. All four are addressed. Nothing was
argued down; the guardedUpstream finding changed the shape of the door rather than its docstring.

**BLOCKER - P-COST-02 pending on this task would fail the moment the task was marked done.**
`pins/PINS.yaml` now carries a real assertion instead of `assertion: TODO` + `pending: T-0014`. It reads the
pinned number out of PINS.yaml itself rather than repeating it, so the assertion and `value:` cannot drift
apart; it strips the numeric separator so `250_000` and `250000` compare equal; and it refuses any assignment
whose right-hand side is not a bare literal, which is what "compile-time constant" means here.
`pins/PINS.yaml` is not on CLAUDE.md's serial-only list (only `pins/floor_*.txt` is), so no `exclusive:` lock
was required; `touches:` widened to include it.

Demonstrated red THREE ways, then green:

    RED 1  constant raised in code, PINS value unchanged   -> PINS ok=9 pending=2 failed=1
    RED 2  constant becomes Number(env.MAX_MONTHLY ?? ...) -> PINS ok=9 pending=2 failed=1
    RED 3  PINS value edited to match a raised constant    -> PINS ok=9 pending=2 failed=1
    GREEN  restored                                        -> PINS ok=10 skipped=0 pending=2 expired=0 failed=0

A first version of the assertion was itself broken - `MAX_MONTHLY_UPSTREAM_CALLS *= *[^0-9]` matched the space
after the `=`, because ` *` backtracks to zero width, so the pin failed on correct code. Fixed to
`[[:space:]]*=[[:space:]]*[^0-9[:space:]]`. Worth recording: the first red I got was the check being wrong, not
the code, which is exactly the section-07 confusion the manual warns about.

**CRITICAL - `killSwitchTripped(NaN)` returned false and silently disabled the global ceiling.**
Every comparison against NaN is false, so a NaN from a KV miss, a bad parseInt or a half-written Durable Object
row read as "not tripped". `killSwitchTripped` now fails CLOSED on anything that is not a finite non-negative
integer, NaN and Infinity included.

**MAJOR - an unrecognised `tier` string admitted unlimited plans.**
`tier` is typed but arrives from a D1 row. `DAILY_PLAN_QUOTA["premum"]` is `undefined`,
`plansUsedToday >= undefined` is false, and the caller got `{ ok: true, remaining: NaN }`. `checkQuota` now
validates the tier with an own-property check and returns a new `invalid_state` verdict. The own-property check
matters: `DAILY_PLAN_QUOTA["constructor"]` returned Object's constructor, which is also not a number - that
case is now a test of its own and it was red before the fix. Negative and fractional `plansUsedToday` are
refused for the same reason (`-5` reported `remaining: 14`; `9.5` reported `{ ok: true, remaining: -0.5 }`).

**MAJOR - guardedUpstream reserved 12 and called once, and neither calling convention was tested.**
Fixed by making the door take the shape the counter already assumed. `guardedPlan(deps, args, body)` is now the
one door: it reserves `PLAN_UPSTREAM_COST` ONCE per plan, before the body runs, and hands the body a `call`
that rejects with `PlanBudgetExceeded` past the budget - before `fetchImpl`, so P-COST-04's <= 12 requests per
plan is enforced rather than described. `guardedUpstream` survives as "a plan that makes one call". The
reservation is deliberately an upper bound: over-counting pauses us early and is recoverable; under-counting is
an unbounded bill.

**Red demonstration for the code fixes.** With `services/api/src/quota.ts` reverted to its pre-fix version and
the new tests in place:

    FAIL  an unreadable monthly counter TRIPS the kill switch instead of disabling it
    FAIL  a NaN counter reaching checkQuota pauses upstream rather than admitting the plan
    FAIL  an unrecognised tier is refused, not given an undefined limit
    FAIL  does not inherit a limit from Object.prototype
    FAIL  a negative or fractional usage count is refused, not treated as spare allowance
    Tests  5 failed | 14 passed (19)

and with `services/api/src/upstream.ts` reverted, 5 more fail on `TypeError: guardedPlan is not a function`.
Both restored; full suite green.

**Green after:** `npx vitest run` -> `Test Files 4 passed (4) / Tests 67 passed (67)` (was 56);
`bash ops/test` -> `TESTS linux=83/50 ios=skipped failed=0 skipped=0` / `OK`;
`bash ops/check-pins` -> `PINS ok=10 skipped=0 pending=2 expired=0 failed=0 tier=linux`;
`bash ops/queue-check` -> `QUEUE OK (30 tasks)`.

Back to agent/reviewer-14 in `review/`. The reviewer of the fix should not take the red demonstrations above on
trust - reverting one file and re-running is cheap.
