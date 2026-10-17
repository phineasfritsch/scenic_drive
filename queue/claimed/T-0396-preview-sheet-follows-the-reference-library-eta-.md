---
id: T-0396
title: Preview sheet follows the reference library - ETA (distance) with the estimate badge as a tag on it, why line, one hazard row, labelled climb and scenic-share line, Start + Save, the disclaimer line directly under Start
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T15:13:44Z
lease_expires_at: 2026-10-18T15:13:44Z
worktree: .worktrees/T-0396
branch: task/T-0396
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/, Sources/ScenicKit/, Tests/, ops/lib/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-SAFE-03, P-SAFE-07, P-A11Y-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The owner asked for the app's UI to lean on a reference library built from real shipping apps (Mobbin "Download
all screens" packs, 11 apps). The library lives outside git at
`C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md` (section
"Plan preview", and "Global rules" for the type ramp, spacing, button hierarchy); the reference screens it cites
are under `.artifacts/mobbin/screens/<app>/NNN.png` in the same checkout. Today's shot of this screen is
`.artifacts/shots-39035404874/ios-screenshots/plan-preview-{light,dark,ax5}.png` (ios-screenshot run 39035404874).

Scope (the medium-detent sheet content of the plan preview, `-screen preview` in PlanRehearsal):
1. Destination is the title (not "Plan a drive").
2. ETA row: duration .title2 semibold + "(distance)" secondary, with the badge "estimate · no traffic data" as a
   gray caption TAG on the same line (wraps under the number at AX sizes, never detached).
3. Why line .subheadline secondary, copy "+N min over fastest · ..." instead of "N min longer than the fastest way".
4. One hazard row (the most severe): amber glyph + one line; "+N more" when there are more; the slot collapses when
   there is none (never "all clear").
5. The unlabelled ~145pt chart goes; in its place a .footnote climb/descent line and a labelled scenic-share bar
   ONLY if the data the sheet already holds supports it - otherwise rule it out in the Log and drop the chart to
   nothing rather than draw an unlabelled one.
6. Actions: "Start the drive" filled + "Save" tonal; "Choose another place" and the loop/trip links leave the
   visible sheet (a "..." menu or the large detent).
7. "Conditions change. Verify locally." as .footnote DIRECTLY under Start, in the same scroll view, at every size.

OWNER RULING 2026-10-17 ("go with recs"): after a corridor has >= 5 learned samples the tag is replaced by
"Learned from N drives" (.footnote, count shown). Build it only if the preview already has the sample count in
hand; if not, rule it out in the Log and file the follow-up - the badge-until-5 invariant (P-SAFE-07) must hold
either way.

Out of scope: putting a map on the preview, alternative-route callouts, the large-detent chart and road cards.

Invariants that must survive (product rules in CLAUDE.md): the disclaimer stays visible on the route screen
(P-SAFE-03), the estimate badge until >= 5 samples (P-SAFE-07), attribution where a map is drawn. Copy that tests
pin must move with its test, not be deleted.

