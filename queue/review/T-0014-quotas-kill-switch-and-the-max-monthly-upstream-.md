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
touches: [services/api/]
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
