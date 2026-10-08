---
id: T-0323
title: P-STORE-02 asserts the app's side of the paid tier - the AccountToken suites bound by name, and a whitelist guard that confines the x-scenic-account-token identifier to IdentityHeaders so a fourth client cannot inline it
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T15:27:38Z
lease_expires_at: 2026-10-08T23:27:38Z
worktree: .worktrees/T-0323
branch: task/T-0323
exclusive: []
touches: [ops/lib/, ops/check-pins, pins/PINS.yaml, Tests/ScenicAPIClientTests/]
pins_affected: [P-STORE-02]
reviewer: agent/rv2-t0323
depends_on: [T-0315]
verify: [ops/check-pins]
acceptance:
  - "pins/PINS.yaml P-STORE-02 no longer says the app side is NOT ASSERTED; AccountTokenHeaderTests and AccountTokenCandidateTests are bound by name in ops/lib/named-tests.json (quoted strings per memory pins-yaml-strict); run-named-tests seen red with one mutant, then green"
  - "A guard under ops/lib refuses any occurrence of the header name string outside its approved site(s) in Sources/ and apps/ios (WHITELIST of sites, whole-line per memory source-guards-fail-closed, never a blacklist of spellings); prove-red rows: an inlined header in a new client file, and the identifier split across a concatenation if the guard claims to see it - each refused by name"
  - "R1 of rv1-t0315 ruled in the Log: whether StoreKitAccountToken (Apple-only) gets a behavioural oracle (an Apple-side test target) or stays digest-pinned, with the reason"
---
## Brief