Demonstration: dispatch ios-compile and ios-screenshot on the task branch; quote both run ids; look at
plan-preview light, dark AND ax5 and state, row by row against items 1-7, what each shot shows. At AX5 Start and
the disclaimer line must both be reachable. Any new or changed guard is shown red then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the reference library pass 2 ("Biggest changes" 6 and 18).
- 2026-10-17T15:13:44Z claimed by agent/claude-opus-5; lease until 2026-10-18T15:13:44Z
- 2026-10-17T15:27:22Z RULINGS before code (author rule). Read: the Brief, CLAUDE.md, library "Plan preview" + "Global
  rules", Google Maps #205/#241, Transit #041/#062, today's plan-preview-light/ax5 (run 39035404874).
  - R1 (item 1, title). The nav bar reads "Plan a drive" over a card that already titles "Zuma Beach". Ruled: in the
    preview state the navigation title is empty and the card's .title3 semibold destination is the one title (it
    wraps; a nav-bar title truncates). Close and Saved stay in the nav bar.
  - R2 (item 2, distance). PlanPreview holds no distance field, but it holds the drawn `route`. Ruled: distance is
    the route's summed haversine (`Geo.distanceMeters`, DriveLeg.lengthMeters' formula), in miles (the only region is
    LA; metric is not in scope): one decimal under 10 mi, whole miles from 10, nothing when the route has < 2 points.
    New ScenicKit API on PlanPreview: `etaHero` ("55 min"), `distanceLabel` ("(14 mi)" or nil), `whyLine`. The
    rehearsal fixture's line is sparse, so its shot shows the fixture's straight-segment length, not a real 32 mi.
  - R3 (item 2, tag). The badge text stays verbatim `PlanPreview.estimateBadge`, identifier plan.estimate, gated by
    `showsEstimateBadge` exactly as before (P-SAFE-07 unchanged); it becomes a .caption gray capsule on the ETA line,
    under the number via ViewThatFits when the line does not fit (AX sizes). The library's (i) popover is ruled out:
    no copy for it exists in the Brief or library; filed as nothing (cosmetic).
  - R4 (owner ruling, learned successor). PlanPreview carries `etaIsEstimate` and nothing else: no sample count
    (RetimedPreview folds the provider's answer into one Bool). Ruled OUT: "Learned from N drives" is not built;
    when the badge is off the slot is empty, as today. Follow-up filed: T-0399 (carry the corridor sample count on
    PlanPreview and show the successor).
  - R5 (item 3, why line). `PlanPreview.etaLine` is ALSO the drive screen's formatter (T-0330 R4, DriveDisplay and
    its tests) - it is not changed. New `whyLine`: "+N min over fastest", or "About as quick as the fastest way" when
    extra is 0. The " · <episodes>" half is ruled out: the preview holds no episode or road names.
  - R6 (item 4, hazard). The order of `HazardCopy.lines(for:)` (closure crossed first, then closure state, then runs
    in Worker order, T-0341 R2) is taken as the severity order; the first line is the row, amber glyph
    (DesignTokens.hazard), "+N more" (44pt) expands the rest IN PLACE - nothing is dropped (T-0339). No hazard: the
    slot collapses; `Text(HazardCopy.noneFlagged)` leaves the card (HazardCopy keeps the constant; its test stays).
    The line wraps rather than truncating (library "Wrap, never break"); shortening the T-0339 sentences and the
    source/age caption are ruled out (no data, other cards share the table).
  - R7 (item 5, chart). The ~145pt "chart" is PlanRouteShape - the route OUTLINE, not an elevation profile.
    Coordinate has no elevation and the preview holds no per-segment scenic score (`lambda` is one weight), so
    neither the climb/descent line nor the scenic-share bar is supported. Ruled: the outline goes and nothing is
    drawn in its place; PlanRouteShape.swift (no other user) is deleted and its digest row removed.
  - R8 (item 6, actions). "Start the drive" filled 50pt + "Save" tonal 50pt, 8pt gap; at AX sizes stacked full
    width. "Choose another place", "Just drive a loop" and "Plan a road trip" move into a 44pt "..." Menu on the title
    row; PlanSheetScreen hides its bottom bar while the preview is on screen. After Save the Save slot shows saveLine
    (plan.saved) as today.
  - R9 (item 7). `PlanPreview.conditions` (plan.conditions) as .footnote directly under Start: under the button row
    at default size; at AX sizes the stack is Start, the line, then Save. Same ScrollView as Start.
  - R10 (guard). check-hazard-copy-sites' whitelist moves with the card (the noneFlagged row goes); its prove-red row
    "the table call is gone" was anchored on `Text(HazardCopy.noneFlagged)` and is re-anchored on the shipped
    `HazardCopy.lines(for: preview)` call. Shown RED on the re-anchored row then GREEN below.
  - R11 (attribution). The preview draws no map; AttributionFooter stays in the bottom inset exactly once
    (check-map-attribution FOOTER_SET), unchanged. Its AX5 size is DesignSystem's (outside touches).
  - R12 (AX5 reachability). The shot is at rest; reachability is structural (Start and the line in one ScrollView,
    nothing floats over it once the bottom bar is hidden). A scrolled AX5 shot is not in the harness; not added.

