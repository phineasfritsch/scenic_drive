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
  - "swift test -> 36 tests in 5 suites passed, exit 0"
  - "python ops/mutate/corridorspeeds.py -> 27 of 27 caught BY A NAMED TEST (trapped, compile-only, MISSED and skipped all 0), both EQUIVALENT mutants MISSED, exit 0"
  - "RED: python ops/mutate/corridorspeeds.py --prove-vacuity -> caught 0 AND MISSED 27 of 27 with both test files removed"
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

---

## Second fix pass: reviewer-pr75's re-review (FAIL). Three BLOCKING findings, all reproduced first

Every finding below was re-run against the tree the reviewer saw (`LearnedCorridorSpeeds.swift`
md5 `63f529c816a3ca9f022d7bf619174c28`, `CorridorKey.swift` md5 `938ae18bf4c7d587c0fd15c99888fafd`, matching
the report byte for byte) BEFORE anything was changed. Nine mutations, nine MISSED, exit 0 every time. The
same nine after the fix: nine caught, exit 1 every time.

    F1-hashable-ignores-cell   MISSED -> caught      F5-smoothing-0.001   MISSED -> caught
    F1-cell-masked             MISSED -> caught      F5-smoothing-0.15    MISSED -> caught
    F2-guard-dropped           MISSED -> caught      F5-smoothing-0.4     MISSED -> caught
    F2-guard-weakened          MISSED -> caught      F7-record-false      MISSED -> caught
    F4-bucket-forced-utc       MISSED -> caught

### F1 BLOCKING - the `cell` half of the key had never been tested at all

There was a `hoursAreSeparate` and no `cellsAreSeparate`. Every store-level test used ONE cell and every
key-construction test used `cell: 1`, so both halves of `CorridorKey` were nominally covered while only the
hour half actually was. A hand-written `Hashable` combining only `hourOfWeek`, and `self.cell = cell & 0xFFFF`,
each left all 29 tests green.

The user-visible failure is the badge invariant defeated from the inside, and it is worse than an ETA being
wrong: after five crawling drives on a freeway cell, a back road at the same hour that the user has **never
driven** reports `samples=5`, drops the *estimate - no traffic data* badge, and doubles its ETA on somebody
else's evidence. CLAUDE.md's ">= 5 learned samples" is satisfied by five samples of a different road.

`cellsAreSeparate` (store level) plus `cellIsNotTruncated` and `differentCellsAreDifferentKeys` (key level).
The two cell ids differ ONLY above the low sixteen bits, which is what makes the truncating mutant fail;
`cell: 1` survives any mask, which is why nothing had failed before. Equality and hashing are asserted
separately, because a `==` that agrees with a `hash(into:)` that does not is still a broken dictionary key,
and the same-cell direction is asserted too, so a `==` that simply returns false cannot satisfy the test.

### F2 BLOCKING - prior finding #5, not closed the first time and not mentioned in the Log

`adjust`'s guard was still unpinned. `record` has six parameterised cases for exactly this input class;
`adjust` had none. On a corridor learned at ratio 0.75, dropping the guard turns `freeFlow = -600` into
`(-800.0000000000001, learned: true)` and `freeFlow = nan` into `(nan, learned: true)` - a nonsense number
wearing the badge that means "we checked". The weaker `guard freeFlow.isFinite, let r = ...` lets 0 and
negatives through the same way.

`adjustRejectsUnusableFreeFlow` is parameterised over `0, -600, nan, +inf, -inf`, asserts `learned == false`
and that the input comes back untouched. Both reductions are now caught, and both are in the harness.

The honest note about the first pass: this finding was filed, and the fix pass shipped without a test, a
mutation, or a line in the Log about it. Nothing in the process caught that; the reviewer re-running their
own demonstration did.

### F3 BLOCKING - the harness counted a crash as a pass, and it is the shared defect

    return 0 if caught + len(trapped) == len(MUTATIONS) else 1

