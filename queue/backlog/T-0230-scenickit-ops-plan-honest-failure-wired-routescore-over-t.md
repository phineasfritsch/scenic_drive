---
id: T-0230
title: ScenicKit/ops/plan - honest failure wired (plan:117): RouteScore over the chosen route < 0.45 -> a named plan state printed by ops/plan, the +40 / 'all back roads' offer at its real ETA, and couldNotUseBudget as a product state instead of a doc comment
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, ops/plan, ops/mutate/, Tests/]
pins_affected: []
reviewer: null
depends_on: [T-0182]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ScenicPlanner.plan computes RouteScore over the chosen route's PlanTable rows (RouteScore.swift:92-94's honestFailureThreshold 0.45 / isHonestFailure gain their first caller in Sources); below it ops/plan prints a named state ('not much pretty within N minutes of this drive') with the +40 minute and 'all back roads' (lambda 8, its REAL ETA) offers, never a bare table; RED by name on the motorway fixture (RouteScore.swift:84, 0.320162) before green; couldNotUseBudget (today only a comment at BudgetOutcome.swift:27) becomes a state the CLI prints when the returned ETA is under fastest + 0.5*B"
  - "T-0182's R4 ruling corrected in a NEW dated Log line here with a pointer on T-0182's: a notActuallyDifferent refusal over the score-8 Topanga corridor is NOT plan:117's 'not much pretty' - the two predicates are named and kept apart; the meta-tests gain the honest-failure case; ops/mutate/plan.py extended (floor raised) with the threshold mutants killed by name; swift test count line; check-mutate-population.py, check-line-cap, queue-check bare"
---
## Brief

From the 14:13 panel (CODE, grounded): RouteScore has zero callers in Sources; PlanFailure has no honest-failure case;
the CLI today refuses the prettiest road in the canyon window under a message the Log mislabels. plan:284 makes
ops/plan the M3 exit and step 3 of Problem A is its honest failure. Ranked before T-0221 in slot order.

## Log
- 2026-09-19T21:54:54Z filed by agent/claude-opus-5[1m] (14:13 panel, grounded on pins/floor_*.txt, T-0203 Log :34, queue.py:541-548, RouteScore.swift:92-94). Not started; after PR #124 merges.
