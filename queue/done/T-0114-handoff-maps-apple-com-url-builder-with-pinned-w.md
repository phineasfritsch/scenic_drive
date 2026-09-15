---
id: T-0114
title: Handoff: maps.apple.com URL builder with pinned waypoints, the whole payload of the walking skeleton
state: done
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T13:14:26Z
lease_expires_at: 2026-09-08T15:14:26Z
worktree: .worktrees/T-0114
branch: task/T-0114
exclusive: [Package.swift]
touches: [Package.swift, Sources/Handoff/, Tests/HandoffTests/, ops/mutate/]
pins_affected: []
reviewer: agent/so-pr70
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test -> 51 tests in 8 suites passed, exit 0"
  - "PY=\"${PYTHON:-$(command -v python3 || command -v python)}\"; $PY ops/mutate/handoff.py -> population line reads mutations=39 (floor 30) subjects=2 test files=5 (floor 3), then 39 caught by a named test of 39, trapped/compile-only/MISSED/skipped all 0, 1 equivalent mutant MISSED, exit 0"
  - "RED: $PY ops/mutate/handoff.py --prove-vacuity -> caught=0 and MISSED=39 of 39 with every Tests/HandoffTests file replaced by an empty suite"
  - "RED: $PY ops/mutate/handoff.py --prove-floor -> FLOOR PROOF OK: 5 of 5 arms refused (MUTATIONS empty, MUTATIONS truncated, EQUIVALENT empty, TESTS under floor, HandoffError mutated by nothing) and the control did not, exit 0"
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

