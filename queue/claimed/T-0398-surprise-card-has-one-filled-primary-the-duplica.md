---
id: T-0398
title: Surprise card has one filled primary - the duplicate Open in Apple Maps goes, secondary actions become tonal or text, and the hand-off button carries the external-link glyph
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T15:13:51Z
lease_expires_at: 2026-10-18T15:13:51Z
worktree: .worktrees/T-0398
branch: task/T-0398
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureSurpriseMe/, Sources/ScenicKit/, Tests/, ops/lib/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-A11Y-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The owner asked for the app's UI to lean on a reference library built from real shipping apps. The library lives
outside git at `C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md`
(section "Surprise card", "Global rules" -> Button hierarchy); reference screens under
`.artifacts/mobbin/screens/<app>/NNN.png`. Today's shot: `.artifacts/shots-39035404874/ios-screenshots/` (the
`-screen surprise` shots, run 39035404874). "Biggest changes" 2: the Surprise state shows TWO "Open in Apple Maps".

Scope (FeatureSurpriseMe; if the second button is drawn by a FeatureScenicHome file, say so in the Log and either
widen touches by a ruling or file the follow-up - do not edit outside touches):
1. Exactly one filled primary on the Surprise card; the duplicate hand-off goes.
2. Secondary actions (loop, not-this) become tonal or text per the library's button hierarchy.
3. The hand-off button ("Open in Apple Maps") carries a trailing arrow.up.right glyph - the user leaves the app.
4. The card follows the library's recommended order (hook, round trip + return leg, golden-hour line) using only
   data the card already has.
Keep: attribution adjacent to off-map results (P-ATTR-03), the four not-this reasons, round-trip time shown.

