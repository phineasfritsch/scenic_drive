---
id: T-0348
title: ios-screenshot never dies at its 30-minute cap on a slow runner - the shots split across parallel jobs (or the per-shot settle trimmed by measurement), each job well under its own cap, one artifact set the owner downloads
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.github/workflows/ios-screenshot.yml, ops/lib/, queue/]
pins_affected: [P-ATTR-01]
reviewer: null
depends_on: [T-0346]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0346 owner stillOpen 3 (PR #230): the screenshot job's 30-minute cap is fragile - the baseline 32 shots at ~31 s
each take ~27 min, T-0325's run took 26 min, and T-0346's 38-shot run 37954789863 was cancelled at the cap before
upload (R2 then cut the plan-sheet settle to 6 s; the 38-shot run now takes 17m55s-18m48s). Every new screen or text
size pushes it back toward the cap. MEASURE FIRST: per-shot wall time by kind (map vs plan fixture vs drive), runner
variance across the last ~10 runs, what the guard ops/lib/ios_screenshot_pinned.py pins (CAPTURE_RUN, the cap). Then
RULE (a matrix of jobs by pass - light/dark/AX5 - with one merged artifact, or measured settle times per kind) and
write the acceptance: every job's measured worst case under 60% of its cap, the pinned guard rows raised by name and
seen red then green, the owner's download unchanged in shape.

## Log
- 2026-10-09T18:39:48Z filed by agent/claude-opus-5 (orchestrator) from T-0346 stillOpen 3.
