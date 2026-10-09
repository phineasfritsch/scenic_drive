---
id: T-0346
title: The plan sheet's bottom bar never hides a card's own actions - on the road-trip card "Change the trip" sits under the "Plan a drive / Just drive a loop" bar; every card's last control stays reachable above the bar at every Dynamic Type size
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T15:45:25Z
lease_expires_at: 2026-10-10T01:45:25Z
worktree: .worktrees/T-0346
branch: task/T-0346
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, .github/workflows/ios-screenshot.yml, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt]
pins_affected: [P-ATTR-01, P-A11Y-01]
reviewer: null
depends_on: [T-0341]
verify: [ops/check-pins]
acceptance:
  - "MEASURED FIRST and quoted in the Log: every plan card's last control against the bottom bar at default (run 37945135739) and AX5 (run 37959095574) - default: only trip's Change the trip is under the bar; AX5: preview, loop, trip and saved lose the last control below the fold, offered truncates all three labels, the preview's footer shows content through it"
  - "The screenshot job shoots the six plan cards at AX5 (light) beside default light and dark, under its 30-minute cap; each new guard row in ops/lib/ios_screenshot_pinned.py is raised by name and seen red then green (check-ios-compile-guardrails.py bare and --prove-red)"
  - "After the fix, in one ios-screenshot run on the final code: in plan-trip-{light,dark,ax5} Change the trip, in plan-loop-* Change the loop, in plan-preview-* Choose another place and in plan-offered-* Choose another place are each fully on screen above the bottom bar, legible and untruncated; plan-offered-ax5 shows no truncated label; plan-nothingPretty-* and plan-saved-* no worse than measured; every plan shot (18) looked at and quoted in the Log"
  - "Attribution unchanged: the preview's AttributionFooter is on screen in plan-preview-{light,dark,ax5}; bash ops/lib/check-map-attribution green (P-ATTR-01); no toolbar item added, removed or renamed (PlanSheetScreen.swift untouched)"
  - "Every control the fix adds or moves is >= 44 pt tall (PlanCardExit minHeight 44) and scales with Dynamic Type (no fixed font size)"
  - "ios-compile success on the final head; bare guards green on the merged head: check-safety-disclaimer (digests re-approved), check-map-attribution, check-screen-rehearsals.py, check-ios-compile-guardrails.py, check-hazard-copy-sites.py; check-line-cap, check-pins-yaml, queue-check green"
---
## Brief

