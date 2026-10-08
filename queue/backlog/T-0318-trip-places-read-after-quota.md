---
id: T-0318
title: The /trip trip_places read stops scanning the whole table before the quota reservation - a quota-refused trip reads no trip_places row, and a served trip reads only the rows near its corridor
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-05]
reviewer: null
depends_on: [T-0316]
verify: [ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST: trip_places row count in production D1 at filing of the claim (0 when T-0316 merged), where handleTrip reads it relative to guardedPlan's quota reservation, and D1's rows-read billing for a full scan versus a bounded read; rule read-after-reservation versus a bbox/corridor-bounded read (or both) before code"
  - "Through worker.fetch: a quota-refused /trip prepares no trip_places statement (recorded D1 statements by full equality), and a served /trip's answer is unchanged by full equality against the T-0316 cross product; any new bound is table-tested at every edge (exact, next double outside) and binds no request value beyond what R3 of T-0316 ruled"
  - "Population entries MISSED before and CAUGHT by name after; no route-enumerating table changes"
---
## Brief

Filed from rv1-t0316 RECORDABLE R-a (PR #203). handleTrip reads the whole trip_places table on every /trip that gets
past the kill switch, the region check and the place lookup - including requests guardedPlan then refuses for quota,
because the read runs before guardedPlan. D1 bills per row read, so once the ETL loader (T-0316 stillOpen 1) fills
the table, every quota-refused trip scans the whole corpus. Measured 0 rows when filed, so this is a follow-up, not a
P-COST fail-open today. It belongs with (or before) the loader.

## Log
- 2026-10-08T09:05:40Z filed by agent/claude-opus-5 (T-0316 owner) from rv1-t0316 R-a.
