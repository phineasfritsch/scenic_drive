---
id: T-0116
title: ScenicKit Budget: the lambda bisection that makes the extra-time budget a ceiling instead of a hope
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T13:32:03Z
lease_expires_at: 2026-09-08T15:32:03Z
worktree: .worktrees/T-0116
branch: task/T-0116
exclusive: []
touches: [Sources/ScenicKit/Budget/, Tests/ScenicKitTests/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test -> 33 tests in 4 suites passed, exit 0"
  - "python .artifacts/mutate-T0116.py -> 8 of 8 mutations caught, exit 0"
  - "RED: each of the 8 mutations alone makes swift test exit 1"
---
## Brief

The product is one sentence - *"I have 25 extra minutes, keep me off the freeway, make it pretty"* - and
`lambda` is the single knob that spends those minutes. At 0 the scenic score is ignored and the router
returns the fastest route; as it rises, dull edges are penalised and the route wanders toward pretty ones and
takes longer. The search finds the largest lambda whose route still fits inside `fastest + budget`.

CLAUDE.md: *"The extra-time budget is a **ceiling**: returned ETA <= fastest + budget. Always."*

**No `Package.swift` change.** `Sources/ScenicKit/Budget/` is inside the existing ScenicKit target path, which
SwiftPM globs, so this needed no edit to the serial file - whose lock is held by T-0114. That is the reason
this task was picked to run alongside it.

### The design decision worth arguing with

The plan's method is a bisection on lambda, and a bisection is only correct if duration is monotone in
lambda. The plan states it is, on a graph we own. **That is an assumption about a routing engine, not a
theorem** - ties, alternative-route selection and contraction-hierarchy shortcuts can each break it near the
margins, and a heavier scenic penalty flipping the engine onto a different, quicker corridor is an ordinary
thing for a router to do.

A bisection that trusts monotonicity concludes "everything below the bracket is feasible" and can return a
lambda it never measured. So the search does not trust it:

  * **Only measured, verified-feasible candidates may be returned.** `BudgetOutcome.duration` is always a
    value the router returned for that exact `lambda` - never an interpolation, never the bracket, never the
    ceiling. The ETA on the screen has to be a number somebody computed for the route being shown.
  * A non-monotone router therefore costs accuracy and never costs the invariant.
  * Violations are detected and reported rather than relied upon.

## Log

### GREEN

    swift test --scratch-path .build-T0116
    Test run with 33 tests in 4 suites passed after 0.051 seconds.   exit 0

### The suite was wrong twice, and the mutation harness is what said so

`.artifacts/mutate-T0116.py` breaks the search eight ways and requires each break to fail. First run:

    5 of 8 mutations caught
    NOT CAUGHT: return the bracket instead of a measured candidate;
                let the ceiling slip by one percent;
                keep the last feasible candidate rather than the best

Two of those three are the failure this file exists to prevent, and **both produce a believable lambda and a
believable ETA**. Nothing crashes. The suite had thirteen tests and none of them could tell.

The cause was that every fixture had the bisection's final bracket and the correct answer coinciding, so
returning either looked the same. The fixture that separates them: `fastest = 3000`, and a router that
returns 2000 s for every lambda at or above 4. The bracket climbs to ~7.5 because everything from 4 up is
feasible; the best feasible route - the *slowest* that still fits, which is the most scenic affordable one -
is at lambda 0 with 3000 s. Pinning that exact pair catches both mutations at once.

### The third one was my mutation being wrong, and that is a finding about the code

`let the ceiling slip by one percent` aimed at `if d <= ceiling {` inside the bisection and was not caught.
That is correct behaviour, not a hole: **that line only steers the bracket.** Feasibility is filtered
separately, where `best` is updated. Loosening the bracket makes the search waste an evaluation exploring an
infeasible region; it cannot breach the invariant, because nothing infeasible can ever become `best`.

So the guard that actually enforces the ceiling is a different line, and the mutation was retargeted at it.
Re-run:

    8 of 8 mutations caught     exit 0

The separation is worth keeping deliberately: the bisection can be wrong about where to look next without
the returned answer ever being wrong about the ceiling.

### A third correction: what `monotonicityViolated` can and cannot mean

The first draft asserted that a non-monotone router would be *detected*. It failed. The curve spikes over
`fastest + 4000` for lambda in 1..3, and the bisection samples 0, 4, 6, 5, 5.5, 5.75 - every one outside the
spike. The dip is invisible to it.

The test was wrong, not the code. The flag reports violations **observed among the lambdas actually
sampled**, and six samples out of a continuum cannot prove monotonicity. `true` is evidence of a violation;
`false` is only the absence of evidence. That is now written on the field, with an explicit warning not to
build a check on top of `false` - such a check would be vacuous exactly whenever the dip goes unsampled,
which is this repository's signature defect.

Detection is covered separately by a curve the search does sample, and the unsampled case still asserts the
thing that matters: the ceiling holds, because the returned duration was measured.

### Other properties pinned

  * `ceilingAlwaysHolds` sweeps 41 slopes x 7 budgets including zero and 4 hours.
  * A budget of 0 returns the fastest route and counts as *used* - there was nothing to leave unspent.
  * When nothing scenic fits, `usedBudget` is false rather than the ETA quietly concealing it. A user who
    asks for 25 minutes and is handed 90 seconds has been told yes and given no.
  * `evaluations` is bounded and reported, because each one is a request to our router and the plan caps a
    plan at twelve. A cap of 1 still measures lambda 0, so there is always a feasible answer.
  * A router that overshoots even at lambda 0 is refused rather than rounded down to a breach. That should be
    impossible - lambda 0 is the problem `car_fast` already solved - so it means the two requests disagree,
    and the honest answer is `PlanError.noRoute`, which is worse and true.
  * The plan's meta-test: a stub always returning lambda 0 satisfies the ceiling on every other test here.
    `actuallyUsesTheBudget` is what distinguishes a search from that stub.

### Not done

No alternative-route scoring, no `areas` rat-run repair, no closure polygons. Those are the caller's job and
each needs the router. This type is the arithmetic, and it is injected with a duration function so it can be
tested against exact adversarial curves without a network, a graph or a container.
