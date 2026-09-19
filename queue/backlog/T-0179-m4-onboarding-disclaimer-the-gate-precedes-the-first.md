---
id: T-0179
title: M4 onboarding disclaimer - the gate precedes the first plan, the home-screen onBlocked sheet retires, one-tap accept proceeds, and P-SAFE-03 is rewritten around the route screen's SafetyDisclaimerDisplaying
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer, pins/PINS.yaml]
pins_affected: [P-SAFE-03]
reviewer: null
depends_on: [T-0153]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the disclaimer is shown in onboarding BEFORE any plan or route exists (plan 'Onboarding (vehicle, disclaimer)'), acknowledged once per install; accepting it PROCEEDS with what the user was doing (gate -> grant -> proceed, the platform pattern) - no dead second tap; the home-screen onBlocked sheet from T-0153 is removed"
  - "the route screen carries a visible SafetyDisclaimerDisplaying (CLAUDE.md invariant) and ops/lib/check-safety-disclaimer is rewritten around it: the sole-caller and sole-builder anchors move from ScenicHomeScreen to the route screen, --prove-red re-demonstrated red by name for every row, P-SAFE-03's why_no_test_catches_it updated"
  - "ios-compile dispatch green with the run id quoted; bash ops/lib/check-safety-disclaimer and --prove-red, bash ops/check-pins --source-only, bash ops/lib/check-line-cap bare at the final commit"
---
## Brief

From the 2026-09-18 18:13 panel (CODE F4, DRIVER ONE F2 and both drivers' recommendations, grounded). T-0153 hung
the disclaimer off the handoff button's `onBlocked` (ScenicHomeScreen.swift:84, .sheet :98): the drive's name and
every road on it are readable before any warning exists, and accepting returns the user to the same screen
where the same button must be tapped again - deliberate today (:26-28) and unrendered, but the shape is
backwards for M4 (plan:140/318 put the disclaimer in Onboarding; plan:244 P-SAFE-03 "blocks the first plan").
The one-tap accept was judged right on pattern and wrong on cost while the check pins a sole caller
(check-safety-disclaimer:176-180) - so it lands here, with the check, not as a T-0153 round. T-0153's R1 rules
the home; no M4 task carried this until now.

## Log
- 2026-09-19T00:57:37Z filed by agent/claude-fable-5-1 from the 18:13 panel's grounded synthesis. Not started; M4 scope.
