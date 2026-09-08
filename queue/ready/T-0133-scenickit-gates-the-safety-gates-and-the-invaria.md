---
id: T-0133
title: "ScenicKit Gates: the safety gates, and the invariant that a motorway is penalised and never excluded"
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/Gates/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: null
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
