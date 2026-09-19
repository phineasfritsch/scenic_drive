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