rv1-t0315 recordables R1, R2 and R4 (PR #206).

## Log
- 2026-10-08T12:24:40Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0315's recordables R1, R2, R4.
- 2026-10-08T15:27:38Z claimed by agent/claude-opus-5; lease until 2026-10-08T23:27:38Z
- 2026-10-08T15:31:07Z MEASURED then RULED (agent/claude-opus-5, before any code), at e158ddbc.
  MEASUREMENT. `grep -rn -i "x-scenic-account-token" Sources apps/ios Tests`: 9 lines. CODE lines (not //-leading):
  Sources/ScenicAPIClient/IdentityHeaders.swift:9 `public static let accountHeader = "x-scenic-account-token"`;
  Tests/ScenicAPIClientTests/AccountTokenHeaderTests.swift:41, :44, :108, :109 (literals). COMMENT lines (/// or //):
  IdentityHeaders.swift:4, Sources/ScenicAPIClient/PlanClient.swift:8, apps/ios/.../Entitlements/PaywallScreen.swift:33,
  apps/ios/.../PlanAdapter/StoreKitAccountToken.swift:5. The identifier `accountHeader` (any case) in Sources/ and
  apps/ios: IdentityHeaders.swift:9 and :13 (`if let account { headers[accountHeader] = ... }`) only. `account-token`
  (any case) on a code line in Sources/ and apps/ios: IdentityHeaders.swift:9 only. Worker (services/api/src): one
  code line, asn.ts:11 `export const ACCOUNT_TOKEN_HEADER = "x-scenic-account-token";`, plus comments in accountTier.ts,
  asn.ts, index.ts, routerDeps.ts, sessionIdentity.ts.
  - R1 SCOPE OF THE GUARD. It scans every *.swift under Sources/ and apps/ (as check-learned-speeds-sites.py), not
    Tests/: a test MUST spell the header as its own literal - AccountTokenHeaderTests compares the whole request to
    literals (memory full-equality-oracle), and ops/mutate/accounttoken_mutations.py's mutant 3 (the header
    misnamed in IdentityHeaders) is caught only because the test does not read IdentityHeaders.accountHeader. A
    test file sends no request, so a literal there is no fourth client. The Worker is OUT of scope: TypeScript, its
    own ACCOUNT_TOKEN_HEADER, the reading side, bound by its own tier tests; recorded as not asserted by this guard.
  - R2 WHAT THE GUARD READS, a WHITELIST OF SITES. Every line (trailing whitespace dropped) of every scanned file that
    matches `account-token|accountheader` case-insensitively, skipping only lines whose first non-blank characters
    are `//` (memory source-guards-fail-closed), must be one of the approved (file, whole line) pairs, as many times
    as approved: exactly IdentityHeaders.swift's :9 and :13. Case-insensitive because HTTP header names are - an
    `X-Scenic-Account-Token` sends the same header. `account-token` sees the split at the prefix
    (`"x-scenic-" + "account-token"`), so that split is a prove-red row; `accountheader` sees a new client writing
    `headers[IdentityHeaders.accountHeader]` beside the shared json(). An approved line that is gone is red too.
    WHAT IT CANNOT SEE: a split INSIDE `account-token` (`"x-scenic-acc" + "ount-token"`), unicode escapes, a name
    built at runtime, non-Swift files; a line inside `/* */` is read as code, so it can only fail closed.
    Exit 0 ok, 1 refused by name, 2 fail-closed (root missing, no site at all).
  - R3 THE NAMED TESTS. AccountTokenHeaderTests and AccountTokenCandidateTests, every @Test function, bound in
    ops/lib/named-tests.json under P-STORE-02's new "swift" key beside its "vitest" one (run_pin runs both); names
    are the Swift Testing identifiers the xunit report carries, quoted below once measured. P-STORE-02 stays anchor
    api, runs_on [linux]: linux-core's core job has swift and node and runs the full check-pins.
  - R4 rv1-t0315 R1, StoreKitAccountToken: STAYS DIGEST-PINNED (its PINNED_APP_SWIFT row in
    ops/lib/check-safety-disclaimer-pinned), no Apple-side oracle in this task. Reason: its one decision - which
    purchase's token - is AccountTokenCandidate.latest, Linux-tested by AccountTokenCandidateTests and now bound by
    name; what remains is the Transaction.all walk and its verified + autoRenewable filter, which only StoreKitTest's
    SKTestSession on a simulator with a .storekit configuration could exercise. No CI job runs any Apple test today
    (ios-compile builds, ios-screenshot captures), and an Apple test target edits apps/ios's Package.swift and
    project.pbxproj (serial-only, outside touches). The digest pin makes any edit to the walk a reviewed
    re-approval; the gap is written into P-STORE-02's WHAT IT CANNOT SEE.
  - R5 PINS.yaml. P-STORE-02's "NOT ASSERTED HERE: the app's side ... no Linux test can name it" clause is replaced
    by what is now asserted and what is not (StoreKit's own walk, the paywall UI); the assertion becomes the guard,
    its --prove-red, then run-named-tests P-STORE-02.
- 2026-10-08T15:40:03Z BUILT (agent/claude-opus-5). ops/lib/check-account-token-sites.py (192 lines, data 100644,
  APPROVED inline: IdentityHeaders.swift's two lines). R3's names, measured from `swift test --filter
  'ScenicAPIClientTests\.(AccountTokenHeaderTests|AccountTokenCandidateTests)' --xunit-output` (6 tests in 2 suites
  passed; x-swift-testing.xml): AccountTokenHeaderTests/planRequest(_:), tripRequest(_:_:), loopRequest(_:),
  refusalReadsNothing(), rowsFollowThePurchase(); AccountTokenCandidateTests/latest(_:) - all six bound under
  P-STORE-02 "swift" with filter `ScenicAPIClientTests\\.(AccountTokenHeaderTests|AccountTokenCandidateTests)`.
  GUARD SEEN RED, THEN GREEN. Live on the worktree: Sources/ScenicAPIClient/WeatherClient.swift with
  `let header = "x-scenic-" + "account-token"` -> `REFUSED  site not on the whitelist:
  Sources/ScenicAPIClient/WeatherClient.swift: let header = "x-scenic-" + "account-token"`, `FAILED - 1 unapproved,
  0 missing of 2 approved`, exit 1; removed -> `ok - 2 sites, every one approved, in 1 file(s)`, exit 0. --prove-red:
  CONTROL unmodified copy exit=0, CONTROL a //-comment naming the header is not a site exit=0; red (exit=1, refused
  by name) for all 8 rows - the header inlined in a new client file; split across a concatenation; in another case,
  in the app; a new client writes IdentityHeaders.accountHeader; a code line with a trailing comment; a block comment
  line fails closed; an approved line repeated; the approved constant changed - `PROVE-RED OK: 8 of 8 rows red by
  name, controls green`. The prove-red itself seen red by two guard mutants, each restored: NAMES without
  re.IGNORECASE -> `PROVE-RED FAILED: 6 of 8 rows red by name, controls NOT GREEN` (another-case and
  accountHeader rows GREEN, NOT NAMED); the comment skip `line.lstrip().startswith("//")` -> `"//" in line` ->
  `PROVE-RED FAILED: 7 of 8` (the trailing-comment row GREEN). Through the pin's assertion (bash of PINS.yaml's
  P-STORE-02 assertion string): an inlined `forHTTPHeaderField: "x-scenic-account-token"` in WeatherClient.swift ->
  REFUSED by name, ASSERTION EXIT=1; removed -> `ok`, `NAMED P-STORE-02 passed=67/67`, ASSERTION EXIT=0.
  RUN-NAMED-TESTS SEEN RED, THEN GREEN (SCENIC_SWIFT_SCRATCH=.build/t323): green `NAMED P-STORE-02 passed=67/67`
  (61 vitest + 6 swift). M1 refusalReadsNothing() renamed refusalReadsNothingRenamed() -> `RED
  ScenicAPIClientTests.AccountTokenHeaderTests/refusalReadsNothing(): MISSING - no test of this name ran`,
  `passed=66/67`, exit 1. M2 IdentityHeaders `account.uuidString.lowercased()` -> `account.uuidString` -> planRequest,
  tripRequest, loopRequest `FAILED - ['failed']`, `passed=64/67`, exit 1 (and the guard: 1 unapproved, 1 missing).
  Each restored by git checkout; then 67/67. check-pins-yaml: `PINS-YAML ok pins=48 fields=387`.
- 2026-10-08T15:52:00Z FINAL PRE-REVIEW (agent/claude-opus-5). `git fetch origin`; `git merge origin/main`: Already up to
  date (main at e158ddbc; `merge-base --is-ancestor origin/main HEAD` exit 0). ACCEPTANCE re-run on 2d3f290a:
  (1) P-STORE-02 no longer says the app side is NOT ASSERTED (`grep -c "NOT ASSERTED HERE: the app's side"` 0); the
  six AccountToken names bound in named-tests.json; `NAMED P-STORE-02 passed=67/67` exit 0, red by M1/M2 above.
  (2) `P-STORE-02 account-token sites: ok - 2 sites, every one approved, in 1 file(s)` exit 0; `PROVE-RED OK: 8 of 8
  rows red by name, controls green`. (3) R4 ruled above: StoreKitAccountToken stays digest-pinned. Gates:
  `PINS-YAML ok pins=48 fields=387` exit 0; `QUEUE OK (316 tasks)` exit 0; `P-OPS-01: 185 files, 23 required
  present, all modes correct` exit 0.
- 2026-10-08T16:25:51Z FIX - PRE-REVIEW SURVIVOR M3b (agent/claude-opus-5). FINDING: AccountTokenCandidateTests
  dropped from named-tests.json P-STORE-02 in both places (filter `ScenicAPIClientTests\.AccountTokenHeaderTests`,
  the `latest(_:)` row removed) -> `NAMED P-STORE-02 passed=66/66` exit 0, and P-STORE-02's assertion passed, so
  check-pins stayed green with the StoreKit-order oracle unbound. run-named-tests.py refuses only a zero-name entry;
  the 67 and the two suites lived only in the pin's prose. RULING: option (a), and by CLASS - the class is "the gate's
  own table edited" (a row dropped with or without its filter, replaced, repeated or added; the filter changed; a
  file dropped), not only M3b's spelling. A count alone would not close it: run_pin counts rows, not distinct names,
  so a row replaced by a repeat of planRequest keeps 67/67. CLOSED BY: ops/lib/check-named-table.py (183 lines, data
  100644) holds P-STORE-02's whole entry to the sha256 of its canonical JSON (sort_keys, no whitespace) and to 67
  DISTINCT names - both literals in the assertion, so any edit of the entry re-approves them in the same diff - and
  the assertion also requires the runner's printed line to be exactly `NAMED P-STORE-02 passed=67/67`. Digest
  measured: c5af543b66fddaa83383aa7ea350972e006831984f6e0799062067b680841147. NOT CHANGED (out of T-0323's scope,
  same shape): P-SAFE-01/04/07/08/09, P-PRIV-04/06, P-COST-01/04, P-PROD-02/05, P-NAV-01 bind no count or digest;
  recorded in P-STORE-02's prose for a follow-up task.
  SEEN RED, THEN GREEN. --prove-red on the live entry: `CONTROL the entry as is: green`, `CONTROL keys reordered:
  green`, and red by name for all eight rows - `a swift suite dropped with its filter (T-0323 M3b)` (count 66 != 67;
  digest), `a vitest row dropped`, `a row replaced by a repeat of another` (duplicate name
  ScenicAPIClientTests.AccountTokenHeaderTests/planRequest(_:)), `a row replaced by another name`, `the swift filter
  changed alone`, `a row added` (count 68), `a whole vitest file dropped` (count 60), `the entry emptied` -
  `PROVE-RED OK: 8 of 8 rows red by name, controls green`. The prove-red itself seen red by three guard mutants, each
  restored (cmp RESTORED): G1 `sort_keys=True` -> `False` -> `CONTROL the entry as is: RED`, `PROVE-RED FAILED: 8 of
  8 rows red by name, controls NOT GREEN`; G2 the duplicate append -> `pass` -> `GREEN a row replaced by a repeat of
  another: NOT NAMED ['duplicate name']`, `7 of 8`; G3 `if len(seen) != want_count:` -> `if False:` -> four rows
  NOT NAMED ['count'], `4 of 8`. Count literal: `check-named-table.py P-STORE-02 <sha> 66` -> `REFUSED count 67
  distinct names != approved 66` exit 1. THROUGH THE PIN'S ASSERTION (bash of PINS.yaml's P-STORE-02 string via
  yaml.safe_load, SCENIC_SWIFT_SCRATCH=.build/t323): green -> `ok - 2 sites`, `NAMED-TABLE P-STORE-02 ok - 67
  distinct names, sha256 c5af543b66fd`, ASSERTION EXIT=0. M3b applied -> run-named-tests.py alone `NAMED P-STORE-02
  passed=66/66` runner exit=0 (the survivor reproduced), assertion `REFUSED count 66 distinct names != approved 67`,
  `REFUSED digest 418a8d5618eb... != approved c5af543b66fd...`, ASSERTION EXIT=1. M3b with the digest and count both
  re-approved to 418a8d5618eb.../66 (the printed-line literal left at 67) -> `NAMED-TABLE P-STORE-02 ok - 66`,
  `NAMED P-STORE-02 passed=66/66`, ASSERTION EXIT=1 - the third literal is live on its own. named-tests.json
  restored by git checkout (diff --quiet RESTORED). `PINS-YAML ok pins=48 fields=387` exit 0.
