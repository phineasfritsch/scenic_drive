---
id: T-0307
title: The app keeps its Surprise history through a reinstall - the install id lives in the Keychain, a signed-in device posts each shown place to /ledger and merges /ledger's 90 days into the on-device no-repeat history
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T22:19:39Z
lease_expires_at: 2026-10-08T18:19:39Z
worktree: .worktrees/T-0307
branch: task/T-0307
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-PROD-02]
reviewer: null
depends_on: [T-0302, T-0304, T-0294, T-0273]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: where the install id lives today (T-0294 R7: UserDefaults in PlanAdapter's StoredInstallID) and the move to the Keychain (kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly, never synced) with a one-time migration from UserDefaults; who holds a session (no session -> no ledger calls, history stays device-only; never the legacy header path - T-0302 R1); what the app sends (place id + the H3-5 cell of the PLACE, never the device's position - T-0302 R2, P-PRIV-05)"
  - "ScenicAPIClient LedgerClient: POST /ledger and GET /ledger request bodies built and parsed by full equality to a recomputation (memory full-equality-oracle); every Worker answer (200, 400, 401, 405, 429 ledger_daily_cap, 503) maps to one typed outcome by a table test; a 429 or 401 never retries"
  - "ScenicKit: the Surprise no-repeat history becomes the union of the device history and the ledger's 90 days, deduplicated by place id, ordered by day; the selector's P-PROD-02 reproducibility and 90-day no-repeat still hold - table over {no session, empty ledger, ledger overlapping device, ledger only} by full equality"
  - "Every new or changed Sources/ and non-Swift apps/ios file re-approves its row in ops/lib/check-safety-disclaimer-linked-digests.txt; ios-compile + ios-screenshot pass on the head; a mutation population for the client mapping and the merge with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Surprise Me (paid): "Unlimited, 90-day no-repeat"; Entitlement row: identity survives reinstall via the iCloud
keychain. T-0302/T-0304 shipped the server half (/ledger, sub-only identity, 200/day cap); T-0302's author noted the
client half (Keychain install id, the app calling /ledger) as M6 Apple-package work. Calm copy (memory owner-route-intent).

## Log
- 2026-10-07T22:19:14Z filed by agent/claude-opus-5 (orchestrator) from T-0302's stillOpen (client half).
- 2026-10-07T22:19:39Z claimed by agent/claude-opus-5; lease until 2026-10-08T18:19:39Z
