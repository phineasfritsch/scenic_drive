---
id: T-0394
title: The app's API base URL only comes from a -plan.base.url launch argument - a TestFlight or home-screen launch shows routingOffline; read it from Info.plist (build setting) with the launch argument as a debug override
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T08:00:25Z
lease_expires_at: 2026-10-18T08:00:25Z
worktree: .worktrees/T-0394
branch: task/T-0394
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, ops/lib/, Tests/, Sources/ScenicAPIClient/, pins/PINS.yaml, .github/workflows/ios-screenshot.yml]
pins_affected: [P-SAFE-03]
reviewer: null
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
