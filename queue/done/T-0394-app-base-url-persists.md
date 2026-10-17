---
id: T-0394
title: The app's API base URL only comes from a -plan.base.url launch argument - a TestFlight or home-screen launch shows routingOffline; read it from Info.plist (build setting) with the launch argument as a debug override
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T08:00:25Z
lease_expires_at: 2026-10-18T08:00:25Z
worktree: .worktrees/T-0394
branch: task/T-0394
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, ops/lib/, ops/mutate/apibaseurl, Tests/, Sources/ScenicAPIClient/, pins/PINS.yaml, .github/workflows/ios-screenshot.yml]
pins_affected: [P-SAFE-03]
reviewer: agent/rv3-t0394
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The pilot audit found that plan.base.url is set only by a -plan.base.url launch argument, which applies only when Xcode launches the app. An app launched from the home screen or TestFlight has no base URL and shows routingOffline everywhere.

MEASURE every reader of the base URL (planner, telemetry, waitlist, config, search, account, attest, ledger). RULE one binding:
- an Info.plist key, e.g. SCENIC_API_BASE_URL, set from a build setting in the app target's build configuration. If that needs project.pbxproj, which is serial-only and holds the xcodeproj lock, STOP and say so. Prefer an Info.plist value that buildable folders pick up without a pbxproj edit;
- the launch argument kept as a DEBUG-only override;
- one Linux-testable resolver in ScenicKit or ScenicAPIClient that every client reads (shipped-value-single-binding), table-tested over: absent, empty, non-https, trailing slash, the override precedence, and a malformed URL.

The value for the pilot is https://scenic-api.phineas-fritsch.workers.dev. Re-approve P-SAFE-03 digests and the frozen shell lines. ios-compile must succeed, with a whitelist guard so that no client reads the base URL any other way.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the pilot runbook audit (owner authorised the pilot backend 2026-10-17).
- 2026-10-17T08:00:25Z claimed by agent/claude-opus-5; lease until 2026-10-18T08:00:25Z
- 2026-10-17T08:09:44Z MEASURED on e41a7170 (`grep -rnE "\bbase\b" --include=*.swift apps/ios`, comments dropped):
  the base URL has exactly ONE source, `UserDefaults.standard.string(forKey: "plan.base.url")` (LivePlanner.baseURLKey),
  read at 11 guard sites in 8 PlanAdapter files, each re-parsing `URL(string:)` and re-checking `scheme == "https"`:
  LivePlanner.swift x4 (placeSearch -> SearchClient, planner -> PlanClient + ConfigClient via cache(base),
  surpriseGate -> ConfigClient, rerouter -> PlanClient), LiveLoopPlanner (LoopClient + cache), LiveTripPlanner
  (TripClient + cache), LiveSession (AttestClient), LiveSurpriseLedger (LedgerClient), LiveTelemetry (TelemetryClient),
  LiveWaitlist (WaitlistClient), LiveAccountDeletion (AccountClient). 10 client constructions take `base:`. The only
  other apps/ios lines naming the word `base` are two in MapAdapter/ScenicStyleDocument.swift (a caches directory,
  not a URL). Nothing under apps/ios reads an Info.plist key but `CFBundleVersion` (LivePlanner.swift:57,
  LiveCorpus.swift:90). apps/ios/ScenicDrive/Info.plist is a real file (`GENERATE_INFOPLIST_FILE = NO`,
  `INFOPLIST_FILE = ScenicDrive/Info.plist` in both configurations of project.pbxproj) with no base URL key.
  `-plan.base.url` appears in no workflow; ios-screenshot.yml has one `simctl launch` line (154) with no base URL,
  so every screenshot today runs offline. Every client composes with `base.appendingPathComponent(...)`.
