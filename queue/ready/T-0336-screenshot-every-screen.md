---
id: T-0336
title: ios-screenshot shows every screen the owner will design against and the App Store will list - the route preview (with badge, explanation, hazard strip), the honest-failure card, Surprise, the loop preview, the road-trip itinerary, onboarding with the disclaimer, the Saved tab and Legal/Attribution - each a DEBUG `-screen` rehearsal over fixed sample data, light and dark
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, .github/workflows/ios-screenshot.yml, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-ATTR-01, P-SAFE-03, P-SAFE-07]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the shots ios-screenshot takes today (home x2 detents, settings, paywall, surprise, drive), how a `-screen <name>` DEBUG rehearsal is wired (T-0324 DriveRehearsal: the shell carries no `#` directive), which guard rows each new rehearsal raises (check-map-attribution, check-safety-disclaimer frozen/pinned, ios_screenshot_pinned.py, ios-compile-guardrails), and the sample data each screen shows - real LA place names from the corpus/curated seeds, never invented business names; the estimate badge visible on the preview"
  - "New shots, light and dark: preview, nothingPretty, surprise (if not already the card), loop, trip, onboarding, saved, legal - every map surface in them shows its attribution (P-ATTR-01 green, raised by name where a new surface appears), the preview shows the safety line (P-SAFE-03) and the estimate badge (P-SAFE-07); every rehearsal is DEBUG-only (a release build carries none - a guard row seen red then green)"
  - "ios-compile + ios-screenshot pass; the owner can open one artifact with every screen; the shots are looked at and quoted in the Log (what each shows, anything clipped or illegible filed as a follow-up, not fixed here)"
---
## Brief

Owner asked (2026-10-08) whether the UI needs design work and offered Claude Design; the answer was yes, before human
gate #1 and the M8 listing - but CI only shoots home, settings, paywall, surprise and drive, so most screens cannot be
seen without a Mac. This task makes every screen visible in one ios-screenshot artifact, so the owner can design
against the real current state. It changes no screen's design. Snapshot references are not recorded here (CLAUDE.md:
human-initiated only).

## Log
- 2026-10-09T05:06:37Z filed by agent/claude-opus-5 (orchestrator) for the owner's design pass and the M8 listing.