## Acceptance (T-0396)
- A1 `swift test --jobs 4 --scratch-path .build/t-0396 --filter "PlanPreviewLinesTests|PlanSheetTests|HazardCopyTests|DriveDisplayTests"` passes; PlanPreviewLinesTests covers whyLine (extra 0, >0, quicker), etaHero, distanceLabel (nil < 2 points, 9.94 -> "9.9 mi", 9.96 -> "10 mi", 15.5 -> "16 mi") by exact equality.
- A2 `grep -c "PlanRouteShape\|HazardCopy.noneFlagged" apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/PlanPreviewCard.swift` prints 0, and PlanRouteShape.swift is gone.
- A3 `python ops/lib/check-hazard-copy-sites.py` ok and `--prove-red` prints `PROVE-RED OK` with every row red (re-anchored row shown red then green in the Log).
- A4 bare gates exit 0: check-safety-disclaimer, check-map-attribution, check-mutate-population.py, check-mutate-only.py, check-pins-yaml.py, check-exec-bits, queue-check.
- A5 every FeaturePlanSheet file <= 300 lines (`wc -l`).
- A6 ios-compile on task/T-0396 concludes success (run id quoted).
- A7 ios-screenshot on task/T-0396 concludes success; plan-preview-light, -dark and -ax5 are LOOKED at and the Log states for each: title = destination and no "Plan a drive"; ETA + (distance) with the gray tag on it (ax5: under it); "+20 min over fastest"; one amber hazard row + "+N more"; no outline; Start + Save; the conditions line under Start; no trip/loop bottom bar; attribution footer present.
- A8 (pre-review M1, M2) the T-0396 rows of ops/lib/check-safety-disclaimer-mutations, run alone, print `prove-red: 3/3 mutations refused by name`; M1 and M2 applied with their -pinned sha256 row re-approved make check-safety-disclaimer exit 1 naming `a frozen preview render block changed`.
- 2026-10-17T16:33:06Z EVIDENCE, first pass (commit d41f8973).
  - Correction to R4: the follow-up id is T-0400, not T-0399 (T-0399 exists on another branch; ids on main + every
    origin task branch listed, max T-0399). Filed: queue/backlog/T-0400 (learned-from-N needs the sample count) and
    queue/backlog/T-0401 (plansheet mutation rows for the new PlanPreview lines - ops/mutate is outside touches).
  - A1: `swift test ... --filter "PlanPreviewLinesTests|PlanSheetTests|HazardCopyTests|DriveDisplayTests"` ->
    `Test run with 24 tests in 4 suites passed`.
  - Hand mutants on PlanPreview.swift (driver in the session scratchpad, file restored after): M1 `tenths < 100` ->
    `<= 100` KILLED ("(10.0 mi)" != "(10 mi)"); M2 `route.count >= 2` -> `>= 1` KILLED; M3 legs -> ends only KILLED
    ("(0.0 mi)" != "(6.0 mi)"); M4 tenths truncated KILLED ("(9.9 mi)" != "(10 mi)"); M5 why line on etaMinutes
    KILLED ("+55 min over fastest"). `MUTANTS OK`.
  - Guard R10 RED then GREEN. RED on the new card with main's guard: `REFUSED  approved site missing:
    .../PlanPreviewCard.swift:             Text(HazardCopy.noneFlagged)` / `P-SAFE-03 hazard copy: FAILED - 0
    unapproved, 1 missing of 14 approved` (exit 1), and --prove-red `STALE    the table call is gone   anchor found 0
    times` / `PROVE-RED FAILED: 12 of 13 rows red by name, control 1`. GREEN after the whitelist row went and the row
    was re-anchored on SHIPPED: `P-SAFE-03 hazard copy: ok - 13 sites, every one approved, in 5 files`; `red      the
    table call is gone   A7-grep=caught  sites=CAUGHT by name exit=1`; `PROVE-RED OK: 13 of 13 rows red by name,
    control 0`.
  - check-safety-disclaimer RED first (`added .../PlanPreviewActions.swift missing .../PlanRouteShape.swift`), then
    rows re-approved (PlanPreviewActions added, PlanRouteShape removed, PlanPreviewCard + PlanSheetScreen rehashed,
    linked PlanPreview.swift rehashed) -> exit 0.
  - A6 ios-compile 39047588676: completed success (4m37s).
  - A7 ios-screenshot 39047593126: completed success. LOOKED at plan-preview-{light,dark,ax5}:
    light: (1) title "Zuma Beach" .title3, no "Plan a drive" (nav bar shows only Close / Saved), orange "..." circle
      trailing; (2) "55 min" bold + "(17 mi)" gray on one line with the gray "estimate · no traffic data" tag on the
      same line; (3) "+20 min over fastest" gray subheadline; (4) ONE row: amber triangle + the closure sentence
      (wraps 3 lines), then orange "+1 more"; (5) no outline/chart; (6) "Start the drive" filled orange with car
      glyph + "Save" tonal pale-orange with bookmark, one row; (7) "Conditions change. Verify locally." gray footnote
      directly under Start; no "Plan a road trip / Just drive a loop" bottom bar; attribution footer at the bottom.
    dark: same rows in dark tokens (lighter orange Start with dark label, brown tonal Save, yellow hazard glyph,
      dark tag fill); nothing clipped.
    ax5: title wraps "Zuma / Beach" with the "..." circle; "55 min (17 mi)" on one line; the tag WRAPS UNDER the
      number (2 lines); "+20 min / over fastest"; then the bottom inset's attribution footer (~500pt at AX5,
      DesignSystem's AttributionFooter, outside touches) - the hazard row, Start and the conditions line are below
      the fold in the same ScrollView (reachable by scroll, R12), nothing floats over them. DEFECT: the 2-line tag's
      text runs into the capsule's rounded ends ("estimate" and "traffic" touch the curve). FIX: the tag background is
      a 8pt continuous rounded rectangle; card re-hashed in check-safety-disclaimer-pinned; one re-run below.
- 2026-10-17T17:08:44Z RE-RUN (commit bdc8891c) and FINAL acceptance on the merged head f7c67df4 (origin/main merged last; main's
  b865a822 renumbered its own T-0400/T-0401 to T-0402/T-0403, so this branch's T-0400/T-0401 stand).
  - ios-compile 39050077285 completed success (3m10s); ios-screenshot 39050070882 completed success (16m32s).
  - LOOKED at the re-run: plan-preview-light and -dark unchanged from the first pass, items 1-7 as recorded above
    (title "Zuma Beach" + "..."; "55 min (17 mi)" with the gray tag on the line; "+20 min over fastest"; one amber
    hazard row + "+1 more"; no outline; Start filled + Save tonal; "Conditions change. Verify locally." directly
    under Start; no bottom trip/loop bar; attribution footer). plan-preview-ax5: the tag now wraps under the number
    on an 8pt rounded rectangle and its two lines sit inside it - the clipping is gone; title, ETA, why line wrap,
    no word broken; the hazard row, Start and the line are below the fold in the same ScrollView above the
    DesignSystem attribution footer (R12).
  - A1 `Test run with 24 tests in 4 suites passed` (exit 0).
  - A2 `grep -c` -> 0; PlanRouteShape.swift gone.
  - A3 `P-SAFE-03 hazard copy: ok - 13 sites, every one approved, in 5 files`; `PROVE-RED OK: 13 of 13 rows red by
    name, control 0`.
  - A4 check-safety-disclaimer exit 0; check-map-attribution exit 0; `P-PROC-06: every added module is covered or
    allowlisted; the floor of 173 holds`; `MUTATE-ONLY OK: 248 of 248 driver runs refused with exit 64`;
    `PINS-YAML ok pins=53 fields=426`; `P-OPS-01: 250 files, 23 required present, all modes correct`;
    `QUEUE OK (393 tasks)`.
  - A5 largest FeaturePlanSheet file PlanSheetScreen.swift 281 lines; PlanPreviewCard 140, PlanPreviewActions 80.
  - A6 39050077285 success. A7 39050070882 success, shots as above. The CI runs are on bdc8891c, before the merge of
    main; the merged head re-passed every local gate above.
- 2026-10-17T18:27:27Z PRE-REVIEW SURVIVORS CLOSED (M1, M2 BLOCKING; M3 was caught by PlanPreviewLinesTests).
  - Ruling: both survivors are one class - an edit inside a preview render block, green once the file's sha256 row is
    re-approved because nothing anchored on the view. Closed as -frozen's class, not by spelling: new sourced lib
    ops/lib/check-safety-disclaimer-preview freezes PlanPreviewCard's `var body` (mounts PlanPreviewActions and the
    footer), `etaRow`, `estimateTag` and PlanPreviewActions' `var body` (the line in BOTH stacks) and `conditions` as
    whole-line whitelists, plus the `#` directive fence on both files; reuses frozen_block/frozen_directives. It runs
    in check-safety-disclaimer right after require_frozen_blocks and BEFORE the digest pins, so a re-approved digest
    does not change the refusal. check-safety-disclaimer stays at 300 lines (the LIB loop and the call share lines).
    Rows 62-64 added to ops/lib/check-safety-disclaimer-mutations (M1, M2, and M1's twin: the actions block
    unmounted from the card).
  - RED (stage B: mutant applied in the worktree AND its -pinned row re-approved, then both restored):
    M1 `/^ *conditions$/d` on PlanPreviewActions.swift (sha256 c6285c0a.. -> dcfbedae.., row re-approved) ->
    `P-SAFE-03: a frozen preview render block changed:` / `PlanPreviewActions' body line 5 of 18 in .../PlanPreviewActions.swift:
    approved `conditions`, found `save`` / `check-safety-disclaimer rc=1`.
    M2 `if preview.showsEstimateBadge {` -> `if !preview.showsEstimateBadge {` (1bb26a36.. -> 9d911ad2.., re-approved) ->
    `PlanPreviewCard's estimateTag line 2 of 13 ...: approved `if preview.showsEstimateBadge {`, found
    `if !preview.showsEstimateBadge {`` / rc=1.
    Twin: the `PlanPreviewActions(saveLine: ...)` line deleted (-> 35e40f70.., re-approved) -> `PlanPreviewCard's body
    line 12 of 23 ...: approved `PlanPreviewActions(saveLine: saveLine, onDrive: onDrive, onSave: onSave)`, found
    `.padding(.top, 12)`` / rc=1.
  - GREEN on the restored tree: check-safety-disclaimer rc=0, `Frozen (-frozen, -preview); 37 feature file(s), shell,
    footer pinned (-pinned); doors over 115 .swift (-doors); LAST all 115 app .swift, then 336 root + pbxproj file(s)`.
  - Table rows alone (owner-approved: touched rows only): `T-0396 M1 ... 1 yes` / `T-0396 M2 ... 1 yes` /
    `T-0396 M1 twin ... 1 yes` / `prove-red: 3/3 mutations refused by name`.
  - Still unseen (recorded in the lib's header): whether PlanSheetScreen presents the card (its digest row covers the
    file), what showsEstimateBadge computes (P-SAFE-07's learner tests), modifier overloads elsewhere, `/* */`.
- 2026-10-17T18:55:14Z FINAL acceptance re-quoted on the merged head bbc8b382 (c86846c2 + origin/main merged last).
  - A1 rc=0 `Test run with 24 tests in 4 suites passed after 0.018 seconds.`
  - A2 `grep -c` -> 0; PlanRouteShape.swift: `No such file or directory`.
  - A3 `P-SAFE-03 hazard copy: ok - 13 sites, every one approved, in 5 files`; `PROVE-RED OK: 13 of 13 rows red by
    name, control 0`.
  - A4 check-safety-disclaimer rc=0 (`Frozen (-frozen, -preview); 37 feature file(s), shell, footer pinned ...`);
    check-map-attribution rc=0; `P-PROC-06: every added module is covered or allowlisted; the floor of 173 holds`;
    `MUTATE-ONLY OK: 248 of 248 driver runs refused with exit 64`; `PINS-YAML ok pins=53 fields=426`;
    `P-OPS-01: 253 files, 23 required present, all modes correct`; `QUEUE OK (393 tasks)`.
  - A5 largest FeaturePlanSheet file PlanSheetScreen.swift 281 lines (no Swift file changed in this round).
  - A6/A7 unchanged from 39050077285 / 39050070882: this round touched no Swift, no apps/ios file.
  - A8 `prove-red: 3/3 mutations refused by name`; stage-B red quoted in the 18:27:27Z entry.
