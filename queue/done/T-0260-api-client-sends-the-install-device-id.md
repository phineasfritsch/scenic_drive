---
id: T-0260
title: ScenicAPIClient sends the install UUID as x-scenic-device on every Worker call, so each install gets its own quota bucket instead of sharing device:unidentified
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T16:33:17Z
lease_expires_at: 2026-10-06T04:33:17Z
worktree: .worktrees/T-0260
branch: task/T-0260
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/lib/mutate-population-allowlist.json, queue/]
pins_affected: [P-COST-01, P-PRIV-05]
reviewer: agent/rv1-t-0260
depends_on: [T-0251, T-0256]
verify: [ops/test, ops/check-pins]
acceptance:
  - "every request ScenicAPIClient builds carries x-scenic-device equal to an injected install-id provider's lowercased RFC 4122 UUID, asserted on the recorded request by EXACT equality of the whole header set; the id is generated once per install and never derived from location, and no other identifying header is added (P-PRIV-05)"
  - "a request built with no provider is refused at build time (a typed error), never sent without the header - RED by name"
---
## Brief

T-0256 (PR #147) R2: until App Attest exists, the Worker keys quota by the app's install UUID from the
x-scenic-device header; a missing or malformed header lands in one shared device:unidentified bucket, so every
install would share 3 anon plans a day. The keychain-backed provider itself lives in the Apple package (M6); this
task is the root-package half: the header and the provider protocol.

## Log
- 2026-10-05T14:31:22Z filed by agent/claude-opus-5 (orchestrator) from T-0256's stillOpen (e).
- 2026-10-05T16:31:14Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): dependencies merged (T-0175 #142, T-0251 #148, T-0256 #147).
- 2026-10-05T16:33:17Z claimed by agent/claude-opus-5; lease until 2026-10-06T04:33:17Z
- 2026-10-05T16:44:39Z RULINGS by agent/claude-opus-5 (owner), before any code. Measured: the only request
  builder in ScenicAPIClient is `PlanClient.plan` (one `PlanHTTPRequest(... headers: ["content-type": ...])`);
  the only `PlanClient(` call site in the tree is Tests/ScenicAPIClientTests/PlanWire.swift:40 (apps/ and Sources/
  have none). The Worker's contract (services/api/src/routerDeps.ts): `DEVICE_HEADER = "x-scenic-device"`,
  `DEVICE_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/` read after `.toLowerCase()`;
  anything else is `device:unidentified`.
  R1 (the provider). New `public protocol InstallIDProvider: Sendable { func installID() -> UUID }` in its own
  file. It returns Foundation's `UUID`, not a String, so a malformed id cannot be represented; it takes NO
  argument, so the client has nothing - no origin, no place - to derive it from (P-PRIV-05). The keychain-backed
  conformer that generates the UUID once per install is the Apple package's (M6, per the Brief); this package
  never generates an id - `PlanClient` only reads the provider. Not optional-returning: a keychain read that fails
  is the M6 conformer's to handle; this package's "no id" is "no provider" (R3).
  R2 (the header). `PlanClient.plan` adds exactly ONE header, `x-scenic-device: <uuid.uuidString.lowercased()>`
  (Foundation's uuidString is UPPERCASE; the Worker lowercases too, but the acceptance asks the client to send the
  lowercased form). The whole header set is then exactly {content-type, x-scenic-device}; no other identifying
  header. Asserted by EXACT equality of the whole `PlanHTTPRequest` (url, method, headers, body) - the existing
  T-0251 full-equality tests, including the URLSession stub test, gain the header in their expected literals.
  "Generated once, never derived from location": two plans through one client from DIFFERENT origins carry the
  same header byte-for-byte, equal to the provider's id.
  R3 (no provider). `PlanClient.init(base:transport:installID:)` takes `(any InstallIDProvider)?` with NO default,
  so omitting it is a compile error and nil must be written. A nil provider is refused when the request is built,
  as the typed `PlanError.refusedOnDevice(.noInstallID)` (new `PlanRefusal` case) with ZERO transport calls -
  the same shape as T-0251's other device refusals. Checked BEFORE the body is validated, so it is reached by
  every plan; RED by name: `testRefusesAPlanWithNoInstallIDProviderAndSendsNothing`.
  R4 (scope). `pins_affected: [P-COST-01, P-PRIV-05]` - neither id occurs under pins/ or ops/ (grep -rln, 0 files);
  no pin is edited. The new Sources file needs a P-PROC-06 allowlist entry (a protocol, no code), so touches: gains
  ops/lib/mutate-population-allowlist.json; queue/ for this file's own transition.
- 2026-10-05T16:57:57Z RED then GREEN by agent/claude-opus-5 (owner). RED, with the API surface in place (PlanClient.init takes
  installID:, PlanRefusal.noInstallID exists) and no behavior: `swift test --scratch-path .build/t0260 --filter
  ScenicAPIClientTests` -> "Executed 43 tests, with 8 failures (0 unexpected)", exit 1; failing BY NAME:
  PlanClientDeviceTests.testRefusesAPlanWithNoInstallIDProviderAndSendsNothing (got unexpectedResponse(status: 200),
  count 1 != 0), .testNoInstallIDIsRefusedBeforeTheOriginIsJudged (got originMoreThanTwoDecimals),
  .testSendsTheInjectedProvidersIDLowercasedAsTheWholeHeaderSet, .testOneClientSendsTheSameIDFromEveryOrigin,
  PlanClientRequestTests.testSendsExactlyTheBodyT0248Ruled, .testDepartsAtIsSentAsAUTCInstantInWholeSeconds,
  URLSessionPlanTransportTests.testURLSessionCarriesTheWholeRequestAndReturnsTheWholeReply (each: headers
  ["content-type"] only vs the expected whole set with x-scenic-device). GREEN after PlanClient.plan's guard and
  header: same command -> "Executed 43 tests, with 0 failures (0 unexpected)", exit 0.
  Pre-review mutants (driver .build/t0260-mutants.py, filter PlanClientDeviceTests, source restored after each):
  M1 drop .lowercased() -> exit 1 KILLED by testSendsTheInjectedProvidersIDLowercasedAsTheWholeHeaderSet and
  testOneClientSendsTheSameIDFromEveryOrigin; M2 send a fixed literal id -> exit 1 KILLED by
  testSendsTheInjectedProvidersIDLowercasedAsTheWholeHeaderSet; M3 move the nil guard after body validation ->
  exit 1 KILLED by testNoInstallIDIsRefusedBeforeTheOriginIsJudged. 0 survivors.
- 2026-10-05T17:22:40Z FINAL PRE-REVIEW by agent/claude-opus-5 (owner): `git fetch origin` + merge origin/main (80b5f4e, T-0261 PR #149)
  -> merged head 0e4fda0. R5 (ruled after the merge, amending R4): T-0261 added pins/PINS.yaml rows P-PRIV-05 and
  P-COST-01; both are `anchor: api` rows binding Worker vitest tests BY NAME through ops/lib/run-named-tests.py
  (planPrivacy/loopShape; quota-before-upstream). This task touches no Worker code and neither row names a Swift test,
  so both rows hold unchanged; binding PlanClientDeviceTests by name to P-PRIV-05 needs a Swift tier in
  run-named-tests.py and is left open, not done here. ACCEPTANCE on the merged head:
  (1) whole-header-set equality - `swift test --scratch-path .build/t0260 --filter ScenicAPIClient` -> exit 0,
  "Executed 43 tests, with 0 failures (0 unexpected)": PlanClientDeviceTests.testSendsTheInjectedProvidersIDLowercasedAsTheWholeHeaderSet,
  .testOneClientSendsTheSameIDFromEveryOrigin, PlanClientRequestTests.testSendsExactlyTheBodyT0248Ruled,
  .testDepartsAtIsSentAsAUTCInstantInWholeSeconds and URLSessionPlanTransportTests.testURLSessionCarriesTheWholeRequestAndReturnsTheWholeReply
  compare the whole PlanHTTPRequest, headers exactly {content-type, x-scenic-device}.
  (2) no provider -> typed refusal, zero requests - testRefusesAPlanWithNoInstallIDProviderAndSendsNothing and
  testNoInstallIDIsRefusedBeforeTheOriginIsJudged pass (RED by name above).
  Gates: `python ops/lib/check-mutate-population.py` -> "P-PROC-06: every added module is covered or allowlisted;
  the floor of 55 holds", exit 0; `bash ops/queue-check` -> "QUEUE OK (253 tasks)", exit 0. wc -l: Sources/ScenicAPIClient/PlanClient.swift 58; Sources/ScenicAPIClient/InstallIDProvider.swift 12; Sources/ScenicAPIClient/PlanRefusal.swift 15; Tests/ScenicAPIClientTests/PlanClientDeviceTests.swift 55; Tests/ScenicAPIClientTests/FixedInstallID.swift 13; Tests/ScenicAPIClientTests/PlanWire.swift 60; Tests/ScenicAPIClientTests/PlanClientRequestTests.swift 126; Tests/ScenicAPIClientTests/URLSessionPlanTransportTests.swift 27; 
  all under the 300 cap; `ops/lib/check-line-cap` (whole-tree walk) had not finished on this contended box at
  this entry - CI is its run of record.
- 2026-10-05T17:54:30Z REVIEW PASS by agent/rv1-t-0260 (reviewer, not the owner) of PR #151 at head 8aa7ebf.
  Acceptance (1), whole header set by exact equality: read PlanClient.plan - the one PlanHTTPRequest carries headers
  exactly {content-type, x-scenic-device: installID.installID().uuidString.lowercased()}; PlanClientDeviceTests,
  PlanClientRequestTests and URLSessionPlanTransportTests compare the whole PlanHTTPRequest. The provider takes no
  argument and returns a Foundation UUID (R1); generating it once per install is the M6 keychain conformer's, per
  the Brief. Bare `swift test --scratch-path .build/rv1-t0260 --filter ScenicAPIClient` on the unmutated head ->
  exit 0, "Executed 43 tests, with 0 failures (0 unexpected)".
  Acceptance (2), no provider: the nil guard is the first statement of plan() and throws
  .refusedOnDevice(.noInstallID) before the transport is reached; testRefusesAPlanWithNoInstallIDProviderAndSendsNothing
  and testNoInstallIDIsRefusedBeforeTheOriginIsJudged pass, and the owner's RED run above names them.
  Reviewer mutant MD (not M1-M3, not MA-MC), P-PRIV-05 "never derived from location": PlanClient.swift's header value
  becomes `installID.installID().uuidString.lowercased() + (origin.latitude < 36 ? "" : "-n")` -> same command exit 1,
  "Executed 43 tests, with 1 failure (0 unexpected)", KILLED by name by
  PlanClientDeviceTests.testOneClientSendsTheSameIDFromEveryOrigin (second request sent
  "6f9619ff-8b86-4d01-b42d-00c04fc964ff-n"). Source restored, `git diff --stat` empty.
  Gates: `bash ops/queue-check` -> "QUEUE OK (253 tasks)", exit 0; `gh pr checks 151` -> core pass, pins-source-only
  pass. `git merge-base --is-ancestor origin/main origin/task/T-0260` -> exit 1: main moved by PR #150 (T-0262)
  and two queue commits. The drift is services/api/ and queue/ only; it changes no ops/, pins/, .github/,
  .githooks/, Package.swift, Sources/ or Tests/ path, and routerDeps.ts DEVICE_HEADER/DEVICE_ID are unchanged on
  main. `git merge-tree --write-tree origin/main origin/task/T-0260` -> exit 0, a clean merge. Non-blocking.
  Recorded, not blocking: P-PRIV-05 binds no Swift test by name yet (needs a Swift tier in
  ops/lib/run-named-tests.py; the owner has not filed it).
