---
id: T-0080
title: whether an assertion can fail is not decidable by reading it; only mutation can answer it
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/pins.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

[[T-0072]] added `vacuous()` to `ops/lib/pins.py` to refuse an assertion that cannot fail. It refuses
`assertion: "true"`. It accepts `assertion: "true || false"` - two more characters - which executes, exits 0,
and reproduces the round-one green byte for byte with a banned `import CoreLocation` sitting in
`Sources/ScenicKit/Model/Coordinate.swift`. The round-two verifier table-tested 32 cannot-fail shapes through
the real module: **28 were accepted.**

And a syntactic check cannot win this, because the next case is not even vacuous. Deleting one alternative
from P-SRC-01's real regex -

    (CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)  ->  (MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)

- leaves a genuine grep that can absolutely fail, still runs, still counts toward `MIN_RAN`, and no longer
catches the import it was written for. There is no property of the assertion's TEXT that separates that from
the correct one.

**So stop reading assertions and start mutating.** For each pin in `REQUIRED_RAN`, the pin's own
`statement` already names the violation it exists to catch. Inject that violation and require the assertion to
go RED. A pin whose assertion stays green against the thing it names is a dead pin, whatever its text says.

This is the honest closure and it is a task, not a line - which is why the T-0072 fixer filed it rather than
half-attempting it, and that judgement was right.

- Start with the pins where the violation is cheap and reversible to inject: P-SRC-01 (add a banned import),
  P-OPS-01 (chmod a required script), P-SRC-02 (append 301 lines to a tracked file), P-GIT-01, P-PROC-01
  (a task in done/ with owner == reviewer).
- The injection must be reverted whether the check passes or fails. Do it in a scratch worktree, never in the
  caller's tree - and prove the tree is clean afterwards, as the verifiers here are required to.
- Not every pin can be mutation-tested cheaply. Say which and why, in the file, rather than quietly covering a
  subset and reporting a number.
- This is slow. It probably belongs in `ops/check-pins --mutate` run in CI and not on every developer
  invocation - but decide that explicitly, because a check nobody runs is the thing this queue keeps finding.
- `vacuous()` should stay. It is cheap and it catches the careless case; it just must not be described as
  closing this route. [[T-0072]]'s log has been corrected accordingly.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-two adversarial verification of T-0072, which
  executed all 32 shapes through the module rather than reasoning about them.
