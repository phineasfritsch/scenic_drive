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
acceptance: []
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
- 2026-09-09T00:10:00Z GREEN: `swift test --scratch-path .build-T0133` -> **28 tests in 4 suites passed**. `bash ops/check-pins --source-only` -> `PINS ok=5 skipped=9 pending=0 expired=0 failed=0`. `bash ops/queue-check` -> `QUEUE OK`. Line counts 56 / 90 / 164 / 288, all under the 300 cap. `ops/mutate/gates.py` committed **100644** (see [[T-0127]]).
- 2026-09-09T00:10:00Z **THE INVARIANT IS THE POINT AND IT IS PINNED TWICE.** CLAUDE.md lists it first: motorway and trunk carry `scenic_score = 0` and are **penalised, not hard-excluded**. `motorwayIsNeverGated` asserts `.allowed` for motorway, motorway_link, trunk and trunk_link, and again for a motorway carrying the tags a real freeway has. The mutation harness attacks it two ways - a literal `highway == "motorway" || == "trunk"` refusal, and the `hasPrefix` form a real "tidy-up" would take, since that is what somebody writes when they think they are being thorough. **Both caught.** There is deliberately no `GateReason` case that could describe a motorway refusal, and `decide` has no branch that could grow one - refusing by omission rather than by a branch, because a branch is something a later edit can invert.
- 2026-09-09T00:10:00Z **ABSENT IS NOT NEGATIVE, and that is half the mutation set.** A gate that fires on a *missing* `surface` tag would refuse most of the rural lanes this product exists to find - the plan handles those with x0.8 and a `surfaceUnknown` flag, a note to the driver rather than a refusal. Six mutations turn a positive-evidence rule into an absent-or-present one (refuse a way with no surface tag; refuse any way that has one; refuse every gate rather than only locked ones; refuse `locked=yes` with no barrier; refuse every service way; refuse `ford=no`). All caught, because every rule has a test for its tag being **absent** as well as present.
- 2026-09-09T00:10:00Z `barrier=gate` alone is **allowed**, and only `barrier=gate` + `locked=yes` is refused. An unlocked gate may be openable and the driver can see it; the hazard strip tells them it is there. Refusing every gate would cut off a large share of the ranch and park roads this product is for. Pinned on both sides, plus `locked=yes` with no barrier, which says nothing.
- 2026-09-09T00:10:00Z Boundaries pinned on the allowed side too, since a gate set is only as good as where it stops: `tracktype` grade1 and grade2 allowed while grade3-5 are refused; `smoothness` **intermediate allowed** ("worse than intermediate" means intermediate passes) while bad and worse are refused; `service=alley` allowed while driveway and parking_aisle are refused; `access=permissive` allowed while destination is refused. Four mutations move those boundaries one step in each direction; all caught.
- 2026-09-09T00:10:00Z HARNESS `ops/mutate/gates.py`: **21 of 21 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. `--prove-vacuity` -> `caught=0 (need 0) and MISSED=21 of 21`, OK, exit 0. `KNOWN_MISSED` is **empty**, and that is a claim rather than an omission: every mutation here is expected to be killed by a named test.
- 2026-09-09T00:10:00Z **A REAL DEFECT IN THE HARNESS CONTRACT, found by this harness's own first run.** It reported `baseline does not build; nothing below would mean anything` and exited 2 - while `swift build --build-tests` at the same commit succeeded with no errors. Cause: on this Windows checkout the first build into a *fresh* scratch directory can fail with `unable to create symbolic link ... encountered an I/O error (code: 512)` and succeed immediately after. The mutation loop already built twice before believing a compile failure; the **baseline did not**, so a transient failure aborted the whole run and nothing was ever measured - the harness reporting a hard stop for a reason unrelated to the code. Baseline now builds twice as well. **This applies to every sibling harness** and none of them have it.
- 2026-09-09T00:10:00Z The tests do not commit the defect they exist to guard against. `noMotorwayReasonExists` asserts the complete `GateReason` set as a **written-out literal**, not as a count and not as a filter over `GateReason.allCases` - a count passes when one reason is swapped for another, and a filter over the enum is asking the thing under test what it contains. Every `surface`, `access`, `tracktype` and `smoothness` value is written out rather than looped over `Gates.unpavedSurfaces` and friends, which would assert each set against itself.
- 2026-09-09T00:10:00Z SCOPE HELD, and the limit is stated in the source rather than implied. P-PROD-01 wants one fixture set driven through **three** implementations - this one, `services/routing/profiles/*.json` and the ETL - and asserts they agree. **Neither of the other two exists in this repository.** `Gates.swift` says so in as many words: this is the reference implementation and it is not evidence that anything else agrees with it. No `Package.swift` change - `Sources/ScenicKit/Gates/` is inside the existing target path.
- 2026-09-09T00:10:00Z moved to review/. Reviewer must not be agent/claude-opus-5 (`ops/queue-check`).
