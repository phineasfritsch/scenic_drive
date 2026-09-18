---
id: T-0135
title: services/routing: assert the pinned GraphHopper image version equals GuidanceSign.sourceRelease
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/routing/, pins/PINS.yaml, ops/lib/]
pins_affected: [P-ROUTE-01]
reviewer: null
depends_on: [T-0031]
verify: [ops/test, ops/check-pins]
acceptance:
  - "bash ops/check-pins -> P-ROUTE-01 carries an assertion (no pending:) and passes against the pinned image"
  - "RED: the pinned GraphHopper version edited to 10.2 -> ops/check-pins exits 1 naming P-ROUTE-01"
  - "RED: GuidanceSign.sourceRelease edited to 10.2 -> the same assertion fails, proving it compares two independently-sourced values and not one against itself"
---
## Brief

`GuidanceSign` (T-0129) transcribes GraphHopper's 22 sign constants from **release 11.0** and records that
release as an identifier, `GuidanceSign.sourceRelease`, so that a check can assert it. Nothing asserts it yet,
because `services/routing/` does not exist: T-0129 could only say "the codes release 11.0 defines", never "the
codes our server emits".

This task closes that gap. When the routing service is stood up with a pinned GraphHopper image, the pinned
version and `GuidanceSign.sourceRelease` must be compared, and the comparison must be a check that runs - pin
**P-ROUTE-01**, which today carries `pending: T-0135` and therefore fails `ops/check-pins` the moment this task
reaches `queue/done/` without an assertion behind it.

Why it matters: the sign space is not stable across releases. 11.0 declares no `-4` and no `-5`; a release that
fills those in, renumbers `FERRY`, or adds a code makes the shipped table quietly wrong, and a wrong table is a
driver told nothing - or told the wrong thing - at a junction. The mapping is guarded by the compiler for signs
this build knows about (`GuidanceMapping` has no catch-all, enforced by `ops/lib/check-guidance-gate` and by the
named test `signSwitchHasNoCatchAll`), but nothing can notice that the *router* moved underneath us.

### Do

1. Write P-ROUTE-01's assertion and delete its `pending:` line. It compares two independently-sourced values:
   the version pinned for the GraphHopper container (image tag / `services/routing/config.yml` - whatever the
   routing task actually pins) and the string `GuidanceSign.sourceRelease` read out of
   `Sources/ScenicKit/Guidance/GuidanceSign.swift`. Neither side may be computed from the other: reading the
   image tag and then asserting it equals itself is this repository's signature defect and would pass for every
   possible release.
2. Demonstrate it RED twice, and record both runs: once with the pinned image edited to a different release,
   once with `sourceRelease` edited to a different release. A check that only goes red when one of the two moves
   is comparing something against a constant.
3. If the pinned image is **not** 11.0, the sign table must be **re-derived** from that release's
   `Instruction.java` - not assumed still correct. Record the new `sourceCommit`/`sourceBlob` the way T-0129 did
   and re-run `python ops/mutate/guidance.py`.

### Not in scope

Standing the routing service up - that is T-0031. This task is the assertion and the pin, and it cannot land
before there is a pinned image to read.

## Log
- filed by the fixer of PR #81, closing blocking finding F1 of the review of T-0129: `requiresRoutingServiceVersion`
  is a name that claimed a requirement nothing required. The obligation now lives in a queue task and in a pin
  with `pending: T-0135`, not in the log of a closed task.