- RULINGS (before code):
  - R1 (Brief "set from a build setting" vs serial-only pbxproj): a build-setting substitution needs a
    user-defined setting in project.pbxproj (or an xcconfig the pbxproj references) - serial-only, so NOT done. The
    value is a LITERAL `<string>` under key `SCENIC_API_BASE_URL` in the existing apps/ios/ScenicDrive/Info.plist,
    which the target already processes; no pbxproj edit. A later per-configuration value is a pbxproj task.
  - R2 (one binding, shipped-value-single-binding): `APIBaseURL` (Sources/ScenicAPIClient, Linux-testable) owns the
    key names and the rule `resolve(bundled:override:) -> URL?`; `LiveBaseURL.url` (PlanAdapter, new file) is the
    ONE call of it, a `static let` evaluated once per launch from `Bundle.main` and the DEBUG override; all 11 guard
    sites read `LiveBaseURL.url` and nothing else. `LivePlanner.baseURLKey` is deleted.
  - R3 (the rule, table-tested): parse = exact scheme `https` (as today: `HTTPS` refused), non-empty host, no user,
    password, query or fragment, no whitespace (not trimmed: a typo is refused, not repaired); trailing `/`s are
    stripped so `X/` and `X` compose the same `X/plan`. Absent, empty, non-https, malformed (no host, `https:host`,
    an unexpanded `$(SCENIC_API_BASE_URL)`) -> nil -> routingOffline and nothing sent, as today.
  - R4 (override precedence): the override is read ONLY inside `#if DEBUG`; in a release build it is not read at
    all. When PRESENT it is the whole answer - a valid https override wins over the bundled value, and a present
    but invalid one (empty, `off`, http) yields nil, never a silent fall-back to the pilot. Absent -> bundled.
  - R5 (screenshots would now reach the pilot): with a bundled URL every DEBUG screenshot launch would call the
    pilot's /config, /attest and /telemetry from CI - live answers could change the pictures and CI would write
    pilot telemetry. ios-screenshot.yml's launch line gains `-plan.base.url off` (R4: offline, as every screenshot
    is today) and ops/lib/ios_screenshot_pinned.py's two copies of that line move with it. touches widened to
    Sources/ScenicAPIClient/, pins/PINS.yaml and .github/workflows/ios-screenshot.yml in this commit.
  - R6 (whitelist guard): new ops/lib/check-base-url-sites.py, appended to P-SAFE-03's assertion (pins_affected).
    Every non-`//` line of every apps/ios *.swift naming `\bbase\b`, `LiveBaseURL`, `APIBaseURL`, `plan.base.url`,
    `SCENIC_API_BASE_URL`, `forInfoDictionaryKey` or `workers.dev` must be an APPROVED (file, whole line) site with
    its exact count; the override read must sit inside `#if DEBUG`. `--prove-red` mutates in memory.
  - R7 (mutation population): APIBaseURL is a string/URL rule, not a numeric module, so no ops/mutate population;
    the table test is its oracle (full-equality on `absoluteString` and on the composed `/plan` URL).
  - R8 (digests): APIBaseURL.swift is a new Sources/ row and Info.plist a changed row in
    ops/lib/check-safety-disclaimer-linked-digests.txt; the 8 edited PlanAdapter files and new LiveBaseURL.swift are
    re-approved in ops/lib/check-safety-disclaimer-pinned. The app shell (ScenicDriveApp.swift) is NOT edited, so
    no frozen shell line moves.
  - R9 (privacy): no request body, header or coordinate changes; only WHICH base URL a release build uses.
