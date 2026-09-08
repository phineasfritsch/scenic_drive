---
id: T-0118
title: ScenicKit LearnedCorridorSpeeds: honest rush-hour ETAs on day one, and a badge that admits when we do not know
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T14:07:13Z
lease_expires_at: 2026-09-08T16:07:13Z
worktree: .worktrees/T-0118
branch: task/T-0118
exclusive: []
touches: [Sources/ScenicKit/Traffic/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test -> 29 tests in 4 suites passed, exit 0"
  - "python ops/mutate/corridorspeeds.py -> 18 caught by a named test, 0 missed, exit 0"
  - "RED: python ops/mutate/corridorspeeds.py --prove-vacuity -> 0 caught with the tests removed"
---
## Brief

The plan's second-highest risk: *"rush-hour ETA over-promises - High likelihood, trust blast radius."* There
is no traffic feed at launch. The router knows free-flow speeds and nothing about Tuesday at 17:40, so an
unadjusted ETA says 34 minutes for a drive that takes 51 - on the commute, which is the exact drive this
product exists for.

The mitigation is to learn the ratio of free-flow to actual duration per corridor per hour-of-week, on the
device, from drives the user has already completed. Hour of the WEEK, not of the day: Tuesday 08:00 and
Sunday 08:00 have nothing in common, and 168 buckets is the smallest thing that can tell them apart.

**Two product invariants live here, and both are things a well-meaning person removes on purpose.**

CLAUDE.md: *"ETAs show the estimate - no traffic data badge until a corridor has >= 5 learned samples."*
`ratio(for:)` returns nil below that, and **nil means show the badge, not assume 1.0**. Defaulting to 1.0 is
the tempting simplification, and it silently restores the unbadged free-flow ETA this type exists to replace
- the over-promise wearing the costume of the fix. `adjust()` returns `(duration, learned)` as a pair
precisely so no call site can take the number without the badge.

P-PRIV-05: *"learned speeds have no Codable conformance."* This is a record of when and where one person
drives - a commute pattern. Conformance is the mechanism by which it leaks: one `JSONEncoder` in a
diagnostics payload, one `Codable` request body with a field of this type, and the pattern is on a server.
Persistence is deliberately explicit SQL in PlaceStore, written and reviewed as its own thing. **The compiler
does not warn when somebody adds `: Codable` later**, so the absence is asserted at runtime in the suite.

**H3 is not implemented here.** The plan specifies H3 resolution 8, and that is a large, exacting piece of
geometry that deserves its own task with the reference library as an oracle. `CorridorKey` takes the cell id
as an opaque `UInt64`, which is honest about what has been built and lets everything about the *learning* be
tested exactly. **No `Package.swift` change**: `Sources/ScenicKit/Traffic/` is inside the existing target path.

## Log

### GREEN

    swift test --scratch-path .build-T0118
    Test run with 28 tests in 4 suites passed after 0.035 seconds.   exit 0

### RED, nine ways

    caught  default the ratio to 1.0 instead of admitting we do not know
    caught  always claim the ETA is learned
    caught  drop the badge after one sample
    caught  add Codable to the key so it can be logged
    caught  accept any sample the caller offers
    caught  count a rejected sample toward confidence
    caught  blend the first sample against an assumed 1.0
    caught  stop clamping the ratio
    caught  bucket the week from the calendar's first weekday
    9 of 9 mutations caught                                          exit=0

The first run caught six. All three misses are worth writing down, because only one of them was a hole.

### The one real hole was in MY test, and it is this repository's signature defect

`drop the badge after one sample` lowered `confidenceThreshold` from 5 to 1 and **nothing objected**. The
test looped:

    for n in 1..<LearnedCorridorSpeeds.confidenceThreshold {

which becomes `1..<1` - an empty range. The test for a product invariant passed over zero iterations, and
would have kept passing for any threshold of 1.

That is a check whose expected value is derived from the thing it checks: the exact defect class CLAUDE.md
is organised around, sitting in the test for one of its own product invariants. CLAUDE.md names the number -
*">= 5 learned samples"* - so it is specified, not incidental, and the test now writes it out:

    #expect(LearnedCorridorSpeeds.confidenceThreshold == 5)
    for n in 1...4 { ... }

### The other two misses were mis-aimed mutations, and each revealed a defense

`count a rejected sample toward confidence` first added a no-op line *after* the guard, where it could never
run for a rejected sample. Retargeted to increment before the guard returns - which is what somebody writes
when they move bookkeeping to the top of the function - it is caught.

`blend the first sample against an assumed 1.0` took three attempts, and the reason is worth keeping:
**there are two independent defenses and either alone is sufficient.** The `n == 0` branch takes the first
sample at face value; the `?? sample` fallback in the else branch would do the same if that branch were
gone. Mutating either on its own is a no-op. The failure - a first sample dragged halfway toward free flow,
so a corridor reads as faster than it is for its first few drives - needs both removed, which is precisely
what one "simplify this if/else away" edit does. That is the mutation now, and it is caught.

A mutation that changes no behaviour must never be recorded as a caught defect. Two of the three here would
have been, if the harness had been written to flatter itself.

### Other properties pinned

  * **Monday is bucket 0 regardless of the calendar.** `Calendar.firstWeekday` is 1 in en_US and 2 across
    most of Europe. Deriving the bucket from it would bucket the same drive differently for two users and
    re-bucket a user's own history when they travelled. `Calendar.weekday` is always 1 = Sunday, so
    `(weekday + 5) % 7` is stable; the test asserts a US and a European calendar agree on the same instant.
  * The ratio is clamped to `0.3 ... 1.0`. Nothing is faster than free flow (that is a GPS glitch or a
    skipped corridor); below a third is a closure, not congestion. Clamped rather than rejected, because a
    genuinely terrible Tuesday is real data.
  * One bad day moves the estimate but cannot redefine the corridor - asserted as a bound on the move, not
    as an exact EWMA value, so the smoothing constant can be tuned without rewriting the test.
  * A rejected sample does not count toward confidence. Five unusable drives must not drop the badge.

### Not done

No H3. No `TrafficProvider` protocol or paid flow source - that is V1.1 in the plan. No persistence: the
store is in-memory here and its SQL belongs with PlaceStore, deliberately, for the privacy reason above.

---

## Fix pass: reviewer-pr75 found the same defect thirty lines below where I had just fixed it

`#expect(r2 <= LearnedCorridorSpeeds.maxRatio, "nothing is faster than free flow")` is stated in terms of
the constant it checks, so it is true for **any** value that constant takes.

The reviewer mutated `maxRatio` from 1.0 to 3.0. The whole suite stayed green. Five drives at
`actual = 600, freeFlow = 1800` then produced a stored ratio of 3.0, and `adjust(1800)` returned **600 s
with `learned == true`** - an ETA below the free-flow duration it was handed, badge off. That is the
rush-hour over-promise this type exists to prevent, arrived at from the opposite direction.

The Log entry directly above describes finding and fixing exactly this defect for `confidenceThreshold`.
It was thirty lines away in the same file, in the same test suite, written in the same sitting. **Finding
this defect once does not inoculate a file against it**, which is worth recording because the obvious
lesson - "now I know to look for it" - is demonstrably false.

Fixed in the shape already used for the threshold: the constants are written out
(`#expect(minRatio == 0.3)`, `#expect(maxRatio == 1.0)`), the clamp assertions use literals, and - more
useful than either - the **property** is asserted rather than the number:

    #expect(adjusted.duration >= 1800)   // a learned ETA may never be shorter than free-flow

That survives any refactor of the clamp, and it is what actually failed under the mutation.

### The transposed comments, which are the same finding wearing a different hat

`minRatio`'s doc comment described `maxRatio` and vice versa - "cannot be learned as faster than free-flow"
sat above the floor, "nor meaningfully slower than a third" above the ceiling. The reviewer put the two
observations together: **the one constant with no real test was also the one whose comment pointed at the
wrong identifier.** Not a coincidence - a comment nothing checks is a comment nobody reads against the code.
Both rewritten, and `maxRatio`'s now records what happened to it.

### The structural gap behind the blend

`if n == 0` widened to `if n <= 1` - so drive #2 discards drive #1 entirely - was uncaught, because **every
multi-sample test fed identical values**, which makes "blend the new sample in" and "replace the estimate
with it" produce the same number. `laterSamplesBlend` uses heterogeneous samples: ratios 1.0 then 0.5 with
smoothing 0.3 give 0.85 blended and 0.5 replaced.

### The harness, rebuilt

`ops/mutate/corridorspeeds.py`: tracked (the old one was in gitignored `.artifacts/`), mutates both source
files, builds before believing a compile failure, requires a NAMED TEST to fail rather than a non-zero exit,
and reports `trapped` separately.

    caught by a named test: 18   trapped: 0   compile-only: 0   MISSED: 0   of 18
    VACUITY PROOF OK: with no tests present, 0 mutations were reported caught

Nine of the eighteen are numeric-constant mutations, including both clamp ends in both directions, the
smoothing weight, and the badge threshold moved up as well as down. The previous harness had nine mutations
and only one touched a number.
