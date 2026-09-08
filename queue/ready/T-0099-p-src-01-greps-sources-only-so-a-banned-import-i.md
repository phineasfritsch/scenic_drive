---
id: T-0099
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
