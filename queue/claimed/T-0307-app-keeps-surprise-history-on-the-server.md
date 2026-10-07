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
- 2026-10-07T22:25:28Z MEASURED, then RULINGS (author rule, before any code), agent/claude-opus-5:
  - MEASURED at 3c8b6106. (a) The install id: apps/ios/.../PlanAdapter/StoredInstallID.swift generates a UUID once
    and keeps it in `UserDefaults.standard` under `plan.install.id` (T-0294 R7); its one caller is LivePlanner.make.
    (b) Sessions: `grep -rli "session|bearer|authorization"` over Sources/ and apps/ios Swift finds no session
    token, no Authorization header and no attest or Sign in with Apple client - the Worker issues sessions
    (attest.ts:118/162, account.ts:115) but NO Swift code holds one today. (c) The device history: SurpriseCard keeps
    `@State history = SurpriseHistory()` in memory and appends only `feedback`; `history.shown` is never appended,
    so the on-device 90-day no-repeat has nothing to act on today. (d) The H3-5 encoder: the only Swift one is
    Telemetry.H3Cell; ScenicAPIClient depends on ScenicKit only and PlanAdapter on ScenicKit + ScenicAPIClient
    (both Package.swift), and T-0305 (PR #195, open) holds `exclusive: [package-swift]` and edits both files.
    (e) /ledger (services/api/src/ledger.ts): GET/POST only, 405 `GET or POST only`; 503 auth_unavailable; 401
    unauthorized; POST body exactly {place_id, cell}; 400 invalid_request {detail}; 503 ledger_unavailable; 429
    ledger_daily_cap; 200 {recorded: true} / {places: [{place_id, cell, day}]} newest day first.
  - R1 install id -> the Keychain. StoredInstallID (type name and file kept; one caller) reads a generic-password item
    (service `scenic.install`, account `install-id`) with kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly and
    kSecAttrSynchronizable false - never synced, kept across a reinstall by iOS. Absent: a valid `plan.install.id`
    in UserDefaults is MIGRATED (written to the Keychain, then the defaults key removed); else a new UUID is
    generated and written. A failed Keychain write keeps the UserDefaults value (or writes it there) so the id stays
    stable for this install - never a fresh id per launch. Apple-only (Security); proven by ios-compile, not Linux.
  - R2 session. ScenicAPIClient gains `LedgerSessionProvider` (`sessionToken() -> String?`). No token -> the client
    makes ZERO requests and answers `.noSession`; the history stays device-only. The ledger request carries ONLY
    `authorization: Bearer <token>` (+ content-type on POST) - never `x-scenic-device`, never the legacy header path
    (T-0302 R1). Production's provider is PlanAdapter `NoLedgerSession` (nil): by (b) no Swift code holds a session,
    so the shipped app makes no ledger call until a sign-in/attest client lands (filed, stillOpen).
  - R3 what is sent (P-PRIV-05). POST body is exactly {"cell","place_id"} sorted-key JSON: the corpus place id string
    and the H3-5 cell OF THE PLACE, both supplied by the caller as a `LedgerEntry`; the client refuses on the device
    (zero requests, `.refusedOnDevice`) a place id that is not canonical decimal 1...2^63-1 or a cell that is not 15
    lowercase hex - ledger.ts R3's own admission, so the device never sends what the Worker would 400. No device
    position is a field of LedgerEntry; GET has no body and no query.
  - R4 outcome table (one per status, `LedgerReplyReader`): 200 POST {recorded:true} -> .recorded; 200 GET {places}
    -> .places([LedgerRow]) (every row's day parsed YYYY-MM-DD into CivilDate, any malformed row -> .unreadable);
    200 otherwise -> .unreadable; 400 -> .invalidRequest; 401 -> .unauthorized; 405 -> .methodRefused; 429 with
    error ledger_daily_cap -> .dailyCap, any other 429 -> .unexpected(429); 503 -> .unavailable; any other status ->
    .unexpected(status); no reply -> .offline. The client NEVER retries: one call, at most one request, any status.
  - R5 merge (ScenicKit `SurpriseHistoryMerge.merged(device:ledger:candidates:)`). `ledger == nil` (no session or no
    answer) -> the device history, identical. Otherwise shown = device shown + each ledger place (`SurpriseLedgerPlace`
    {candidateId, date}) whose id is a candidate (category and corridor from that candidate; an id outside the deck
    can never be picked, so it is dropped), deduplicated by candidate id keeping the LATEST date (the most restrictive
    for both the 90-day and the category-corridor rule; on a date tie the device entry), ordered by date ascending
    then candidate id; feedback is the device's, unchanged. The ledger day is the UTC day, the device's the local
    day: at most one day apart, ruled acceptable (the Worker's window is UTC by T-0302 R5).
  - R6 app wiring. FeatureSurpriseMe takes a ScenicKit protocol `SurpriseLedgerSource` (`ledgerPlaces() async ->
    [SurpriseLedgerPlace]?`) and reads it once in `.task`; PlanAdapter `LiveSurpriseLedger` conforms through
    LedgerClient with NoLedgerSession. NOT WIRED, ruled out of scope and filed: posting each SHOWN place - (c) the
    card records no shown place today, and the POST needs the place's H3-5 cell from Telemetry.H3Cell, reachable only
    through a Package.swift edit under T-0305's package-swift lock (d). The client's POST is shipped and tested.
  - R7 reproducibility (P-PROD-02): merged() is a pure function of its inputs and is independent of the ledger's
    order; the table over {no session, empty ledger, ledger overlapping device, ledger only} compares the whole
    merged history AND the whole pick to a hand-built expectation by full equality.
