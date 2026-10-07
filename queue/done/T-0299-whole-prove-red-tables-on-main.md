---
id: T-0299
title: Run both P-SAFE-03 / P-ATTR-01 prove-red tables whole on main and quote the N/N lines and both bare-guard times
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T19:11:23Z
lease_expires_at: 2026-10-08T01:11:23Z
worktree: .worktrees/T-0299
branch: task/T-0299
exclusive: []
touches: [queue/]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: agent/rv2-t0299
depends_on: [T-0295]
verify: [ops/check-pins]
acceptance:
  - "On main after T-0295, with the box otherwise idle: 'bash ops/lib/check-safety-disclaimer --prove-red' prints 'prove-red: 52/52 mutations refused by name' (or the table's current row count) and 'bash ops/lib/check-map-attribution --prove-red' prints 'prove-red: 46/46 ...'; both bare guards exit 0 with wall times quoted; every line quoted in the task Log"
  - "Any row not refused by name is a finding filed as its own task (no code change in this task)"
---
## Brief

rv2-t0295 recordable (PR #184): neither table has one whole-table summary line since T-0295 - the safety table's rows 1-49
ran whole and died at row 50 when the table was rewritten mid-run; rows 50-52 and the map table's 46th row ran one-row.
A measurement task, no code.

## Log
- 2026-10-07T13:52:22Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0295's recordable.
- 2026-10-07T19:11:23Z claimed by agent/claude-opus-5; lease until 2026-10-08T01:11:23Z
- 2026-10-07T19:26:36Z measured by agent/claude-opus-5 (owner) on head 2aa59b97 (main after T-0295 PR #184 and T-0303 PR #193), the four
  stages run one after another (logs in the main checkout's .worktrees/T-0299-logs/, gitignored), stage starts
  19:12:08Z / 19:12:21Z / 19:12:42Z / 19:17:58Z, done 19:25:01Z. Two other agents' worktrees (T-0305, T-0306) existed and
  may have been building at the same time, so the wall times are upper bounds, not idle-box times.
  - 'time bash ops/lib/check-safety-disclaimer': EXIT=0, real 0m12.674s
  - 'time bash ops/lib/check-map-attribution': EXIT=0, real 0m20.800s
  - 'time bash ops/lib/check-safety-disclaimer --prove-red': "prove-red: 60/60 mutations refused by name", EXIT=0, real 5m15.894s
  - 'time bash ops/lib/check-map-attribution --prove-red': "prove-red: 47/47 mutations refused by name", EXIT=0, real 7m2.915s
  Every row refused by name; no row UNREFUSED or UNNAMED, so no follow-up task is filed (acceptance 2).
- 2026-10-07T19:34:26Z review PASS (round 2) by agent/rv2-t0299 (not the owner), PR #194 at 5dfddfda. Round 1
  (agent/rv1-t0299) failed only because the owner had committed nothing yet; that is now closed by the 19:26:36Z entry.
  - 'git diff origin/main...origin/task/T-0299 --stat': 1 file, queue/claimed/T-0299-whole-prove-red-tables-on-main.md, 9 insertions.
  - Re-run in a detached worktree at origin/task/T-0299: 'bash ops/lib/check-map-attribution --prove-red' printed
    "prove-red: 47/47 mutations refused by name", exit=0, 242 s wall; no UNREFUSED or UNNAMED row. Matches the owner's quote.
  - Owner logs .worktrees/T-0299-logs/: safe-red.log "prove-red: 60/60 mutations refused by name" real 5m15.894s EXIT=0;
    map-red.log "prove-red: 47/47 mutations refused by name" real 7m2.915s EXIT=0; safe-bare.log real 0m12.674s EXIT=0;
    map-bare.log real 0m20.800s EXIT=0; meta.txt head 2aa59b97. Every quoted line in the Log matches the logs.
  - Acceptance 1 names 52/52 and 46/46 "or the table's current row count"; the current counts are 60 and 47, ruled as satisfying it.
  - 'bash ops/queue-check' bare: QUEUE OK (297 tasks), exit 0. 'git merge-base --is-ancestor origin/main origin/task/T-0299': exit 0.
  - 'gh pr checks 194': pins-source-only pass (2m19s); core still pending after one 300 s wait (recorded, not blocking: queue-only diff).
