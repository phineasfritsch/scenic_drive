---
id: T-0004
title: pins/PINS.yaml + ops/check-pins with runs_on, last_verified and expiry
state: review
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: 2026-09-07T03:31:44Z
lease_expires_at: 2026-09-07T07:31:44Z
worktree: ../wt/T-0004
branch: task/T-0004
exclusive: []
touches: [pins/PINS.yaml, ops/check-pins, ops/lib/pins.py, ops/lib/queue.py, LICENSE-DATA, pins/evidence/]
pins_affected: [P-ATTR-02, P-PROD-01, P-COST-02, P-DATA-02]
reviewer: agent/reviewer-1
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
- 2026-09-07T03:40:00Z scope note: ops/lib/queue.py added to touches - it wrote task files with CRLF on Windows (write_text default newline), which trips agent-preflight; pins.py must not repeat it. LICENSE-DATA added so P-ATTR-02 is green for real rather than a placeholder.
- 2026-09-07T03:55:00Z GREEN: ops/check-pins -> PINS ok=7 skipped=0 pending=4 expired=0 failed=0 tier=linux; preflight OK; queue-check OK (13 tasks); ops/test 3/3
- 2026-09-07T03:55:00Z RED 1 (TODO assertion, no pending) -> failed=1 exit 1 naming P-TMP-01
- 2026-09-07T03:55:00Z RED 2 (human pin last_verified 97 days ago) -> expired=1 exit 1
- 2026-09-07T03:55:00Z RED 3 (pending on T-0001 which is done) -> failed=1 exit 1: the pin must be real now
- 2026-09-07T03:55:00Z RED 4 (Sources/ScenicKit/Tmp.swift with import SwiftUI, --source-only) -> P-SRC-01 failed, exit 1
- 2026-09-07T03:55:00Z pending mechanism: P-PROD-01 -> T-0012, P-COST-02 -> T-0005, P-SAFE-05 -> T-0011, P-HUMAN-01 -> T-0013 (backlog tasks created)
- 2026-09-07T03:55:00Z queue.py now writes LF on Windows; claim round-trip file has 0 CR bytes
- 2026-09-07T03:55:00Z moved to review/, reviewer agent/reviewer-1
