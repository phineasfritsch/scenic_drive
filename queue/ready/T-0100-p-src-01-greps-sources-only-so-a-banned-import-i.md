---
id: T-0100
title: P-SRC-01 greps Sources/ only, so a banned import in a root-package TEST target is invisible
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml, ops/lib/pins_mutation_cases.py]
pins_affected: [P-SRC-01]
reviewer: null
depends_on: [T-0080]
verify: [ops/test, ops/check-pins, ops/pins-mutation]
acceptance:
  - "ops/pins-mutation --pin P-SRC-01 -> 7 killed, 0 survived, 0 gaps (the case is promoted to expect=red)"
  - "RED first: with the current assertion, that same command reports the Tests/ case as SURVIVED"
---
## Brief

Found by `ops/pins-mutation` ([[T-0080]]), which injects each pin's own statement violation and requires the
assertion to go red. P-SRC-01 states *"Root-package targets import Foundation only - never CoreLocation,
MapKit, UIKit, SwiftUI, MapLibre, Ferrostar"*. Its assertion is

    ! grep -rEn '^\s*(@testable\s+)?import\s+(CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)' Sources/

`Sources/` is the whole search path, so the six banned imports are caught there and nowhere else.
`Tests/ScenicKitTests/` is a root-package target too: it builds on Linux CI, `import UIKit` there fails the
Linux build exactly as hard as it would in `Sources/`, and this pin does not see it. The `@testable` branch of
the pin's own regex is evidence the author meant to cover test code - `@testable import` only appears in tests.

The injection is already written and running: `ops/lib/pins_mutation_cases.py` carries it as an
`expect="gap"` case pointing at this task, so the hole is measured on every mutation run instead of being a
sentence in a log. It is exempted there, not skipped.

The fix is one path in the assertion (`Sources/ Tests/`) plus whatever falls out of it, and it belongs to a
task that owns `pins/PINS.yaml` - a pin change needs its own red/green and its own reviewer.

When it lands, flip the case in `ops/lib/pins_mutation_cases.py` from `expect="gap"` to `expect="red"` and
delete the `gap_task`. The runner FAILS if a gap case starts being killed, so this cannot be forgotten: the
mutation run will print `PROMOTE` until the exemption is removed.

## Log
- 2026-09-08 filed by agent/pins-mutation from T-0080's first full mutation run.

- 2026-09-08 — **filed as `T-0099` and renumbered to `T-0100`: that id was allocated twice, minutes apart, on
  two different branches.** `T-0099` on `main` is "every merge-readiness tool enumerates open PRs, so eleven
  branches of work are invisible" — a different finding entirely.

  `next_id()` consults `_ids_in_refs()`, which scans every remote ref precisely to stop this ([[T-0017]]).
  It narrowed the window; it did not close it. Allocation reads the refs and the commit that publishes the
  id happens later, so two allocators that both read before either pushed get the same number. That is not
  a bug in the scan — it is the difference between a read and a compare-and-swap. The claim protocol is
  safe for exactly this reason (`git mv` + push, and a rejected push means someone else won); id allocation
  has no equivalent step.

  Caught by hand while reconciling two agents' output, which is the part that should not be relied on.
  Filed as its own finding rather than fixed here.
