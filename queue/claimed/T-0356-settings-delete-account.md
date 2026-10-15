---
id: T-0356
title: Settings has Delete account in at most 3 taps - an AccountClient sends DELETE /account over the session, the app forgets its local identity on success, and P-PRIV-04's client half is held by tests
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-15T20:03:45Z
lease_expires_at: 2026-10-16T20:03:45Z
worktree: .worktrees/T-0356
branch: task/T-0356
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-04]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 Client by exact request equality (R1, R4): Tests/ScenicAPIClientTests/AccountClientTests.swift drives the SHIPPED AccountClient.deleteAccount() over ScriptedTransport - the one request EQUALS the PlanHTTPRequest literal {url <base>/account, method DELETE, headers exactly [authorization: Bearer <token>], body empty}; no session token is .noSession with ZERO requests; a 401 hands the token back (accountSessionRejected) and makes exactly ONE more request with the renewed token, a second 401 is .unauthorized after two requests, a renewal that yields nothing or the same token is .unauthorized after one."
  - "A2 Every answer (R2): AccountClientTests maps every DELETE /account answer account.ts can give to one AccountOutcome by full equality - 200 {deleted:true, revoke_pending, plans_pending} at all four boolean pairs -> .deleted(revokePending:plansPending:); every fail-closed 200 body (not JSON, deleted false, deleted missing, a flag missing or not a boolean, an extra key, an array) -> .unreadable; 401 -> .unauthorized; 405 -> .methodRefused; 503 auth_unavailable -> .authUnavailable; 503 account_unavailable -> .accountUnavailable; 503 other body -> .unexpected(503); 400/404/429/500 -> .unexpected(status); a thrown transport -> .offline."
  - "A3 Local erase as a table over every stored item (R3, R5): Tests/ScenicAPIClientTests/AccountEraseTableTests.swift - LocalAccountItem.allCases EQUALS the measured inventory literal (13 items, so a new stored item fails by name until it is ruled); the cross product of every AccountOutcome reachable through the transport x every item, through the SHIPPED AccountDeletion.run(): the eraser receives exactly {session, installIDKeychain, installIDDefaults} (a literal, not the table) on .deleted and NOTHING on every other outcome; a meta test that no row's expected erase set ignores its outcome. SessionStore.forgetSession() removes the Keychain item and the next sessionToken() never hands back the forgotten token."
  - "A4 Tap path (R1): Tests/ScenicKitTests/AccountDeletionPathTests.swift - ScenicKit AccountDeletionPath.steps has <= 3 actions in the order home.settings -> settings.deleteAccount -> settings.deleteAccount.confirm, and each step's identifier is set by exactly one `.accessibilityIdentifier(\"<id>\")` line of the shipped app sources (apps/ios/Packages/ScenicApp/Sources). Copy (R6): AccountDeletionCopy.note(for:) EQUALS the ruled string for every AccountOutcome."
  - "A5 RED first: the new test files run against the tree before the code commit fail by name (missing symbols = compile failure), quoted in the Log; then green natively with `swift test --filter 'AccountClientTests|AccountEraseTableTests|AccountDeletionPathTests|SessionStoreTests'`."
  - "A6 Wiring: SettingsScreen carries the Delete Account row and its confirmation; the shell hands it PlanAdapter's LiveAccountDeletion; every touched apps/ios Swift file re-approved in ops/lib/check-safety-disclaimer-pinned and every new/edited Sources file in check-safety-disclaimer-linked-digests.txt; ios-compile and ios-screenshot success with the Settings shots looked at. The XCUITest that taps the path waits on T-0180's xcodeproj lock (recorded)."
  - "A7 P-PRIV-04's client half bound by name: the new Swift tests in ops/lib/named-tests.json under P-PRIV-04 (swift), the pin's why_no_test text extended; `python ops/lib/run-named-tests.py P-PRIV-04` passes. New Sources modules are either in a population or in mutate-population-allowlist.json with a reason read from the module."
  - "A8 On the merged head: the touched Swift filter green; check-safety-disclaimer, check-mutate-population, check-mutate-only, check-line-cap, check-pins-yaml, check-exec-bits and queue-check all exit 0, each quoted."
  - "A9 (rv1-t0356 B1) AccountEraseTableTests `forgetSession removes the Keychain item and the forgotten token is never handed back` asserts the post-forget Keychain write is an ADD (MemorySessionStorage.writes, by equality of the whole KeychainWrite list); the hand mutant that deletes `keychain = .absent` from SessionStore.forgetSession() is RED by that test's name, GREEN without."
  - "A10 (rv1-t0356, P-PRIV-04 R3) Telemetry later in the launch never carries the deleted install id: PlanAdapter LiveTelemetry reads StoredInstallID per record and rebuilds its TelemetryClient when the id changed (InstallBoundTelemetry); Apple-only, so held by the P-SAFE-03 digest, the P-PRIV-05 emit-site whitelist and ios-compile success - no Linux test (Sources/Telemetry is outside touches; ruled in the Log)."
