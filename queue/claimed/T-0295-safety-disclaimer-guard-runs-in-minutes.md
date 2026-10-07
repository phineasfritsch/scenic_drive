---
id: T-0295
title: The P-SAFE-03 / P-ATTR-01 guards run in minutes on the Windows box, and the linked-tree pin lists tracked files so a Finder .DS_Store is not a false red
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T06:54:20Z
lease_expires_at: 2026-10-07T20:54:20Z
worktree: .worktrees/T-0295
branch: task/T-0295
exclusive: []
touches: [ops/lib/check-safety-disclaimer, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-linked, ops/lib/check-map-attribution, ops/lib/check-map-attribution-mutations, ops/lib/check-safety-disclaimer-mutations]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0289]
verify: [ops/check-pins]
acceptance:
  - "MEASURE FIRST: wall time of a bare 'bash ops/lib/check-safety-disclaimer' and 'bash ops/lib/check-map-attribution' on this box, alone, with a per-limb breakdown (rv1-t0289 measured ~72 min alone, 2.5 h with eight in parallel; CI pins-source-only takes ~2 min) - quote it and name the dominant limb before changing anything"
  - "Both guards finish under 10 minutes alone on this box with the same refusal set: the full --prove-red table refuses every row BY NAME exactly as before (quote the before and after summaries; any row whose printed reason changes is ruled)"
  - "-linked enumerates files via 'git ls-files' (tracked) plus untracked-but-not-ignored, so a .DS_Store ignored by .gitignore is not a refusal; a prove-red row shows an untracked, unignored file IS still refused by name"
---
## Brief

rv1-t0289 recordables (PR #179 sign-off): each full guard takes ~72 min alone on the Windows box (8944-9317 s under
load), which makes every review that touches apps/ios or Sources/ hours long; and -linked lists the working tree, so an
untracked .DS_Store on a Mac is a false red. Memory faster-verification-in-rounds.

## Log
- 2026-10-07T06:46:49Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0289's recordables on PR #179.
- 2026-10-07T06:54:20Z claimed by agent/claude-opus-5; lease until 2026-10-07T20:54:20Z
