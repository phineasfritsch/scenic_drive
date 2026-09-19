---
id: T-0197
title: pins - P-ATTR-01 (the Protomaps attribution visible on every map surface at every detent) and P-DATA-03 (PMTiles/corpus meta.region == the active region; built_at under 30 days) entered in pins/PINS.yaml with runs_on and assertions that run
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T12:02:22Z
lease_expires_at: 2026-09-19T18:02:22Z
worktree: .worktrees/T-0197
branch: task/T-0197
exclusive: []
touches: [pins/PINS.yaml, services/tiles/, ops/lib/, apps/ios/Packages/ScenicApp/Sources/MapAdapter/]
pins_affected: [P-ATTR-01, P-DATA-03]
reviewer: null
depends_on: [T-0165, T-0195, T-0178]
verify: [ops/test, ops/check-pins]
acceptance:
  - "P-DATA-03 (runs_on: [linux]) asserts through services/tiles/check_pmtiles.py over the built artifact that meta.region equals the active region and built_at is under 30 days - seen red on a stale built_at fixture first; the corpus half names the corpus manifest field it reads or is recorded as pending with the task that owns it"
  - "P-ATTR-01 (runs_on: [mac]) names the XCUITest identifier and the snapshot it will assert over once T-0180's XCUITest half exists; until then its assertion is the structural check that MapStyle's attributionText for the protomaps case is the plan's string and that AttributionFooter is not accessibilityHidden (a grep-free anchor on identifiers), demonstrated red first"
  - "P-ATTR-01's structural half is ARM-anchored, not count-anchored (T-0195's mutant pass: swapping the two credit arms leaves every count unchanged): the line after 'case .protomapsLALight, .protomapsLADark:' in MapStyle.swift returns MapStyle.protomapsAttribution and the demo arm returns demoAttribution - RED first with the arms swapped on a copy, then green; T-0178 ships the mount (the style FOLLOWS THE SELECTED DRIVE: the LA archive covers -119.0,33.7,-117.85,34.45 only and the Skyline map is centred on San Francisco, so the LA drive resolves BasemapResolver.losAngeles() and the Skyline drive keeps the demo case; caption and credit follow the RESOLVED style) and this task asserts it as a WHITELIST in ops/lib: every occurrence of protomapsLA outside Sources/MapAdapter/ fails, and BasemapResolver.losAngeles( occurs in FeatureScenicHome - red on a copy that names MapStyle.protomapsLALight at the mount, then green; never anchored on the credit string, which is right even over a blank map"
  - "BasemapResolver.archiveURL tests WHOLENESS, not existence (rv1-pr112 RV-1): a byte floor from the built artifact's sidecar (63,520,949 bytes; the same floor T-0165's checker carries) before a protomaps case is returned, so an interrupted copy never buys the Protomaps credit over an unreadable archive; the atomic write in ScenicStyleDocument paired with an idempotent skip (RV-2); the drift test asserts the ARM (light -> ScenicLightStyle) not only the bytes (RV-3); the recorded fourth grep (AttributionFooter call sites) is NOT lifted verbatim - it hits a doc comment on MapStyle.swift today (RV-4) - the structural check anchors on the mount sites"
  - "services/tiles/tests asserts the raw literals in ScenicLightStyle.swift / ScenicDarkStyle.swift are byte-equal to styles/scenic-light.json / scenic-dark.json (extract between the literal delimiters; 4563 / 4591 bytes today) - red on one flipped hex digit, then green; the embedded shape is KEPT until M4's download sheet or the next time the app Package.swift is opened"
  - "bash ops/check-pins --source-only bare at the final commit; PINS.yaml ids unique"
---
## Brief

From T-0165's STILL OPEN 6 (PR #109): the plan's pin table carries P-ATTR-01 and P-DATA-03 and pins/PINS.yaml has
neither (grep -c -> 0). T-0165 built the artifact P-DATA-03 asserts over; T-0195 puts the Protomaps string on the
surface P-ATTR-01 asserts over.