---
## Brief

Survey 2026-10-10 (M6, P-PRIV-04): services/api/src/account.ts handles DELETE /account and revokes the Apple token
internally (there is no separate /auth/revoke route), but the app has no row - SettingsScreen.swift says Delete
account arrives "with the features they control" - and Sources/ScenicAPIClient has no account client.

MEASURE FIRST: account.ts's request, auth and answers (quote them), what the app holds locally that names the account
(keychain install id, session JWT, paid token, saved drives, learned speeds - which are account data and which are
device data), and App Review 5.1.1(v)'s requirement. RULE the tap path (Settings -> Delete account -> confirm =
3 taps), what is erased on success, and the honest failure copy. Tests: the client by exact request equality and
every answer; the local erase as a table over every stored item; a ScenicKit model test that the path is <= 3
actions. Every apps/ios Swift edit needs the P-SAFE-03 digest re-approval; if the permission classifier refuses it,
ship the Linux slice and say so in stillOpen. The XCUITest half waits on T-0180's xcodeproj lock - record that.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-2).
- 2026-10-15T20:03:45Z claimed by agent/claude-opus-5; lease until 2026-10-16T20:03:45Z
- 2026-10-15T20:08:17Z MEASURE. services/api/src/account.ts (index.ts ROUTES["/account"] -> handleDeleteAccount):
  request = any body ignored; method must be DELETE; identity = `Authorization: Bearer <session JWT>` and nothing
  else (BEARER regex over AUTHORIZATION_HEADER, verifySession). Answers, each `content-type: application/json;
  charset=utf-8`, `cache-control: no-store`: 405 {"error":"DELETE only"}; 503 {"error":"auth_unavailable"} (no
  SESSION_JWT_SECRET); 401 {"error":"unauthorized"} (no/invalid/expired Bearer); 503 {"error":"account_unavailable"}
  (D1 read or the batch failed); 200 {"deleted":true,"revoke_pending":<bool>,"plans_pending":<bool>}. The user is
  {deviceId: sub, appleSub: apple claim, accountToken: act claim}; Apple revocation is internal (no /auth/revoke
  route); a repeat is 200 with nothing left (idempotent - P-PRIV-04's bound test). Session JWT lifetime <= 3600 s;
  a plan the sweep misses lives to its KV TTL <= 43200 s (P-PRIV-04 text, T-0326 R8).
  Local inventory (grep of apps/ios/Packages/ScenicApp/Sources and Sources for Keychain/UserDefaults/AppStorage/
  Application Support/caches): (1) Keychain scenic.session/session = SessionRecord {key_id, token, expires_at, act}
  - names the account (token sub = install id, apple, act); (2) Keychain scenic.install/install-id = the install
  UUID = the session sub, i.e. the server's user key - names the account; (3) UserDefaults plan.install.id = the
  same id's fallback copy (StoredInstallID) - names the account; (4) the App Attest key in the Secure Enclave
  (DCAppAttestService has no delete API; its key_id lives only inside (1)); (5) StoreKit appAccountToken - the
  App Store's purchase record, not the app's to erase; (6) Application Support/user.sqlite - saved drives
  (SavedDriveShelf) and the Surprise shown history (SurpriseShownLog), device-only content, names no account;
  (7) safety.disclaimer.acknowledged.v1, (8) VehicleProfile.storageKey, (9) corpus.wifi.only - device
  preferences; (10) the downloaded corpus files (LiveCorpus), (11) the downloaded basemap tiles/la.pmtiles,
  (12) plan.base.url and (13) corpus.manifest.url - device configuration. Learned speeds: NO app storage site
  exists (ScenicKit only, no persistence in apps/ios) - not an item. App Review 5.1.1(v): an app that supports
  account creation must let the user initiate deletion of the account in the app; the app creates a server
  account implicitly (App Attest session keyed by the install id), so the row is required.
- 2026-10-15T20:08:17Z RULINGS (before code).
  R1 tap path = home.settings -> settings.deleteAccount -> settings.deleteAccount.confirm (3 taps from home), held
  by a ScenicKit AccountDeletionPath model whose identifiers each must appear on exactly one shipped
  `.accessibilityIdentifier` line; the XCUITest that taps it waits on T-0180's xcodeproj lock (no UI-test target
  can be added without project.pbxproj).
  R2 AccountClient: DELETE <base>/account, headers exactly [authorization: Bearer <token>], empty body - never
  x-scenic-device (the Worker reads only the Bearer). Every answer maps to one AccountOutcome; a 200 is .deleted only
  for exactly {deleted:true, revoke_pending:bool, plans_pending:bool}, anything else .unreadable (fail closed: no
  erase on a body we cannot read; a retry is safe because the route is idempotent).
  R3 erased on .deleted only: (1) the session Keychain item AND the in-memory session (SessionStore.forgetSession,
  so this launch never sends the deleted session again), (2) the Keychain install id and (3) its UserDefaults copy -
  the next request mints a fresh install id, so nothing links later use to the deleted account. Not erased: (4)
  cannot be (no API; its id goes with (1)); (5) is Apple's - the copy says the subscription is billed by Apple and
  where to cancel; (6)-(13) name no account and never left the phone - the copy says saved drives stay on this
  iPhone until the app is deleted. Disagreement with the task title ("forgets its local identity") ruled: identity
  = (1)-(3), not device content.
  R4 401: the token is handed back (accountSessionRejected = SessionStore's plan-family regrant, one re-acquisition
  per purchase value per launch) and exactly one more request is made with the renewed token; at most two requests
  per tap. No session -> .noSession, zero requests. Offline (no reply) -> .offline, nothing erased.
  R5 failure erases nothing and claims nothing: every non-.deleted outcome leaves (1)-(13) untouched.
  R6 copy (AccountDeletionCopy, ScenicAPIClient so it can switch on AccountOutcome): success "Your account is
  deleted." + subscription/saved-drives sentences (+ Sign in with Apple sentence when revoke_pending, + 12-hour
  sentence when plans_pending); offline/noSession say nothing was deleted and to check the connection; 503/401/
  unexpected say the account was not deleted and to try later; unreadable says the deletion could not be confirmed
  and that trying again is safe.
  R7 the shell (apps/ios/ScenicDrive/ScenicDriveApp.swift) is the only module that sees both Entitlements and
  PlanAdapter, so the row's action is handed in there: touches widened to that one file (pinned digest
  re-approved); no Package.swift change - Entitlements stays DesignSystem-only and receives a
  `() async -> String` (the note).
  R8 the screenshot workflow's LIST is in .github (not in touches): no new launch screen; the existing `settings`
  shot is where the row is looked at, and the confirmation dialog is not shot (recorded for the XCUITest task).
  R9 the new Sources modules compute no number reaching score, route or tags (status-code switch, boolean body
  read, string copy, an item table): allowlisted in mutate-population-allowlist.json with a reason each.
