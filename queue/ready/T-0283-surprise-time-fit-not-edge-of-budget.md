---
id: T-0283
title: Surprise picks stop clustering at the edge of the time budget - the time-fit term peaks inside the dial (measured over the bundled LA corpus), and scenic classes outrank cafes when quality is unknown
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, Tests/Fixtures/surprise/, ops/mutate/]
pins_affected: [P-PROD-02]
reviewer: null
depends_on: [T-0253, T-0273]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST: over the committed fallback corpus (apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite) with the T-0273 offline reach from Westwood at dials 30/60/90/120, quote the distribution of picked round-trip minutes / budget for seeds 0..99 and the class mix of the picks, BEFORE changing any weight (T-0273 stillOpen 5: picks land at the far edge, e.g. Calas Park at exactly 120)"
  - "RULE a time-fit term that peaks at a ruled fraction of the budget (e.g. 0.6-0.75) and a class prior (viewpoint/peak/waterfall/beach/trailhead/garden above park/museum/town above cafe) consistent with the owner's taste memory (winding back roads, scenery over the obvious; 'calm adventure'); re-measure and quote the new distribution; the Python oracle (Tests/Fixtures/surprise/model.py) and Swift agree on the whole permutation by full equality"
  - "P-PROD-02 reproducibility and >= 90% distinct still hold; existing filter tests unchanged; population entries for the new terms with a literal floor"
---
## Brief

T-0273 stillOpen 5: 'The pick tends to land at the far edge of the 120-min budget (Calas Park at exactly 120), because
every place has quality 50 and the selector's minutes/budget term wins.' A Surprise for someone with time to kill
should land comfortably inside it. Product taste: memory owner-route-intent.

## Log
- 2026-10-06T16:04:49Z filed by agent/claude-opus-5 (orchestrator) from T-0273's open item.
