---
id: T-0100
title: P-SRC-01 greps Sources/ only, so a banned import in a root-package TEST target is invisible
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T08:45:02Z
lease_expires_at: 2026-09-08T11:45:02Z
worktree: null
branch: task/T-0100
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
- 2026-09-08T08:45:02Z claimed by agent/claude-opus-5; lease until 2026-09-08T11:45:02Z

- 2026-09-08 — **closed, and measured by the tool that found it.**

  `pins/PINS.yaml` P-SRC-01 now searches `Sources/ Tests/`. The assertion passes on the tree as it stands,
  so the widening adds coverage without a pre-existing violation to fix first.

  **RED** — `ops/pins-mutation --pin P-SRC-01` before the change:

        GAP       P-SRC-01  import UIKit in Tests/ScenicKitTests/GeoTests.swift (test target)
                            (survives; T-0099 owns it)
        PINS-MUTATION mutable=9 covered=1 cases=7 killed=6 survived=0 gaps=1 errors=0

  **GREEN** — after:

        PINS-MUTATION mutable=9 covered=1 cases=7 killed=7 survived=0 gaps=0 errors=0
        real exit 0

  The exemption is promoted, not deleted: `expect="gap"` becomes `expect="red"` and `gap_task` is dropped.
  The runner FAILS when a gap case starts being killed, so this could not have been forgotten — it would
  have printed `PROMOTE` on every run until somebody did it. That is the design working, and it is worth
  saying that the hole was found, tracked, and closed without a human remembering anything.

  **A stale pointer this uncovered, which is worse than a broken one.** The exemption read
  `gap_task="T-0099"`, and the runner printed *"survives; T-0099 owns it"*. That sentence was false: this
  task was FILED as T-0099 and renumbered to T-0100 when the id turned out to have been issued twice
  ([[T-0101]]). The reference stayed **valid** — T-0099 exists, it is just a different task now — so no
  check complained. A dangling reference fails loudly; a resolvable one that points somewhere wrong does
  not. Removed here rather than repointed, since the exemption itself is going away.

  **What is NOT demonstrated, and why.** The full gate with floors applied refuses:

        $ ops/pins-mutation
        MUTATION FAIL: P-OPS-01 is already RED in a clean worktree of HEAD, so nothing this run
          could say about it would mean anything. Fix `ops/check-pins` first.
            ops/lib/pins_mutation.py (script, should be 100755, is 100644)
        real exit 2

  That red is deliberate and belongs to [[T-0080]]: those two files are `ops/lib/*.py`, which
  [[T-0036]] reclassifies as data, so 100644 is correct after T-0036 and wrong before it. There is no mode
  that is right in both merge orders. **The refusal is the runner being correct** — it will not report on a
  pin that is already failing — so the probe above (`--pin P-SRC-01`, floors deliberately not applied, which
  it says out loud) is the evidence for this change, and the full gate becomes available when T-0036 merges.

        $ ops/check-pins --source-only    PINS ok=3 skipped=8 pending=1 expired=0 failed=0   real exit 0
        $ ops/queue-check                 QUEUE OK                                            real exit 0

  Exit codes above were read with the pipe removed. `ops/pins-mutation | tail -6; echo $?` printed `0` for
  the run that exits 2 — `$?` after a pipeline is the last command's status, which CLAUDE.md warns about by
  name and which cost a wrong reading in this very session before it was caught.
