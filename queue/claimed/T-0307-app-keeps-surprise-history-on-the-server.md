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
- 2026-10-07T23:06:37Z RED then GREEN, guards, agent/claude-opus-5:
  - R3 CORRECTION (ruled before the client code, recorded here): the device's cell check is h3Res5.ts's FIRST test
    only, HEX15 (fifteen lowercase hex); isResolution5Cell's mode, resolution, base-cell and digit tests stay the
    Worker's, and a cell failing them comes back `.invalidRequest` - so R3's "never sends what the Worker would 400"
    holds for the place id and for the cell's shape, not for every H3 bit. The cell's producer is the follow-up's
    Telemetry.H3Cell (R6), which emits only valid res-5 cells.
  - RED first, by name: LedgerClientTests.swift + SurpriseHistoryMergeTests.swift written against stub bodies
    (LedgerClient answering .noSession, merged() returning the device history). `swift test --filter
    "LedgerClientTests|SurpriseHistoryMergeTests"` exit 1, 9 of 10 red by name: POST /ledger is exactly the
    bearer... (6 issues), GET /ledger is exactly the bearer... (2), A GET body that is not {places...} is
    unreadable (24), Every Worker answer is one typed outcome... never a retry (36), No reply at all is offline (3),
    A place id or cell the Worker would refuse is refused on the device (16), The merged history is exactly the
    expected one (6), The pick over the merged history is the pick over the expected history (2), A ledger place
    shown 89 days ago is never picked (1); `Without a session nothing is sent` was green on the stub (it answered
    .noSession by construction). `Test run with 10 tests in 2 suites failed ... with 96 issues.`
  - GREEN: LedgerEntry, LedgerReplyReader, LedgerClient, SurpriseHistoryMerge -> `Test run with 10 tests in 2
    suites passed`. Apple: StoredInstallID (Keychain, R1), NoLedgerSession, LiveSurpriseLedger (PlanAdapter),
    SurpriseLedgerKey (FeatureSurpriseMe environment), SurpriseCard reads it in `.task`, ScenicDriveApp sets
    `.environment(\.surpriseLedger, LiveSurpriseLedger.make())` - the frozen shell line (DOORS_SHELL_LINE) untouched.
  - DIGESTS re-approved, each a file this task changed or added: -linked-digests.txt + 9 rows (6 Ledger*.swift,
    SurpriseHistoryMerge/LedgerPlace/LedgerSource); -pinned PINNED_SURPRISE (SurpriseCard changed,
    SurpriseLedgerKey added), PINNED_APP_SWIFT (SurpriseCard, SurpriseLedgerKey, StoredInstallID, NoLedgerSession,
    LiveSurpriseLedger, ScenicDriveApp), PINNED_SHELL_DIGEST (ScenicDriveApp); -frozen FROZEN_APP_SHELL gains the one
    `.environment(...)` line. Seen red first: `P-SAFE-03: a frozen render block changed: ... found
    .environment(\.surpriseLedger, LiveSurpriseLedger.make())`, then `FeatureSurpriseMe's file set is not the
    approved one: added SurpriseLedgerKey.swift`, then `ScenicDriveApp.swift content changed`; after:
    check-safety-disclaimer exit=0, check-map-attribution exit=0.
  - POPULATION ops/mutate/ledger{,_mutations,_run}.py (28 entries, floor 28; 1 EQUIVALENT with witness; 2 test
    files), registered in mutate_population_table.py DRIVERS + COVERED_FLOOR. Pre-review pass, three unwritten
    mutants run at 5b303043 before their tests: `MISSED 26 the 400-year leap rule dropped`, `MISSED 27 the first
    date separator unchecked`, `MISSED 28 a day tie handed to the ledger` (caught=0/3). Tests added at 71fef75b
    (2000-02-29 parsed; 2100-02-29 and 2026x10-01 unreadable; a day tie keeps the device entry).
  - named-tests.json: P-PROD-02 runs SurpriseHistoryMergeTests (mergedHistory, pickReproducible, ninetyDays);
    P-PRIV-05 runs LedgerClientTests postRequest, getRequestAndRows, refusedOnDevice.
- 2026-10-07T23:16:10Z POPULATION and iOS CI, agent/claude-opus-5:
  - Full run at 71fef75b (`python ops/mutate/ledger.py`, scratch .build/mledger in the main checkout):
    `caught by the test that names it: 27 of 28 (wrong killer 0, trapped 0, compile-only 0, MISSED 1, skipped 0)`;
    the one survivor `MISSED 21 an unknown id kept`: the unknown ledger id was dated 06-01, so mapped onto the first
    candidate (malibu-00) it lost to malibu-00's 06-15 and changed nothing. The row now dates nowhere-9 06-19, after
    every kept day; `--only 21` at the fix commit: `caught 21 an unknown id kept by: The merged history is exactly
    the expected one...`, `MUTATE OK caught=1/1`. E1 MISSED as an equivalent must be. So 26-28 MISSED before
    (5b303043) and CAUGHT after (71fef75b), each by the test it names: `caught 26 ... by: GET /ledger is exactly
    the bearer...`, `caught 27 ... by: A GET body that is not {places...} is unreadable`, `caught 28 ... by: The
    merged history is exactly the expected one...`.
  - `run-named-tests.py P-PROD-02`: `NAMED P-PROD-02 passed=7/7`.
  - iOS on 5b303043 (the app files are unchanged since): ios-compile run 37698263738 `completed success` (4m7s),
    ios-screenshot run 37698268012 `completed success` (13m28s).
