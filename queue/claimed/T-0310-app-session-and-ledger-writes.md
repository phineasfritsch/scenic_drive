---
id: T-0310
title: The app holds a Worker session (App Attest -> session JWT, Keychain-held) and records every Surprise place it shows - into the device history and, signed in, to /ledger with the place's H3-5 cell
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T01:56:47Z
lease_expires_at: 2026-10-09T01:56:47Z
worktree: .worktrees/T-0310
branch: task/T-0310
exclusive: [package-swift]
touches: [apps/ios/Packages/ScenicApp/Package.swift, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-PROD-02, P-SAFE-03]
reviewer: null
depends_on: [T-0307, T-0278, T-0280]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the Worker's /attest/challenge -> /attest -> session JWT and /attest/assert flow as shipped (T-0278, T-0280 - read services/api/src/attest*.ts), which parts are Linux-testable (request/response construction, token storage policy, expiry/refresh decisions) and which are Apple-only (DCAppAttestService), where the session token lives (Keychain, ThisDeviceOnly), and the Package.swift edit that lets PlanAdapter use Telemetry.H3Cell for the PLACE's cell (T-0307 stillOpen), under the package-swift lock"
  - "ScenicAPIClient AttestClient + SessionStore: every request body by full equality to a recomputation; every Worker answer mapped to one typed outcome by a table; an expired or rejected session is dropped and re-attested at most once per launch; LiveSurpriseLedger's session provider is the real store (replacing NoLedgerSession)"
  - "The Surprise card records each shown place into the device history (the 90-day no-repeat) and, with a session, POSTs {place_id, cell} where cell is the H3-5 cell of the PLACE's coordinate, never the device's (P-PRIV-05) - a ScenicKit test over {no session, session, ledger 429, ledger 401} shows the history and the request count by full equality; P-PROD-02 reproducibility still holds"
  - "Keychain items (the install id from T-0307 and the new session token) are written with replace semantics: an existing item that is not the expected shape is updated (SecItemUpdate, or delete-then-add), never left in place while the value silently moves to UserDefaults (rv2-t0307 recordable on PR #197) - the decision logic is a Linux-testable pure function over {absent, valid, malformed, read failure} with a full-equality table"
  - "P-SAFE-03 unchanged (no plan before the disclaimer); ios-compile + ios-screenshot pass on the head; digests re-approved; a mutation population with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

T-0307 stillOpen (PR #197): no Swift code can obtain a Worker session (NoLedgerSession ships), the Surprise card never adds
shown places to the device history, and PlanAdapter needs Telemetry.H3Cell (a Package.swift edit) for the place's cell.
The Worker side of App Attest + session JWT shipped in T-0278/T-0280. Real attestation needs the owner's Apple Team ID and
a device, so the Apple-only half is compile-checked in CI and exercised on device later (T-0009 device pipeline).

## Log
- 2026-10-08T00:42:33Z filed by agent/claude-opus-5 (orchestrator) from T-0307's stillOpen.
- 2026-10-08T01:56:47Z claimed by agent/claude-opus-5; lease until 2026-10-09T01:56:47Z