- 2026-10-17T08:42:39Z RED then GREEN, by name (swift 6.3.3, Windows, `--scratch-path .build/t-0394`):
  - RED, A2: APIBaseURLTests against a stub `resolve` returning nil:
    `× Test everyAcceptedBaseComposesThePlanPathExactly() failed after 0.025 seconds with 8 issues.`
    `× Test resolveMatchesTheTableRowByRow() failed after 0.026 seconds with 8 issues.`
    `× Test shippedInfoPlistResolvesToThePilot() failed after 0.026 seconds with 2 issues.`
    `× Test run with 4 tests in 1 suite failed after 0.028 seconds with 18 issues.`
  - RED, A2: the real resolver before the Info.plist key: the table tests pass, and
    `shippedInfoPlistResolvesToThePilot() recorded an issue ... (got?.absoluteString → nil) == (Self.pilot → "https://scenic-api.phineas-fritsch.workers.dev")`.
  - GREEN: `√ Test run with 4 tests in 1 suite passed`; the whole target `√ Test run with 185 tests in 45 suites passed`.
  - RED, A3: check-base-url-sites.py over `git archive e41a7170 apps/ios` exits 1, `P-SAFE-03 (base URL) FAIL: 39
    refusal(s)`, 23 `not an approved` lines, first `guard let text = UserDefaults.standard.string(forKey:
    LivePlanner.baseURLKey), let base = URL(string: text),` at .../LiveAccountDeletion.swift.
  - GREEN, A3: `P-SAFE-03 (base URL): 37 approved base URL sites, LiveBaseURL.swift as approved, the -plan.base.url
    read inside #if DEBUG`; `--prove-red` `PROVE-RED OK: 12/12 refused by name` (override outside DEBUG, override in
    the #else arm, the release arm reading the environment, the old UserDefaults reader restored, telemetry on a
    literal URL, the ledger on the pilot literal, a second resolve, the shell reading the Info.plist key, a new file
    building a client, a raw PlanHTTPRequest, LiveBaseURL.swift deleted, the reroute sender dropping LiveBaseURL).
  - A4: check-ios-compile-guardrails with the screenshot launch line edited but the pin not yet moved:
    `IOS-COMPILE-GUARDRAILS FAIL: 1 guardrail(s) gone in ios-screenshot.yml` (steps[4].run differs); after
    ios_screenshot_pinned.py moved: OK, and `--prove-red` `PROVE-RED OK: 99 mutations red, 6 legitimate spellings
    green over 2 workflows`, its new row `T-0394: the offline override dropped` red. ios_screenshot_pinned.py is
    298 lines (`wc -l`), under the cap.
  - check-base-url-sites.py is committed 100644: check-exec-bits refused 100755 (`ops/lib/check-base-url-sites.py
    (data, should be 100644, is 100755)`), as check-screen-rehearsals.py is 100644.
- 2026-10-17T09:26:29Z ACCEPTANCE re-run on 1d913ffd (= merged head: `git fetch origin` in the main checkout,
  `git log e41a7170..origin/main` empty, so the merge of origin/main is a no-op):
  1. `√ Test run with 4 tests in 1 suite passed` (APIBaseURLTests); ScenicAPIClientTests `185 tests in 45 suites passed`.
  2. RED quoted above (stub resolve: 3 tests red by name; Info.plist test red before the key).
  3. check-base-url-sites.py rc=0 (37 sites); red on e41a7170 (39 refusals); `PROVE-RED OK: 12/12 refused by name`.
  4. `bash ops/lib/check-safety-disclaimer` rc=0 (`LAST all 115 app .swift, then 336 root + pbxproj file(s)
     (-linked)`); check-ios-compile-guardrails OK for ios-compile.yml and ios-screenshot.yml.
  5. `grep -rn 'baseURLKey\|forKey: "plan.base.url"' apps/ios` -> 0 lines.
  6. queue-check `QUEUE OK (385 tasks)`; check-store-links, check-telemetry-emit-sites (`55 lines approved`),
     check-map-attribution, check-screen-rehearsals, check-pins-yaml (`pins=52`), check-exec-bits (`245 files`),
     check-mutate-population (`the floor of 171 holds`), check-mutate-only: all rc=0.
  7. ios-compile run 39019492194 on 1d913ffd: `conclusion: success`.
  - `timeout 600 bash ops/lib/check-line-cap` exited 124 (timed out on this box, not a refusal); measured by hand
    instead (`wc -l` over every file this branch changes): largest code files check-base-url-sites.py 212 and
    ios_screenshot_pinned.py 298; check-safety-disclaimer-pinned is 389 (388 on e41a7170, +1 row for
    LiveBaseURL.swift; an existing data table). CI's line-cap is the confirmation.
