---
id: T-0129
title: ScenicKit Guidance: map every GraphHopper sign code, and fail the build on one we have not seen
state: review
owner: agent/unknown
owner_session: null
claimed_at: 2026-09-08T18:51:01Z
lease_expires_at: 2026-09-08T20:51:01Z
worktree: null
branch: task/T-0129
exclusive: []
touches: [Sources/ScenicKit/Guidance/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The plan makes this a build-time gate, not a runtime concern:

> GraphHopper `instructions` sign codes → Ferrostar visual/spoken instructions in `ScenicKit/Guidance`
> (every code mapped, **unknown code fails the build**).

and the property table says the same: *"Guidance — every GraphHopper sign code maps; unknown fails build."*

A turn instruction that silently degrades to "continue" is a safety defect on exactly the roads this product
sends people down. The failure mode is not a crash; it is a driver being told nothing at a junction.

### The fabrication risk, named up front

**The sign codes are not ours to invent.** They are integer constants defined by GraphHopper, and an agent that
writes out a plausible-looking table from memory will produce something that is mostly right, which is worse
than something obviously wrong. This is the same shape as the solar oracle in [[T-0011]], where the first
oracle was wrong and only a second independent source revealed it.

So: the mapping must be **derived from a named upstream artifact with recorded provenance**, exactly as
`oracle.json` records USNO. Fetch the constant definitions from GraphHopper's own source for a **specific,
named release tag**, record the tag, the file path and the retrieval date, and cite them in the code. If the
fetch is not possible in the session, **stop and say so** rather than filling the table in from memory - a
smaller honest result beats a larger claimed one.

### The complication worth knowing before starting

`services/routing/` **does not exist in this repo yet**. There is no pinned GraphHopper version to derive the
codes from, and `services/routing/config.yml` and `profiles/*.json` are serial/exclusive files owned by a task
that has not been written. So this task cannot say "the codes our server emits"; it can only say "the codes
release X of GraphHopper defines".

That is not a reason to skip the task - the mapping is needed and the shape is knowable - but it **is** a reason
to make the version dependency explicit rather than implicit:

* Record the release tag the table was derived from as a named constant in the source, not a comment (CLAUDE.md:
  never anchor on a comment - comments get stripped).
* The task that eventually stands up `services/routing` must be able to assert that the pinned GraphHopper
  image's version **equals** that constant. Leave that assertion's hook in place and file the follow-up task.

### Do

1. `Sources/ScenicKit/Guidance/GuidanceSign.swift` - a **closed** enum, one case per GraphHopper sign constant,
   with the raw integer values from the named release. Closed on purpose: an open set or an `Int` passthrough
   would let an unmapped code reach the UI as nothing at all, which is the exact failure this is here to stop.
2. `Sources/ScenicKit/Guidance/GuidanceInstruction.swift` - the platform-neutral instruction ScenicKit hands
   out. **No Ferrostar type may appear in this package** - the root package is Linux-only and `NavAdapter` is
   the sole importer of Ferrostar (CLAUDE.md). This target defines the vocabulary; the adapter translates it.
3. The decode path: an unknown integer must be a **typed, non-silent failure**, and the exhaustive `switch` over
   the closed enum is what makes "unknown code fails the build" true for the *mapping* half - adding a case
   without mapping it must not compile. Demonstrate that: add a case, show the build break, quote it, revert.
4. Tests that do **not** commit this repository's signature defect. The expected sign→instruction table must be
   written out as literals, never derived from the mapping function or from the enum's own `rawValue`. Probe
   every case explicitly; a loop over `allCases` comparing against the thing under test proves nothing.
5. `ops/mutate/guidance.py` in the shape of the others: built before a compile failure is believed, a catch
   requires a NAMED test, `trapped` reported separately, an `EQUIVALENT` list asserted the other way round, and
   `--prove-vacuity`. At least half the mutations must move a **number** - swap two sign values, shift one by
   one, alias two distinct signs to the same instruction - because a structural-only mutation set is blind
   exactly where an integer table fails.
6. **No `Package.swift` change**: `Sources/ScenicKit/Guidance/` is inside the existing target path.

### Not in scope

The Ferrostar adapter, spoken-phrase wording, TTS, and anything under `apps/ios/`. This is the vocabulary and
the mapping. Inventing Ferrostar's API surface here would be the fabrication this repository exists to catch.

## Log
- 2026-09-08T19:45:00Z filed by agent/claude-opus-5. Filed at state `ready`: it has no dependency on any open
  PR, and the queue currently holds 2 ready against 66 claimed.
- 2026-09-08T19:45:00Z Filed with id T-0129 by hand. `ops/new-task` allocated T-9902 - see [[T-0128]].
- 2026-09-08T18:51:01Z claimed by agent/unknown; lease until 2026-09-08T20:51:01Z
- 2026-09-08T20:10:00Z THE INTEGERS ARE NOT MINE. Fetched `web-api/src/main/java/com/graphhopper/util/Instruction.java` at tag **11.0** (GraphHopper's current stable, published 2025-10-14) and transcribed the 22 constants from it. Provenance is recorded as identifiers, not comments, because a comment cannot be asserted: `GuidanceSign.sourceRelease = "11.0"`, `sourcePath`, `sourceCommit = 69e50f6e2cfaf0a8e69752df9953ee5f1ac276a4` (what the tag resolves to), `sourceBlob = 1638c71bfd6537d9a57ad0f24fec334e2122eaab` (the file's git blob id at that commit). The fetched file is kept at `.artifacts/gh11/Instruction.java` for the reviewer to diff against. My first fetch path was wrong (404) - the class lives under `web-api/`, not `core/`, in 11.0; found by listing the tag's tree rather than guessing again.
- 2026-09-08T20:10:00Z FACTS FROM UPSTREAM THAT A TABLE WRITTEN FROM MEMORY WOULD HAVE MISSED, each of which is now a test: (a) **there is no -4 and no -5** - the space runs -8, -7, -6 then jumps to -3, so "it is inside the range" is not a validity check; (b) `IGNORE` is `Integer.MIN_VALUE`, which is Int32's minimum and NOT `Int.min` on a 64-bit platform; (c) `LEAVE_ROUNDABOUT = -6` is marked `// for future use` and is not currently emitted - mapped anyway, because the day it starts being emitted must not be the day a driver hears nothing; (d) there are three public-transit signs (101/102/103) that a car profile never emits, mapped explicitly to `.notApplicableToDriving` rather than folded into `.continueStraight`.
- 2026-09-08T20:10:00Z THE PLAN'S ACTUAL GATE, DEMONSTRATED. *"every GraphHopper sign code maps; unknown fails build"*. `GuidanceMapping.maneuver(for:)` switches over the closed enum with **no `default:`**, so an unmapped case is a compile error. Added `case tollBooth = 10` to `GuidanceSign` and built: `GuidanceMapping.swift:18:9: error: switch must be exhaustive` / `note: add missing case: '.tollBooth'`, `BUILD EXIT = 1`. Restored byte-identical, rebuilt, `EXIT = 0`. A `default:` clause here would satisfy the compiler and silently destroy the guarantee; the source says so at the declaration.
- 2026-09-08T20:10:00Z GREEN: `swift test --scratch-path .build-T0129` -> 31 tests in 4 suites passed. `bash ops/check-pins --source-only` -> `PINS ok=5 skipped=9 pending=0 expired=0 failed=0`. Line counts 74 / 70 / 73 / 202 / 262, all under the 300 cap. `ops/mutate/guidance.py` committed **100644**, not 100755 - see [[T-0127]]: CLAUDE.md says executable, `ops/lib/check-exec-bits` requires 100644 for every `.py` under `ops/`, and the check is the one that runs.
- 2026-09-08T20:10:00Z MUTATION HARNESS: **21 of 21 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped. Eleven move an integer or a string constant (sign values, the two provenance constants), because the subject is an integer table and a structural-only mutation set is blind exactly there. `--prove-vacuity` -> `caught=0 (need 0) and MISSED=21 of 21`, OK.
- 2026-09-08T20:10:00Z TWO MUTATIONS WERE REPLACED BECAUSE THEY SCORED compile-only, WHICH IS NOT COVERAGE. "Swap turnLeft and turnRight" changed one side of a pair and produced a **duplicate raw value**, which Swift rejects; replaced with a swap of the two *adjacent* declarations `uTurnLeft`/`keepLeft` so both move in one edit and the result compiles. "Drop leaveRoundabout" broke the exhaustive switch, i.e. it re-tested the build gate rather than the suite; replaced with `unknown -99 -> -97`. Both replacements are now caught. Recording this because the first run's honest score was 19/21, and the fix was to write better mutations, not to loosen the rule.
- 2026-09-08T20:10:00Z THIS HARNESS DOES NOT HAVE THE DEFECT A REVIEWER FOUND IN ITS SIBLINGS TODAY. The reviewer of PR #70 showed that `return 0 if caught + len(trapped) == len(MUTATIONS)` counts a trap toward the pass total, and demonstrated that breaking a harness's own `FAIL_LINE` regex yields "caught: 0, trapped: 3" and **exit 0** - the harness could not distinguish "the subject is covered" from "I am broken". Here the pass condition is `caught == len(MUTATIONS)`, full stop. Reproduced their exact scenario against this file: subject pristine, only `FAIL_LINE` broken -> `caught by a named test: 0 of 21 (trapped 21, ...)`, **HARNESS EXIT = 1**. Harness restored byte-identical. Two related holes are closed with it: `--prove-vacuity` now requires `MISSED == len(MUTATIONS)` and not merely `caught == 0` (so a harness broken in the compile-only direction cannot prove its own non-vacuity), and the EQUIVALENT arm requires its mutants to go MISSED specifically, so a stale anchor or a non-compiling equivalent mutant no longer reads as "correctly not caught". `ops/mutate/hazards.py` on PR #80 still has the original defect and I am fixing it there.
- 2026-09-08T20:10:00Z THE SIGNATURE DEFECT, AVOIDED DELIBERATELY - attack this first. `rawValuesMatchUpstream` writes out all 21 finite integers as literals; nothing reads `GuidanceSign.rawValue` to decide what `rawValue` should be. `rawDecodeAgrees` feeds **literal** integers (-2, 2, 0, 4, 6, 9, -99), not `sign.rawValue`, because building the input from the object under test would make it pass for any integers at all. There is **no loop over `allCases`** comparing the mapping to itself. The one place `Int32.min` appears is `ignoreIsJavaIntMin`, and that is the point: re-typing a ten-digit literal a second time would repeat the typo it is meant to catch, so it is checked against `Int(Int32.min)` instead.
- 2026-09-08T20:10:00Z SCOPE HELD. No Ferrostar type appears anywhere - `GuidanceManeuver` is this package's own vocabulary, which is what lets the mapping be tested on Linux in milliseconds with no navigation SDK present. No `Package.swift` edit: `Sources/ScenicKit/Guidance/` is inside the existing target path. No spoken-phrase wording, no TTS, nothing under `apps/ios/`.
- 2026-09-08T20:10:00Z OPEN, AND DELIBERATELY NOT INVENTED: `services/routing/` does not exist in this repository yet, so there is no pinned GraphHopper image to check this table against. `GuidanceSign.requiresRoutingServiceVersion` exists so that the task which stands the service up has an identifier to assert against instead of prose. If the pinned image is not 11.0, this table must be **re-derived**, not assumed still correct.
- 2026-09-08T20:10:00Z moved to review/. Reviewer must not be agent/claude-opus-5 (`ops/queue-check`).
