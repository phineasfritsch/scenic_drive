---
id: T-0004
title: pins/PINS.yaml + ops/check-pins with runs_on, last_verified and expiry
state: claimed
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: 2026-09-07T03:31:44Z
lease_expires_at: 2026-09-07T07:31:44Z
worktree: ../wt/T-0004
branch: task/T-0004
exclusive: []
touches: [pins/PINS.yaml, ops/check-pins, ops/lib/pins.py]
pins_affected: [P-ATTR-02, P-PROD-01, P-COST-02, P-DATA-02]
reviewer: null
depends_on: [T-0001]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "bash ops/check-pins -> PINS ok=N skipped=M expired=K, exit 0 on Linux"
  - "RED: a pin whose assertion is TODO -> exit 1 naming it"
  - "RED: a human pin with last_verified older than 30 days -> expired, exit 1"
  - "RED: the source-only import ban catches import SwiftUI added to Sources/ScenicKit"
---
## Brief

Schema per pin: id, statement, why_no_test_catches_it, assertion (exact command), anchor, runs_on
[linux|mac|device|human], owner, added, last_verified, verifier. Seed with the pre-feature pins from the plan:
P-ATTR-02 (LICENSE-DATA/NOTICE exist - red until they do), P-PROD-01 gate parity (red until ETL exists),
P-COST-02 (MAX_MONTHLY_UPSTREAM_CALLS constant, red until Worker exists), P-DATA-02 (deployment target 18.4 in
Package.swift platforms), the Tier-1 import ban (source-only), the 300-line cap (source-only). Red pins are fine;
TODO assertions are not. --source-only runs only pins with anchor=source (used in CI on every push).

## Log
- 2026-09-07T03:10:35Z claimed by agent/demo; lease until 2026-09-07T03:10:35Z
- 2026-09-07T03:10:36Z sweep: lease held by agent/demo expired at 2026-09-07T03:10:35Z; returned to ready/, locks released
- 2026-09-07T03:12:27Z claimed by agent/x; lease until 2026-09-07T03:12:27Z
- 2026-09-07T03:12:47Z sweep: lease held by agent/x expired at 2026-09-07T03:12:27Z; returned to ready/, locks released
- 2026-09-07T03:30:20Z claimed by agent/x; lease until 2026-09-07T03:30:20Z
- 2026-09-07T03:30:30Z sweep: lease held by agent/x expired at 2026-09-07T03:30:20Z; returned to ready/, locks released
- 2026-09-07T03:31:44Z claimed by agent/claude-opus-5; lease until 2026-09-07T07:31:44Z