- 2026-10-08T16:28:20Z MERGED HEAD (agent/claude-opus-5). Fix committed as 735d6537 and pushed. `git fetch origin`;
  `git merge origin/main` (T-0319's PR #209: PlanClient, PlanRequestBody, named-tests.json +4, the linked digests)
  merged clean as 2a34e2d1; `merge-base --is-ancestor origin/main HEAD` exit 0. Re-run on the merged head: P-STORE-02's
  assertion -> `ok - 2 sites, every one approved, in 1 file(s)`, `NAMED-TABLE P-STORE-02 ok - 67 distinct names,
  sha256 c5af543b66fd` (T-0319's rows are under other pins; this entry's digest unchanged), ASSERTION EXIT=0;
  run-named-tests.py alone `NAMED P-STORE-02 passed=67/67` exit 0; check-named-table --prove-red `PROVE-RED OK: 8 of
  8 rows red by name, controls green`; check-account-token-sites --prove-red `PROVE-RED OK: 8 of 8 rows red by name,
  controls green`; `PINS-YAML ok pins=48 fields=387`; `QUEUE OK (317 tasks)` exit 0.
- 2026-10-08T16:58:11Z agent/claude-opus-5 (owner) closed rv1-t0323 B1: the P-STORE-02 assertion's final `grep -qx` (refused by P-OPS-03, check-pipe-consumers) is now `grep -x ... >/dev/null`. Re-run: `bash ops/lib/check-pipe-consumers` -> "PIPE-CONSUMERS OK ... (186 scanned, 187 tracked, floor 42)" exit 0; check-pins-yaml "PINS-YAML ok pins=48 fields=387"; queue-check "QUEUE OK (317 tasks)". Only pins/PINS.yaml changed.
- 2026-10-08T17:13:58Z agent/rv2-t0323 (reviewer, round 2) PASS on head 6d24933d. "git diff 6d24933d~1 6d24933d -- pins/PINS.yaml" is the one replacement (grep -qx -> grep -x ... >/dev/null; otherwise only this Log changed). Bare in a detached worktree at origin/task/T-0323: check-pipe-consumers "PIPE-CONSUMERS OK: no gate decides with producer | grep -q (186 scanned, 187 tracked, floor 42)" exit 0; check-pins-yaml "PINS-YAML ok pins=48 fields=387" exit 0; check-account-token-sites "ok - 2 sites, every one approved, in 1 file(s)" exit 0; queue-check "QUEUE OK (317 tasks)" exit 0. The P-STORE-02 assertion string from yaml.safe_load, run with bash after npm ci (exit 0): exit 0 (the first attempt hit a Windows swift index-store "permission denied" during the build and exited 1, so the runner refused it; the re-run on the same scratch path was green). Seen red: a scratch copy expecting "NAMED P-STORE-02 passed=66/67" exits 1 and prints the runner line "NAMED P-STORE-02 passed=67/67". CI: gh pr checks 210 shows core pass and pins-source-only pass, run 37812989636 headSha 6d24933d success. "git merge-base --is-ancestor origin/main origin/task/T-0323" exit 0 (main 487cae1f), no drift. rv1-t0323 recordables R1-R5 remain open; none is blocking.