- 2026-10-15T20:43:08Z A5 RED (commit 96277cb6, tests before code): `swift build --build-tests` -> AccountClientTests:
  cannot find 'AccountClient' (1), type 'AccountOutcome' (4); AccountDeletionCopyTests: 'AccountDeletionCopy' (1),
  'AccountOutcome' (2); AccountEraseTableTests: 'AccountClient' (1), 'AccountDeletion' (1), 'LocalAccountItem' (8),
  'AccountOutcome' (4); RecordingEraser: 'LocalAccountEraser' (2), 'LocalAccountItem' (5); ScriptedAccountSession:
  'AccountSessionProvider' (2); `swift build --target ScenicKitTests` -> AccountDeletionPathTests: cannot find
  'AccountDeletionPath' (lines 27, 28, 35). After the ScenicKit/ScenicAPIClient code and before the Settings row:
  everyStepIsShipped FAILED twice by name (settings.deleteAccount and settings.deleteAccount.confirm count 0, the
  home.settings line counted 1) - the source binding seen red; then green with the row.
  R3 addendum (ruled while writing the eraser): the erase ORDER is installIDDefaults, installIDKeychain, session - the
  UserDefaults copy first so a concurrent StoredInstallID.installID() cannot move the old id back into an emptied
  Keychain item, the install id before the session so a session acquired after the forget cannot carry the old id.
  Residue: a request already in flight with the old Bearer (stateless JWT <= 3600 s; P-PRIV-04 NOT ASSERTED).
  R7 consequences: the Settings mount line is whitelisted in three places (check-safety-disclaimer-frozen,
  check-safety-disclaimer-doors, store_links_pinned.SETTINGS_MOUNT) - all three re-approved with the new
  `deleteAccount:` argument; store_links_pinned's Settings section run gains `account`, its identifier whitelist
  gains settings.deleteAccount, settings.deleteAccount.confirm and settings.deletionNote, and FROZEN[SettingsScreen]
  is re-approved (4e0dc5e8...). check-store-links --prove-red: 33/33 rows as required.
  Hand mutants (.artifacts/mutants.py, swift filter of the four account suites), each CAUGHT by name:
  erase-on-any-outcome (AccountDeletion's guard removed) -> `Every outcome x every item: erased exactly on deleted,
  and only the identity`; user-store-erased (.userStore erasedOnDeletion) -> the same; deleted-false-accepted ->
  `Every answer is one outcome after exactly one request` + the erase table; retry-without-renewal-check -> `A 401
  whose renewal yields no token or the same token is unauthorized after one request`; device-header-sent -> five
  AccountClientTests incl. `DELETE /account is exactly the Bearer and nothing else ...`.
  `python ops/lib/run-named-tests.py P-PRIV-04` -> NAMED P-PRIV-04 passed=83/83 (68 vitest + 15 swift).
- 2026-10-15T21:06:46Z A6 iOS CI on 4f840a4a: ios-compile run 38804308890 = success (3m48s); ios-screenshot run
  38804313035 = success (16m13s). Looked at settings-light.png and settings-dark.png: Subscription, Vehicle,
  Offline places, then the `Account` section header at the bottom edge in both looks - the Delete Account ROW itself
  is below the fold of the first screen, so the shot does not show it rendered (R8: no new launch screen, the
  workflow's LIST is in .github). Its render and the confirmation dialog are unseen - with the tap path, the
  XCUITest half that waits on T-0180's xcodeproj lock.
  FINAL (merged origin/main at 0849cfe5, T-0355 in; auto-merged allowlist, named-tests.json, PINS.yaml, digests):
  `swift test --filter 'AccountClientTests|AccountEraseTableTests|AccountDeletionCopyTests|AccountDeletionPathTests|
  SessionStoreTests|PlanSessionRetryTests|PlanBearerTests|LedgerClientTests'` -> Test run with 36 tests in 8 suites
  passed; `run-named-tests.py P-PRIV-04` -> NAMED P-PRIV-04 passed=83/83; check-safety-disclaimer exit 0;
  check-store-links exit 0; check-mutate-population `P-PROC-06: every added module is covered or allowlisted; the
  floor of 154 holds`; check-mutate-only `NAME-PAIRS OK: 196788 pair tokens over 42 id populations`; check-line-cap
  `P-SRC-02: 601 Swift files tracked ... none over 300 lines`; check-pins-yaml `PINS-YAML ok pins=50 fields=403`;
  check-exec-bits `P-OPS-01: 218 files, 23 required present, all modes correct`; queue-check `QUEUE OK (354 tasks)`.
- 2026-10-15T21:25:37Z PR #243 core FAILED on check-pins P-PRIV-05 (CI run 38807412822): T-0355's ops/lib/check-telemetry-emit-sites.txt
  (arrived with the origin/main merge) whitelists the shell's Settings mount line - `REFUSED site not on the
  whitelist: apps/ios/ScenicDrive/ScenicDriveApp.swift: SettingsScreen(... deleteAccount: ...)` and `REFUSED approved
  site missing`. A fourth whitelist of the same line (R7): re-approved there; `check-telemetry-emit-sites.py` ->
  `P-PRIV-05 emit sites: ok - 32 lines approved; 3 of 14 cases emitted once, 11 pending by task`.
- 2026-10-15T22:13:30Z rv1-t0356 FAIL (PR #243, head c967117d) - rulings before code. B1 ACCEPTED: with
  `keychain = .absent` deleted from SessionStore.forgetSession() the cached read stays .valid(old), so the next
  session's write is KeychainWrite.replacing(over: .valid) = .update - on device a SecItemUpdate on the item the
  forget just deleted (errSecItemNotFound), `keep` then leaves `keychain` at .valid(old), every later write in the
  launch is an update too, the new session is never persisted and the post-deletion key is orphaned at the next
  launch's attest. The test gap is real: `forgetSession()` reads storage.removes and the next token, never
  storage.writes. Fix = test only (the shipped code is right): the post-forget writes EQUAL [.add] by the whole
  KeychainWrite list; the mutant shown RED by the test's name, then GREEN.
  Recordable (P-PRIV-04 R3, "nothing links later use to the deleted account") ACCEPTED: T-0355's LiveTelemetry builds
  its TelemetryClient once per launch (`static let client = build()`) with StoredInstallID().installID() captured
  in its x-scenic-device header, so an event after a confirmed deletion carries the deleted id. RULING on where the
  fix lives: Sources/Telemetry and Tests/TelemetryTests are outside this task's touches (the pre-commit hook rejects
  them), and changing TelemetryClient's init would also change T-0355's shipped API under T-0355's tests. So the fix
  is Apple-only, in PlanAdapter: a new actor InstallBoundTelemetry reads StoredInstallID().installID() at EACH record
  and rebuilds the TelemetryClient (same base, same transport type) when the id differs from the one it was built
  with; LiveTelemetry holds that actor instead of a client. Batching/capacity (T-0355 R3) are unchanged within one id.
  Held by: the P-SAFE-03 digest rows (re-approved), the P-PRIV-05 emit-site whitelist (the new lines approved) and
  ios-compile success. No Linux test and no mutant by name - recorded as a gap, not claimed; a TelemetryClient fed an
  id provider with a per-request Linux test is the follow-up when a task may touch Sources/Telemetry.
- 2026-10-15T22:23:41Z rv1 fixes landed. Hand mutants (continued from the 20:xx list; .artifacts/b1mutant.sh, swift
  filter `AccountClientTests|AccountEraseTableTests|AccountDeletionPathTests|AccountDeletionCopyTests|
  SessionStoreTests|TelemetryTests`): b1-forget-keeps-keychain-cache (`keychain = .absent` deleted from
  forgetSession()) -> CAUGHT: `× Test "forgetSession removes the Keychain item and the forgotten token is never
  handed back" recorded an issue at AccountEraseTableTests.swift:102:9: Expectation failed: (storage.writes.map(\.write)
  → [ScenicAPIClient.KeychainWrite.update]) == ([.add] → [ScenicAPIClient.KeychainWrite.add])`, `× Test run with 38
  tests in 12 suites failed after 0.068 seconds with 1 issue`; restored clean; GREEN `√ Test run with 38 tests in 12
  suites passed after 0.702 seconds`.
  Telemetry (A10): InstallBoundTelemetry.swift (new, PlanAdapter) + LiveTelemetry.swift. P-PRIV-05 emit sites seen RED
  on the change before re-approval: `P-PRIV-05 emit sites: FAILED - 13 refusals` (9 new lines not on the whitelist,
  4 approved LiveTelemetry lines missing); re-approved in ops/lib/check-telemetry-emit-sites.txt -> `P-PRIV-05 emit
  sites: ok - 37 lines approved; 3 of 14 cases emitted once, 11 pending by task`. P-SAFE-03 digests re-approved in
  ops/lib/check-safety-disclaimer-pinned: LiveTelemetry.swift 34d306a8254b269e04bde804c4d332e700e479e463e640ba011ddfb40d986686,
  InstallBoundTelemetry.swift 00cf5e6e8ca446c303cc68f6fca49190e1dce8df4c3266ca2bc763744396fa6c (new row).
- 2026-10-15T22:41:55Z FINAL rv1 (merged origin/main 2fdde971 at 1553c173, T-0360 waitlist in). Conflicts resolved
  as unions: check-telemetry-emit-sites.txt (main's LiveWaitlist `import Telemetry` kept, the old LiveTelemetry
  transport row dropped), -linked-digests.txt (both sides' rows), -pinned (both sides' rows; ScenicDriveApp.swift
  recomputed on the merged file = 23e298393a25a0b01144ef94d6907f3dd0e62c8863dde7b33391037ae26505b4). On 1553c173:
  swift filter `AccountClientTests|AccountEraseTableTests|AccountDeletionPathTests|AccountDeletionCopyTests|
  SessionStoreTests|TelemetryTests` -> `Test run with 38 tests in 12 suites passed after 0.095 seconds`;
  `bash ops/lib/check-safety-disclaimer` exit 0 (`... LAST all 99 app .swift, then 299 root + pbxproj file(s)
  (-linked).`); check-mutate-population `P-PROC-06: every added module is covered or allowlisted; the floor of 157
  holds` exit 0; check-telemetry-emit-sites `P-PRIV-05 emit sites: ok - 38 lines approved; 3 of 14 cases emitted
  once, 11 pending by task` exit 0; check-pins-yaml `PINS-YAML ok pins=50 fields=403` exit 0; queue-check `QUEUE OK
  (355 tasks)` exit 0; check-line-cap `P-SRC-02: 615 Swift files tracked (Sources=298, Tests=218, apps/ios=99), none
  over 300 lines` exit 0. ios-compile run 38817042776 on 1553c173 = success (4m49s); PR linux-core run 38817047779 on
  1553c173 = success (7m0s). origin/main re-fetched at this entry: still 2fdde971, an ancestor of HEAD.
