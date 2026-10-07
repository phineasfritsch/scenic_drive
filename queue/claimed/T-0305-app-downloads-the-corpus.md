---
id: T-0305
title: The app downloads and activates the places corpus - a URLSession CorpusFetcher, a first-run download sheet (resumable, Wi-Fi-only by default, progress), and openForLaunch on every cold launch, with the bundled fallback until a download lands
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T19:10:12Z
lease_expires_at: 2026-10-08T15:10:12Z
worktree: .worktrees/T-0305
branch: task/T-0305
exclusive: [package-swift]
touches: [Package.swift, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Sources/PlaceStore/, Tests/PlaceStoreTests/, apps/ios/Packages/ScenicApp/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PROD-05, P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0300, T-0294, T-0303]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: where the manifest URL comes from (the same UserDefaults/config seam T-0294 R7 uses for the plan base URL; absent -> no download, the bundled fallback corpus stays - T-0270), which target owns URLSession (ScenicAPIClient beside URLSessionPlanTransport, Linux-buildable via FoundationNetworking), how the shell wires it without a feature target importing ScenicAPIClient (CLAUDE.md), and the Wi-Fi-only default + Settings toggle"
  - "URLSessionCorpusFetcher conforms to T-0300's CorpusFetcher; tested on Linux with a URLProtocol stub: a 200 body is streamed to the staging path exactly; a non-200, a short body and a dropped connection each throw a typed error and leave no staging file; resume uses a Range request when a partial staging file exists (table over 0 bytes / partial / complete-but-unverified)"
  - "The shell calls CorpusUpdater.openForLaunch(isColdLaunch: true) before the first PlaceStore open, and the home's searches read the activated corpus when one exists, else the bundled fallback - a ScenicKit/PlaceStore-level test over {no download, pending, activated, rejected} chooses the right file by full equality"
  - "The download sheet shows progress, never blocks Surprise Me on the fallback corpus, keeps AttributionFooter visible on every map surface (P-ATTR-01: any new sheet is full-height or gets a typed whole-line approval in check-map-attribution-sheet, never a widened pattern), and ios-compile + ios-screenshot pass on the head"
  - "Every new or changed Sources/ and non-Swift apps/ios file re-approves its row in ops/lib/check-safety-disclaimer-linked-digests.txt (memory sources-digest-pin); a mutation population for the fetcher's error/resume logic with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Runtime lifecycles, First run + Corpus OTA: "download sheet: Bay Area PMTiles + corpus, resumable, progress; bundled
tiny fallback corpus so the app is never empty; Wi-Fi-only default with a Settings toggle". T-0300 shipped the decision/
verify/activate core (PlaceStore CorpusUpdater, CorpusFetcher protocol); this task is the app half for the CORPUS only.
PMTiles download is a later task. The R2 manifest is not published yet (owner deploy), so tests use stubs.