`trapped` is this file's own name for "non-zero exit with NO named test failing", and its docstring says
that is not a catch. The exit code added it back. Reproduced exactly as filed - the tracked harness, subject
pristine, one trapping mutation (`counts[key] ?? 0` -> `counts[key]!`):

    caught by a named test: 0   trapped: 1   compile-only: 0   MISSED: 0   of 1
    HARNESS EXIT CODE: 0                                        <- the harness said PASS

Rebuilt against the corrected reference (`ops/mutate/guidance.py` on task/T-0129). Same run now:

    caught by a named test: 0 of 1   (trapped 1, compile-only 0, MISSED 0, skipped 0)
    HARNESS EXIT CODE: 1

Four changes, and all four are load-bearing rather than tidying:

  * pass is `caught == len(MUTATIONS)`; trapped, compile-only and skipped each fail the run;
  * SKIP is its own bucket. It used to be folded into MISSED, which reads a stale anchor - a check that no
    longer runs - as a known coverage gap. Those are opposites;
  * `--prove-vacuity` requires `caught == 0` **and** `missed == len(MUTATIONS)`. Demonstrated why, with
    `build()` forced to fail after the baseline: every mutant then scores compile-only, `caught == 0` holds,
    and the OLD rule prints VACUITY PROOF OK for a harness that measured nothing. The new rule exits 1;
  * an EQUIVALENT arm whose two mutants must go MISSED specifically. Reordering `record`'s four independent
    guard conditions and flipping `isConfident`'s comparison cannot change behaviour, so a catch there would
    mean a test has an opinion about how the code is WRITTEN rather than what it DOES. Both MISSED.

Both test files are blanked during the vacuity proof. Splitting the key tests into their own file and
blanking only one would have let the surviving file "prove" the other's non-vacuity - the same shape of
mistake the exit code was making.

**The score dropped and then was earned back.** Under the corrected rule the old 18-mutation set scored
18 of 18 still, but the nine gaps above were outside it. The set is now 27 and the harness's own trapping
self-test fails as it should.

### F6 - the signature defect again, inside the test written to close the last one

`laterSamplesBlend`'s second block said "two samples only, so the value is exactly the blend or exactly the
replacement" and then recorded five, with `#expect(r2 > 0.5)` - true under BOTH hypotheses (0.94855 blended,
0.8285 replaced). The reviewer deleted the first block, left the advertised discriminator standing, and
`if n == 0` -> `if n <= 1` sailed through. The direct discriminator discriminated nothing.

This defect has shipped eleven times across the fleet this session, four of those inside a test written to
close a previous instance, and this is one of the four - the block was added in the last fix pass, in this
file, to close prior finding #4. So both blocks now carry a **written-out literal, arithmetic done by hand**:

    1.0, 0.5, 0.5, 0.5, 0.5  ->  1.0, 0.85, 0.745, 0.6715, 0.62005     (replace lands on 0.5)
    0.5, 1.0, 1.0, 1.0, 1.0  ->  0.5, 0.65, 0.755, 0.8285, 0.87995     (replace lands on 1.0)

The second is the same five ratios in the opposite order, so it also states what "history is retained" means.
Cross-check that costs nothing: the EWMA is affine, so swapping 0.5 and 1.0 throughout maps r to 1.5 - r, and
1.5 - 0.62005 = 0.87995 - the two literals were not transcribed twice from the same slip. Re-ran the
reviewer's attack in both directions: `n <= 1` with the FIRST half deleted is caught, with the SECOND half
deleted is caught, whole test standing is caught. Neither half is decorative now.

### F5 - `smoothing` was pinned from above and at exactly zero, and nowhere else

0.7 fails `ewmaResistsOutliers`; 0.0 fails only because `#expect(after < before)` becomes a tie; 0.4, 0.15
and 0.001 all passed. At 0.001 the suite is green while the model is inert - the reviewer's probe had forty
drives at three times free-flow still reporting 1848 s for a 90-minute drive, `learned == true`, badge off.
That is the headline over-promise, reached through the one constant the suite deliberately left loose, and
the Log said the tolerance was deliberate without saying it was one-sided.