> **Correction appended in the fourth pass (reviewer-4's NIT 7).** "122 and 98" is wrong and was wrong when
> it was written: `awk 'END{print NR}'` gave 122 and 103. The sentence above is left as it was written
> because `## Log` is append-only (queue/README.md); **the number to trust is 103.** A count typed from
> memory, in a log whose entire purpose is to be re-run.

### Not fixed, and named

`bash ops/test` still exits 1 with "services/api exists but vitest produced no report" -
`services/api/node_modules` is absent in every checkout on this box. Pre-existing, this PR touches no
TypeScript, and the Swift half is green. Unchanged from the previous pass and still not folded into this
task.

## Fourth fix pass: reviewer4-pr70's two BLOCKING findings, SHOULD FIX 3, 4 and 5, and NIT 6 and 7

**No line of `Sources/Handoff` changed in this pass.** Every one of reviewer-4's findings is a test or a
harness that claimed more than it covered, and the builder was right each time. That is worth saying plainly,
because the tempting way to close a mutation finding is to edit the source until the mutation stops
compiling.

Reproduced before fixing, re-run after. Scripts in `.artifacts/fix70/` (gitignored, evidence for this log):
`subdir_repro.py`, `which_tests.py`, `scan_red.py`. Each reads the pristine bytes first, restores in a
`finally` and prints the md5; `git status --porcelain` after every run showed nothing stray. The floor
demonstration is NOT in `.artifacts/` - see below.

**One thing went wrong in this pass and is worth writing down.** A harness run was killed mid-flight to save
time. `TaskStop` killed the wrapper shell and not the python child, so the `finally` that restores the tree
never ran: `AppleMapsDirections.swift` was left carrying a mutation and all five test files were left as the
empty suites `--prove-vacuity` writes. It was caught by hashing the subject against HEAD, which is the check
that exists for exactly this, and the files were rebuilt and re-verified from scratch. The harness is not
safe to interrupt, and the tree state after an interrupted run is not evidence of anything.

### 1 (BLOCKING) - the source-text check read one directory; SwiftPM compiles the tree

`Package.swift:33` declares `path: "Sources/Handoff"`, which SwiftPM compiles RECURSIVELY.
`HandoffSourceTests.shippingSource()` read it with `FileManager.default.contentsOfDirectory(atPath:)`, which
lists ONE directory. So a locale-bearing helper one level down was compiled, called, and invisible to the
check written to make exactly that impossible - while the file's own doc claimed the allow-list was "closed
where a deny-list is open" and that "no locale-bearing type can be reached without failing it". Third
recurrence of this task's signature defect, inside the fix for the second one.

`.artifacts/fix70/subdir_repro.py`, the reviewer's reproduction, run verbatim on HEAD and then on the fix:

    ARM sub   Sources/Handoff/Fmt/point.swift   before: exit=0, 41 tests passed      <- MISSED
                                                 after: exit=1, 2 issues             <- caught
              failing: every capitalised identifier in the shipping source is on the allow-list
                       the shipping source uses none of the lowercase locale-sensitive spellings
    ARM top   Sources/Handoff/LocalePoint.swift before: exit=1  after: exit=1        <- the control,
              red both times, so the check could always fire on this code where it looked

The scan is now `subpathsOfDirectory(atPath:)`, which recurses, and returns paths relative to the root.

**The completeness guard.** `#expect(files.count >= 2)` could not see a whole directory being skipped,
because both top-level files were still there. Two things replace it, and both had to be seen red:

  * `scanIsRecursive`, a new named test, builds a throwaway tree in the temp directory - `Top.swift`,
    `Fmt/point.swift`, `Fmt/notes.md` - and asserts the walk returns the two `.swift` files including the
    one a directory down. It does not wait for `Sources/Handoff` to grow a subdirectory before it can
    observe anything, which is the whole reason a count floor and a same-shaped second walk are not enough;
  * both source checks now assert `Set(files.map(\.0)) == swiftFilesByHand(under:)` - a hand-written
    recursive walk over `contentsOfDirectory(at:)` and `.isDirectoryKey`, deliberately a DIFFERENT mechanism
    from the scan. A guard that recursed the way the scan does would agree with it by construction, which is
    an expectation computed from the thing it checks.

`.artifacts/fix70/scan_red.py` puts the old `contentsOfDirectory` scan back:

    narrowed, tree exactly as it ships      exit=1  FAILING: the source scan descends into subdirectories
    narrowed + the Fmt/point.swift helper   exit=1  FAILING: the source scan descends into subdirectories
                                                             every capitalised identifier ... allow-list
                                                             the shipping source uses none of the ... spellings

The first arm is the one that matters: the guard fires with `Sources/Handoff` untouched, so it is not
waiting on a layout that does not exist yet.

The harness carries the mutation as **"a locale-bearing helper one directory down, which SwiftPM compiles
and a flat scan cannot see"**. It is the first mutation here that CREATES a file rather than editing one -
`old is None` means create - and the cleanup deletes both the file and the directory it had to make.

### 2 (BLOCKING) - the waypoint cap had no fixture carrying a source

`refusesTruncation`, `capIsInclusive` and the at-cap shape inside `neverAvoidsHighways` were the only
fixtures that reached the cap and all three omitted `source` - the field that exists precisely because the
app knows where the user is standing. Two one-line edits to `url()`'s first line were MISSED with 41 green:

    count the origin as one of the nine pinned stops     MISSED -> caught
      `if waypoints.count + (source == nil ? 0 : 1) > Self.maxWaypoints {`
      caught by: exactly nine pinned stops is allowed WITH an origin - the shape the app always builds
    enforce the cap only when the caller gave no origin  MISSED -> caught
      `if source == nil, waypoints.count > Self.maxWaypoints {`
      caught by: ten pinned stops is refused, not truncated, WITH an origin
                 a refusal emits no URL at all, rather than a shorter drive

The cap moved to its own file, `AppleMapsDirectionsCapTests.swift`, with both shapes enumerated the way
`neverAvoidsHighways` and `noSource` were enumerated in the pass before this one. The counts there are
written out as 9 and 10 rather than reached through `AppleMapsDirections.maxWaypoints`: building the fixture
out of the constant under test is what left the cap without a witness in the first place.

### 3 (SHOULD FIX) - every coordinate fixture sat in one northern, western box

Latitude 34.02..34.09, longitude -118.44..-118.78, in every URL-level fixture in the module. `edgesAreValid`
asserted `throws: Never.self` and nothing about the value that came out, under a name that reads as though
it covered the edge.

    normalise the longitude, which turns the antimeridian into the prime meridian   MISSED -> caught
      `decimal(c.longitude.truncatingRemainder(dividingBy: 180))`
      caught by: a destination in each quadrant reaches Apple unchanged, latitude first
                 the poles and the antimeridian are coordinates, and reach the URL unchanged
    swap latitude and longitude, but only in the southern hemisphere                MISSED -> caught
      caught by: a destination in each quadrant reaches Apple unchanged, latitude first
                 a whole route in the southern hemisphere - source, waypoint and destination all unswapped
                 the poles and the antimeridian are coordinates, and reach the URL unchanged

`edgesAreValid` now asserts the emitted value as a literal at all four pole/antimeridian corners.
`everyQuadrant` adds Reykjavik, Westminster, Ushuaia, Sydney, Nairobi and both antimeridian signs as whole
URLs; `southernRoute` puts a Melbourne-to-Sydney drive through `source`, `waypoint` AND `destination`,
because the quadrant test only ever fills `destination` and a claim about `pair(_:)` proved on one emitter
is the same shape as everything else on this list.

### 4 (SHOULD FIX) - the harness's stated subject was the module, its actual subject one file

`ops/mutate/handoff.py` opened "Mutation harness for Sources/Handoff" while `SRC` named
`AppleMapsDirections.swift` and nothing else. `HandoffError.swift` - public API, `Equatable` with associated
values, a `CustomStringConvertible` description - had zero mutation coverage and zero assertions.

`SUBJECTS` is now a list, every mutation names the file it edits, and `population_floor()` REFUSES to run if
any subject is mutated by nothing. Four mutations land on `HandoffError.swift`, all four MISSED before:

    the too-many-waypoints refusal stops saying how many, and how many are allowed  MISSED -> caught
    count and max swapped in the refusal message                                    MISSED -> caught
      both caught by: the refusal message says how many stops were pinned and what the limit was
    the not-a-coordinate refusal quotes longitude first                             MISSED -> caught
    the not-a-coordinate refusal drops the pair entirely                            MISSED -> caught
      both caught by: the not-a-coordinate message quotes the pair, latitude first

A fifth mutation is mine rather than the reviewer's, and it is the reason `refusalsAreEquatableByPayload`
exists at all. Writing a test with no mutation behind it is writing a check that has never been seen red:

    Equatable stops comparing the payload, weakening every refusal assertion at once  MISSED -> caught
      a hand-written `==` in an extension suppresses the synthesised one; nothing stops compiling, and
      every `#expect(throws: HandoffError.someCase(...))` in the suite silently stops comparing the numbers
      caught by: the two refusals are distinguishable, and so are their payloads

### 5 (SHOULD FIX) - the refusal payload was asserted only by its type

`refusesNonCoordinates` said `#expect(throws: HandoffError.self)` and stopped, so swapping the arguments at
the throw site was MISSED.

    the refusal names the offending coordinate with its arguments swapped           MISSED -> caught
      caught by: the refusal names the coordinate that was refused, latitude first

The fixtures there are asymmetric on purpose - 91 against -12, not 91 against 91 - because a swapped pair is
the mutation in question and a symmetric fixture cannot see it. NaN is deliberately excluded from the
payload assertions and the reason is written in the test: `HandoffError` is `Equatable` and NaN != NaN, so
an `#expect(throws:)` over a payload containing one can never match, which would be an assertion that cannot
pass rather than one that cannot fail - the same defect wearing the other sign.

### 6 (NIT) - an assertion that could not fail

`roundTrip` compared `items(reparsed).map(\.1)` against `items(url).map(\.1)`: the same `URLComponents` parse
run twice over the same string, f(x) == f(x), in a test named for an encoding property it therefore could
not observe. The reparse is now compared against five written-out `name=value` literals, and `%2C` is
asserted absent by name.

### 7 (NIT) - the log's own numbers

"the two new files are 122 and 98" was 122 and 103. `## Log` is append-only, so the third pass's sentence is
left exactly as written and a blockquote immediately under it carries the correction. Editing the number in
place would have made the log agree with itself about a thing that did not happen, which is the same move as
a green test that has never been red.

### The harness gained a floor, and the floor was seen red

`caught == len(MUTATIONS)` is trivially true with an empty list - the same hole reviewer-5 found in
`ops/lib/check-exec-bits`, where `test -z "$(...)"` over an empty file list passed forever. That check
answered with `MIN_FILES`; this one answers with `MIN_MUTATIONS = 30`, `MIN_EQUIVALENT = 1`,
`MIN_TEST_FILES = 3` and the per-subject coverage check, and REFUSES with exit 2 below any of them.

The demonstration is `ops/mutate/handoff.py --prove-floor`, IN THE COMMITTED HARNESS rather than in a
gitignored script, because this task has already shipped an `acceptance:` line naming a file under
`.artifacts/` that no fresh clone could run:

    FLOOR ARM   MUTATIONS emptied - reports success over nothing     MUTATIONS holds 0 entries, below the floor of 30
    FLOOR ARM   MUTATIONS truncated to 5                             MUTATIONS holds 5 entries, below the floor of 30
    FLOOR ARM   EQUIVALENT emptied                                   EQUIVALENT holds 0 entries, below the floor of 1
    FLOOR ARM   TESTS globbed down to 2 ...                          TESTS globbed 2 files from HandoffTests, below the floor of 3
    FLOOR ARM   every HandoffError mutation removed                  these subjects are mutated by nothing: HandoffError.swift.
    FLOOR ARM   CONTROL: unpatched                                   no refusal, as required
    FLOOR PROOF OK: 5 of 5 arms refused and the control did not

Three other harness changes, all from the shared contract:

  * **`TESTS` is globbed, not listed.** The hardcoded list was three files and the suite is now five.
    Reviewer-4's `vacsplit` attack showed the old list failing LOUD on a fourth file rather than silently -
    the right direction, but only because somebody looked. A glob cannot fall behind a split.
  * **the baseline build is retried twice**, like every mutation build already was. T-0132: a first build
    into a fresh scratch directory on this box can fail with "unable to create symbolic link ... I/O error
    (code: 512)", and a transient failure used to abort the whole run with "baseline does not build" having
    measured nothing.
  * **`KNOWN_MISSED` exists and is EMPTY**, which is the claim that every mutation in the list is expected to
    be caught by a named test. Nothing was moved into it. All six of reviewer-4's survivors are in
    `MUTATIONS` with tests behind them; an entry saying "no assertion can kill this" would have been false
    for every one of them, and a false entry there records a closable gap as a feature.

The subject-coverage half of the floor counts `MUTATIONS` only, deliberately not `MUTATIONS + EQUIVALENT`.
An `EQUIVALENT` entry asserts that nothing catches it, so a subject reachable only from that list is still
measured by nothing that HAS to be caught - which is the same "stated subject wider than actual subject"
shape the floor exists to refuse, one level in.

### Caught, and caught by the right test

`caught` alone can mean "caught by something unrelated", which leaves the test that CLAIMS the property
still unable to see the defect. `.artifacts/fix70/which_tests.py` re-runs all eleven new mutations and
prints the failing test NAMES; every mapping above is from that output, and in each case the named test is
the one written for the property. The script reads its mutation list out of `ops/mutate/handoff.py`, so the
two cannot drift.

### Result

    swift test --scratch-path .build/T0114fix   51 tests in 8 suites passed          exit 0
    $PY ops/mutate/handoff.py                   population mutations=39 (floor 30) equivalent=1
                                                  known-missed=0 subjects=2 test files=5 (floor 3)
                                                39 caught by a named test of 39
                                                  (trapped 0, compile-only 0, MISSED 0, skipped 0)
                                                EQUIVALENT: 1 MISSED as required      exit 0
    $PY ops/mutate/handoff.py --prove-vacuity   caught=0 (need 0), MISSED=39 of 39    exit 0
    $PY ops/mutate/handoff.py --prove-floor     FLOOR PROOF OK: 5 of 5 arms refused   exit 0
    bash ops/check-pins                         PINS ok=11 pending=2 failed=0         exit 0
    bash ops/sane                               SANE OK                              exit 0
    bash ops/queue-check                        QUEUE OK                             exit 0

Line counts (`awk 'END{print NR}'`, the method `ops/lib/check-line-cap` uses):

    158 Sources/Handoff/AppleMapsDirections.swift      unchanged this pass
     30 Sources/Handoff/HandoffError.swift             unchanged this pass
    287 Tests/HandoffTests/AppleMapsDirectionsTests.swift
    165 Tests/HandoffTests/AppleMapsDirectionsURLTests.swift
    103 Tests/HandoffTests/AppleMapsDirectionsCapTests.swift    new
    103 Tests/HandoffTests/HandoffErrorTests.swift              new
    178 Tests/HandoffTests/HandoffSourceTests.swift
    600 ops/mutate/handoff.py

Every Swift file is under the 300 cap that P-SRC-02 scopes to tracked `Sources/**/*.swift` and
`Tests/**/*.swift` (`ops/lib/check-line-cap`, `MIN_FILES=5`). `AppleMapsDirectionsTests.swift` at 287 is
the tight one, which is why the cap and the refusals moved to files of their own rather than being added to
it. `handoff.py` at 600 is outside that pin's scope, and it is long: about 230 of those lines are the
mutation table, which is data. Precedent on main is `ops/lib/queue.py` at 372. Named here rather than left
for a reviewer to find, and a reviewer who wants the table split into its own module has a fair case.

Every file this pass wrote is LF in both the index and the working tree (`git ls-files --eol`). The editor
used for it writes CRLF by default, `.gitattributes` is `* text=auto eol=lf`, and `ops/sane` greps every
TRACKED file in the WORKING TREE for a CR - so a CRLF working copy fails the repo-sanity gate with exit 2
even though the blob git stores would be normalised on add.

### Not fixed, and named

`bash ops/test` still exits 1 with "services/api exists but vitest produced no report". `services/api/node_modules`
is absent in every checkout on this box, already filed as T-0040, this PR touches no TypeScript, and the
Swift half is green at 51/51. Unchanged from every previous pass and still not folded into this task.

**PROCESS 8, the expired lease, is not fixed here and not fixed by hand.** `lease_expires_at` reads
2026-09-08T15:14:26Z and the clock is long past it. There is no renewal command - `ops/claim` has no renew
path and nothing under `ops/` writes `lease_expires_at` except the sweeper - so the only way to "fix" it in
this PR would be to retype the field, which is editing the record instead of the process. `ops/queue-check`
is green, T-0131 is already filed for it, and reviewer-4 filed it as an observation rather than a defect of
this PR. Named, not touched.

The residue `HandoffSourceTests` names in its own doc is unchanged and still real: the allow-list is closed
over TYPE names written under `Sources/Handoff`, and a locale consulted through a member of an
already-allowed type would pass both halves. It is stated there, not implied, and it is why the load-bearing
half is the closed one.

- 2026-09-15T05:10:00Z **Finished by the orchestrator after the session that was fixing this ended mid-run.** The agent's work was complete and green; what it had not reached was the restore at the end of its red demonstration. `git status` showed the shipping source modified and tests failing, which reads exactly like a broken fix and is not one - the failing tests WERE the demonstration succeeding.

  Restored with `git checkout --` and re-verified from a clean tree. Nothing was lost: no commit had been
  made, and the mutation was confined to the working tree.

  The generalisation is recorded on [[T-0130]]: a red demo that mutates a tracked file and relies on a
  `finally` to restore it has a window, minutes long, in which the process can die. That is a second source
  of the same hazard the task was filed for, and it needs no second agent.

- 2026-09-15 **Fifth review, PR #70, by agent/so-pr70 (owner agent/claude-opus-5). PASS.** Four detached
  reviewer worktrees, each with its own `--scratch-path`; sources extracted with `git show HEAD:<path>`, never
  copied from a working tree; every subject hashed against HEAD before and after each run. All four worktrees
  end clean with `git hash-object == git rev-parse HEAD:<path>` on every subject and test file.

  **Acceptance, all four re-run and matching character for character**

        swift test --scratch-path .build/rvw-pr70
          Test run with 51 tests in 8 suites passed after 0.058 seconds.            exit 0
        python3 ops/mutate/handoff.py
          population  mutations=39 (floor 30)  equivalent=1  known-missed=0
                      subjects=2  test files=5 (floor 3)
          caught by a named test: 39 of 39  (trapped 0, compile-only 0, MISSED 0, skipped 0)
          EQUIVALENT  MISSED  hardcode the scale ...                                exit 0
        python3 ops/mutate/handoff.py --prove-vacuity
          VACUITY PROOF OK: with no tests present, caught=0 (need 0) and MISSED=39 of 39   exit 0
        python3 ops/mutate/handoff.py --prove-floor
          FLOOR PROOF OK: 5 of 5 arms refused and the control did not               exit 0

  `ops/check-pins` PINS ok=11 skipped=0 pending=2 expired=0 failed=0 exit 0 · `ops/sane` SANE OK ·
  `ops/queue-check` QUEUE OK (104 tasks). `ops/test` exits 1 on `FAIL: services/api exists but vitest produced
  no report`; checked, `services/api/node_modules` is absent on this box, T-0040, not attributed here. The
  line-count table above reproduces exactly (158/30/287/165/103/103/178/600).

  **The round's two BLOCKING closures re-broken rather than re-read.** Eleven mutations of my own, applied to
  the shipped source, with the failing test NAMES recorded:

        recursion  a locale helper TWO directories down, called from decimal()       caught
                   the same helper one directory down, never called                  caught
                     both by: every capitalised identifier ... is on the allow-list
                              the shipping source uses none of the lowercase ... spellings
        scan       the old contentsOfDirectory scan restored, tree EXACTLY as it ships  RED
                     by: the source scan descends into subdirectories
                   scanIsRecursive DISABLED + scan narrowed + helper one dir down       RED
                     by the completeness guard alone: Set(files) == swiftFilesByHand
                   CONTROLS: scanIsRecursive disabled alone -> GREEN; disabled + narrowed
                     with no subdirectory -> GREEN, which is the residue the suite doc states
        cap        the cap is one higher whenever the caller gave an origin          caught
                   truncate (not refuse) whenever the caller gave an origin          caught
                   the refusal reports the CAP as the count, only when a source is present  caught
                   the origin silently dropped once the route is at the cap          caught
                   dedupe before applying the cap / truncate in init()               caught
        error      the pair separated by a semicolon / only the latitude printed     caught
                   the advice dropped / the cap reported as the count                caught

  **Harness attacked by import-and-override; the tracked file was never edited.** `MUTATIONS=[]` -> exit 2
  REFUSING; `EQUIVALENT=[]`, `TESTS=[]` -> refuse; 31 entries with every anchor stale -> all SKIP, exit 1; 30
  no-op edits -> did not land, exit 1; `FAIL_LINE` broken with the subject PRISTINE -> `caught by a named
  test: 0 of 2 (trapped 2)`, exit 1. Baseline build retried twice, as claimed.

  **Three findings, none blocking, all filed with a reproduction and a control.**

  1. `ops/mutate/handoff.py:83` `TESTS = sorted(TEST_DIR.glob("*.swift"))` is NON-recursive, under a comment
     at :82 reading *"A glob cannot fall behind a split."* `Package.swift:39` declares
     `path: "Tests/HandoffTests"`, which SwiftPM compiles recursively - the same mechanism as this round's
     BLOCKING 1, one directory over, in the same commit. With one suite at `Tests/HandoffTests/Sub/`,
     `glob('*.swift')`=5 while `rglob`=6, the subdirectory suite is NOT emptied by `--prove-vacuity`, and the
     proof reports `VACUITY PROOF FAILED: caught=1 (need 0)`, exit 1 - control with no subdirectory, exit 0.
     Not blocking because the failure is LOUD, never a silent green; `rglob` closes it. Same comment at :80
     says the suite "has since split to six"; it is five, and the population line prints `test files=5`.
  2. `Sources/Handoff/AppleMapsDirections.swift:31` declares `Equatable` and nothing asserts it. A
     hand-written `==` returning `true` for every pair SURVIVES all 51 tests and all 39 mutations. Control:
     a test asserting two different plans are `!=` is GREEN on pristine and RED under it. Same gap the owner
     closed one type over this pass; weaker here, because no `#expect` in the module compares two
     `AppleMapsDirections`, so no existing assertion is silently weakened.
  3. The order "cap first, coordinates second" at :72 is not pinned. Hoisting `for w in waypoints { _ = try
     Self.pair(w) }` above the cap SURVIVES: a ten-stop route containing a NaN then refuses with
     `notACoordinate` instead of `tooManyWaypoints`. Control GREEN/RED as above. Both branches refuse and
     neither emits a URL, so only the payload a bug report quotes changes.

  **`queue/LOCKS/Package.swift.lock` is released in this same commit, deliberately.** Moving T-0114 out of
  `claimed/` leaves the lock held by a non-claimed task, and `ops/queue-check` then fails with
  `queue/LOCKS/Package.swift.lock held by T-0114, which is not in claimed/`. CI runs `bash ops/queue-check`
  (`.github/workflows/linux-core.yml`), so a sign-off without the release would turn the branch red and
  `ops/merge` would refuse - a PASS that unblocks nothing. Nothing under `ops/` releases a lock on sign-off:
  `ops/merge` never mentions LOCKS and only `queue-sweep` releases, on lease expiry. Dry-run first: with the
  move alone, QUEUE CHECK FAIL; with the release, QUEUE OK (104 tasks).
