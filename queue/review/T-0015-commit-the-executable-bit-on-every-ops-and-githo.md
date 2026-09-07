---
id: T-0015
title: Commit the executable bit on every ops/* and .githooks/* script (git mode 100755)
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T04:57:13Z
lease_expires_at: 2026-09-07T07:57:13Z
worktree: ../wt/T-0015
branch: task/T-0015
exclusive: []
touches: [ops/, .githooks/, pins/PINS.yaml, CLAUDE.md]
pins_affected: []
reviewer: agent/reviewer-3
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Every file in ops/ and .githooks/ was committed 100644 because core.filemode is false on the Windows checkout
this repo is driven from. CI stayed green because the workflow invokes them as `bash ops/x`, but queue/README.md
tells agents to run `ops/agent-preflight && ops/queue-sweep && ops/queue-check` directly, and Xcode Cloud requires
ci_scripts to be executable (that instance was fixed in T-0007; this is the repo-wide rest).

Fix: `git update-index --chmod=+x` on all 18 scripts, plus pin P-OPS-01 so it cannot silently regress - the exec
bit is invisible to every other check we have. ops/api-url and ops/lib/ro_cases.json are DATA and stay 100644.

## Log
- 2026-09-07T04:57:13Z claimed by agent/claude-opus-5; lease until 2026-09-07T07:57:13Z
- 2026-09-07T06:30:00Z GREEN: 18 scripts now git mode 100755 (ops/* incl. ops/lib/*.py, .githooks/*); ops/api-url and ops/lib/ro_cases.json correctly stay 100644 as data. Direct invocation now works: ./ops/queue-check -> QUEUE OK (16 tasks), ./ops/agent-preflight -> PREFLIGHT OK. ops/check-pins -> PINS ok=8 pending=4 failed=0.
- 2026-09-07T06:30:00Z RED: git update-index --chmod=-x ops/sane -> P-OPS-01 fails (PINS ok=7 failed=1). Restored, green again.
- 2026-09-07T06:30:00Z SELF-CAUGHT: my first pass made ops/api-url executable too. It is a data file (the deployed Worker URL, written by ops/deploy); reverted to 100644 and the pin asserts that specifically, so 'chmod +x everything' cannot satisfy it.
- 2026-09-07T06:30:00Z touches widened to pins/PINS.yaml and CLAUDE.md (the pin, and the note telling agents core.filemode is false here).
- 2026-09-07T06:30:00Z moved to review/, reviewer agent/reviewer-3