Demonstration: dispatch ios-compile and ios-screenshot on the task branch; quote both run ids; look at the surprise
shots (light, dark, ax5 if present) and state, item by item, what each shows. Any new or changed guard is shown red
then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the reference library pass 2 ("Biggest changes" 2).
- 2026-10-17T15:13:51Z claimed by agent/claude-opus-5; lease until 2026-10-18T15:13:51Z
- 2026-10-17T15:28:41Z agent/claude-opus-5 (author rule, before code). Read: the Brief, CLAUDE.md, library "Surprise
  card" + "Global rules -> Button hierarchy", today's surprise-light.png / surprise-dark.png (run 39035404874; there is
  NO surprise-ax5 shot - the ax5 LIST omits surprise). Rulings on every disagreement:
  R1 The duplicate "Open in Apple Maps" is NOT drawn by FeatureSurpriseMe. The Surprise card holds exactly one filled
     button (`surprise.openInAppleMaps`); the second one in the shot is the home sheet's GatedHandoffButton
     (FeatureScenicHome/GatedHandoffButton.swift, Copy.label "Open in Apple Maps") for the selected drive (Saddle
     Peak) underneath. FeatureScenicHome is outside touches AND inside claimed T-0397's touches, so touches are NOT
     widened: the follow-up is filed as T-0399 (the home sheet's hand-off steps back while the Surprise card shows).
     This task's acceptance therefore binds "exactly one filled primary" to the Surprise CARD, and records the second
     button in the full screen as known and filed (A4), not as fixed.
  R2 "Secondary actions (loop, not-this)": the card has no loop action - grep of FeatureSurpriseMe finds none; loop
     lives in FeaturePlanSheet (T-0396's touches). Only the four not-this reasons are restyled.
  R3 Tonal vs text for not-this: TONAL capsules (pale fill of DesignTokens.primary at 14 %, no outline), 44 pt min.
     Library says "accent label"; ruled `fg` label instead: #EA580C on white is ~3.6:1, below 4.5:1 at subheadline
     size. No tonal token exists in DesignSystem and DesignSystem is outside touches, so the tonal fill is derived
     from the semantic primary token. The library's "one 'Not this one' capsule + reason sheet" is RULED OUT: the
     Brief keeps the four reasons one tap away, and a sheet adds a tap and a presentation.
  R4 Hand-off glyph: trailing `arrow.up.right`, accessibilityHidden (VoiceOver reads "Open in Apple Maps" once);
     the primary becomes a 50 pt capsule per the button hierarchy. The gated call `onOpenInMaps(candidate.coordinate)`
     stays byte-identical (check-safety-disclaimer-mutations row "the Surprise card opens Apple Maps itself" seds it).
  R5 Order (hook, round trip + return leg, golden hour): the code already orders class, name, hook, round trip,
     golden hour, failure, primary, not-this. SurpriseReason carries hook, roundTripMinutes and goldenHourLine only -
     there is NO separate return-leg datum, so "return leg" is ruled to be the origin the round trip returns to:
     the round trip becomes a stat (label "Round trip from Westwood" .footnote over value "About 84 min" .headline),
     with the estimate tag ON the value line (beside it, or under it via ViewThatFits at AX sizes) - fixes the
     library's clutter row "wraps to two lines with the estimate pill wedged inline". Golden hour stays a glyph row
     (.subheadline) shown only when goldenHourLine is non-nil; a gray "unknown" golden-hour tile is ruled out - nil
     means sunset is outside the visit, not unknown. Hook goes .subheadline -> .body, class .caption -> .footnote
     (library type notes). The two-tile strip, hero, heart/Save, hours/weather rows and the clearable reason chip
     need data or features the card does not have - out of scope.
  R6 The library's "Conditions change. Verify locally." under the Surprise primary is RULED OUT here: not in the
     Brief's scope, and the disclaimer copy is frozen by check-safety-disclaimer; recorded under T-0399's Brief.
  R7 pins_affected lists P-A11Y-01, but `grep -n P-A11Y-01 pins/PINS.yaml` finds no such pin: nothing to change.
  R8 Keeps: attribution adjacent to off-map results (P-ATTR-03) is drawn by the home, untouched; four reasons kept;
     round-trip minutes shown; the estimate badge stays on the round trip (no learned samples on the card).
  R9 ax5: add `surprise` to the ax5 LIST in ios-screenshot.yml and its pinned twin ops/lib/ios_screenshot_pinned.py
     (lines 72 + 184). Changed guard shown RED then GREEN: workflow edited alone ->
     `IOS-COMPILE-GUARDRAILS: workflow.jobs.simulator-screenshot.steps[4].run: differs from the pinned value`,
     `IOS-COMPILE-GUARDRAILS FAIL: 1 guardrail(s) gone in ios-screenshot.yml`, exit=1; pinned data updated ->
     `IOS-COMPILE-GUARDRAILS OK: ios-screenshot.yml equals the pinned workflow ...`, exit=0.
  Acceptance (each can fail):
  A1 shot surprise-light/-dark/-ax5: the Surprise CARD shows exactly one filled button, "Open in Apple Maps" with a
     trailing arrow.up.right glyph, unclipped.
  A2 shot (same three): the four reasons render as tonal capsules (pale fill, no outline), all four labels whole.
  A3 shot (same three): card order class, name, hook, "Round trip from Westwood" over "About N min" + estimate tag,
     [golden hour row when present], primary, "Not this one?" + reasons; nothing overlaps.
  A4 shot: the home sheet's own "Open in Apple Maps" below the card is still present (R1) - recorded, filed T-0399.
  A5 `bash ops/lib/check-safety-disclaimer` exits 0 (digests re-approved for SurpriseCard.swift, SurpriseNotThis.swift).
  A6 `grep -c 'onOpenInMaps(candidate.coordinate)' .../FeatureSurpriseMe/SurpriseCard.swift` prints 1.
  A7 `wc -l` SurpriseCard.swift <= 300 and SurpriseNotThis.swift <= 300.
  A8 `python ops/lib/check-ios-compile-guardrails.py` exits 0 with ios-screenshot.yml OK.
  A9 bare gates exit 0: check-mutate-population.py, check-mutate-only.py, check-pins-yaml.py, check-exec-bits,
     queue-check.
  A10 ios-compile run on task/T-0398 concludes success; ios-screenshot run concludes success and holds
     surprise-ax5.png.
- 2026-10-17T16:08:01Z agent/claude-opus-5: code a55f2d2f. Digest guard RED then GREEN: with the Swift edits and the old
  rows, `bash ops/lib/check-safety-disclaimer` printed `P-SAFE-03: the pinned render surface changed: SurpriseCard.swift
  content changed (sha256 ce4fa2fc..., approved 671c8124...)` and `SurpriseNotThis.swift content changed (sha256
  77e50a48..., approved 05e8115a...)`; rows re-approved in ops/lib/check-safety-disclaimer-pinned (4 lines) -> exit=0.
  ios-compile run 39046312312: completed success (2m56s). ios-screenshot run 39046317171: completed success (19m9s),
  holds surprise-light.png, surprise-dark.png and the new surprise-ax5.png (downloaded to
  .artifacts/shots-39046317171/ios-screenshots/). Looked at each:
  surprise-light: card = mountain glyph + "Peak" (footnote), "Tongva Peak", hook "A high point with the basin
    below." (body), clock glyph + "Round trip from Westwood" (gray footnote) over "About 84 min" (headline) with the
    outlined "estimate · no traffic data" tag beside it on one line; ONE filled orange capsule "Open in Apple Maps"
    with a trailing arrow.up.right; "Not this one?" over four pale-orange tonal capsules, no outlines, labels whole
    (Too far / Not my thing / Been there / Wrong time). No golden-hour row (goldenHourLine nil at shot time - absent,
    not hidden). Nothing clipped or overlapping on the card. Below the card, the home sheet's own filled "Open in
    Apple Maps" for Saddle Peak is still there (R1 -> T-0399). Attribution box visible over the map.
  surprise-dark: same order and content; primary is the light-orange capsule with dark label + arrow; the tonal
    capsules are a dark brown-tinted fill with white labels, readable; estimate tag outlined; nothing clipped. Home
    sheet's second "Open in Apple Maps" still present (T-0399).
  surprise-ax5: the CARD renders whole - class, name, hook on one line, "Round trip from Westwood", "About 84 min" with
    the estimate tag moved UNDER it (ViewThatFits fallback), the primary capsule "Open in Apple Maps ↗" on one line,
    four tonal capsules with whole labels. OUTSIDE the card the home squeezes: drive chips clip vertically
    ("West-wood loop", "SF Peninsu-la" cut), the collapsed sheet's route tiles overflow their borders, the sheet's
    hand-off is pushed off-screen, the attribution box overlaps the map's (i) button. home-ax5-collapsed (run
    39035404874, no card) has none of it. Those views are FeatureScenicHome (outside touches, T-0397's touches);
    not fixed here - recorded as scope item 4 in T-0399. No re-run: no element inside touches is clipped,
    overlapping or missing.
