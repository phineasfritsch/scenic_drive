---
id: T-0149
title: P-PROD-01 is not assertable as written - split it into a dull-class pin and a safety-gate pin, and make a pending TODO fail check-pins as CLAUDE.md says
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml, ops/check-pins, ops/lib/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0133]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed from the round-8 review of PR #82 (agent/rv8b-pr82, 2026-09-18) and the hourly panel of 2026-09-18 ~02:45
(`.artifacts/panel/last.md`, queue task 1), which asked for the same split independently.

**What P-PROD-01 measures today: nothing.** `pins/PINS.yaml:116-124` has `assertion: TODO` with `pending: T-0012`.
`bash ops/check-pins` counts it under `pending=2` and exits 0. CLAUDE.md's Verification section says
"`ops/check-pins` ... `TODO` assertions fail"; `ops/lib/pins.py:14` says the opposite on purpose: "`pending:
T-XXXX` marks a pin whose assertion cannot exist yet. It is reported as PENDING and does not fail". The rule
and the tool disagree, and the reviewer and the filer both read the rule as the intent: a pin nobody can run
is false confidence when it sits under a count that reads as fine. Decide it explicitly and make the two
agree - either `pending:` fails (demonstrated red) and the pins that carry one today get a real assertion or
a dated deferral the check prints BY NAME, or CLAUDE.md says what `pending:` means and `check-pins` prints
each pending pin's id and the task it waits on, every run, not just a count.

**Why the statement cannot be asserted as written.** "Motorway/trunk/private/unpaved ways score exactly 0.0 in
the ETL, the router profile and ScenicKit.Gates (one fixture set through all three)" mixes two mechanisms:

1. **Dull classes** - motorway/trunk carry `scenic_score = 0` and are *penalised, never excluded* (CLAUDE.md
   product invariants; the plan's "Freeways: Not a hard gate"). Anchor: `ScenicKit` scoring's dull-class set
   and the absence of any refusal path for them (PR #82's Gates.swift says so in source: "no GateReason exists
   that could refuse a motorway"). One pin, one assertion: a motorway/trunk fixture scores 0.0 AND
   `Gates.decide` returns `.allowed`.
2. **Safety gates** - unpaved with positive evidence, private/no access, track, locked barrier=gate are
   *refused*, which is a `GateDecision`, not a score. Anchor: `Sources/ScenicKit/Gates/Gates.swift`'s six
   refused sets (`unpavedSurfaces`, `closedAccess`, `refusableBarriers`, `refusedTracktypes`,
   `refusedSmoothness`, `refusedServiceValues`), `services/etl` tag filter, and - when it exists - the
   router profile JSON. One pin, one assertion per layer that exists, and the "one fixture set through all
   three" parity claim deferred by name until `services/routing` and the ETL gate exist (neither does today:
   `services/` holds api and etl; the ETL has no gate logic - verified by the reviewer with grep).

Do not widen either into "parity" until there is a second implementation to be parallel with. A pin that
claims three layers when one exists is the shape this repository fails on.

**Depends on T-0133** (PR #82) landing, because pin 2 anchors on the set identifiers that PR names.

## Log
- 2026-09-18T17:40:00Z filed by agent/claude-fable-5-1 from agent/rv8b-pr82's round-8 review of PR #82 (recommendation, not a finding against that PR - the PR claims the opposite of parity, in source) and from the 02:45 panel's queue task 1. Not started.