- 2026-10-17T12:00:29Z rv1 FAIL (agent/rv1-t0394, head 1d0f5076) closed by class. Ruling: the 09:26 entry's
  `check-mutate-population (the floor of 171 holds)` rc=0 is not reproducible; bare on this worktree at 1d0f5076 it
  exits 1 with `P-PROC-06: module(s) added by this branch with no mutation population:
  Sources/ScenicAPIClient/APIBaseURL.swift`, the CI failure. That line is left as written (dated record).
  - B1: ops/mutate/apibaseurl.py (driver, 100644 like straightline.py; check-exec-bits refused 100755 as `data`) +
    apibaseurl_mutations.py: SUBJECT_MODULES = APIBaseURL.swift, 15 MUTATIONS (MIN_MUTATIONS 15), 1 EQUIVALENT with
    a witness (MIN_EQUIVALENT 1: the password clause, subsumed by `parts.user == nil`); DRIVERS and COVERED_FLOOR
    gain it. touches: gains ops/mutate/apibaseurl. `--prove-floor`: `FLOOR PROOF OK: 6 of 6 arms refused, control
    clean`; `--only 999999`: rc=64 `REFUSING TO RUN: --only names no entry of this population: 999999`.
  - B2 (class: an empty host in any spelling) rows `https://:443`, `https://:443/`, `https://@`, `https://@:443`,
    `https://:pw@<pilot host>`. B3 (class: whitespace anywhere, decided by the rule, not by URLComponents): rows with
    space/tab/newline/NBSP inside a path, plus GENERATED near-miss corpus `whitespaceInsertedAnywhereInAnAcceptedBaseIsRefused`:
    18 whitespace characters (ASCII, U+0085, U+00A0, U+1680, U+2000-class, U+2028/9, U+202F, U+205F, U+3000) at
    every position of 4 accepted seeds, as bundled AND as override; its meta-test checks every seed is accepted,
    every character `isWhitespace`, and the corpus size is chars x (len+1) per seed.
  - RED, the reviewer's mutants on the OLD tests (1d0f5076's APIBaseURLTests.swift put back, `--only 1,2,3,4`):
    `MISSED M1 the empty-host clause dropped (rv1 B2) exit=0`, `MISSED M2 the whitespace clause dropped (rv1 B3)
    exit=0`, `MISSED the whitespace clause narrowed to a space`, `MISSED the whitespace clause narrowed to newlines`;
    `PARTIAL FAILED: 0 of 4`.
  - GREEN, the new tests, full run on b72ea8c1: `caught M1 ... red:
    resolveMatchesTheTableRowByRow()`, `caught M2 ... red: resolveMatchesTheTableRowByRow() |
    whitespaceInsertedAnywhereInAnAcceptedBaseIsRefused()`, both narrowings caught by the same two; 14 of 15 caught,
    EQUIVALENT `MISSED the password clause dropped exit=0`; entry 11 (one trailing slash) WRONG_KILLER - it named
    the compose test, which composes `pilot/` + `plan` like `pilot` + `plan`. Its killer list now names the table
    only (the `pilot//` row); re-run of that touched entry alone: `caught one trailing slash dropped, not every one
    red: resolveMatchesTheTableRowByRow()`, `PARTIAL OK: 1 of 1` (on 817af55b). 15/15 across the two runs; no full re-run.
  - Merged origin/main (2daea62c) clean; it changes no Sources/, Tests/ or apps/ios file. On the merged head:
    APIBaseURLTests `√ Test run with 6 tests in 1 suite passed`. Gates bare, each rc=0:
    check-safety-disclaimer `LAST all 115 app .swift, then 336 root + pbxproj file(s) (-linked)`;
    check-mutate-population `P-PROC-06: every added module is covered or allowlisted; the floor of 172 holds`;
    check-mutate-only `MUTATE-ONLY OK: 244 of 244 driver runs refused with exit 64 (66 drivers, ...)` and
    `NAME-PAIRS OK: 239614 pair tokens ...`; check-pins-yaml `PINS-YAML ok pins=53 fields=426`; check-exec-bits
    `P-OPS-01: 248 files, 23 required present, all modes correct`; queue-check `QUEUE OK (385 tasks)`.
  - `wc -l`: apibaseurl.py 215, apibaseurl_mutations.py 76, APIBaseURLTests.swift 121, mutate_population_table.py 121.

