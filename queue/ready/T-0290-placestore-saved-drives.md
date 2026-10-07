---
id: T-0290
title: PlaceStore saves drives on the device - a GRDB user store with migrations, and saved drives re-resolve against a new corpus or say they need a re-plan
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/PlaceStore/, Tests/PlaceStoreTests/, ops/mutate/, pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0255]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULE FIRST in a dated Log entry: the user-store file is separate from corpus.sqlite (the corpus is replaced by OTA; the user store never is), its schema is owned by a GRDB DatabaseMigrator with named migrations, and what one saved drive holds per the plan's Saved drives row: segment ids, midpoints at exactly 5 decimal places, lambda, budget minutes, a name and created_at; nothing else (no raw origin/destination address, no breadcrumb - P-PRIV-05)"
  - "SavedDriveStore (one type per file) saves, lists newest-first, renames and deletes; every write round-trips by FULL EQUALITY of the whole SavedDrive value; midpoints with more than 5 dp are refused with a typed error, not rounded silently - table over every bound per memory range-checks-every-bound (lat/lon exact bounds accepted, nextafter outside refused, NaN/inf refused)"
  - "Re-resolve on corpus activation: for each saved segment id absent from the new corpus, the nearest segment within 25 m of the saved midpoint replaces it; if any segment has none within 25 m the drive is marked needsReplan and keeps its old ids. Table over {all present, one moved 24.9 m, one moved 25.1 m, one gone, empty drive} through the shipped entry point, each row compared by full equality, with a meta-test that no row's expected value ignores its input"
  - "Migrations: opening a store written by an earlier migration set upgrades in place and preserves every row by full equality; opening a store whose migration identifiers are unknown to this build refuses with a typed error and does not modify the file (sha256 before == after)"
  - "P-PRIV-05 binds a test that the user store's DDL has no column matching /home|address|breadcrumb|trail|speed/ and that SavedDrive has no field carrying more than 5 dp; seen red, then green"
  - "A mutation population under ops/mutate/ for the re-resolve and validation code with a literal floor; three population entries shown MISSED before the tests and CAUGHT by name after"
---
## Brief

Plan, Runtime lifecycles, Saved drives: "On-device (GRDB) only: segment ids + 5-dp midpoints + lambda + B; re-resolve on
corpus activation (nearest within 25 m), mark needs re-plan if unresolved; replay = one /plan with the saved waypoints at
the new time." Milestone M6 lists saved drives. This task is the store and the re-resolve rule only; the Saved tab UI and
the replay call are later tasks. Linux-only target: Foundation + GRDB, never CoreLocation. Swift is native on this box
(memory swift-native-on-windows-box): `swift test --scratch-path .build/<own-id>`.

## Log
- 2026-10-07T01:27:54Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 saved drives).
