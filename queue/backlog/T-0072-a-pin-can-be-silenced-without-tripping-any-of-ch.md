---
id: T-0072
title: a pin can be silenced without tripping any of check-pins' new floors
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/check-pins]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Follow-up to [[T-0066]], whose fix added `MIN_PINS`, `MIN_RAN`, `MIN_RAN_SOURCE_ONLY`, a `REQUIRED` list of
pin ids and a `REQUIRED_SOURCE` anchor check to `ops/lib/pins.py`. A second agent reproduced that fix's
transcript, then executed thirteen evasions against it. **Nine went red. Four did not.** The full report is
in T-0066's `## Log`; the four open routes are:

**1. A pin can be silenced one line at a time, and no floor notices.** Set one pin's `runs_on: [linux, mac]`
to `runs_on: []`. Its id is still in `REQUIRED`, its `anchor` is still `source`, `MIN_PINS` is satisfied, and
`MIN_RAN` is satisfied by the pins that still run. The verifier did this to **P-SRC-01**, then injected the
exact import violation P-SRC-01 exists to catch into `Sources/ScenicKit/Model/Coordinate.swift` wrapped in
`#if canImport(CoreLocation)` — so the tree still compiles and every other pin stays green. That is precisely
the "code compiles and tests pass on the Mac" scenario P-SRC-01's own `why_no_test_catches_it` field
describes. `check-pins` reported success.

**2. The floor has headroom, and it was measured.** The verifier bisected: several REQUIRED pins can be
silenced this way before `MIN_RAN` trips. `MIN_RAN = 6` against 9 running today is not a ratchet, it is a
suggestion. This is the same slack problem as [[T-0071]] in a different file.

**3. `assertion: "true"` keeps the ran count high and asserts nothing.** Rewriting every `assertion:` value in
`pins/PINS.yaml` to `"true"` leaves `ran` at its full value, every floor satisfied, `failed=0`, exit 0. The
`ran` counter proves an assertion was *executed*, not that it *asserted anything* — the guard counts calls,
not content.

**4. `PYTHON=` bypasses the hardened module entirely, with no file edit.** `ops/check-pins` is
`exec "${PYTHON:-$(command -v python3 || command -v python)}" .../pins.py "$@"`, so the environment chooses
the interpreter. Pre-existing, not introduced by T-0066, and it defeats every guard in the file at once. The
same shape exists in `ops/queue-check`, `ops/new-task`, `ops/claim` and every other `ops/*` wrapper. Decide
whether that is acceptable (it is a local convenience knob, and an attacker with the environment already has
the box) or whether CI should pin the interpreter — but decide it explicitly rather than by omission, and if
it stays, say so in the file.

**The pattern, which is the point.** Each of the three fixes verified this round hardened the specific hole it
was pointed at and left the property reachable by a neighbouring route. T-0066 hardened *how many* pins run;
routes 1 and 3 change *which* and *what*. See [[T-0073]] and [[T-0074]] for the same shape in two other files.

- Route 1 is the one that matters: a REQUIRED pin must be required to RUN, not merely to exist. `runs_on: []`
  on a pin in `REQUIRED` should be a failure, not a skip.
- Route 3 wants the assertion to be non-trivial. A cheap, honest version: refuse an assertion that is a
  bare truth literal, and keep `TODO` failing as it already does.
- Re-ratchet the floors to just under today's counts and say in the log what they were when set.
- Demonstrate each red then green. Route 1's demonstration must include the injected import violation, or it
  proves only that the flag changed and not that the pin came back to life.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the adversarial verification of T-0066, every case executed by
  an agent that did not write the fix.
