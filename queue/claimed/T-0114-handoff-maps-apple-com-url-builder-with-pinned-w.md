---
id: T-0114
title: Handoff: maps.apple.com URL builder with pinned waypoints, the whole payload of the walking skeleton
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T13:14:26Z
lease_expires_at: 2026-09-08T15:14:26Z
worktree: .worktrees/T-0114
branch: task/T-0114
exclusive: [Package.swift]
touches: [Package.swift, Sources/Handoff/, Tests/HandoffTests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test -> 41 tests in 6 suites passed, exit 0"
  - "PY=\"${PYTHON:-$(command -v python3 || command -v python)}\"; $PY ops/mutate/handoff.py -> 28 caught by a named test of 28, trapped/compile-only/MISSED/skipped all 0, 1 equivalent mutant MISSED, exit 0"
  - "RED: $PY ops/mutate/handoff.py --prove-vacuity -> caught=0 and MISSED=28 of 28 with every HandoffTests file replaced by an empty suite"
---
## Brief

**The first app-facing code in this repository.** `apps/ios` currently holds exactly one file, a CI script.
`Sources/` holds Geo, Coordinate, CivilDate and Solar. Everything between a scored road and a person driving
it is unwritten, and this is the piece at the very end of that chain.

It is also the entire free tier. From the plan's feature table, free = *"Plan, preview, hazard strip, Open in
Apple Maps with pinned waypoints"*; in-app turn-by-turn is what the $29.99 buys. So for every user who never
pays, and for the walking-skeleton milestone M1.5, **this URL is the product**. A URL that opens Apple Maps
and navigates somewhere other than the route on screen is the app failing at the only moment most of its
users will ever judge it, with no error and no log line.

### The format is verified, not remembered

Read from Apple's *Adopting unified Maps URLs* documentation on 2026-09-08. The legacy
`maps.apple.com/?daddr=&saddr=` form that everyone remembers is the ARCHIVED `iPhoneURLScheme_Reference`
scheme and is not what this builds. The documented `/directions` parameters are `source`,
`source-place-id`, `destination`, `destination-place-id`, `waypoint`, `waypoint-place-id`, `mode`, `avoid`,
`transit-preferences`, `start`. Coordinates are *"a comma-separated pair of floating point values"*.
`waypoint` is the repeatable one: *"You can specify multiple waypoints by repeating the `waypoint`
parameter."*

**One correction to the plan, which asserts a nine-waypoint limit.** Apple documents NO maximum waypoint
count. Nine is therefore ours, and it is named as ours in the source. Recording it as Apple's limit would
invent a constraint, and would make any later decision to raise it look like a spec violation rather than
the product choice it is.

### What is deliberately not used

`avoid=highways` is documented and is precisely the wrong tool. CLAUDE.md's first product invariant:
motorway and trunk are penalised, **not** excluded, because almost every drive over 15 km needs freeway
shoulders around a scenic middle. The scenic route is already computed with those shoulders chosen on
purpose; asking Apple to avoid highways discards it and re-plans a different drive. There is a test whose
only job is to fail if someone adds that one line.

### What cannot be checked from here, stated so nobody mistakes green for proof

Whether Apple Maps on a real iPhone actually follows the pinned waypoints rather than re-planning
source-to-destination. No unit test can answer that. It needs a phone, it belongs in `pins/PINS.yaml` as
`runs_on: device`, and it is NOT claimed by this task. Green here means the URL is well-formed against
Apple's documented grammar - nothing more.

## Log

- Built `Sources/Handoff/AppleMapsDirections.swift` and `HandoffError.swift`; added the `Handoff` target and
  `HandoffTests` to `Package.swift` (held the `Package.swift` lock for the whole task; `exclusive:
  [Package.swift]` declared at claim time, `queue/LOCKS/Package.swift.lock` created by `ops/claim`).

  `Handoff` depends on `ScenicKit` for `Coordinate` and nothing else, and the dependency must never run the
  other way: ScenicKit is the scoring and routing core and has no business knowing a third-party maps app
  exists. Recorded as a comment on the target because nothing mechanical checks it yet.

### GREEN

    swift test --scratch-path .build-T0114
    Test run with 29 tests in 4 suites passed after 0.035 seconds.    exit 0

### RED, eight ways, each one a change somebody would plausibly make

`.artifacts/mutate-T0114.py` reads the pristine bytes, asserts each mutation landed before trusting a red,
restores from those bytes in a `finally`, and verifies the md5 matches at the end.

    pristine AppleMapsDirections.swift md5 257d654b0f751e580bea4cadfc4f0b32
    BASELINE                                                    exit=0
    caught  truncate instead of refusing                        exit=1
    caught  sort the waypoints, losing the route order          exit=1
    caught  deduplicate the waypoints                           exit=1
    caught  go back to the archived daddr scheme                exit=1
    caught  helpfully ask Apple to avoid highways               exit=1
    caught  apply the 2-decimal privacy rule that governs OUR server, not this URL   exit=1
    caught  off-by-one on the cap, silently dropping a decision point                exit=1
    caught  drop the range check and keep only the NaN check    exit=1
    restored, md5 257d654b0f751e580bea4cadfc4f0b32
    8 of 8 mutations caught                                     exit=0

Every one of those eight produces a URL that opens Apple Maps successfully. That is the shape of the whole
risk here: there is no crash to notice, only a different drive.

### Three decisions worth arguing with

**Refuse, never truncate.** More than nine waypoints throws. Dropping the tail yields a shorter, still
plausible route that is no longer the scenic one - the pinned waypoints ARE the scenic middle. Choosing
which stops matter is the planner's job, upstream.

**Five decimal places, not two.** P-PRIV-05 caps coordinates at 2 dp, and that rule governs what reaches OUR
server, where coarseness is a privacy property we chose. This URL is the user handing their own route to
Apple by tapping a button; 2 dp is about a kilometre and would put the pins on the wrong roads. The mutation
harness includes that confusion as a mutation precisely because it is the plausible mistake.

**The formatter is pinned to `en_US_POSIX`.** `String(format:)` follows the current locale, so on a German
device `34.06890` becomes `34,06890` - a decimal comma inside a comma-separated pair, which parses as four
numbers and navigates into the Gulf of Guinea. The test asserts the property (no comma in the number) rather
than the mechanism, so a different locale-correct formatter stays green.

### Not done, deliberately

No `place-id`, no `avoid`, no `start`, no `transit-preferences`. Each is a documented parameter with no
caller today, and an unused parameter with no test is a place for a wrong default to hide.

---

## Fix pass: four findings from reviewer-pr70, all of them mine and all of them real

The reviewer verified the Apple documentation independently (`/directions`, all ten parameter names, the
coordinate form, and - importantly - that no maximum waypoint count is documented, so naming nine as ours
was correct). Then they attacked the suite and the harness, and found four things.

### 1. The waypoint-order fixture was a palindrome

`[piuma, latigo, piuma]` reads the same backwards, so `for w in waypoints.reversed()` passed a test named
*"waypoints repeat, in the order given"*. The round-trip test could not help: it compares the URL against a
reparse of itself.

Fixed with `[piuma, latigo, latigo, malibu]` - still deliberately out of geographic order, still with a
repeat, but the repeat is at one end so order is observable. The test now also asserts the fixture itself is
not a palindrome, so the next person cannot quietly reintroduce one.

### 2. The locale defence was worth nothing, so the dependency is gone

`String(format:locale: Locale(identifier: "en_US_POSIX"), ...)` looked careful. The reviewer mutated the
locale to `Locale.current` - the obvious simplification, what somebody writes who does not know why the
identifier is there - and every test stayed green, because CI runs on an en_US machine. The German-device
bug the doc comment describes (`34,06890`, a decimal comma inside a comma-separated pair, read as four
numbers) would have shipped with a green suite and a comment explaining why it could not.

**Removed rather than defended.** `decimal` is integer arithmetic and `String(Int)` now, neither of which
consults a locale. There is no longer a line here for a locale change to break, which is better than a test
clever enough to catch one. The replacement arithmetic gets its own cases - rounding up, rounding down, the
carry into the whole part, the negative sign, negative zero, and zero padding - none of which the old
single-value assertion covered either.

### 3. `maxWaypoints` had no witness

9 -> 99 left the suite green: every test reaches the cap through the symbol. Nine is OUR number (Apple
documents no maximum), which makes it a decision that should have to be changed deliberately.
`#expect(AppleMapsDirections.maxWaypoints == 9)`.

This is the same defect I had just found in T-0118's own tests - an assertion parameterised by the value it
is meant to pin - which is a reasonable argument that finding it once does not inoculate you against writing
it again.

### 4. The harness was untracked, and scored a build failure as a catch

`.artifacts/` is gitignored, and the `acceptance:` line named a file in it. From a fresh clone the command
was unrunnable and the red evidence lived only in my worktree. Red evidence that exists only on the machine
that produced it has the same shape as no red evidence.

Worse: it counted ANY non-zero `swift test` as caught. **A mutation that does not compile also exits
non-zero**, so the score would have been identical with every test deleted.

Now `ops/mutate/handoff.py`, tracked, with `touches:` widened to `ops/mutate/` and disclosed here. Each
mutation is BUILT first; a compile failure is reported as `compile-only` and does not count. A run must also
see a named test fail, not merely a non-zero exit.

**Writing that check found a bug in the check.** The first version matched Swift Testing's `U+00D7` failure
glyph, and `subprocess` was decoding the child's UTF-8 output with the Windows code page, so the glyph
arrived mangled and **all twelve mutations reported as `compile-only`** - a harness silently classifying
every real catch as a non-catch. Both halves are fixed: the runs decode as UTF-8, and the pattern is ASCII
(`recorded an issue`) so no decoding question can reach it again.

### The harness is now demonstrated non-vacuous

Not argued - run. With `AppleMapsDirectionsTests.swift` replaced by an empty suite:

    caught by a named test: 0 ... MISSED: drop the range check ... truncate the coordinate ...
    lose the sign on a southern or western coordinate ... stop zero-padding the fraction

Every mutation reports MISSED, which is the proof that the harness measures this suite rather than the Swift
compiler. Restored, and the source md5 is unchanged: `887a32aee0044fd817dbdaa58a3c331e`.

### Result

    swift test                    30 tests in 4 suites passed          exit 0
    python ops/mutate/handoff.py  12 caught by a named test,
                                  0 compile-only, 0 MISSED, of 12      exit 0

Four mutations are new, covering the three findings above: `reverse the waypoint order`, `raise the cap from
9 to 99`, `truncate the coordinate instead of rounding it`, `lose the sign on a southern or western
coordinate`, and `stop zero-padding the fraction`.

### Not fixed, and named

The reviewer notes `bash ops/test` exits 1 with *"services/api exists but vitest produced no report"* -
`services/api/node_modules` is absent in every checkout on this box. It is pre-existing, this PR touches no
TypeScript, and it means the declared `verify: [ops/test, ops/check-pins]` cannot currently pass here.
`ops/check-pins` is green (exit 0). I am not folding an unrelated environment failure into this task.

---

## Second fix pass: reviewer2-pr70 confirmed all four findings closed, then found three more

They verified the closures by RUNNING them rather than reading the diff - re-applying the reversal mutation
(now red), restoring the palindromic fixture (now red on the new anti-palindrome guard), lowering the cap
(red), and putting a deliberately non-compiling mutation through the tracked classifier to confirm it prints
`compile-only ... NOT a test catch` and is excluded from the count.

### A - the `source` parameter was emitted and asserted by nothing (BLOCKING)

Three mutations, all green against 30 tests:

  * emit the source under another documented name (`start`);
  * emit it as `source-place-id`;
  * **validate the source and then send the DESTINATION's coordinate as `source`.**

That last URL tells Apple Maps the drive starts where it ends.

Why nothing saw it: `refusesNonCoordinates` guards only the *validation call*, so keeping
`try Self.pair(source)` leaves the value free. `onlyDocumentedParameters` asserts every emitted name is a
MEMBER of the documented set - never which names must appear - so it would pass over an empty query string.
`roundTrip` compares the URL against a reparse of itself, and its only literal is the destination. Of the
four things `url()` emits, three had a value assertion and `source` had none.

Closed with `sourceValueIsPinned` (literals, not `pair(...)`, so the assertion does not run through the code
it checks) and `requiredParametersArePresent`, which checks the direction membership cannot.

### B - a test whose NAME promised a property it could not observe (BLOCKING)

`the coordinate format consults no locale at all` was green under a mutant using `Locale.current`, while the
same body pinned to `de_DE` went red - proving the locale path is live and the test simply cannot see it.
Deleting the dependency was right; leaving a test named for a property nothing checks is the same shape as
the finding it replaced, one level up.

Renamed to what it pins. The no-locale property is now checked separately by `noLocaleInTheSource`, anchored
on identifiers in the shipping sources - comments excluded, because the file discusses `String(format:)` at
length to explain why it is gone, and failing on that prose would be anchoring on a comment.

### C - a constant that no longer governed the value it named, in the fix (BLOCKING)

    let scale = 100_000    // 10^coordinateDecimals, see the assertion below

**There was no assertion below.** The reviewer grepped Sources, Tests and `pins/PINS.yaml`. The padding loop
read `coordinateDecimals`; the scale did not. Setting it to 2 produced `34.6890` - not a coarser coordinate
but a different one, about 69 km north - so the harness mutation named "apply the 2-decimal privacy rule"
was being caught for a reason unrelated to the confusion it is named for.

This repository's signature defect, in code added to fix that same defect class, with a comment pointing at
a check that does not exist. The scale is now derived from the constant, and `scaleFollowsTheConstant` is
the assertion the comment used to promise - written as a property that holds for ANY precision (the fraction
has exactly `coordinateDecimals` digits) rather than as a claim about 5.

### D - a doc comment describing the mechanism its own commit deleted

`pair(_:)` still explained the `String(format:locale:)` call, fifteen lines above a comment explaining at
length why it was gone. Both cannot be true. Rewritten.

### The harness gained a category: EQUIVALENT MUTANTS

Hardcoding the scale on its own reported MISSED, and that is correct - with `coordinateDecimals` at 5 the
derived value IS 100_000, so the output is byte-identical and no test can tell. **A harness that demands an
equivalent mutant be caught is demanding the impossible**, and the way a person satisfies it is by anchoring
a test on the source text, which CLAUDE.md forbids.

So equivalent mutants are asserted the other way round: they are run, and **a catch is a failure**, because
it means a test has an opinion about how the code is written rather than what it does. The real protection
is the two-step regression - hardcode now, change the precision later - which is a separate mutation and is
caught.

    caught by a named test: 20   trapped: 0   compile-only: 0   MISSED: 0   of 20
    EQUIVALENT MUTANTS - a catch is a FAILURE
    MISSED      hardcode the scale to the value coordinateDecimals currently derives
    VACUITY PROOF OK: with no tests present, 0 mutations were reported caught

`--prove-vacuity` was also added, which acceptance line 3 named and the harness did not have.

---

## Third fix pass: reviewer3-pr70's six BLOCKING findings, plus 7, 8 and the two they found unanswered

Every finding below was reproduced before it was fixed and re-run after. The scripts are in `.artifacts/`
(gitignored, evidence for this log): `missed_to_caught.py`, `which_tests.py`, `scale_named_test.py`,
`trap_before_after.py`, `make_brokenregex.py`, `make_holes.py`. All of them read the pristine bytes first,
restore in a `finally`, and print the md5 at the end; `git status` after every run showed no stray file.

### The five source mutations, MISSED -> caught, run both ways

`.artifacts/missed_to_caught.py` puts each of the reviewer's mutations through the suite AS THEY FOUND IT
(HEAD's source, HEAD's single test file, the two new files absent) and then through today's suite:

    M3 avoid=highways only when waypoints.isEmpty        before=MISSED      after=caught
    M1 mode raw values renamed to walk/public/bike       before=MISSED      after=caught
    M6 NumberFormatter().decimalSeparator                before=MISSED      after=caught
    M2 waypoints.first promoted to source                before=MISSED      after=caught
    M4 destination emitted twice                         before=MISSED      after=caught
    M5 a scale one decade too small                      before=caught      after=caught

M5 reads "before=caught" because the reviewer filed it as a CONTROL, not a miss - see SHOULD FIX 7 below.

`caught` is not enough on its own, because it can mean "caught by something unrelated". `which_tests.py`
prints the failing test NAMES, and in each case the test that claims the property is among them:

    NumberFormatter().decimalSeparator   -> every capitalised identifier ... is on the allow-list
                                            the shipping source uses none of the lowercase ... spellings
    avoid=highways only when isEmpty     -> avoid=highways is never emitted, in any shape a caller can build
    mode raw values renamed              -> each mode reaches the URL as the exact string Apple documents
    waypoints.first promoted to source   -> the source is omitted when there is none, and never invented
    destination emitted twice            -> nothing is emitted twice - not source, not destination, not mode

All six are now in `ops/mutate/handoff.py`, which is why they cannot silently reopen.

### 1 (BLOCKING) - avoid=highways, guarded by `waypoints.isEmpty`, violating the first product invariant

`neverAvoidsHighways` said it asserted the invariant "at the one place it could be violated by a one-line
fix" and had exactly one fixture, which carried a waypoint. So the one-line fix in the OTHER branch - the
branch that serves every short drive and every first plan - passed it. Motorway and trunk are penalised, not
excluded; asking Apple to avoid them discards the computed route and re-plans a different drive.

Now six shapes, empty waypoints first, and `start` and `transit-preferences` checked alongside `avoid`
because they are the other two documented ways to make Apple re-plan rather than reproduce. The whole query
string is also written out as a literal for five shapes in the new `AppleMapsDirectionsURLTests`, so the
extra parameter fails four more tests as well.

### 2 (BLOCKING) - the mode loop recomputed its expectation from the object under test

    for m in Mode.allCases { #expect(emitted(m) == m.rawValue) }

passes for any raw values at all. Renaming walking/transit/cycling to `walk`/`public`/`bike`, which Apple
does not document, was green; only `driving` had a literal witness. Replaced by four whole URLs typed out
one per case, plus `allCases.count == 4` and a check that every case has an entry in the table - by CASE
identity, not by raw value, so a rename cannot satisfy it.

### 3 (BLOCKING) - a deny-list of two spellings named as if it covered a class

`noLocaleInTheSource` was called "no locale is consulted anywhere in the shipping source" and grepped for
`String(format:` and `Locale`. `NumberFormatter().decimalSeparator ?? "."` contains neither, and the
reviewer showed the separator IS locale-derived on this toolchain - so the German-device bug was live again
behind a green suite, for the third time in this PR.

**Deny-lists cannot be complete, so the load-bearing check is now an ALLOW-list**, in the new
`HandoffSourceTests`: every capitalised identifier in `Sources/Handoff` must be one on a list transcribed by
hand. `NumberFormatter` is not on it, and neither is any other type a future edit reaches for without saying
so. That check's stated scope and its coverage are the same sentence, which is the part the last two
versions got wrong. A five-entry deny-list survives only for the lowercase spellings an allow-list of TYPE
names cannot see (`String` is allowed, `format:` is an argument label), and its name now claims exactly that
and nothing more.

Two costs, both named rather than implied. The allow-list must be edited when a new type legitimately
arrives - that is the gate working, the check fails first and the argument happens second. And the residue:
the allow-list is complete for TYPE names, so no locale-bearing type can be reached without failing it, but
the deny-list half is a list of spellings and cannot be complete. A locale consulted through a member of an
already-allowed type (`Array`, `String`, the numeric types, the three URL types) would pass both. That is
the whole remaining surface, and it is why the load-bearing half is the closed one.

### 4 (BLOCKING) - the first waypoint promoted to source

`noSource` built a destination-only route, so `else if let first = waypoints.first` was unreachable from it,
and every waypoint-bearing fixture elsewhere passed a source. The URL starts the drive at the first pinned
stop instead of where the user is. `noSource` now runs three fixtures, two of them with waypoints, and also
refuses `source-place-id` and `start`; `waypointsWithoutASource` pins the whole query string for that shape.

### 5 (BLOCKING) - destination emitted twice

`source` had an exactly-once assertion and `destination` had none, and every reader uses `.first { ... }`.
Added for `destination` and `mode` in `sourceValueIsPinned`, plus `nothingIsEmittedTwice` across three
shapes, plus the five written-out query strings.

### 6 (BLOCKING) - the shared harness defect, on the file where it was found

    return 0 if caught + len(trapped) == len(MUTATIONS) and not wrongly_caught else 1

`trapped` is this file's own name for "non-zero exit, no named test failed" - what its docstring calls not a
catch - added back into the pass total. Reproduced on a copy of the shipped harness with the subject
PRISTINE and only `FAIL_LINE` broken (`.artifacts/make_brokenregex.py`, three mutations to keep it cheap):

    caught by a named test: 0 of 3   (trapped 3, compile-only 0, MISSED 0, skipped 0)
    OLD RULE  caught + trapped == len(MUTATIONS)  -> exit 0
    NEW RULE  caught == len(MUTATIONS)            -> exit 1

The other two holes, each on its own copy (`.artifacts/make_holes.py`):

    hole 2  --prove-vacuity with build() broken after the baseline:
            caught=0, compile-only=2, MISSED=0
            OLD RULE  caught == 0                     -> exit 0
            NEW RULE  caught == 0 and MISSED complete -> exit 1
    hole 3  EQUIVALENT anchor made stale:
            SKIP  hardcode the scale ... anchor not found - the harness is stale
            OLD RULE  equivalent arm inspects only eq_caught -> eq_ok=True
            NEW RULE  equivalent arm needs MISSED complete   -> eq_ok=False   exit 1

Fixed to the reference on `task/T-0129` (`ops/mutate/guidance.py`, read, not guessed): the pass condition is
`caught == len(MUTATIONS)`; trapped, compile-only and skipped each fail the run; `--prove-vacuity` needs
`caught == 0` AND `missed == len(MUTATIONS)`; the EQUIVALENT arm needs its mutants MISSED specifically; SKIP
is its own bucket and is never folded into MISSED.

**The honest number.** Under the strict rule the shipped run is **28 caught of 28, with trapped,
compile-only, MISSED and skipped all 0** - it did not drop, because this subject's trapped bucket is empty.
It was not always: the reviewer's own demonstration used `coordinateDecimals -> 0`, which trapped inside
`(1..<0)`. `.artifacts/trap_before_after.py` runs both arms -

    BEFORE (HEAD source, HEAD tests)  coordinateDecimals -> 0 : trapped
    AFTER  (today's source and tests) coordinateDecimals -> 0 : caught

- so that mutation can now sit in MUTATIONS under a rule that refuses to count traps. The old rule was not
hiding a miss in this subject today; what it was hiding is a BROKEN HARNESS, and that is what the three
copies above demonstrate. Eight mutations were added, so the count went 20 -> 28 for reasons that are all
new coverage, not a relaxed rule.

### 7 (SHOULD FIX) - the test named for the scale never fired on a wrong scale

Confirmed, then closed. `.artifacts/scale_named_test.py` lists the failing test names for a scale one decade
too small:

    BEFORE:  a coordinate is a comma-separated pair at five decimals
             the built URL survives a parse ...
             the coordinate arithmetic rounds, signs, pads and carries correctly
             the source carries the origin ...                       <- scaleFollowsTheConstant absent
    AFTER:   ... and "the scale is ten to the coordinateDecimals - a decade either way changes the
             coordinate", in BOTH directions (too small and too large)

Its assertions used to hold for every scale up to 10^5, and `fraction.count ==
AppleMapsDirections.coordinateDecimals` was an assertion stated in terms of the constant it checks. It now
pins four values with five distinct decimal digits, which survive the round trip at 10^5 and at no other
scale. Both decades are mutations in the harness.

### 8 (NIT) - a public constant whose own function could not survive one of its values

`(1..<coordinateDecimals).reduce(10)` is `(1..<0)` at zero, a Swift precondition failure. Folding over
`0..<coordinateDecimals` from 1 gives the same 100000 at five decimals and an empty fold at zero. The doc
comment now states the range, and `coordinateDecimals -> 0` is a harness mutation that is CAUGHT rather than
a crash - which is what emptied the trapped bucket, above.

### 9 (PROCESS) - R2-E and R2-G, filed twice and answered in neither log

Both fixed, neither declined:

  * **R2-E** `waypointOrder` compared `pair()` output to `pair()` output, so it agreed with the builder
    about the order by construction. The four expected values are now written out as literals.
  * **R2-G** the harness left an untracked `.build-mutate-handoff/`, because `.gitignore` has `.build/` and
    not `.build-*/`. The scratch path is now `.build/mutate-handoff`, which the existing rule already covers
    - a one-line fix inside `touches:`, rather than widening `touches:` to reach `.gitignore`. `git status`
    after a full harness run is clean.

### Result

    swift test --scratch-path .build/T0114     41 tests in 6 suites passed          exit 0
    $PY ops/mutate/handoff.py                  28 caught by a named test of 28
                                               (trapped 0, compile-only 0, MISSED 0, skipped 0)
                                               EQUIVALENT: 1 MISSED as required      exit 0
    $PY ops/mutate/handoff.py --prove-vacuity  caught=0 (need 0), MISSED=28 of 28    exit 0
    bash ops/check-pins                        PINS ok=11 pending=2 failed=0         exit 0
    bash ops/sane                              SANE OK                              exit 0
    bash ops/queue-check                       QUEUE OK (104 tasks)                  exit 0

`AppleMapsDirectionsTests.swift` was held at 296 lines by moving the mode assertions and the source-text
check out; the two new files are 122 and 98. Nothing is over the 300 cap.

### Not fixed, and named

`bash ops/test` still exits 1 with "services/api exists but vitest produced no report" -
`services/api/node_modules` is absent in every checkout on this box. Pre-existing, this PR touches no
TypeScript, and the Swift half is green. Unchanged from the previous pass and still not folded into this
task.
