---
id: T-0129
title: ScenicKit Guidance: map every GraphHopper sign code, and fail the build on one we have not seen
state: claimed
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