T-0341 owner stillOpen 2 (PR #227): in the plan-trip shot the bottom toolbar ("Plan a drive / Just drive a loop")
covers the trip card's "Change the trip" button; the added closures row pushed content down. T-0336's shots also
showed the plan sheet's two bottom-toolbar buttons change meaning per tab (an open design question for the owner).
MEASURE FIRST: every card in the plan sheet (preview, nothingPretty, offered, loop, trip, saved), the toolbar's
height at default and AX5 Dynamic Type, and whether each card's last control is above it (screenshots at both sizes);
RULE the fix (safe-area inset / content margin, not removing the bar), then the acceptance: shots at default and AX5
looked at, no control under the bar, attribution unchanged (P-ATTR-01). Do not redesign the toolbar - that is the
owner's design pass.

## Log
- 2026-10-09T15:24:28Z filed by agent/claude-opus-5 (orchestrator) from T-0341 stillOpen 2; T-0345 is held by task/T-0344.
- 2026-10-09T15:45:25Z claimed by agent/claude-opus-5; lease until 2026-10-10T01:45:25Z
- 2026-10-09T15:50:07Z MEASURE (default text size) by agent/claude-opus-5. Population: the six plan-sheet rehearsals the
  screenshot job shoots (preview, nothingPretty, offered, loop, trip, saved). Source: ios-screenshot run 37945135739
  (task/T-0341 at its final head, the last run before PR #227 merged; no Swift file changed on main since), shots
  plan-*-light.png, 1206x2622 px = 402x874 pt @3x, looked at side by side. The bottom bar (the "Plan a road trip /
  Just drive a loop" capsule, iOS 26 floating glass) spans about y 800-845 pt on every card. Each card's LAST control:
  | card | last control | its y (pt, approx) | above the bar? |
  | preview | "Choose another place" (then the attribution footer at ~765) | ~725 | yes |
  | nothingPretty | "Choose another place" | ~231 | yes |
  | offered | "Choose another place" | ~352 | yes |
  | loop | "Change the loop" | ~674 | yes |
  | trip | "Change the trip" | ~843 | NO - drawn behind the bar, half visible through the glass; the conditions line above it sits at ~790, against the bar's top edge |
  | saved | "Delete" on the last row | ~437 | yes |
  The defect reproduces on exactly one card at default size: the trip itinerary, a List longer than the screen whose
  last row lands under the floating bar at rest. No AX5 shot exists anywhere yet - that half of the measurement needs
  the screenshot job to shoot AX5, which is the first commit.
- 2026-10-09T15:50:07Z R1 (the AX5 harness, before any code). The screenshot job gains a third pass, LOOK=ax5: light
  appearance, the six plan cards only, launched with -UIPreferredContentSizeCategoryName
  UICTContentSizeCategoryAccessibilityXXXL (the argument domain, per launch - the device setting is never changed, so
  no other shot can inherit it). Six shots at ~18 s each add ~2 min to a ~19 min job, under the 30-minute cap; AX5 in
  dark as well (+2 more min) is RULED OUT: dark changes colour, not layout. Guard rows raised by name in
  ops/lib/ios_screenshot_pinned.py: "T-0346: the AX5 pass dropped", "...launched at the default text size", "...at a
  smaller accessibility size (AX3)", "...the AX5 trip card dropped", "...shoots every home screen too (the 30-minute
  cap)". Seen red then green:
  - RED: python ops/lib/check-ios-compile-guardrails.py <main's ios-screenshot.yml> -> "IOS-COMPILE-GUARDRAILS:
    workflow.jobs.simulator-screenshot.steps[4].run: differs from the pinned value (compared by equality)" rc=1
  - GREEN: python ops/lib/check-ios-compile-guardrails.py -> both "IOS-COMPILE-GUARDRAILS OK" lines, rc=0
  - python ops/lib/check-ios-compile-guardrails.py --prove-red -> each of the five T-0346 rows "[red rc=1]";
    "PROVE-RED OK: 78 mutations red, 6 legitimate spellings green over 2 workflows, 0 unexpected result(s)" rc=0
- 2026-10-09T16:25:13Z R1's run did NOT fit the cap: ios-screenshot run 37954789863 (head 9e8d2e98) - pre-capture
  10 min (toolchain 2:09, boot 1:59, build 5:46), capture 16:01:19 -> 16:20:50 = 19.5 min for 38 shots (~31 s a shot),
  then the 30-minute job timeout cancelled it before "upload the screenshots": conclusion cancelled, no artifact, no
  AX5 measurement. For comparison T-0341's run 37945135739 captured 32 shots in 10.5 min (~20 s a shot) and T-0325's
  run 37937330449 took 15.8 min of capture: the runner's speed varies by ~1.6x, and the BASELINE 32 shots on the slow
  runner would already take ~27 of the 30 minutes.
- 2026-10-09T16:25:13Z R2 (fit the cap without dropping a shot). The plan-sheet shots draw fixtures from the
  -screen rehearsal, never a tile or a network call, so they do not need the map's 15 s settle (the comment's own
  reason: "a cold first launch, the remote demo style, and its first tiles"). Each shot now waits WAIT, which is
  SETTLE (15) for every home/map/settings shot and PLAN_SETTLE (6) for the 18 plan shots (6 default light, 6 dark,
  6 AX5). Saving 9 s x 18 = 2.7 min against 6 added shots x ~(6 + 13 overhead) s = 1.9 min: the job is no longer than
  before T-0346 on any runner. Liveness is still checked after the wait and after the capture. Guard rows raised by
  name: "T-0346: no settle before a plan-sheet capture", "T-0346: the plan shots wait the map settle (the 30-minute
  cap)", "T-0346: the wait chosen per shot but never slept". Seen red then green:
  - RED: python ops/lib/check-ios-compile-guardrails.py <R1's ios-screenshot.yml at 9e8d2e98> -> "IOS-COMPILE-GUARDRAILS:
    workflow.jobs.simulator-screenshot.steps[4].run: differs from the pinned value (compared by equality)" rc=1
  - GREEN: python ops/lib/check-ios-compile-guardrails.py -> both "IOS-COMPILE-GUARDRAILS OK" lines, rc=0
  - --prove-red: the three new rows and R1's five each "[red rc=1]"; "PROVE-RED OK: 81 mutations red, 6 legitimate
    spellings green over 2 workflows, 0 unexpected result(s)" rc=0
  The cap's fragility on a slow runner is older than T-0346 and is not closed here (stillOpen).
- 2026-10-09T16:55:30Z MEASURE (AX5, the code on main) from ios-screenshot run 37959095574 (head a9f65c11, success:
  pre-capture 10.6 min, capture 16:37:08 -> 16:46:38 = 9.5 min for 38 shots, ~21 min in all), plan-*-ax5.png looked
  at side by side. The bottom bar does NOT grow with Dynamic Type (same capsule, same ~800-845 pt band as default);
  the plan content does:
  | card | at rest at AX5 | last control |
  | preview | ScrollView; the AttributionFooter inset grows to four lines (~640-880 of the 1000 px montage row, i.e. ~560-770 pt) and is TRANSLUCENT: the ETA, the estimate badge and the hazard line show through it and continue under the bar | "Choose another place" - below the fold, never on screen at rest |
  | nothingPretty | VStack, fits: the line (6 lines) and its one filled action | "Choose another place" (filled) at ~545-665 pt - above the bar |
  | offered | VStack, NOT a scroll view, so SwiftUI compresses it to fit: "Try 65 extra..." "All back roads: about 60 min,..." "Choose anot..." - all three labels TRUNCATED | "Choose anot..." at ~675 pt, above the bar but unreadable |
  | loop | List; "estimate - no" then "traffic data" drawn behind the bar | "Change the loop" - below the fold |
  | trip | List; the estimate line drawn behind the bar | "Change the trip" - below the fold |
  | saved | List; the second drive's name drawn behind the bar | "Delete" on the last row - below the fold |
  Attribution: present on the preview (its one map-like surface) at both sizes; the plan sheet is full height, no detent.
- 2026-10-09T16:55:30Z R3 (what "reachable above the bar" means here). A launch-and-shoot run cannot scroll, so the
  property a shot can prove is AT REST: a card's own way out (its last control) is on screen, above the bar, legible.
  Content that scrolls is reachable by scrolling; SwiftUI's scroll content inset already clears a bottom toolbar and
  a bottom safe-area inset, and that is NOT claimed from a shot. So the fix pins each card's last control, not its
  whole content.
- 2026-10-09T16:55:30Z R4 (the fix, no toolbar change). A new FeaturePlanSheet view PlanCardExit (a full-width,
  >= 44 pt, multi-line Button on the bar material) carries each card's last control in that card's
  .safeAreaInset(edge: .bottom), which SwiftUI lays out above the sheet's bottom bar at every text size and which
  adds the same height to the card's scroll content inset:
  - trip: "Change the trip" (trip.change) leaves the List for the inset.
  - loop: "Change the loop" (loop.change) leaves the List for the inset.
  - preview: "Choose another place" joins the AttributionFooter in the one bottom inset (the exit above the footer;
    the inset gets the bar material behind it, so the AX5 footer no longer shows content through it). The footer's
    construction stays one per file (check-map-attribution FOOTER_SET unchanged).
  - offered: its two filled offers move into a ScrollView with fixedSize(vertical) labels (no truncation), and
    "Choose another place" (plan.offer.action) moves to the inset.
  - nothingPretty: unchanged - one control, on screen and legible at both sizes as measured.
  - saved: unchanged - a list of the person's own drives has no card exit; its rows' last control is reachable by
    scrolling (R3), and pinning one row's Delete would be a redesign.
  - The trip and loop failure VStacks (no rehearsal shot) are not changed; their two lines and two buttons fit at AX5
    by the nothingPretty measurement's scale - not claimed, recorded.
  Digests: every touched file's row in ops/lib/check-safety-disclaimer-pinned is re-approved after reading its diff,
  and PlanCardExit.swift gets a new row.
