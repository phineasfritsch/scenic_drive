---
id: T-0432
title: The home sheet at medium is taller than the screen - DriveDetails runs off the bottom edge at the default text size, where HomeSheet does not scroll its details
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/HomeSheet.swift, ops/lib/, .github/workflows/ios-screenshot.yml, queue/]
pins_affected: [P-SAFE-03, P-ATTR-01, P-A11Y-01]
reviewer: null
depends_on: [T-0408]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Measured in T-0408 round 2 from ios-screenshot 39137239496 (task/T-0408 at 1ef8b9d1), home-light-medium.png: the
medium sheet holds the summary (title, the option's meta line, the button, the conditions line), the option rows,
the estimate caption and DriveDetails' road paragraph and caption. Together they are taller than the space under
the credit, so the screen's VStack compresses every compressible Text and the rest leaves by the bottom edge
("About 10 miles as the crow flies, pin to pin. The roads" is cut at the screen edge). HomeSheet.swift scrolls the
details only when `typeSize > .large`; at the default size they are laid out unbounded. T-0408 round 2 stopped the
via lines from being the ones cut (fixedSize) but did not bound the sheet.

Scope: HomeSheet's medium details scroll at every type size inside a bounded height, so nothing in the sheet is cut
or leaves the screen, while the summary (the button and the conditions line directly under it, P-SAFE-03) stays
outside the scroll and the credit stays on the sheet edge (P-ATTR-01). HomeSheet.swift is a frozen block
(check-safety-disclaimer-frozen FROZEN_HOME_SHEET) and sha256-pinned: the approved list is edited in the same
commit. Demonstration: ios-screenshot home-light-medium, home-dark-medium, home-ax5-medium looked at, the bottom of
the details reachable by scroll and nothing cut at the screen edge.

## Log
- 2026-10-18 filed by agent/claude-opus-5 from T-0408 round 2 (rv1-t-0408 B2's measured cause).
