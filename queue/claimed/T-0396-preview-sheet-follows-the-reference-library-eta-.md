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
