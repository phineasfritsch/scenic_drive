---
id: T-0354
title: check-mutate-only's POSIX process-group tree kill is seen red then green on Linux CI, and PAIR_FLOOR is raised to the measured merged-head count
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-mutate-only.py, ops/lib/mutate_only_pairs.py]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: [T-0353]
verify: [ops/check-pins]
acceptance: []
---
## Brief

rv2-t0353 recordables (a) and (b), PR #239, filed per the two-round rule. (a) run_tree()/kill_tree() kill a timed-out
probe's whole tree: the Windows `taskkill /T /F` branch was seen red on HEAD's probe_once and green after, but the
POSIX branch (start_new_session + os.killpg SIGKILL) has never run - this box is Windows. Demonstrate it red/green
where it runs (a Linux CI job step or the swift:6.1-noble docker via WSL, no git in WSL) with the same
parent-plus-sleeping-grandchild demo. (b) PAIR_FLOOR = 192168 is the pre-merge measurement; the merged head counts
195379 pair tokens. Re-measure on today's head and set the literal floor to it.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0353 recordables (a), (b).
