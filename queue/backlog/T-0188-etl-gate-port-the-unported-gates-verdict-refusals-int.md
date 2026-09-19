---
id: T-0188
title: ETL gate port - the unported Gates.verdict refusals (tracktype, smoothness, locked barrier, ford=yes, service values) into assemble.gate_reason with fixture rows and the enumeration pinned against Gates.swift
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/assemble.py, services/etl/tests/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0146]
verify: [ops/test, ops/check-pins]
acceptance:
  - "assemble.gate_reason refuses every rule Gates.verdict refuses (Sources/ScenicKit/Gates/Gates.swift): tracktype >= grade3, smoothness worse than intermediate, barrier=gate+locked=yes, ford=yes, highway=service with a driveway/parking_aisle service value, in addition to the three already ported; one fixture row per rule, each RED BY NAME before the rule exists; the rule COUNT and the reason names pinned against Gates.swift / GateReason.swift by a test that parses the Swift (the existing _swift_set pattern), red when either side gains a rule"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From rv1-pr102's review (RECORDABLE, T-0146 Log) via the 21:13 panel (grounded): ruling R5 ported three of the
plan's gates into the assembly and deliberately not five more; the "five" count was itself wrong at that head.
The corpus the device reads (T-0185) must honour the same gates ScenicKit does (P-PROD-01 gate parity), so the
port lands before the first corpus write; the routing profile's gates (T-0031's car_scenic_base) are the
router's own and are not this task.

## Log
- 2026-09-19T03:29:43Z filed by agent/claude-fable-5-1 from the 21:13 panel's grounded synthesis. Not started; after #102 merges.