- 2026-10-07T23:27:22Z ACCEPTANCE re-run on the pre-review head (origin/main 3c8b6106 merged: `Already up to date`;
  PR #195 / T-0305 still OPEN - whichever lands second merges the other's digest, frozen-shell, SurpriseDeck and
  ScenicDriveApp rows, keeping both sides), agent/claude-opus-5:
  1. MEASURE then RULE FIRST: the 22:25:28Z entry (a)-(e), R1-R7, committed alone at f7539647 before any code;
     R3's cell clause corrected at 23:06:37Z.
  2. LedgerClient: `swift test --filter "ScenicAPIClientTests|ScenicKitTests\.Surprise"` -> `Test run with 57
     tests in 12 suites passed` + XCTest `Executed 46 tests, with 0 failures`; POST/GET by full equality to a
     recomputation (postRequest x3, getRequestAndRows), 18-row answer table (200/400/401/405/429 x2/503/other),
     one request per call, offline after one, zero without a session or for a refused entry.
  3. Merge: SurpriseHistoryMergeTests over {no session, empty ledger, ledger overlapping device, ledger only,
     ledger tying device}, whole history + whole 60-seed pick by full equality; ninetyDays (89 excluded, 90
     picked). `run-named-tests.py P-PROD-02` -> `NAMED P-PROD-02 passed=7/7`.
  4. Digests: check-safety-disclaimer exit=0, check-map-attribution exit=0; ios-compile and ios-screenshot green
     on 5b303043 (the app tree since: unchanged); population 28/28 caught with 21's fix, 26-28 MISSED -> CAUGHT;
     check-mutate-population `every added module is covered or allowlisted; the floor of 88 holds` (five
     code-free types allowlisted with reasons); check-line-cap `none over 300 lines`; check-pins-yaml `PINS-YAML
     ok pins=44`; queue-check `QUEUE OK (298 tasks)`.
  - `ops/check-pins --source-only`: ok=16 failed=1 - P-SAFE-05 SolarFixtureTests, whose assertion runs `swift test`
    with the default scratch path inside the worktree (the long-path index-store failure); the same suite with a
    short scratch path: `Test run with 6 tests in 1 suite passed`. Untouched by this task.
  - NOT DONE (stillOpen, to be filed): the app POSTs no shown place yet - it needs (i) a session client (attest /
    Sign in with Apple) to replace NoLedgerSession, (ii) the card to record each shown place in the device history
    (today `shown` is never appended - measured (c)), and (iii) PlanAdapter -> Telemetry for H3Cell, a
    Package.swift edit under T-0305's lock. The Keychain move and the GET merge ship; with no session the shipped
    app makes no ledger request.
- 2026-10-08T00:08:09Z PRE-REVIEW SURVIVOR M2 closed by class, agent/claude-opus-5:
  - M2 (BLOCKING): the merge deduped by category instead of place id survived 10/10 green - every MERGED row held at
    most one place per category. Closed as the CLASS "the dedupe key is not the place id": population entries 29
    category, 30 corridor, 31 category+corridor, 32 day (both lines of the key swapped; floor 28 -> 32), committed
    at 1deebae2 BEFORE the test. `python ops/mutate/ledger.py --only 29,30,31,32` there:
    `MISSED 29 the merge keyed by category exit=0 no test objected`; 30, 31, 32 already caught (30/32 by the pch
    corridor and the 06-19 day the existing rows share; 31 by the tying row, whose device corridor is inland);
    `MUTATE FAILED caught=3/4`.
  - Test at d03f5d74: MERGED row "one category, corridor and day, different places" - device as before, ledger
    malibu-08 (park, pch) 06-10 and topanga-07 (park, topanga) 03-30; the expected history keeps all four ids.
    `--only 29,30,31,32` there: `caught 29 the merge keyed by category by: The merged history is exactly the
    expected one, whatever the ledger's order | The pick over the merged history is the pick over the expected
    history, seed for seed`, 30-32 caught by the same two; `MUTATE OK caught=4/4`. Suites
    `LedgerClientTests|SurpriseHistoryMergeTests`: `Test run with 10 tests in 2 suites passed` (6 rows each).
  - No Sources/ file changed, so no digest row moves. Reviewer notes, not mutants: LedgerClient.record has no
    caller yet and LiveSurpriseLedger.make() wires NoLedgerSession, so read() is .noSession in production and
    R5/R6 run only under test until a session client lands (the NOT DONE list above; T-0309).
  - origin/main merged at 01f08c34 (T-0305 landed): conflicts in ScenicDriveApp.swift, -frozen, -pinned and
    mutate_population_table.py, each resolved keeping both sides - main's corpus-download sheet, then this task's
    `.environment(\.surpriseLedger, ...)`; DRIVERS has corpusfetch.py and ledger.py; -pinned re-approved for the
    merged SurpriseDeck.swift (fd057725...) and ScenicDriveApp.swift (6be4dca9..., shell digest and app row). On
    the merged head: check-safety-disclaimer exit=0, check-map-attribution=0, check-line-cap=0, P-PROC-06 `the
    floor of 91 holds`, `PINS-YAML ok pins=44`, `QUEUE OK (300 tasks)`; `swift test --filter
    "ScenicAPIClientTests|ScenicKitTests\.Surprise|PlaceStoreTests"` -> `Test run with 100 tests in 23 suites
    passed`; CI on 01f08c34: ios-compile 37706582493, ios-screenshot 37706585749, linux-core 37706583464, all
    `completed success`.
