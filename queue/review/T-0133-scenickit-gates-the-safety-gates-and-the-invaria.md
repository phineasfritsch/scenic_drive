---
id: T-0133
title: ScenicKit Gates: the safety gates, and the invariant that a motorway is penalised and never excluded
state: review
owner: agent/unknown
owner_session: null
claimed_at: 2026-09-08T20:59:29Z
lease_expires_at: 2026-09-08T22:59:29Z
worktree: null
branch: task/T-0133
exclusive: []
touches: [Sources/ScenicKit/Gates/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: agent/reviewer-pr-gates
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - 'swift test --scratch-path .build/T0133 -> Test run with 37 tests in 6 suites passed, exit 0'
  - 'python3 ops/mutate/gates.py -> caught by a named test: 37 of 37   (trapped 0, compile-only 0, MISSED 0, skipped 0), exit 0. Every catch line names the tests: the EQUIVALENT arm prints MISSED      spell a GateReason case fully qualified - the same case either way exit=0  no test objected'
  - 'python3 ops/mutate/gates.py --prove-vacuity -> VACUITY PROOF OK: with the 3 discovered test file(s) emptied, caught=0 (need 0) / and MISSED=37 of 37, exit 0. grep -rlE "\bGates\b|\bGateDecision\b|\bGateReason\b" Tests --include=*.swift lists exactly those 3 files.'
  - 'RED the class (review finding 1): insert if tags["expressway"] == "yes" { return .refused(.noAccess) } above return .allowed plus an untracked control asserting an expressway-tagged trunk is allowed. At 9f3606e: Test run with 34 tests in 5 suites failed ... with 2 issues, failing NAME "control: an expressway-tagged trunk is allowed", exit 1. At this branch: exit 0, no failing names - the branch cannot refuse a freeway. And python3 ops/mutate/gates.py REFUSES exit 2 instead of printing 28 of 28.'
  - 'RED the four survivors, from the harness output: "delete the key filter and refuse expressway=yes" / "...refuse anything with five or more lanes" / "...refuse a maxspeed of 100 or more" -> "a tag key no safety rule is written on cannot change any decision"; "...be thorough about access tags, incl. foot and bicycle" -> that plus "every earlier rule beats every later rule, over all 35 combinable pairs"; "widen consideredTagKeys so a freeway branch would work again" -> "the gate set considers only the tag keys its own rules are written on".'
  - 'RED rule order (review finding 2): "try a locked barrier before access, so a private way blames the gate" and "try smoothness before highway=track, so a rough track blames the surface" -> both "every earlier rule beats every later rule, over all 35 combinable pairs". Both were silent on 9f3606e.'
  - 'RED the unpaved set (review finding 3): "call cobblestone and sett unpaved, refusing a scenic cobbled lane" -> "a cobbled or sett-paved lane is allowed, because those surfaces are paved". Silent on 9f3606e.'
  - 'RED the HEAD check: edit Gates.swift on disk, then python3 ops/mutate/gates.py -> REFUSING: the subject is not what HEAD says it is ... Sources/ScenicKit/Gates/Gates.swift: differs from HEAD, exit 2, before any build.'
  - 'RED the floor: cut the three invariant entries out of MUTATIONS in ops/mutate/gates_corpus.py ON DISK, harness re-run as a separate interpreter -> REFUSING: 34 mutations and 1 equivalent mutants, expected at least 37 and 1., exit 2; gates_corpus.py restored and re-checked against git show HEAD:.'
  - 'Deleting the consideredTagKeys filter (committed in a throwaway worktree): swift test -> Test run with 37 tests in 6 suites passed, exit 0 - the suite does NOT object; python3 ops/mutate/gates.py -> six SKIP ... anchor not found - harness is stale, caught by a named test: 0 of 6 (skipped 6), exit 1.'
  - 'RED known-gap arm: put a mutation that IS caught into KNOWN_MISSED -> KNOWN-GAP ARM FAILED: 0 of 1 stayed MISSED as asserted., exit 1; with one that really is missed, exit 0. Both on a 1-mutation corpus with MIN_MUTATIONS lowered in memory, stated.'
  - 'RED T-0132 decay, on the real three-file split: TEST_FILES pinned to the single old GatesTests.swift path -> VACUITY PROOF FAILED: with the 1 discovered test file(s) emptied, caught=2 (need 0) / and MISSED=0 of 2, exit 1; with discovery, 3 discovered -> VACUITY PROOF OK ... MISSED=2 of 2, exit 0. Two-mutation corpus, floors lowered in memory, stated.'
  - 'bash ops/check-pins -> PINS ok=12 skipped=0 pending=2 expired=0 failed=0 tier=linux, exit 0; --source-only -> PINS ok=5 skipped=9 pending=0 expired=0 failed=0 tier=linux source-only, exit 0'
  - 'bash ops/queue-check -> QUEUE OK (126 tasks), exit 0'
  - 'bash ops/test -> Test run with 37 tests in 6 suites passed, then FAIL: services/api exists but vitest produced no report, exit 1. Pre-existing and environmental (T-0040): services/api/node_modules is absent in this worktree and in the main checkout, and git diff --name-only main...task/T-0133 -- services/ is empty. Checked, not attributed.'
---
## Brief

The gates are the only place this product refuses a road outright, and CLAUDE.md lists the rule they must not
break under **"Product invariants you must not 'optimize away'"**:

> Motorway/trunk ways carry `scenic_score = 0`; they are penalized, **not** hard-excluded (freeway shoulders,
> scenic middle). Hard gates are safety only: unpaved (positive evidence), private/no access, track.

That invariant has already failed once in this repository - the whole-route freeway exclusion made the
flagship Mountain View -> SF fixture unroutable, and the plan records the fix. It is the single easiest thing
for a future agent to "tidy up", because excluding motorways *looks* like exactly what a scenic router should
do, and every short fixture still passes when it does.

### The gates, from the plan

Refuse (`GATE = 0`), on **positive evidence only**:

* `surface` ∈ {gravel, dirt, ground, sand, unpaved, compacted, fine_gravel}
* `highway = track`, or `tracktype` at grade3 or worse
* `smoothness` worse than intermediate
* `access` ∈ {private, no, permit, destination}, or `motor_vehicle = no`
* `barrier = gate` **with** `locked = yes`
* `ford = yes`
* `highway = service` **with** `service` ∈ {driveway, parking_aisle, ...}

Do **not** refuse:

* `highway` ∈ {motorway, motorway_link, trunk, trunk_link} - these score 0 and are penalised by lambda like
  any other dull edge. **This is the invariant.**
* a way with **no** `surface` tag. Absent is not unpaved: most rural lanes have no surface tag, and the plan
  handles them with `×0.8` plus a `surface_unknown` flag rather than a gate. Positive evidence only.
* `barrier = gate` **without** `locked = yes` - it may be openable, and the driver decides.

### What makes this more than a lookup table

**The absent-versus-negative distinction is the whole design.** A gate that fires on a missing tag would
exclude most of the roads this product exists to find. A gate that fires only on a present, positive value
will not. Every gate below needs a test for the tag being *absent* as well as present.

**The parity requirement.** The plan's P-PROD-01 wants one fixture set driven through three implementations -
this one, `services/routing/profiles/*.json`, and the ETL - and asserts they agree. Neither of the other two
exists in this repository yet. So this task builds the **reference** implementation and the fixture set in a
form the other two can consume later; it does not invent their formats. Say so in the source rather than
implying parity that cannot be checked.

### Do

1. `Sources/ScenicKit/Gates/GateDecision.swift` - the verdict, carrying **which** rule fired. A bare `Bool`
   would make `ops/route-autopsy` unable to say why a road was refused, and the plan makes that tool the
   gate-failure playbook.
2. `Sources/ScenicKit/Gates/Gates.swift` - the evaluation, over a plain tag dictionary. Foundation only.
3. Tests pinning, at minimum: every gate firing on its positive value; every gate **not** firing when its tag
   is absent; `barrier=gate` alone not firing while `barrier=gate + locked=yes` does; and - loudest of all -
   **motorway, motorway_link, trunk and trunk_link are NOT gated**, with the reason in the test name.
   Expected values written out as literals, never derived from the rule set under test.
4. `ops/mutate/gates.py` in the corrected shape: pass condition `caught == len(MUTATIONS)`, a catch requires a
   NAMED test, `trapped`/`compile-only`/`skipped` each fail the run, `--prove-vacuity` requires `caught == 0`
   AND `missed == len(MUTATIONS)` and empties **every** test file that could catch a mutation (see
   [[T-0132]]), and an `EQUIVALENT` arm asserted the other way round. The reference implementation is
   `ops/mutate/guidance.py`. **The mutation that matters most is "gate motorways too"** - if the suite does
   not catch that, the suite does not protect the invariant.
5. **No `Package.swift` change**: `Sources/ScenicKit/Gates/` is inside the existing target path.

### Not in scope

The scoring formula, the ETL, the GraphHopper profile JSON, and `services/routing`. This is the gate set and
its refusal reasons. Inventing the profile schema here would be the fabrication this repository exists to
catch.

## Log
- 2026-09-08T23:30:00Z filed by agent/claude-opus-5. Filed at `ready`. Filed with id T-0133 by hand;
  `ops/new-task` allocated T-9902 again - see [[T-0128]].
- 2026-09-08T20:59:29Z claimed by agent/unknown; lease until 2026-09-08T22:59:29Z
- 2026-09-09T00:10:00Z GREEN: `swift test --scratch-path .build-T0133` -> **28 tests in 4 suites passed**. `bash ops/check-pins --source-only` -> `PINS ok=5 skipped=9 pending=0 expired=0 failed=0`. `bash ops/queue-check` -> `QUEUE OK`. ~~Line counts 56 / 90 / 164 / 288, all under the 300 cap.~~ **STRUCK 2026-09-15 (round 3): FALSE WHEN WRITTEN.** `ops/mutate/gates.py` was 307 lines the day this was written, over the cap it claims to be under. Round 2 noted this further down; leaving the sentence standing here meant a top-down reader met the false version first. Current counts are in the round-3 entries below. `ops/mutate/gates.py` committed **100644** (see [[T-0127]]).
- 2026-09-09T00:10:00Z **THE INVARIANT IS THE POINT AND IT IS PINNED TWICE.** CLAUDE.md lists it first: motorway and trunk carry `scenic_score = 0` and are **penalised, not hard-excluded**. `motorwayIsNeverGated` asserts `.allowed` for motorway, motorway_link, trunk and trunk_link, and again for a motorway carrying the tags a real freeway has. The mutation harness attacks it two ways - a literal `highway == "motorway" || == "trunk"` refusal, and the `hasPrefix` form a real "tidy-up" would take, since that is what somebody writes when they think they are being thorough. **Both caught.** ~~There is deliberately no `GateReason` case that could describe a motorway refusal, and `decide` has no branch that could grow one - refusing by omission rather than by a branch, because a branch is something a later edit can invert.~~ **STRUCK 2026-09-15 (round 3): REFUTED, TWICE.** Both reviews of PR #82 added a branch to `decide` that refuses a motorway while reusing `.noAccess`, so the enum was never a guarantee and `decide` grew such a branch six times over. Round 2 removed the equivalent wording from the two source comments but left this sentence standing at the top of the Log, where a top-down reader meets it before the correction. What holds the invariant now is `Gates.consideredTagKeys` plus the behaviour pinned in `GatesInvariantTests`; see the round-3 entries.
- 2026-09-09T00:10:00Z **ABSENT IS NOT NEGATIVE, and that is half the mutation set.** A gate that fires on a *missing* `surface` tag would refuse most of the rural lanes this product exists to find - the plan handles those with x0.8 and a `surfaceUnknown` flag, a note to the driver rather than a refusal. Six mutations turn a positive-evidence rule into an absent-or-present one (refuse a way with no surface tag; refuse any way that has one; refuse every gate rather than only locked ones; refuse `locked=yes` with no barrier; refuse every service way; refuse `ford=no`). All caught, because every rule has a test for its tag being **absent** as well as present.
- 2026-09-09T00:10:00Z `barrier=gate` alone is **allowed**, and only `barrier=gate` + `locked=yes` is refused. An unlocked gate may be openable and the driver can see it; the hazard strip tells them it is there. Refusing every gate would cut off a large share of the ranch and park roads this product is for. Pinned on both sides, plus `locked=yes` with no barrier, which says nothing.
- 2026-09-09T00:10:00Z Boundaries pinned on the allowed side too, since a gate set is only as good as where it stops: `tracktype` grade1 and grade2 allowed while grade3-5 are refused; `smoothness` **intermediate allowed** ("worse than intermediate" means intermediate passes) while bad and worse are refused; `service=alley` allowed while driveway and parking_aisle are refused; `access=permissive` allowed while destination is refused. Four mutations move those boundaries one step in each direction; all caught.
- 2026-09-09T00:10:00Z HARNESS `ops/mutate/gates.py`: **21 of 21 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. `--prove-vacuity` -> `caught=0 (need 0) and MISSED=21 of 21`, OK, exit 0. `KNOWN_MISSED` is **empty**, and that is a claim rather than an omission: every mutation here is expected to be killed by a named test.
- 2026-09-09T00:10:00Z **A REAL DEFECT IN THE HARNESS CONTRACT, found by this harness's own first run.** It reported `baseline does not build; nothing below would mean anything` and exited 2 - while `swift build --build-tests` at the same commit succeeded with no errors. Cause: on this Windows checkout the first build into a *fresh* scratch directory can fail with `unable to create symbolic link ... encountered an I/O error (code: 512)` and succeed immediately after. The mutation loop already built twice before believing a compile failure; the **baseline did not**, so a transient failure aborted the whole run and nothing was ever measured - the harness reporting a hard stop for a reason unrelated to the code. Baseline now builds twice as well. **This applies to every sibling harness** and none of them have it.
- 2026-09-09T00:10:00Z The tests do not commit the defect they exist to guard against. `noMotorwayReasonExists` asserts the complete `GateReason` set as a **written-out literal**, not as a count and not as a filter over `GateReason.allCases` - a count passes when one reason is swapped for another, and a filter over the enum is asking the thing under test what it contains. Every `surface`, `access`, `tracktype` and `smoothness` value is written out rather than looped over `Gates.unpavedSurfaces` and friends, which would assert each set against itself.
- 2026-09-09T00:10:00Z SCOPE HELD, and the limit is stated in the source rather than implied. P-PROD-01 wants one fixture set driven through **three** implementations - this one, `services/routing/profiles/*.json` and the ETL - and asserts they agree. **Neither of the other two exists in this repository.** `Gates.swift` says so in as many words: this is the reference implementation and it is not evidence that anything else agrees with it. No `Package.swift` change - `Sources/ScenicKit/Gates/` is inside the existing target path.
- 2026-09-09T00:10:00Z moved to review/. Reviewer must not be agent/claude-opus-5 (`ops/queue-check`).

### Round 2 — closing the review FAIL on PR #82 (`.artifacts/rv1/pr82.md`)

- 2026-09-15 **THE REVIEWER WAS RIGHT AND I REPRODUCED IT BEFORE TOUCHING ANYTHING.** Against the SHIPPED
  suite (`git show HEAD:Tests/ScenicKitTests/GatesTests.swift` put in place, not the working tree),
  `.artifacts/fix-pr82/phaseA-shipped.log`: `BASELINE exit=0 GREEN`, then **six of seven survivors** —
  `F1 gate one-way motorway_link`, `F2 gate motorroad=yes`, `F4 drop drive-through and emergency_access`,
  `F5 let a graded track through`, `F6 reorder ford before surface`, `F7 reorder access before track`, each
  `exit=0 NO named test objected`. Only `F3 add a GateReason case` was caught, by `no GateReason exists that
  could refuse a motorway` — which is the reviewer's point exactly: that test CAN go red, and the harness
  never once made it do so. **A motorway was refusable with the suite green. The invariant CLAUDE.md lists
  first was not pinned.** Hashes printed before and after; `restore check: CLEAN`.
- 2026-09-15 **THE INVARIANT, PINNED ON BEHAVIOUR THIS TIME.** The old `motorwayIsNeverGated` pinned five
  tag dictionaries and gave only `motorway` a realistic-tags form, so any branch keyed on a SECOND tag was
  invisible — and both refuted branches key on a second tag. `freewayTagsNeverGate` now crosses the four
  freeway `highway` values with **thirteen literal companion tag sets** a freeway really carries (oneway,
  motorroad, lanes, maxspeed, toll, bridge, tunnel, junction, ref, surface, smoothness, and a combined one) —
  52 ways, every input a written-out literal and the expected side the literal `.allowed`, nothing read back
  from `Gates`. Plus two narrow named tests so the harness reports precisely which shape died:
  `onewayRampIsNeverGated` and `motorroadIsNeverGated`. `motorway_link` ways carry `oneway=yes` as a matter of
  course, so refusing them refuses every on-ramp and off-ramp and the freeway shoulder in the middle of a long
  scenic drive becomes unreachable even though the shoulder itself was never refused.
- 2026-09-15 **WHAT I AM NOT CLAIMING (finding 3).** I did **not** make a motorway refusal structurally
  impossible, and I removed the two source comments that said I had. `Gates.swift` used to read "`decide` has
  no branch that could grow one" and `GateDecision.swift` "there is deliberately no case for a motorway"; a
  new branch reuses `.noAccess` and never touches the enum, which is how the reviewer got both branches past a
  closed enum. Both comments now say what actually holds the invariant — the behaviour pinned in `GatesTests`
  — and the suite comment states the residual in as many words: **a branch keyed on a tag none of the 52 cases
  supplies is still invisible.** `noMotorwayReasonExists` keeps its name because it asserts exactly what the
  name says (no case NAMED for a motorway) and nothing more; it now has a mutation behind it, so it has been
  seen red.
- 2026-09-15 **EVERY NEW TEST WAS DEMONSTRATED RED BEFORE IT WAS BANKED.** `.artifacts/fix-pr82/phaseB-fixed.log`,
  the same seven mutations against the fixed suite: **survivors: 0 of 7**, each named:
  F1 -> `a one-way freeway ramp is never gated...` + `no freeway tag combination is gated...`;
  F2 -> `motorroad=yes is never gated...` + `no freeway tag combination...`;
  F3 -> `no GateReason exists that could refuse a motorway`;
  F4 -> `every refused service value is refused...`;
  F5 -> `highway=track is refused whatever else it carries...`;
  F6 and F7 -> `a way that trips two rules reports the first one in the documented order`.
  Not one expected value is computed from `Gates`: every tag dictionary is a literal and every expectation is
  a literal `.allowed` or `.refused(<case>)`. There is no `distance / someConstant` shape here to cancel.
- 2026-09-15 **findings 4, 5, 6 — the three quieter behaviour holes.** `refusedServiceValues` was the only one
  of the five rule sets with neither member-by-member tests nor a shrink mutation; all four members are now
  written out (`drive-through` and `emergency_access` appeared nowhere in the old suite) and
  `shrink refusedServiceValues to the two values the old suite named` is in the corpus. `highway=track` is a
  hard safety gate independent of tracktype, and every old track test supplied either `highway=track` with no
  tracktype or a tracktype on `highway=residential` — `trackIsRefusedRegardlessOfItsOtherTags` combines them.
  **Rule ORDER is behaviour, not formatting**, because `ops/route-autopsy` reads whichever reason fires first:
  `theFirstRuleToFireIsTheReasonReported` pins five two-rule ways, and two reorder mutations are in the corpus.
- 2026-09-15 **HARNESS: the floor is now the real count (finding 7).** `MIN_MUTATIONS = 28` against a
  population of 28 — the old 18-against-21 refused an empty corpus but not a deletion. Measured **on disk**,
  not in memory (`.artifacts/fix-pr82/floor-ondisk.log`): the three invariant entries cut out of
  `gates_corpus.py`, harness re-run as a separate interpreter ->
  `REFUSING: 25 mutations and 1 equivalent mutants, expected at least 28 and 1.` / `exit=2`, and
  `gates_corpus.py after md5 1d8b5fb4... RESTORED`. The corpus now lives in `ops/mutate/gates_corpus.py` and
  the floor in `ops/mutate/gates.py`, so deleting a mutation has to defeat two files — and it put both under
  the 300-line cap (253 / 183) instead of one file at 307.
- 2026-09-15 **HARNESS: `--prove-vacuity` now empties every catching file, and the T-0132 decay is gone
  (finding 8).** `TEST_FILES` is discovered by scanning `Tests/**/*.swift` for `Gates`/`GateDecision`/
  `GateReason` rather than being one hardcoded path under a comment claiming otherwise. Demonstrated both ways
  after splitting the motorway block into `GatesInvariantTests.swift` the way the 300-line cap forces
  (`.artifacts/fix-pr82/attack-3-4-5.log`): with `TEST_FILES` pinned back to the single old path,
  `VACUITY PROOF FAILED ... caught=2 (need 0) and MISSED=0 of 2`, `exit=1` — the decay, reproduced; with
  discovery, `discovered: ['GatesInvariantTests.swift', 'GatesTests.swift']` ->
  `VACUITY PROOF OK ... MISSED=2 of 2`, `exit=0`. `GatesTests.swift` restored (md5 `831433e2...`) and the
  split file removed, both verified in the log. `MIN_TEST_FILES = 1` refuses a discovery that matched
  nothing; it is deliberately **not** a completeness floor, because the count must be free to change on the
  very split it exists to survive, and the comment says so.
- 2026-09-15 **HARNESS: the KNOWN_MISSED arm is executed now, and seen both ways (finding 9).** It was dead
  code — `known = None` was never reassigned, so the comment described an assertion that did not exist and
  line 294 could never print. RED (`.artifacts/fix-pr82/attack-3.log`): assert a mutation that IS caught ->
  `KNOWN-GAP ARM FAILED: 0 of 1 stayed MISSED as asserted.` / `exit=1`. GREEN: assert one that really is
  missed -> `exit=0`. Both probes ran the reduced 1-mutation corpus with the floors lowered **in memory**, and
  that is stated rather than glossed; the real floors are exercised by the unmodified run.
- 2026-09-15 Also closed: the EQUIVALENT arm's only member was NAMED "reorder two independent rules that
  cannot both fire" while being an enum-qualification spelling change — renamed to
  `spell a GateReason case fully qualified`, and the genuine reorders it stood in for are now real MUTATIONS.
  The docstring pointer to `ops/mutate/guidance.py` (no such file on this branch or on main) is dropped rather
  than left dangling. `SCRATCH` moved from `.build-mutate-gates` to `.build/mutate-gates`, which `.gitignore`
  already covers, so a run stops leaving an untracked directory — done inside `ops/mutate/` because
  `.gitignore` is outside this task's `touches:`. The stale line-count claim is superseded below.
- 2026-09-15 **REFUSED — the brief's "fixture set in a form the other two can consume later".** The reviewer
  recorded this as a gap against the brief rather than a false claim, and I am leaving it open on purpose: the
  same brief says under **Not in scope** that inventing `services/routing/profiles/*.json` or the ETL format
  here "would be the fabrication this repository exists to catch", and P-PROD-01 is still
  `assertion: TODO` / `pending: T-0012`. A fixture file in a shape nothing consumes is a guess about two
  schemas that do not exist. It needs its own task once one of the other two implementations lands.
- 2026-09-15 **REFUSED — nothing was banked as an equivalent mutant to avoid work.** The one EQUIVALENT entry
  is the enum-spelling change, and it still goes `MISSED exit=0`, which is what that arm requires. All seven
  survivors the reviewer found changed behaviour and every one was closed with a test, not reclassified.
- 2026-09-15 LINE COUNTS, re-measured with `awk 'END{print NR}'` (the method `ops/lib/check-line-cap` uses),
  replacing the stale `56 / 90 / 164 / 288` claim — which was already wrong as shipped, `ops/mutate/gates.py`
  being **307**: `GateDecision.swift` **57**, `Gates.swift` **97**, `GatesTests.swift` **265**,
  `ops/mutate/gates.py` **253**, `ops/mutate/gates_corpus.py` **183**. No tracked `.swift` file under
  `Sources/` or `Tests/` exceeds 300. Both `ops/mutate/*.py` committed **100644** (T-0127); no new executable
  script, so P-OPS-01 is untouched. Imports: `Foundation` only in the two source files, `Foundation`+`Testing`
  in the tests; no CoreLocation/MapKit/UIKit/SwiftUI/MapLibre/Ferrostar anywhere in the diff. No
  `Package.swift` change.
- 2026-09-15 MECHANICAL. `bash ops/check-pins` -> `PINS ok=12 skipped=0 pending=2 expired=0 failed=0
  tier=linux`, exit 0. `--source-only` -> `PINS ok=5 skipped=9 pending=0 expired=0 failed=0`, exit 0.
  `bash ops/queue-check` -> `QUEUE OK (126 tasks)`, exit 0. `bash ops/test` -> `Test run with 33 tests in 4
  suites passed` then `FAIL: services/api exists but vitest produced no report`, **exit 1 — pre-existing and
  environmental, filed as T-0040**: `services/api/node_modules` is absent in this worktree and in the main
  checkout, so no `TESTS linux=N/F ios=N/F` line is reached. Checked, not attributed. `bash ops/sane` -> exit
  10; T-0133 appears only as `untracked-in-touches: ops/mutate/gates_corpus.py modified:4`, i.e. this
  uncommitted work, and the other ten worktrees flagged belong to other agents.
- 2026-09-15 RESTORE DISCIPLINE. Every probe restored from bytes captured before it ran and the md5 is printed
  on both sides: `reproduce.py` -> `restore check: CLEAN` on both phases; `floor_ondisk.py` -> `RESTORED`;
  `attack.py` probe 5 -> `RESTORED` plus `GatesInvariantTests.swift still on disk: False`. Final
  `git status --porcelain` in this worktree lists only the four intended modifications and the one new file.
  Probes 1-4 never edited a tracked file at all — they load `ops/mutate/gates.py` by path and override module
  attributes in memory.
- 2026-09-15 NOT TRANSITIONED. `state: review` and `reviewer:` left untouched; a different agent reviews this.

### Round 3 — closing the review FAIL on PR #82 (`.artifacts/sg/pr82.md`)

- 2026-09-15 **I REPRODUCED FINDING 1 BEFORE CHANGING ANYTHING**, from bytes, in this worktree
  (`.artifacts/fix2-pr82/repro_f1.log`). `Gates.swift` md5 `3b6ac14e` confirmed identical to `git show HEAD:`;
  the reviewer's line `if tags["expressway"] == "yes" { return .refused(.noAccess) }` inserted above
  `return .allowed`; `swift test` -> `exit=0  Test run with 33 tests in 4 suites passed`;
  `python3 ops/mutate/gates.py` -> `exit=0  caught by a named test: 28 of 28`, and the harness printed the
  MUTANT's md5 `bbfbbc85` as "pristine". Restored to `3b6ac14e`, `git status --porcelain` empty. **A tree that
  hard-excludes every expressway-tagged motorway and trunk way passed both gates this PR shipped.**
- 2026-09-15 **THE CLASS, NOT FOUR MORE INSTANCES.** The previous round answered two refuted branches by
  naming two more companion tags. The reviewer then walked past that suite four more times on keys the
  thirteen companions do not name. Adding `expressway`, `foot`, `bicycle`, `lanes` and `maxspeed` to the cross
  product would have bought a fifth round. `Gates.consideredTagKeys` is the close: `decide` drops every tag key
  no rule is written on **before any rule runs**, so a branch keyed on a freeway tag is dead code the moment it
  is typed. Reviving it takes one of two edits, and both are pinned - widening the set turns
  `the gate set considers only the tag keys its own rules are written on` red by name, and deleting the filter
  while adding the branch turns `a tag key no safety rule is written on cannot change any decision` red
  (sixteen bases x sixteen keys no rule reads, every expectation a written-out `.allowed` or `.refused(<case>)`
  literal, nothing compared to `decide` of anything else). The list **fails toward `.allowed`**: a new rule on a
  key that is missing does nothing until the key is added, which is the right direction for an invariant that
  says penalise, never exclude.
- 2026-09-15 **DECISIVE, AND MEASURED BOTH WAYS** (`.artifacts/fix2-pr82/headcheck-red.log`,
  `control-on-9f3606e.log`). The reviewer's exact one-line edit, plus an UNTRACKED control suite asserting
  `Gates.decide(["highway": "trunk", "expressway": "yes"]) == .allowed`:
  at **9f3606e** -> `Test run with 34 tests in 5 suites failed after 0.141 seconds with 2 issues`, failing NAME
  `control: an expressway-tagged trunk is allowed`, exit 1 - the control is real and the old tree really did
  refuse a freeway; at **this branch** -> exit 0, `failing NAMES: NONE` - the same branch cannot refuse
  anything. Both worktrees restored to their own HEAD md5 with `git status --porcelain` empty and the control
  file deleted.
- 2026-09-15 **EVERY NEW TEST WAS DEMONSTRATED RED BY A MUTATION, AND I READ THE NAME, NOT THE EXIT CODE**
  (`.artifacts/fix2-pr82/final-run.log`; the harness now prints the names itself):
  `delete the key filter and refuse expressway=yes` -> `a tag key no safety rule is written on cannot change
  any decision`; `... and refuse anything with five or more lanes` -> same; `... and refuse a maxspeed of 100
  or more` -> same; `... and be thorough about access tags, incl. foot and bicycle` -> same plus
  `every earlier rule beats every later rule, over all 35 combinable pairs`;
  `widen consideredTagKeys so a freeway branch would work again` -> `the gate set considers only the tag keys
  its own rules are written on`; `try a locked barrier before access` and `try smoothness before highway=track`
  -> both `every earlier rule beats every later rule, over all 35 combinable pairs`;
  `call cobblestone and sett unpaved, refusing a scenic cobbled lane` ->
  `a cobbled or sett-paved lane is allowed, because those surfaces are paved`.
- 2026-09-15 **A CLAIM OF MINE I STRUCK MID-ROUND, BECAUSE I MEASURED IT INSTEAD OF REASONING** (commit
  `5e66bef`). Three comments said the harness catches deletion of the filter because
  *"`drop smoothness from consideredTagKeys` goes MISSED the moment the filter stops being applied"*. Run in a
  throwaway worktree with the filter deleted AND COMMITTED (`.artifacts/fix2-pr82/keys-without-filter.log`):
  that mutation is **still caught, by the literal pin, exit 0**. The sentence was false. This is exactly the
  trap the task brief warns about - the catch would have come from a constants pin next door while the
  behaviour test it was written for passed. What actually objects, measured in the same worktree
  (`filter-removed.log`): `swift test` -> `Test run with 37 tests in 6 suites passed` exit 0, the suite says
  NOTHING; `ops/mutate/gates.py` -> six `SKIP ... anchor not found - harness is stale`,
  `caught by a named test: 0 of 6 ... skipped 6`, **exit 1**, because six mutations are anchored on that line.
- 2026-09-15 **REFUSED - I did not bank "insert a branch on `expressway=` above `return .allowed`" as an
  EQUIVALENT mutant, and it is in neither list.** It cannot change behaviour today, but only because
  `consideredTagKeys` does not list `expressway` - a reason that lives in `decide`'s first line rather than in
  the branch being mutated, and one that EXPIRES the moment somebody widens that set. Banked, it would one day
  fail for the right reason with the wrong message ("a test has an opinion about how the code is WRITTEN").
  The corpus entry that models the real edit replaces the filter line instead, so it changes behaviour and is
  caught by name. `gates_corpus.py` says so where the EQUIVALENT list is defined.
- 2026-09-15 **STILL OPEN, and it is narrower than it was.** Deleting the filter AND keying on a tag that
  neither the thirteen companion sets nor the sixteen noise keys name is invisible to `swift test`. It is not
  invisible to `ops/mutate/gates.py` (six stale anchors, exit 1), but that is the harness, not the suite. A
  refusal on `highway` itself - the one considered key a freeway carries - is covered by the 52-way cross
  product. Both sentences are in `Gates.swift` and in the `GatesInvariantTests` suite comment, as statements
  of what is open rather than of what is impossible.
- 2026-09-15 **FINDING 2 - rule ORDER, pinned as a property instead of five samples.** `GatesOrderTests`
  writes the nine rules out in the documented order with a tag set that trips each and the reason each must
  report, then asserts every earlier rule beats every later one over **all 35 combinable ordered pairs**. The
  one pair that cannot be combined - `highway=track` against `highway=service`, which collide on a key - is
  skipped deliberately and the skip count is pinned at 1, so a collision check that started matching
  everything could not turn the suite into a pass over zero ways. `asserted == 35` is a literal, not
  `n*(n-1)/2`. `theFirstRuleToFireIsTheReasonReported` keeps its five hand-picked pairs; nothing was removed.
- 2026-09-15 **FINDING 3 - the unpaved set, attacked in the widening direction on values the allowed side did
  not happen to cover.** `historicPavedSurfacesAreNotUnpaved` pins cobblestone, sett, unhewn_cobblestone,
  chipseal and concrete:plates as allowed. A cobbled lane is what this product exists to find; making it a
  hard safety refusal is the opposite of the gate set's job.
- 2026-09-15 **FINDING 4 - one type per file.** `GateReason` moved out of `GateDecision.swift` into
  `GateReason.swift`. The corpus entry anchored on `case serviceWay` moved with it (`REASON`), and the runner's
  subject list is now `(GATES, DECISION, REASON)` - so the new file is snapshotted, HEAD-checked and restored
  like the other two.
- 2026-09-15 **HARNESS: a subject that differs from `git show HEAD:` now REFUSES before any build.** This is
  the hole the reviewer's decisive run went through: the harness snapshotted a mutant as "pristine", printed
  its md5 for a human to compare, and certified it `28 of 28`. Subjects AND every discovered test file are
  checked. RED (`headcheck-red.log`): with the expressway line on disk ->
  `REFUSING: the subject is not what HEAD says it is ... Sources/ScenicKit/Gates/Gates.swift: differs from
  HEAD`, exit 2, no build. GREEN: the unmodified run prints `md5 ...  == HEAD` per subject. The restore check
  at the end now compares against HEAD too, not against the in-process snapshot.
- 2026-09-15 **HARNESS: a catch requires a NAMED test and the name is PRINTED.** `FAIL_LINE` used to match
  `Test run with .* failed`, which counts a crash or any non-assertion failure and names nothing - the
  reviewer had to write their own runner to establish the 28 names. It now captures the test name, and a
  non-zero exit with no name stays `trapped`. A regex broken in the over-matching direction still yields
  "names", so the EQUIVALENT arm goes on cross-checking it.
- 2026-09-15 **HARNESS: `MIN_MUTATIONS = 37`, the real population** (28 + 9). RED on disk
  (`floor-ondisk.log`): the three invariant entries cut out of `gates_corpus.py`, harness re-run as a separate
  interpreter -> `REFUSING: 34 mutations and 1 equivalent mutants, expected at least 37 and 1.` / exit 2, and
  `gates_corpus.py` restored and re-checked against `git show HEAD:`. Note the limit, recorded rather than
  claimed as a pass: the floor is a population check, not a content check.
- 2026-09-15 **HARNESS: the T-0132 decay, demonstrated on the REAL three-file split** rather than a synthetic
  second suite (`arms.log`, arms C and D). Discovery finds `GatesInvariantTests.swift`, `GatesOrderTests.swift`
  and `GatesTests.swift`; `grep -rlE '\bGates\b|\bGateDecision\b|\bGateReason\b' Tests --include=*.swift`
  returns exactly those three, checked rather than remembered. With `TEST_FILES` pinned back to the single old
  path -> `VACUITY PROOF FAILED: with the 1 discovered test file(s) emptied, caught=2 (need 0) / and
  MISSED=0 of 2`, exit 1. With discovery -> `VACUITY PROOF OK ... MISSED=2 of 2`, exit 0. The KNOWN_MISSED arm
  re-seen both ways in the same log (arms A and B): `KNOWN-GAP ARM FAILED: 0 of 1 stayed MISSED as asserted.`
  exit 1, then exit 0. All four ran reduced corpora with floors lowered **in memory**, stated rather than
  glossed; the real floor and the real corpus are exercised by the unmodified runs.
- 2026-09-15 LINE COUNTS, `awk 'END{print NR}'`: `GateDecision.swift` **25**, `GateReason.swift` **37**,
  `Gates.swift` **140**, `GatesTests.swift` **283**, `GatesInvariantTests.swift` **99**,
  `GatesOrderTests.swift` **62**, `ops/mutate/gates.py` **299**, `ops/mutate/gates_corpus.py` **264**. Nothing
  over 300. Both `ops/mutate/*.py` still **100644** and the three Swift files 100644 (`git ls-files -s`); no
  new executable script, so P-OPS-01 is untouched. Imports: `Foundation` only in the three source files,
  `Foundation`+`Testing` in the tests. No `Package.swift` change - `Sources/ScenicKit/Gates/` is inside the
  existing target path.
- 2026-09-15 MECHANICAL. `bash ops/check-pins` -> `PINS ok=12 skipped=0 pending=2 expired=0 failed=0
  tier=linux`, exit 0. `--source-only` -> `PINS ok=5 skipped=9 pending=0 expired=0 failed=0 tier=linux
  source-only`, exit 0 (the round-2 acceptance line dropped that trailing text; fixed above).
  `bash ops/queue-check` -> `QUEUE OK (126 tasks)`, exit 0. `bash ops/test` -> `Test run with 37 tests in 6
  suites passed` then `FAIL: services/api exists but vitest produced no report`, **exit 1 - environmental,
  T-0040**, and CHECKED not attributed: `services/api/node_modules` is absent both here and in the main
  checkout, and `git diff --name-only main...task/T-0133 -- services/` is empty. `bash ops/sane` -> exit 10;
  T-0133 appears only as `unpushed:[2 commit(s) not on origin]`, which the push below clears, and the other
  five worktrees flagged belong to other agents.
- 2026-09-15 RESTORE DISCIPLINE. Every probe restored from bytes captured before it ran and then verified
  against `git show HEAD:` rather than trusting a `finally`: `repro_f1.log`, `headcheck-red.log`,
  `control-on-9f3606e.log` and `floor-ondisk.log` each print `== HEAD True` plus an empty
  `git status --porcelain`. The two throwaway worktrees (`.worktrees/T0133-fltr` at a DEMO-ONLY commit with
  the filter deleted, `.worktrees/T0133-old` detached at 9f3606e) were removed with
  `git worktree remove --force`; `git worktree list` no longer lists either. No tracked file in any worktree I
  do not own was written.
- 2026-09-15 NOT TRANSITIONED. `state: review` and `reviewer:` left untouched; a different agent reviews this.
