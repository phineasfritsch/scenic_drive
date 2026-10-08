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
- 2026-10-08T02:01:36Z MEASURED, then RULINGS (author rule, before any code), agent/claude-opus-5:
  - MEASURED at b47f40bb. (a) The Worker flow (attest.ts, appAttest.ts, appAssert.ts, sessionJwt.ts, attestStore.ts):
    POST /attest/challenge reads no body, is limited per `x-scenic-device` and globally (429 challenge_rate_limited),
    503 attest_unavailable without the secret, 405 `POST only`; 200 {challenge: 43 base64url chars, expires_at},
    CHALLENGE_TTL_MS 300000. POST /attest takes exactly {attestation, challenge, device, keyId} (+ optional
    appAccountToken), keyId 43 base64 + "=", device a UUID; clientDataHash = SHA256(UTF-8 challenge)
    (appAttest.ts:134); 200 {token, expires_at} (SESSION_TTL_S 3600), 400 invalid_attestation, 503. POST
    /attest/assert takes exactly {assertion, challenge, keyId}, the same clientDataHash (appAssert.ts:51), 200
    {token, expires_at}, 400 invalid_assertion. (b) Linux-testable: every request's construction, reply -> outcome,
    the session decision (use / renew / attest / none) and its once-per-launch budget, the Keychain write decision,
    the ledger write with an injected cell function. Apple-only: DCAppAttestService (generateKey, attestKey,
    generateAssertion), CryptoKit SHA256, Security SecItem*, the H3Cell call in PlanAdapter - compile-checked by
    ios-compile, exercised on a device later (T-0009). (c) StoredInstallID.storeInKeychain is SecItemAdd only: an
    existing item that is not a UUID reads errSecSuccess with no id, the add fails errSecDuplicateItem and the id
    moves to UserDefaults on every launch - rv2-t0307's finding, confirmed by reading. (d) SurpriseCard recomputes
    the pick from `history` on every render and never appends `shown`: appending the shown pick to the history the
    pick reads would re-pick at once and cascade through the deck. (e) Telemetry is a root product (Package.swift:35);
    PlanAdapter depends on ScenicKit, ScenicAPIClient, PlaceStore - one `.product(name: "Telemetry", package:
    "ScenicDrive")` line in apps/ios/Packages/ScenicApp/Package.swift under the package-swift lock; no root edit.
  - R1 AttestClient (ScenicAPIClient). challenge(): POST {base}/attest/challenge, headers exactly {x-scenic-device:
    install id lowercased}, empty body - the header is the Worker's per-device limit key and the same value /attest
    carries as `device`, so nothing new is disclosed. attest(): POST /attest, headers {content-type:
    application/json}, body sorted-key JSON {attestation, challenge, device, keyId}, slashes unescaped; no
    appAccountToken (no StoreKit token is wired). assert(): POST /attest/assert {assertion, challenge, keyId}. One
    call, at most one request, never retried.
  - R2 AttestReplyReader, one outcome per answer: 200 to the challenge {challenge 43 base64url, expires_at} ->
    .challenge; 200 to attest/assert {token non-empty, expires_at ISO-8601} -> .session; any other 200 -> .unreadable;
    400 -> .rejected; 405 -> .methodRefused; 429 challenge_rate_limited -> .rateLimited, other 429 ->
    .unexpected(429); 503 -> .unavailable; any other status -> .unexpected(status); no reply -> .offline.
  - R3 SessionStep.next(stored:now:spent:) is pure: a valid record whose expiry is more than 60 s after now ->
    .use(token), zero requests; otherwise spent -> .none; a valid record (expired or dropped) -> .renew(keyId)
    (challenge + assert); absent or malformed -> .attest (challenge + a new key); a read failure -> .none (a locked
    Keychain burns no key). SessionStore (an actor, production's LedgerSessionProvider) spends its ONE acquisition
    per launch before its first await, so a launch makes at most one challenge and one attest-or-assert whatever
    happens; an attester that is not supported (the simulator) makes zero requests. Any failure -> nil and the
    history stays device-only.
  - R4 a 401. LedgerSessionProvider becomes async and gains sessionRejected(token). LedgerClient still never retries
    (T-0307 R4): on .unauthorized it hands the token back and the store drops it in memory (expiry distantPast); the
    NEXT call renews if the launch's acquisition is unspent. An assertion answered .rejected forgets the key (the
    Keychain item is removed), so the next launch attests a new key. A rejected token's Keychain copy is not
    rewritten: the next launch meets one 401, then renews - bounded.
  - R5 storage. One generic-password item, service `scenic.session`, account `session`,
    kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly, not synchronizable; the value sorted-key JSON {expires_at (whole
    Unix seconds), key_id, token}; SessionRecord(data:) admits exactly that shape, anything else is malformed.
  - R6 replace semantics, pure and Linux-tested. KeychainWrite.replacing(over:): absent -> .add; valid or malformed
    -> .update (SecItemUpdate of the value and the accessibility); read failure -> .skip. InstallIDDecision.decide(
    keychain:defaults:fresh:): valid(id) -> (id, .skip); absent -> (defaults ?? fresh, .add); malformed -> (defaults
    ?? fresh, .update); read failure -> (defaults ?? fresh, .skip). PlanAdapter KeychainItem maps SecItemCopyMatching
    to KeychainRead and performs the write; a failed write keeps the UserDefaults copy (T-0307 R1 unchanged). The
    table: the four states x {defaults valid, defaults absent}, whole decision by full equality.
  - R7 recording a shown place. ScenicKit SurpriseShowing.recording(_:on:in:) appends Shown{id, category, corridor,
    date} and answers nil when that id is already shown that day (a re-render records and posts nothing). The card
    picks from a `basis` history that moves only on "not this" and "start over", so recording never re-picks (d).
    SurpriseLedgerSource gains recordShown(_ candidate: SurpriseCandidate) - the argument is the place, no device
    position reaches it. LedgerSurpriseSource (ScenicAPIClient; LiveSurpriseLedger's logic moved there to be
    Linux-testable) posts {place_id: candidate.id, cell: cellOf(candidate.coordinate)}; PlanAdapter's cellOf is
    Telemetry H3Cell.containing(...)?.hexString (P-PRIV-05). Start over clears the feedback only: shown stays.
  - R8 disagreement, acceptance 3: "a ScenicKit test" that counts requests - a request count is a transport fact and
    ScenicKitTests cannot import ScenicAPIClient. Ruled: the history half is ScenicKitTests SurpriseShowingTests; the
    table {no session, session, ledger 429, ledger 401} is in ScenicAPIClientTests (which imports ScenicKit), driving
    SurpriseShowing.recording then LedgerSurpriseSource.recordShown in the card's order, the history and the WHOLE
    request list by full equality.
  - R9 the device history is in-memory @State (T-0307 (c)); persisting it across launches is out of scope - across
    launches the ledger is the 90-day memory. Filed stillOpen.
  - R10 P-SAFE-03: the gate is untouched; ScenicDriveApp is unchanged (LiveSurpriseLedger.make() keeps its
    signature); NoLedgerSession is deleted, PlanAdapter gains KeychainItem, KeychainSessionStorage and
    DeviceAppAttester - -pinned PINNED_APP_SWIFT / PINNED_SURPRISE and the digest rows re-approved.
  - R11 population ops/mutate/session{,_mutations,_run}.py over AttestClient, AttestReplyReader, SessionStep,
    SessionStore, KeychainWrite, InstallIDDecision, LedgerSurpriseSource and SurpriseShowing, literal floor.