## Log
- 2026-09-19T05:38:57Z filed by agent/claude-fable-5-1 from T-0165's STILL OPEN 6 (PR #109). Not started; after T-0195.
- 2026-09-19T07:53:50Z two bullets added by agent/claude-fable-5-1 from T-0195's mutant pass (PR #112): the recorded grep assertions are count-anchored and blind to the arms trading places; and BasemapResolver.losAngeles has no call site until the home screen mounts it - the credit exists but sits on no surface. Both land here, after #112 and T-0178 (which also edits the screen).
- 2026-09-19T08:08:53Z bullet added by agent/claude-fable-5-1 from rv1-pr112's PASS on PR #112 (recordables RV-1..RV-4; RV-5 keeps the raw-literal shape; RV-6 confirms apps/ios/ScenicDrive is a PBXFileSystemSynchronizedRootGroup so a file under Tiles/ is in the app target without a pbxproj edit).
- 2026-09-19T09:12:30Z AMENDED by agent/claude-fable-5-1 (02:13 panel, grounded 8 of 11): touches += MapAdapter/ (RV-1/RV-2 cannot be committed without it); the mount is T-0178's and is PER DRIVE, this task whitelists it; depends_on += T-0178 for the mount-site assertion ONLY - the P-DATA-03 half, the drift test, RV-1/RV-2 and the protomapsLA whitelist may start first; the style-identity test added; the embedded-style shape ruled KEEP until M4.
- 2026-09-19T12:02:19Z PROMOTED to ready/ by agent/claude-fable-5-1: #115 (T-0178) merged d949ee2 - the LA basemap is mounted per drive on main, so every dependency is done and the mount-site whitelist can be asserted.
- 2026-09-19T12:02:22Z claimed by agent/claude-opus-5; lease until 2026-09-19T18:02:22Z
- 2026-09-19T12:06:08Z RULINGS by agent/claude-opus-5 (the author rule), before a line of code:
  R0 DISAGREEMENT - acceptance bullet 3 ("every occurrence of protomapsLA outside Sources/MapAdapter/ fails")
  against the tree T-0178 shipped. That predicate is RED on main for a legitimate reason: FeatureScenicHome/
  DriveCopy.swift:75 carries `case .protomapsLALight, .protomapsLADark:` (2 occurrences with // stripped) -
  the caption switch that FOLLOWS THE RESOLVED STYLE - and FeatureScenicHome is outside this task's touches,
  so it cannot be edited to satisfy the bullet as written. RULED: the guard is the house-shape WHITELIST
  (CLAUDE.md; check-safety-disclaimer limb (v)) - a tracked set of typed per-file counts by OCCURRENCE over
  every *.swift under apps/ios, // stripped: MapStyle.swift(6) MapAppearance.swift(2) DriveCopy.swift(2),
  measured 2026-09-19T12:06:08Z - plus a second anchor a count alone cannot give: every protomapsLA
  occurrence OUTSIDE Sources/MapAdapter/ must sit on a `case .`-pattern line, never in an expression. A
  feature target that NAMES a case (`= MapStyle.protomapsLALight`) bypasses the resolver and is refused
  twice - by the count and by the pattern anchor; a feature target that MATCHES one is reading the answer
  the resolver returned, which is what DriveCopy does and what the mount is for.
  R1 P-DATA-03 (runs_on: [linux]) - the 63,520,949-byte artifact is never committed and does not exist in
  CI, so an assertion over it alone would be TODO wearing a command. The assertion is
  ops/lib/check-pmtiles-provenance.py: it runs the SHIPPING entry point - `python services/tiles/
  check_pmtiles.py <archive> --region-json services/etl/regions/la/region.json`, the command build-la.sh
  step 6 and ops/publish-tiles run - over fixtures written in-process by the tests' own writer
  (services/tiles/tests/test_pmtiles_budget.write_pmtiles / good_metadata), and requires: a fresh, region-la
  fixture ACCEPTED; a fixture stamped 40 days back REFUSED naming `older than 30 days (P-DATA-03)`; a
  fixture stamped region `bay` REFUSED naming `meta.region is 'bay'` - so the pin is red by name on both of
  its own limbs, never a table compared with itself. A fixture is BUILT, not committed: a committed archive
  carries a frozen built_at that goes stale in 30 days and would turn the age limb from an assertion into a
  calendar. When SCENIC_LA_PMTILES names a file the same CLI is run over the REAL artifact and must exit 0
  (set and absent = refusal, never a skip - test_check_pmtiles_cli.py's rule). The CORPUS half of P-DATA-03
  is PENDING: no corpus manifest with a region field exists yet. It is named in why_no_test_catches_it with
  its owner, T-0205 (the corpus manifest, queue/claimed/) - and NOT as the `pending:` KEY: ops/lib/pins.py
  lines 125-138 `continue` on a pending pin, so a `pending:` here would stop the tiles half from ever
  running. A debt recorded beside a LIVE assertion, not instead of one.
  R2 P-ATTR-01's structural half - ops/lib/check-map-attribution (bash, 100755, the check-safety-disclaimer
  shape: // stripped, occurrences with multiplicity, whitelists of tracked sites, refusals by name,
  fail-closed on an empty scan). Its mutation table is ops/lib/check-map-attribution-mutations, beside it
  rather than inside it, for the reason check-safety-disclaimer-mutations states in its own header (the
  300-line cap) - the check is still ONE script and --prove-red is still its entry point. Four anchors:
  (a) the ARM - inside `public var attributionText: String`, the first code line after
  `case .protomapsLALight, .protomapsLADark:` is exactly `return MapStyle.protomapsAttribution` and the
  first after `case .maplibreDemoTiles:` is exactly `return MapStyle.demoAttribution` (T-0195's mutant pass:
  swapping the arms moves no count); (b) the LITERAL - `protomapsAttribution = "© OpenStreetMap contributors
  · Protomaps"` verbatim, the plan's string, and that literal occurs in code exactly once over apps/ios, in
  MapStyle.swift (a whitelist, so a credit string typed at a call site is refused by name);
  (c) the protomapsLA whitelist of R0; (d) the MOUNT - `BasemapResolver.losAngeles(` occurs in code exactly
  once under apps/ios, in FeatureScenicHome/DriveBasemap.swift, and every `AttributionFooter(` construction
  is read by its ARGUMENT LIST (the button_args shape), which must pass `text:` a value ending in
  `.attributionText` and carrying no `"` - anchored on the CALL SITE, not on the recorded grep, which hits a
  doc comment (rv1-pr112 RV-4) and is not lifted. runs_on: [linux] for this half - it is source reading that
  needs no Apple toolchain, and CI's linux job is where it is evidence; claiming [mac] too would say the mac
  tier runs it when the only mac-tier half (the XCUITest) does not exist. That half - the footer VISIBLE at
  every sheet detent, in a simulator - is named in why_no_test_catches_it with its owner, T-0180
  (queue/backlog/), for the same pins.py reason as R1: a `pending:` key would stop this assertion running.
  R3 MapAdapter. archiveURL tests WHOLENESS: a byte floor before a protomaps case can be returned. RULED the
  1 MiB floor check_pmtiles.py already carries (MIN_BYTES = 1_048_576), NOT the sidecar's 63,520,949: that
  checker's own words - "a floor set near the real size refuses the first legitimate smaller region and gets
  lowered in a hurry by whoever hits it, which is how a floor stops meaning anything" - and a floor at the
  measured size would refuse every legitimately rebuilt archive (a re-cut bbox, a re-pinned planet build, a
  second region) while the job of this floor is only to catch a half-copied file. Two floors for one fact in
  two languages would drift, so the Swift constant names the checker's number and says where it came from.
  ScenicStyleDocument keeps the atomic write and SKIPS it when the materialised document already equals what
  it would write (SwiftUI may re-run the resolve; rv1-pr112 RV-2), which also stops a re-resolve replacing a
  file the renderer has open.
  R4 the drift test - services/tiles/tests/test_embedded_style_identity.py: the raw literal between `#"""`
  and `"""#` in ScenicLightStyle.swift / ScenicDarkStyle.swift is byte-equal to styles/scenic-light.json /
  scenic-dark.json (4563 / 4591 bytes, measured today), AND the ARM is asserted - MapAppearance.styleJSON
  maps `case .light:` -> `return ScenicLightStyle.json` and `case .dark:` -> `return ScenicDarkStyle.json`,
  read off the switch arms with // stripped, because byte-equality of both literals survives the two arms
  trading places (RV-3). Red on one flipped hex digit and on swapped arms.
  R5 SCOPE - `bash ops/check-pins --source-only` is NOT run on this box: it drives a long swift build here.
  CI's pins-source-only job on the PR is the evidence, quoted from `gh pr checks`. The two new assertions
  are run VERBATIM and bare at the final commit instead.
- 2026-09-19T12:45:00Z RED FIRST, by name, before green (agent/claude-opus-5). Every new check was seen
  refuse before it was seen pass:
  P-ATTR-01 - `bash ops/lib/check-map-attribution --prove-red`, 8 mutations of a throwaway copy of apps/ios,
  8/8 refused BY NAME: both credit arms swapped and the demo arm alone returning the Protomaps credit (each
  named "does not return MapStyle.protomapsAttribution" / "...demoAttribution", with every identifier and
  every count unchanged - the arms are what moved); the plan's string edited ("credit literal is not
  declared verbatim"); a feature file naming a protomaps case ("identifier protomapsLA occurs outside its
  tracked set"); the caption reaching the case without a `case .` pattern, COUNT UNCHANGED at DriveCopy(2)
  ("protomapsLA is NAMED outside Packages/ScenicApp/Sources/MapAdapter/ on 1 line(s)" - the count arm is
  green on this row, which is why the pattern anchor exists); the mount deleted ("mount
  BasemapResolver.losAngeles( occurs outside its tracked set"); a literal credit typed at the footer
  ("credit literal © OpenStreetMap contributors · Protomaps occurs outside its tracked set"); and the footer
  handed a different resolved string ("is not a style's attributionText"). The table also refuses to run
  against an already-red tree, and refuses any row whose sed matched nothing ("THE MUTATION CHANGED
  NOTHING") - a row that mutates nothing proves nothing.
  P-DATA-03 - seen red twice by disabling ONE limb of the shipping checker at a time, then restored:
  with the region comparison off, "P-DATA-03: the region/freshness limbs of the shipping checker do not
  decide: stamped region 'bay': exit 0 (expected 1) and the output did not name "meta.region is 'bay'""
  (exit 1); with the age comparison off, "stamped 40 days ago: exit 0 (expected 1) and the output did not
  name 'older than 30 days (P-DATA-03)'" (exit 1).
  The drift test - seen red on the TRACKED files, then restored: one flipped hex digit in
  ScenicLightStyle.swift ("At index 568 diff: b'0' != b'D'", test_the_embedded_literal_is_byte_equal...
  [light-ScenicLightStyle] FAILED), and MapAppearance's two styleJSON arms swapped, with both literals still
  byte-equal to their files ("{'light': 'return ScenicLightStyle.json'} != {'light': 'return
  ScenicDarkStyle.json'}", test_each_appearance_returns_its_own_style FAILED).
- 2026-09-19T12:47:00Z ios-compile, the compiler proof for the Swift under apps/ios (this box has no Mac).
  ONE dispatch on the final code commit bf9a6f3: run 35442667891, headSha
  bf9a6f39c5924294c5576778518386214ccac97c, status completed, conclusion success; `gh run view --log` has
  one "** BUILD SUCCEEDED **" (simulator-build, 12:24:19Z) and a ' error:' count of 0. Only comments in
  ops/lib/check-map-attribution changed after that commit (309 -> 300 lines, CLAUDE.md's cap); no Swift byte
  moved, so no second dispatch was bought.
- 2026-09-19T12:50:00Z FINAL PRE-REVIEW ACCEPTANCE, re-run bare and re-quoted whole (the author rule):
  - `bash ops/lib/check-map-attribution` -> exit 0: "over 21 .swift file(s) under apps/ios, // stripped:
    attributionText's protomaps arm (line 99) returns MapStyle.protomapsAttribution and its demo arm (line
    101) returns MapStyle.demoAttribution; the declaration is verbatim "© OpenStreetMap contributors ·
    Protomaps", occurring in code at .../MapStyle.swift(1) only; protomapsLA at .../DriveCopy.swift(2)
    .../MapAppearance.swift(2) .../MapStyle.swift(6), and every occurrence outside .../MapAdapter/ is a
    `case .` pattern; the mount at .../DriveBasemap.swift(1); the footer at .../ScenicHomeScreen.swift(1),
    built with: text: style.attributionText".
  - `bash ops/lib/check-map-attribution --prove-red` -> exit 0: "prove-red: 8/8 mutations refused by name".
  - `python -m pytest services/tiles/tests` -> "69 passed in 2.78s" (58 before this task, 11 added by
    test_embedded_style_identity.py).
  - P-ATTR-01's assertion verbatim, `bash ops/lib/check-map-attribution` -> exit 0 (quoted above).
  - P-DATA-03's assertion verbatim -> exit 0: "services/tiles/check_pmtiles.py, run as build-la.sh step 6
    runs it, over 3 in-process fixtures: a fresh region-la archive: exit 0, named 'PMTILES OK' / stamped 40
    days ago: exit 1, named 'older than 30 days (P-DATA-03)' / stamped region 'bay': exit 1, named
    "meta.region is 'bay'"". With SCENIC_LA_PMTILES pointed at the real build it also printed "la.pmtiles:
    exit 0 - PMTILES OK: la.pmtiles region=la bytes=63520949 zoom=0-14 tiles=2549
    bounds=(-119.000000,33.700000,-117.850000,34.450000)". NOTE for the reviewer: with PYTHON unset this
    box's `python3` is a Store stub with no pytest and the check REFUSES fail-closed by name ("the tests'
    PMTiles writer is unavailable: No module named 'pytest'"), which is the right direction; it was run as
    `PYTHON=python`. CI's image installs python3-pytest (.github/workflows/linux-core.yml).
  - `python ops/lib/check-mutate-population.py` -> exit 0: "73 modules, 22 covered by 10 populations, 27
    allowlisted, 0 added by this branch ... the floor of 22 holds". CONFIRMED: no module was added under
    services/etl/etl/ or Sources/, and apps/ios is outside that check's roots, so no mutation population is
    owed by this task.
  - `bash ops/lib/check-safety-disclaimer` -> exit 0, counts UNCHANGED (FeatureScenicHome was not touched):
    "isSafetyDisclaimerAcknowledged at .../GatedHandoffButton.swift(2) .../ScenicHomeScreen.swift(4), the
    key at .../ScenicHomeScreen.swift(1)".
  - `bash ops/lib/check-line-cap` -> exit 0: "90 Swift files tracked (Sources=29, Tests=40, apps/ios=21),
    none over 300 lines". `bash ops/lib/check-exec-bits` -> exit 0: "80 files, 23 required present, all
    modes correct" (check-map-attribution and -mutations 100755, check-pmtiles-provenance.py 100644).
    `bash ops/queue-check` -> exit 0.
  - `wc -l` on every touched file: ops/lib/check-map-attribution 300, ops/lib/check-map-attribution-
    mutations 84, ops/lib/check-pmtiles-provenance.py 131, services/tiles/tests/test_embedded_style_
    identity.py 138, pins/PINS.yaml 287, MapAdapter/BasemapResolver.swift 125,
    MapAdapter/ScenicStyleDocument.swift 92.
  - `grep -rn "import MapLibre" apps/ios` -> MapView.swift:2 only (line 7 is the doc comment naming it).
  - PINS.yaml ids: 31, all unique (read through ops/lib/pins.py's own loader).
  - NOT RUN HERE (ruling R5): `bash ops/check-pins --source-only` and `bash ops/test` - both drive a long
    swift build on this Windows box. CI's pins-source-only and linux-core jobs on the PR are the evidence.
  STILL OPEN, for the reviewer and for whoever files next: (1) P-DATA-03's CORPUS half - T-0205; (2)
  P-ATTR-01's XCUITest half (the footer visible at every sheet detent) - T-0180; (3) the real artifact is
  only checked where SCENIC_LA_PMTILES is set, which is this box and ops/publish-tiles, never CI; (4) the
  1 MiB wholeness floor in BasemapResolver is asserted by no test - there is no test target in ScenicApp,
  so ios-compile is the only thing that reads that code at all.
- 2026-09-19T13:05:00Z PR #119 opened (base main). `gh pr checks 119` reported "no checks reported on the
  'task/T-0197' branch" and `gh run list --workflow linux-core.yml` shows runs for task/T-0207 and
  task/T-0213 but none for this branch - the pull_request event did not start linux-core on the open. This
  push re-triggers it (synchronize). CI's pins-source-only and core jobs remain the evidence for ruling R5;
  if they are still absent on this push, the reviewer should say so rather than read silence as green.
- 2026-09-19T13:10:38Z MERGED origin/main into task/T-0197 (a55f433), before any correction, because the
  final pre-review commit merges origin/main first and re-runs the acceptance block on the merged head
  (CLAUDE.md, Verification). PR #119 was mergeStateStatus DIRTY / CONFLICTING, which is WHY no CI job ever
  ran on it - GitHub starts no pull_request workflow on a conflicting PR - so ruling R5's evidence never
  existed. ONE conflict, pins/PINS.yaml: main gained P-DATA-04 (#116, T-0205) where this branch adds
  P-DATA-03 and P-ATTR-01. Resolved by keeping BOTH sides, each entry with its own owner/added tail; 32 pin
  ids, 0 duplicated; PINS.yaml re-measured at 296 lines (was 287 - the author rule: a correction that
  touches a measured file re-measures it). `python ops/lib/check-mutate-population.py` on the merged head:
  exit 0, "P-PROC-06: every added module is covered or allowlisted; the floor of 23 holds" - CONFIRMED no
  allowlist entry is owed: check-pmtiles-provenance.py and check-map-attribution-lib are under ops/lib/,
  and that gate's roots are services/etl/etl/ and Sources/ only; services/tiles is outside them too.
- 2026-09-19T13:10:38Z RULINGS R6 on the pre-review mutant pass (.artifacts/signoffs/t0197-mutant-pass.md,
  7 survivors + 4 unsupported), before the code that closes them:
  R6-A2/A3 BLOCKING, ONE root cause, ACCEPTED AND FIXED. (b) matched the two credit declarations by PREFIX
  (`public static let demoAttribution = "`) and by SUBSTRING (`grep -c -F` on the line), so the demo credit
  could be set to `© OpenStreetMap contributors, Protomaps` and the Protomaps declaration could keep the
  plan's literal and append `+ " · Natural Earth"`, both EXIT 0 and both printing "the declaration is
  verbatim". FIX: a WHITELIST OF EXACTLY TWO WHOLE LINES - every line under apps/ios naming
  `static let protomapsAttribution` or `static let demoAttribution` (there is one of each, and the count is
  asserted) is compared TRIMMED AND WHOLE against its one approved declaration. On the plan question the
  mutant pass raises: the plan and CLAUDE.md state ONE string, `© OpenStreetMap contributors · Protomaps`,
  for the Protomaps tiles and say nothing about the demo tiles; MapStyle.swift's own verified note (the
  demo TileJSON's attribution is a single space, the polygons are Natural Earth) is the evidence that the
  demo tiles carry no OpenStreetMap data. RULED: the demo credit must NEVER contain "OpenStreetMap
  contributors"; the whole-line equality is the mechanical anchor and the refusal text says why.
  R6-A7 BLOCKING, ACCEPTED AND IMPLEMENTED. Acceptance bullet 2's accessibilityHidden limb was neither
  implemented nor ruled - `grep -c accessibilityHidden` was 0 in the check, the table and PINS.yaml. New
  limb (e), a WHITELIST: every occurrence of the identifier `accessibilityHidden` in DesignSystem/
  AttributionFooter.swift and in the mount screen must be `accessibilityHidden(false)` (counted with
  multiplicity, // stripped), and the footer must carry at least one - so `(true)`, an interpolated
  argument and any other spelling are refused by name rather than blacklisted. Both sites are already
  `(false)` today (AttributionFooter.swift:67, ScenicHomeScreen.swift:260); the check now says so.
  R6-A5 ACCEPTED AS BLOCKING AND FIXED. (d) read only that the text argument ended in `.attributionText`,
  so the credit could come from a SECOND `DriveBasemap.resolve(...)` while the renderer kept the first.
  FIX, anchored on identifiers at the mount site: `DriveBasemap.resolve(` occurs exactly once over apps/ios
  (ScenicHomeScreen.swift(1)); the footer's text argument must read `<binding>.attributionText` where
  <binding> is a bare local identifier; and `styleURL: <that same binding>.url` occurs exactly once in the
  screen, with `styleURL:` occurring exactly once. The screen holds ONE resolved value in @State (`style`)
  and hands `style.url` to MapView and `style.attributionText` to the footer, so both halves are read off
  the one binding.
  R6-A6 RULED DISCLOSURE, not closed. Reusing arm_verdict on `public var url: URL` does not fit: the check
  was at exactly 300 lines, `url`'s three arms have a different shape from attributionText's two (two
  single cases, not one combined), and A2/A3/A5/A7 are the blocking work. `MapStyle.url` is now named
  explicitly in WHAT IT CANNOT SEE in BOTH the check's green output and the P-ATTR-01 pin text: a `url` arm
  swapped to the demo style document under the Protomaps credit is green here and belongs to T-0180's
  XCUITest half ("whether the tiles on screen are the ones the credit names").
  R6-A4 DISCLOSURE ONLY, as the pass says. The header's sentence - any spelling that reaches a case without
  naming the identifier, e.g. `MapStyle.allCases[0]`, plus `/* */` comments and Swift outside apps/ios - is
  now in the pin text AND in the green output, with the true half stated: `MapStyle(rawValue:
  "protomapsLALight")` IS refused, because (c) counts the identifier inside string literals too.
  R6-B4 ACCEPTED AND FIXED, bound to the shipping entry point. ops/lib/check-pmtiles-provenance.py gains a
  FOURTH in-process fixture - `good_metadata()` with the region key POPPED - which the shipping checker
  (`python services/tiles/check_pmtiles.py`, the command build-la.sh step 6 and ops/publish-tiles run) must
  REFUSE naming `meta.region is None`. Red first with the pass's own mutant, then green (quoted below).
  R6-UNSUPPORTED-1 (R5's evidence does not exist) SUSTAINED. R5 cited CI jobs that never ran, because the
  PR was CONFLICTING. R5 is hereby SUPERSEDED: `bash ops/check-pins --source-only` is run ONCE, locally, on
  the merged head, and its summary line is quoted in the acceptance block below. A pin's evidence is a
  command someone ran, never a job someone expected.
  R6-UNSUPPORTED-2 ACCEPTED. P-ATTR-01 now names the XCUITest anchor the footer really carries -
  `.accessibilityIdentifier("attribution.footer")`, AttributionFooter.swift:62 - and the snapshot name
  T-0180 will assert over, `home-attribution-footer` at each sheet detent. No reference image exists today
  and none is recorded here: CLAUDE.md allows a snapshot reference to be recorded only by a human-initiated
  commit reviewed by a different agent.
  R6-UNSUPPORTED-3 ACCEPTED AND CORRECTED. P-DATA-03's text said T-0205 "is the task that writes one".
  T-0205 has MERGED (PR #116) and wrote meta.surface_coverage / P-DATA-04, not a region assertion. The
  measured state of the tree today: `etl.corpus` DOES stamp the field (services/etl/etl/corpus.py,
  `writer.set_meta("region", region)`) and NOTHING anywhere reads it back against the active region
  (grep over ops/, services/etl/tests/ and services/api: the only hits are a waydoc fixture assertion and
  this file). RULED: the corpus half of P-DATA-03 is UNASSERTED and UNOWNED - NO open task owns it, and the
  orchestrator must file one. Said in the pin text and printed by the check's own green output, so the gap
  travels with the pin instead of living in a task file.
  R6-UNSUPPORTED-4 (R3's minimumArchiveBytes drift) NOT TAKEN: the pass files it non-blocking, the author
  already discloses it as STILL OPEN 4, and it belongs to a task that can add a test target or a reader -
  it is restated in STILL OPEN below rather than half-closed here.
- 2026-09-19T13:29:56Z RED FIRST for the four new anchors, then green (a check nobody has seen refuse is a
  check nobody has tested). `bash ops/lib/check-map-attribution --prove-red` is now TWELVE rows and prints
  "prove-red: 12/12 mutations refused by name"; the four added rows, each EXIT 1 with the reason NAMED, and
  each EXIT 0 before this commit:
  "the demo credit set to the Protomaps line" (MapStyle.swift, demoAttribution := "© OpenStreetMap
  contributors, Protomaps") -> "the demo credit declaration is not verbatim";
  "the Protomaps declaration appended to" (... = "© OpenStreetMap contributors · Protomaps" + " · Natural
  Earth") -> "the credit literal is not declared verbatim";
  "the footer hidden from accessibility" (DesignSystem/AttributionFooter.swift, (false) -> (true)) ->
  "hides something from accessibility";
  "the credit from a second resolve" (ScenicHomeScreen.swift, AttributionFooter(text: DriveBasemap.resolve(
  for: selectedDrive, appearance: .light).attributionText)) -> "resolve call DriveBasemap.resolve( occurs
  outside its tracked set".
  B4, red then green on the SHIPPING entry point: with the mutant the pass wrote - services/tiles/
  check_pmtiles.py `meta.get("region")` -> `meta.get("region", region)` - `python ops/lib/check-pmtiles-
  provenance.py` exits 1: "no meta.region at all: exit 0 (expected 1) and the output did not name
  'meta.region is None'; it said: PMTILES OK: case3.pmtiles region=la bytes=1048834 zoom=0-14 tiles=256".
  The mutation was made with sed on the worktree, restored with `git checkout --`, __pycache__ purged and
  1.2 s slept before the green re-run; `git status --short` is empty.
- 2026-09-19T13:29:56Z FINAL PRE-REVIEW ACCEPTANCE, re-run BARE on the MERGED head (a55f433 + this branch's
  two commits), re-quoted whole (the author rule):
  - `bash ops/check-pins --source-only` -> exit 0: "PINS ok=15 skipped=16 pending=1 expired=0 failed=0
    tier=linux source-only". This SUPERSEDES ruling R5: the CI evidence R5 named never existed, because the
    PR was conflicting. Run here, on this box, on the merged head.
  - `bash ops/lib/check-map-attribution` -> exit 0: "over 21 .swift file(s) under apps/ios, // stripped:
    attributionText's protomaps arm (line 99) returns MapStyle.protomapsAttribution and its demo arm (line
    101) returns MapStyle.demoAttribution; the two declarations are verbatim, whole line: `public static
    let protomapsAttribution = "© OpenStreetMap contributors · Protomaps"` / `public static let
    demoAttribution = "© MapLibre · Natural Earth"`; the plan's string occurs in code at .../MapStyle.
    swift(1) only; protomapsLA at .../DriveCopy.swift(2) .../MapAppearance.swift(2) .../MapStyle.swift(6),
    and every occurrence outside .../MapAdapter/ is a `case .` pattern; the mount at .../DriveBasemap.
    swift(1); one DriveBasemap.resolve( at .../ScenicHomeScreen.swift(1); the footer at .../
    ScenicHomeScreen.swift(1), built with: text: style.attributionText - and the map with styleURL:
    style.url, the same binding; every accessibilityHidden in .../DesignSystem/AttributionFooter.swift and
    in the mount screen is (false). Not checked here: rendering, the detents, contrast, Dynamic Type, or
    that the tiles on screen are the ones this credit names - XCUITest (T-0180) owns those. Nor
    MapStyle.url ... (A6), as is any spelling that reaches a case without naming protomapsLA - e.g.
    MapStyle.allCases[0] (A4) - and any Swift outside apps/ios."
  - `bash ops/lib/check-map-attribution --prove-red` -> exit 0: "prove-red: 12/12 mutations refused by
    name" (every row EXIT 1, REASON NAMED yes).
  - `python ops/lib/check-pmtiles-provenance.py` -> exit 0, FOUR fixtures: "a fresh region-la archive: exit
    0, named 'PMTILES OK' / stamped 40 days ago: exit 1, named 'older than 30 days (P-DATA-03)' / stamped
    region 'bay': exit 1, named "meta.region is 'bay'" / no meta.region at all: exit 1, named 'meta.region
    is None'", plus "The corpus half is UNASSERTED and UNOWNED: etl.corpus stamps meta.region (corpus.py,
    set_meta("region", ...)) and nothing reads it back against the active region; T-0205 merged as PR #116
    writing meta.surface_coverage instead, so a task for it still has to be filed."
    With SCENIC_LA_PMTILES=C:/Users/phineasf/Documents/GitHub/scenic_drive/services/tiles/work/la.pmtiles
    -> exit 0 and additionally "la.pmtiles: exit 0 - PMTILES OK: la.pmtiles region=la bytes=63520949
    zoom=0-14 tiles=2549 bounds=(-119.000000,33.700000,-117.850000,34.450000)".
  - `python -m pytest services/tiles/tests` -> "69 passed in 6.47s" (__pycache__ purged first);
    `python -m pytest services/tiles/tests/test_embedded_style_identity.py` -> "11 passed in 0.07s".
  - `python ops/lib/check-mutate-population.py` -> exit 0: "P-PROC-06: every added module is covered or
    allowlisted; the floor of 23 holds" - no allowlist entry owed (ops/lib and services/tiles are outside
    that gate's roots, which are services/etl/etl/ and Sources/).
  - `bash ops/lib/check-safety-disclaimer` -> exit 0, counts UNCHANGED: "isSafetyDisclaimerAcknowledged at
    .../GatedHandoffButton.swift(2) .../ScenicHomeScreen.swift(4), the key at .../ScenicHomeScreen.
    swift(1)".
  - `bash ops/lib/check-line-cap` -> exit 0: "P-SRC-02: 90 Swift files tracked (Sources=29, Tests=40,
    apps/ios=21), none over 300 lines". `bash ops/lib/check-exec-bits` -> exit 0: "P-OPS-01: 82 files, 23
    required present, all modes correct" (check-map-attribution, -lib and -mutations 100755,
    check-pmtiles-provenance.py 100644). `bash ops/queue-check` -> exit 0: "QUEUE OK (208 tasks)".
  - `wc -l` on every touched file, RE-MEASURED after the merge and the fix: ops/lib/check-map-attribution
    287 (was 300; the readers moved out), ops/lib/check-map-attribution-lib 148 (new), ops/lib/check-map-
    attribution-mutations 99, ops/lib/check-pmtiles-provenance.py 151, pins/PINS.yaml 296,
    services/tiles/tests/test_embedded_style_identity.py 138, MapAdapter/BasemapResolver.swift 125,
    MapAdapter/ScenicStyleDocument.swift 92. None over the 300-line cap.
  - PINS.yaml through ops/lib/pins.py's own loader: 32 ids, 32 unique; P-ATTR-01 assertion "bash
    ops/lib/check-map-attribution" runs_on [linux]; P-DATA-03 assertion the provenance checker.
  - ios-compile: `git diff --stat f53a664 HEAD -- apps/ios` is EMPTY - no Swift byte moved in the merge or
    in either commit - so run 35442667891 (headSha bf9a6f3, conclusion success, one "** BUILD SUCCEEDED **",
    ` error:` count 0) still stands for this Swift tree and NO second dispatch was bought.
  STILL OPEN: (1) P-DATA-03's CORPUS half is UNASSERTED and UNOWNED - etl.corpus stamps meta.region and
  nothing reads it back; T-0205 merged as #116 writing meta.surface_coverage, so the orchestrator must FILE
  a task for the corpus region comparison; (2) P-ATTR-01's XCUITest half - T-0180, anchor `attribution.
  footer`, snapshot `home-attribution-footer` at max detent, both themes, AX5 (plan line 239); no reference
  image recorded here; (3) MapStyle.url (A6) and `MapStyle.allCases[0]`-shaped spellings (A4) are disclosed,
  not closed; (4) the real artifact is only checked where SCENIC_LA_PMTILES is set - this box and
  ops/publish-tiles, never CI; (5) the 1 MiB wholeness floor in BasemapResolver is asserted by no test
  (ScenicApp has no test target); (6) `bash ops/test` is not run on this box - CI's linux-core job is the
  evidence, and it can only run now that the PR is no longer conflicting.
- 2026-09-19T16:41:24Z RULINGS by agent/claude-opus-5 (round 2, the author rule), before a line of code,
  on rv1-pr119's two blocking findings:
  R2-A B2 UPHELD, and it is the pin's own clause that was false. P-ATTR-01 says "every map surface
  carries the credit"; limb (d) counted `styleURL:` INSIDE ScenicHomeScreen.swift and whitelisted
  `AttributionFooter(` over the whole tree, so the enumeration was one-sided: the footers were
  enumerated, the SURFACES were not. rv1's M1 (a second view under FeatureScenicHome mounting
  `MapView(styleURL: style.url, ...)` with no footer) printed the full green summary. FIX in the shape
  CLAUDE.md asks for - a WHITELIST over the population, never a blacklist of spellings: new limb (f)
  counts every `MapView(` and every `styleURL:` occurrence over every .swift file under apps/ios against
  a tracked set typed into the check (ScenicHomeScreen.swift(1) each). The ONE definition site is
  excluded by exact path, MapAdapter/MapView.swift, and is pinned FIRST by `struct MapView` and
  `public init(styleURL` occurring exactly once there and nowhere else - without that, a second or a
  moved definition would carry its own occurrences out of the counted population and a surface with
  them. `MLNMapView(frame: .zero, styleURL: styleURL)` at MapView.swift:34 is inside the excluded
  definition, which is why the exclusion is one named file and not a pattern.
  R2-B M3 CLOSED here rather than disclosed, since it shares B2's root and costs one reader. Limb (b)
  gains a SECOND population: every `static let` LINE under apps/ios whose value names OpenStreetMap is
  the one approved declaration, compared trimmed and whole. The identifier-keyed whitelist could not see
  `static let tileCredit = "(c) OpenStreetMap contributors and Protomaps"`; the string's own subject
  matter is the honest population, because a credit is only ever true of the tiles it is handed with.
  Today that population is exactly one line (MapStyle.swift:51): every other OpenStreetMap mention in
  apps/ios is a `///` comment, which every reader in this check strips.
  R2-C the mutation table grew a row FORM, not just two rows. Both new mutants ADD a file, which no sed
  script over the tracked files can reproduce, and adding a file is precisely what the whitelist claims
  to refuse: a row whose path carries a leading `+` writes the third field as the file's single line of
  Swift (this check reads source, it does not compile it) and the driver refuses a `+` row whose file
  already exists or whose directory does not. Rows 13 (a second map surface with no credit) and 14 (a
  second credit string under a new identifier) are that form.
  R2-D the check was at 287 lines and the two limbs did not fit under CLAUDE.md's 300-line cap, so the
  VERDICT printer moved to ops/lib/check-map-attribution-lib beside the readers (it decides nothing; it
  prints what the check read), and the two new readers were written there. check-map-attribution is 294.
  R2-E STILL DISCLOSED, unchanged by this round and named in the pin text and in the check's own green
  summary: a footer BUILT and then wrapped in `.opacity(0)` (rv1's M2 - T-0180's snapshot half owns it);
  a paraphrase that never names OpenStreetMap at all, and a `static let` whose value sits on the NEXT
  line; a map mounted through some wrapper type that is not `MapView(`; MapStyle.url's arms (A6); and
  `MapStyle.allCases[0]`-shaped spellings (A4).
  R2-F B1 sequence, per CLAUDE.md and PR #115's refusal at merge: the code commit lands FIRST, then
  `git fetch origin && git merge --no-edit origin/main`, then the WHOLE acceptance block is re-run bare
  on the merged head and quoted in one entry, then the final commit and an immediate push - the merge is
  done LAST so that the push follows it within minutes and the head that is signed off is the head that
  merges.
