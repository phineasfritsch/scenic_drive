---
id: T-0436
title: The home sheet's frozen closure walks identifiers, not the copy they read or the views injected as closures - a DriveCopy string of 60 newlines, or a view built into the chip band, moves the sheet off screen with no guard red
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, ops/lib/, ops/mutate/, pins/PINS.yaml, queue/]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0408]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Recorded as non-blocking by rv2-t-0408 (PR #302, on 86fb1f3e) and filed by T-0408's owner in round 3. T-0408
round 2 froze, WHOLE FILE, every View type the home sheet's roots mount (ops/lib/frozen_views.py over
ops/lib/check-safety-disclaimer-frozen-views.txt, run from -frozen's require_frozen_blocks), and refuses any
capitalised identifier on those lines that is neither a frozen view, an approved system name nor an approved
non-view. Two classes stay open:

- M1, copy. The closure approves non-view types such as DriveCopy by identifier only. Their string VALUES are not
  pinned: a DriveCopy member returning a string of 60 newlines (or any very tall text) is drawn by a frozen view
  line that never changed, and pushes the button, the conditions line and the credit off the screen. Every frozen
  line and digest stays green.
- M2, injected views. A view passed into the chip band (or any frozen root) as a closure or AnyView - a lowercase
  builder, as the app shell already does for SurpriseGateSlot's `surprise` card from FeatureSurpriseMe - is not a
  named type on a root line, so the closure never walks it. Its geometry is unguarded. T-0408 recorded the
  SurpriseGateSlot instance in -frozen's WHAT IT CANNOT SEE.

Scope: close both by a whitelist, fail closed (CLAUDE.md: a whitelist of approved sites, never a blacklist of bad
spellings). For M1, the approved non-view types' string-returning members the frozen views read are frozen whole
(their bodies, not only their declarations), or their values are bounded by a guard on the shipped symbol (a test
that calls the member the view calls and bounds its line count / length), whichever the filer measures as the
smaller closed set. For M2, every closure- or AnyView-typed parameter of a frozen view, and every argument passed
to one at a frozen site, is an approved whole line naming its builder, and that builder's view types join the
closure.

Acceptance (to be written by the claimant AFTER measuring the population: the approved non-view types the frozen
views read, their string members, and every closure/AnyView parameter of a frozen view - quote the counts here):
each class shown red on a copy (the 60-newline DriveCopy member; a tall view injected through the chip band's
closure), then green with the guard refusing it by name; both inside P-SAFE-03's and P-ATTR-01's assertions; a
mutation population under ops/mutate/ with a literal floor.
