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
