---
id: T-0408
title: Home follows the reference library - full-width Plan field with the gear inside it, one single-line chip row of destinations, chips become stacked sheet rows at AX sizes, and the route option tiles become rows instead of 'good road' x3
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, Sources/ScenicKit/, Tests/, ops/lib/, ops/mutate/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-ATTR-01, P-SAFE-03, P-A11Y-01]
reviewer: null
depends_on: [T-0397, T-0405]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The reference library is at `C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md`.
This task covers its section "Home" and "Biggest changes" 3 and 5. Today's shot, `.artifacts/shots-39066945425/ios-screenshots-ax5/home-ax5-medium.png`
(from T-0404's run), shows these problems:
- Chip labels break mid-word at AX5 ("West-wood", "Peninsu-la").
- Three route tiles each say "good road".
- The road list is cut off at the bottom of the sheet.
- The gear and the Surprise button sit in the chip row.

Scope (FeatureScenicHome, the home screen and its sheet):
1. "Plan a drive" becomes a full-width 48pt capsule with a leading glyph. The gear is a trailing 44pt circle inside the
   same bar (Google Maps #001, Apple Maps #000).
2. Below it, ONE chip row of saved or curated drives: destinations only, single line, ellipsis truncation, horizontal
   scroll, 36pt chips with a 44pt hit area. Surprise leaves the chip row for a right-edge circle that rides the sheet
   top. Surprise is tonal, so the sheet's primary stays the only filled control.
3. AX1+: the chip row is hidden from the map. The same drives appear as stacked rows at the top of the sheet: name
   and "via <road>" on the left, the minutes delta as a right-aligned .title2 numeral over a .caption "min" (Transit
   #016). No word may hyphenate.
4. The Fastest / +13 / +18 tile row with "good road" x3 becomes option rows: "+18 min" with "via <roads>", and the
   estimate caption when unlearned. Use only data the sheet already holds. Callouts on the map are OUT of scope;
   file them as a follow-up.
5. The disclaimer line stays directly under the primary at every detent (P-SAFE-03). Attribution stays on the sheet
   edge at every detent (P-ATTR-01). Every new or changed Swift file gets its check-file-scope block (T-0406).

Demonstration: dispatch ios-compile and ios-screenshot. Look at the home shots: light, dark, ax5 collapsed and
medium. Record item by item what each shot shows. Show any new or changed guard red, then green. Run the full pin set
and check-mutate-anchors before buying review.

## Log
- 2026-10-18 filed by agent/claude-opus-5 from the reference library pass 2 and T-0404's ax5 shot.
