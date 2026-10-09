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
acceptance: []
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