Two fixes, because the two failure directions are different properties. The exact literals above pin the
constant. `consistentlySlowCorridorIsLearned` states the product claim instead: ten free-flow drives then ten
that each took an hour must produce an ETA of at least 55 minutes - 3300 s, written out. At 0.3 it is 3501 s;
at 0.15, 3008 s; at 0.001, 1809 s, which is the free-flow number the badge exists to protect the user from.
0.4, 0.15, 0.001 and 0.7 are all in the harness now, in both directions.

### F4 - the calendar's time zone was never varied

`mondayIsZero` pins `firstWeekday` and sets BOTH calendars to UTC; `sundayIsSix` is UTC too. So the half of
`Calendar` that shifts the WEEK was pinned while the half that shifts the DAY was free, and forcing
`calendar.timeZone = UTC` inside `CorridorKey.init?(cell:date:calendar:)` left everything green. That is
verbatim the failure `mondayIsZero`'s own comment says it prevents, arrived at through the other parameter.

`bucketUsesTheCalendarsTimeZone` uses fixed offsets rather than "Australia/Sydney", deliberately: an
identifier lookup depends on a tzdata snapshot that differs between this box, Linux CI and a future OS
update, and a test whose expected value moves with the host is not a pin. (This box has no tzdata at all -
python's `ZoneInfo("Australia/Sydney")` raises here.) Monday 22:00 UTC read at UTC+10 is Tuesday 08:00,
`hourOfWeek == 32`; the same instant read as UTC is 22. Tuesday 02:00 UTC read at UTC-7 is Monday 19:00,
`hourOfWeek == 19`; as UTC it is 26. All four numbers written out.

### F7 - nothing pinned the accepted path

`rejectsBadSamples` pins `== false` for six bad inputs; nothing pinned `== true` for a good one, so
`return true` -> `return false` was uncaught. `acceptedSampleSaysSo`.

### F8 - the harness scratch directory

`.build-mutate-corridorspeeds/` is not matched by `.gitignore`'s `.build/`, so the command in `acceptance:`
left an untracked directory behind. Moved inside `.build/` rather than widening `touches:` to reach
`.gitignore`, which is a file three other agents are working around today.

### The file split

`LearnedCorridorSpeedsTests.swift` plus everything above is 341 lines, over CLAUDE.md's 300-line cap. The key
tests moved to `Tests/ScenicKitTests/CorridorKeyTests.swift` (`struct CorridorKeyTests`, filename == type
name), which is where the new cell coverage belongs anyway. 286 and 128 lines.

### Verification

    swift test --scratch-path .build-T0118-fix
      Test run with 36 tests in 5 suites passed.                                       exit 0
    python ops/mutate/corridorspeeds.py
      caught by a named test: 27 of 27 (trapped 0, compile-only 0, MISSED 0, skipped 0)
      EQUIVALENT: 2 of 2 MISSED as required                                            exit 0
    python ops/mutate/corridorspeeds.py --prove-vacuity
      VACUITY PROOF OK: caught=0 (need 0) and MISSED=27 of 27                           exit 0
    ops/check-pins    PINS ok=11 pending=2 failed=0                                     exit 0
    ops/sane                                                                            exit 0
    ops/queue-check   QUEUE OK                                                          exit 0

`ops/test` exits 1 on `FAIL: services/api exists but vitest produced no report`. Pre-existing and not this
PR - `git diff --stat main...HEAD -- services/` is empty - and it is not claimed green here, the same way the
reviewer recorded it.

### Deliberately not fixed

The reviewer's closing NOTE, that P-PRIV-05 and P-SAFE-07 are cited in the source and in the tests but are
not in `pins/PINS.yaml`, so `ops/check-pins` enforces neither. They filed it as "not a finding" and confirmed
`pins_affected: []` is correct as written. Adding them would mean editing `pins/PINS.yaml`, which is outside
this task's `touches:` and belongs to whoever owns the pin set. The runtime `#expect(!(learned is any
Encodable))` remains the only enforcement of the Codable ban and still covers exactly these two types; no
serialisation of any kind was added in this pass, and the "add Codable to the key" mutation is still caught.

Task stays in `claimed/`. Moving it to `review/` needs a non-null `reviewer:` or `ops/queue-check` fails and
takes P-PROC-01 red with it, and a fixer does not get to name their own reviewer.
