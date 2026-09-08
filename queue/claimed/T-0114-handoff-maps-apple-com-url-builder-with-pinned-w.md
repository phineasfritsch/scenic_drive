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
touches: [Package.swift, Sources/Handoff/, Tests/HandoffTests/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test -> 29 tests in 4 suites passed, exit 0"
  - "python .artifacts/mutate-T0114.py -> 8 of 8 mutations caught, exit 0"
  - "RED: each of the 8 mutations alone makes swift test exit 1"
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