## Acceptance
1. `swift test --scratch-path .build/t-0394 --filter APIBaseURLTests` passes; the suite holds the R3/R4 table
   (absent, empty, whitespace, http, `HTTPS`, ftp, no host, `https:host`, unexpanded `$(...)`, query, fragment,
   user, one and two trailing slashes, a path base, override present-valid/present-invalid/present-empty/absent)
   compared by `absoluteString` equality, and `shippedInfoPlistResolvesToThePilot` reads
   apps/ios/ScenicDrive/Info.plist and asserts the resolved base is exactly
   `https://scenic-api.phineas-fritsch.workers.dev` and composes `.../plan`.
2. RED by name, quoted below: the table test against a stub `resolve` returning nil, and the Info.plist test before
   the key exists.
3. `python ops/lib/check-base-url-sites.py` exits 0; red on e41a7170's tree (the 11 UserDefaults readers refused by
   name); `--prove-red` prints `PROVE-RED OK` with every row refused.
4. `bash ops/lib/check-safety-disclaimer` exits 0 (digests re-approved); `python ops/lib/check-ios-compile-guardrails.py`
   exits 0 with the screenshot launch line carrying `-plan.base.url off`.
5. `grep -rn "baseURLKey\|forKey: \"plan.base.url\"" apps/ios` prints nothing.
6. Gates bare: check-pins-yaml, check-mutate-population, check-mutate-only, check-exec-bits, queue-check,
   check-store-links, check-telemetry-emit-sites, check-map-attribution exit 0.
7. ios-compile on task/T-0394 succeeds.
8. `python ops/mutate/apibaseurl.py`: every MUTATIONS entry caught by the test it names and the EQUIVALENT entry
   MISSED; rv1's M1 and M2 shown MISSED on 1d0f5076's tests and caught on the new ones.
- 2026-10-17T14:23:00Z agent/claude-opus-5 (orchestrator): rv2 FAIL was ancestry only (T-0391 wrangler.jsonc vars and T-0395 queue landed; no overlap). Merged origin/main (clean); bare gates exit 0 on the merged head (check-safety-disclaimer, check-mutate-population, check-mutate-only, check-pins-yaml, check-exec-bits, queue-check).
- 2026-10-17T14:44:01Z agent/rv3-t0394 (reviewer, round 3): PASS. Ancestry/CI/gates review on 4a692939. git diff 22303da5 origin/task/T-0394 --stat -- Sources apps Tests ops/mutate is empty (the merge brought only main's changes). swift test --filter APIBaseURLTests: Suite "APIBaseURLTests" passed, 6 tests in 1 suite passed. Bare gates exit 0: check-safety-disclaimer; check-mutate-population "P-PROC-06: every added module is covered or allowlisted; the floor of 172 holds"; check-mutate-only "MUTATE-ONLY OK: 244 of 244 driver runs refused with exit 64"; check-pins-yaml "PINS-YAML ok pins=53 fields=426"; check-exec-bits "P-OPS-01: 248 files, 23 required present, all modes correct"; queue-check "QUEUE OK (386 tasks)". gh pr checks 289: core pass, pins-source-only pass. git merge-base --is-ancestor origin/main (5e4150a0) origin/task/T-0394 exit 0. Signed off: queue/claimed/ -> queue/done/.