## Log
- 2026-10-07T19:09:58Z filed by agent/claude-opus-5 (orchestrator) from T-0300 O11 and the milestone gap map (M4).
- 2026-10-07T19:10:12Z claimed by agent/claude-opus-5; lease until 2026-10-08T15:10:12Z
- 2026-10-07T19:14:04Z MEASURED, then RULINGS before any test (agent/claude-opus-5, owner). Read: CLAUDE.md, queue/done/T-0300
  (O1 the manifest's five keys and nothing else, O4 slots, O5 CorpusFetcher, O7 openForLaunch, O11), T-0294 (R1 PlanAdapter
  the only apps/ios importer of ScenicAPIClient, R7 `plan.base.url`, the rv1 B1 full-height ruling), T-0290, T-0303, both
  Package.swift files, ScenicDriveApp.swift, SurpriseDeck.swift and PlanPlaceSearch.swift (each opens `corpus-fallback`
  from Bundle.main in a static lazy), ops/lib/check-safety-disclaimer-{pinned,doors,linked-digests.txt},
  ops/lib/check-map-attribution-sheet, ops/mutate/corpusota*.py. MEASURED: the manifest carries no URL (O1); stage()
  deletes the staging file BEFORE every fetch, so a resume cannot live in the staging file; the shell imports no root
  module; PINNED_APP_SWIFT pins every apps/ios .swift by digest, PINNED_SURPRISE pins SurpriseDeck.swift a second time,
  PINNED_SHELL_DIGEST pins the shell, DOORS_PACKAGE pins the app manifest's name/path/product lines, and every `.sheet(`
  in the app tree is a whole-line approval in check-map-attribution-sheet (today Settings' and the plan sheet's).
  - R1 MANIFEST URL. UserDefaults `corpus.manifest.url` (a `-corpus.manifest.url https://...` launch argument sets it),
    the same seam as T-0294 R7's `plan.base.url`. Absent or not https: no request is ever made, no sheet is shown, and
    the bundled fallback stays the corpus (T-0270). The CORPUS file's URL is not in the manifest (O1 froze five keys),
    so it is RULED here: the manifest's sibling `corpus-<version>.sqlite` (`URLSessionCorpusFetcher.corpusURL(for:)`).
    The owner's R2 publish must lay files out that way - recorded as STILL OPEN, not assumed published.
  - R2 URLSESSION OWNER. ScenicAPIClient, beside URLSessionPlanTransport; FoundationNetworking behind `canImport`, so it
    builds and its tests run on Linux and this box. Root Package.swift (lock held): ScenicAPIClient and its test target
    gain the PlaceStore dependency (CorpusFetcher, CorpusManifest). No path line changes (ROOT_PATH_LINES untouched).
  - R3 FETCHER. `URLSessionCorpusFetcher` conforms to CorpusFetcher and streams through a URLSessionDataDelegate into a
    RESUME file `<staging dir>/corpus-<sha256>.part` (keyed by the manifest's hash, so one corpus never resumes into
    another's bytes; stage() removes only the staging file, so the part survives a failed attempt). Only when exactly
    `manifest.bytes` have arrived is the part renamed to `destination`. Resume table: no part or 0 bytes - no Range
    header, 200 expected; partial n (0 < n < bytes) - `Range: bytes=n-`, a 206 appends, a 200 (Range ignored) rewrites
    from byte 0; complete-but-unverified (n == bytes) - NO request, renamed, and stage()'s verify decides; n > bytes -
    deleted, fresh. Typed `CorpusFetchError`: `.status(Int)` for any other status (part deleted: the server's state is
    unknown), `.shortBody(received:expected:)` (part KEPT: that is a resumable drop), `.longBody(expected:)` (part
    deleted), `.transport(code:)` a dropped connection (part KEPT). None of them leaves a `destination` (staging) file.
    Progress is a `@Sendable (Int, Int) -> Void` of (bytes on disk, manifest.bytes).
  - R4 WIRING WITHOUT A FEATURE IMPORTING ScenicAPIClient. The shell imports no root module and features may not import
    ScenicAPIClient, so the live side is PlanAdapter (already the ONLY apps/ios importer of ScenicAPIClient; a second
    adapter would widen T-0294 R1's whitelist): it gains PlaceStore and `LiveCorpus` (Application Support directory,
    the GRDB-validating `CorpusUpdater(directory:drives:)`, manifest fetch, `CorpusUpdater.decide`, `stage`). PlaceStore
    gains `LaunchCorpus` (+ the value `CorpusLaunch`): `LaunchCorpus.open(updater:fallback:)` runs
    `openForLaunch(isColdLaunch: true)`, then chooses the active corpus when the file exists, else the fallback, and
    records the choice; SurpriseDeck and PlanPlaceSearch ask `LaunchCorpus.url(fallback:)` instead of the bundle alone.
    The shell's `init()` calls `LiveCorpus.launch()` - before any body, so before either feature's static store opens.
  - R5 SHEET. `CorpusDownloadSheet` lives in Entitlements (DesignSystem only; plain values and closures, no PlaceStore -
    it sits beside Settings, whose toggle it shares). The shell presents it FULL HEIGHT (no presentationDetents, the
    T-0294 rv1 B1 ruling) through ONE new approved whole line `.sheet(isPresented: $isShowingCorpusDownload) {` in
    check-map-attribution-sheet, beside Settings' and the plan's - a typed approval, never a widened pattern. It is shown
    on launch only when a manifest URL is configured and no downloaded corpus is active; it shows progress; "Not now"
    closes it and the download carries on - Surprise Me and search keep reading the fallback, nothing waits on it; the
    new corpus is used from the next cold launch (O7), and the sheet says so.
  - R6 WI-FI ONLY. UserDefaults `corpus.wifi.only`, absent = true; a Settings toggle on the same key (@AppStorage).
    `URLSessionCorpusFetcher.configuration(wifiOnly:)` sets `allowsCellularAccess = !wifiOnly`; tested on Linux.
  - R7 TESTS. URLSessionCorpusFetcherTests over a scripted StubCorpusURLProtocol (response, data chunks, a failure,
    finish), every request and the whole directory compared by full equality. CorpusLaunchTests (PlaceStoreTests,
    Foundation only): the cross product active {absent, present} x pending {none, good, bad} x fallback {nil, URL},
    12 rows, each row's expected `CorpusLaunch` computed from the row and compared by full equality with what
    `LaunchCorpus.open` returns AND what `LaunchCorpus.url(fallback:)` answers after it. The acceptance's four states:
    no download (absent, none), pending (good), activated (present, none), rejected (bad).
  - R8 POPULATION. ops/mutate/corpusfetch.py (+ _mutations, _run) over URLSessionCorpusFetcher.swift,
    CorpusDownloadDelegate.swift and LaunchCorpus.swift with a literal floor; DRIVERS and COVERED_FLOOR gain it; the
    declaration-only CorpusFetchError and CorpusLaunch go to the allowlist with one reason each.
  - R9 PINS. apps/ios digests are in check-safety-disclaimer-pinned (PINNED_APP_SWIFT, PINNED_SURPRISE,
    PINNED_SHELL_DIGEST) and its app-manifest lines in -doors DOORS_PACKAGE; Sources/ rows in
    check-safety-disclaimer-linked-digests.txt. Every one is re-typed in the commit that changes its file.
  - R10 TOUCHES. The root Package.swift was missing from `touches:` although `exclusive: [package-swift]` holds its
    lock and R2 edits it; added (the pre-commit hook refused the red commit for it).
- 2026-10-07T19:29:44Z RED FIRST by name (agent/claude-opus-5), native swift 6.3.3, `swift test --scratch-path
  .build/t0305 --filter "URLSessionCorpusFetcherTests|CorpusLaunchTests"` against a fetcher whose `fetch` and
  `fetchManifest` throw `.status(0)` and a `LaunchCorpus.open` that never chooses the active slot:
  `Test run with 6 tests in 2 suites failed after 0.639 seconds with 57 issues` -
  `fetchTableOverEveryResumeFileAndServer() failed ... with 35 issues` (every one of the 35 rows),
  `launchChoosesTheActivatedCorpusElseTheFallback() failed ... with 16 issues` (the 8 rows with a corpus active
  after launch, launch and url(fallback:) each), `manifestFetchReturnsTheBodyOrATypedError() failed ... with 6
  issues`; the two meta-tests and `wifiOnlyRefusesCellularAndTheNamesAreRuled()` passed (no fetcher body involved).
- 2026-10-07T20:20:10Z GREEN, POPULATION, GUARDS RED THEN GREEN, iOS CI (agent/claude-opus-5). The GREEN lines below
  were measured at 19:31:23Z/19:36:18Z on 879e2d05 (the logs' mtimes; this session lost their Log entry and records
  them now, quoting the saved logs, not memory). origin/main (2ef434f4, T-0299 queue files only) merged as d15a878b
  before the population ran; the three subjects are byte-identical between 879e2d05, 8ae23e3c and d15a878b.
  - GREEN on 879e2d05: `--filter "URLSessionCorpusFetcherTests|CorpusLaunchTests"`: `Test run with 6 tests in 2
    suites passed after 0.430 seconds`; `--filter "ScenicAPIClientTests|PlaceStoreTests"`: `Test run with 46 tests
    in 11 suites passed after 3.103 seconds`.
  - VACUITY on d15a878b (ended 20:06:20Z): `python ops/mutate/corpusfetch.py --only 1,13,18 --prove-vacuity`:
    `MISSED 1 the Range header asks one byte late exit=0 no test objected`, `MISSED 13 a 206 is accepted when no
    Range was sent ...`, `MISSED 18 the active slot is chosen without existing ...`, `VACUITY PROOF OK: with the 2
    test file(s) emptied, caught=0 (need 0) and MISSED=3 of 3`, rc=0.
  - FULL RUN on d15a878b (ended 20:11:23Z): `python ops/mutate/corpusfetch.py`: `population mutations=21 (floor 21)
    equivalent=1 (floor 1) subjects=URLSessionCorpusFetcher.swift, CorpusDownloadDelegate.swift, LaunchCorpus.swift
    test files=2`; the same three CAUGHT BY NAME: `caught 1 the Range header asks one byte late by:
    fetchTableOverEveryResumeFileAndServer()`, `caught 13 a 206 is accepted when no Range was sent by:
    fetchTableOverEveryResumeFileAndServer()`, `caught 18 the active slot is chosen without existing by:
    launchChoosesTheActivatedCorpusElseTheFallback()`; `caught by the test that names it: 21 of 21 (wrong killer 0,
    trapped 0, compile-only 0, MISSED 0, skipped 0)`, E1 `MISSED ... no test objected` as required, `MUTATE OK
    caught=21/21 equivalent_caught=0`, rc=0. `--prove-floor`: `FLOOR PROOF OK: 7 of 7 arms refused and the control
    did not`, rc=0.
  - P-ATTR-01 SHEET APPROVAL, red then green (bare `bash ops/lib/check-map-attribution`, restored by git checkout):
    the approved whole line altered to `$isShowingCorpusDownloadX` - rc=1, `the approved line
    \`.sheet(isPresented: $isShowingCorpusDownloadX) {\` occurs 0 time(s) in
    apps/ios/ScenicDrive/ScenicDriveApp.swift, expected 1`; the shell's corpus sheet given
    `.presentationDetents([.medium])` - rc=1, `presentationDetents at ScenicDrive/ScenicDriveApp.swift(1), tracked
    nowhere`; restored - rc=0.
  - iOS CI on the merged head d15a878b: ios-compile run 37678975779 `completed success` (2m46s), ios-screenshot run
    37678980449 `completed success` (13m35s). (Also green on 879e2d05: 37676066334, 37676071207.)
  - STILL OPEN (not an acceptance line; recorded, not fixed): after `.ready` the sheet's Download button is enabled
    again, and a second tap re-downloads the same corpus into the pending slot (decide still sees the old active
    version until the next cold launch). Harmless to correctness (stage verifies), wasteful on data. The R1 R2 layout
    (`corpus-<version>.sqlite` beside the manifest) is the owner's publish, not yet live.
