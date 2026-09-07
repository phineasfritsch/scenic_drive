---
id: T-0006
title: ops/sane: exit codes 2 (dirty/CRLF), 3 (deployed != HEAD), 7 (backend down), 9 (legal URLs)
state: claimed
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: 2026-09-07T03:58:22Z
lease_expires_at: 2026-09-07T07:58:22Z
worktree: ../wt/T-0006
branch: task/T-0006
exclusive: []
touches: [ops/sane]
pins_affected: []
reviewer: null
depends_on: [T-0005]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "bash ops/sane --prod -> exit 0 with one line per check"
  - "RED 2: an untracked .swift file under Sources/ -> exit 2"
  - "RED 3: deploy an older SHA then run -> exit 3"
  - "RED 7: point API at a dead URL -> exit 7"
---
## Brief

Never mutates. Checks 4/5/8 (corpus, goldens, manifests) are added by the ETL tasks in M2.

## Log
- 2026-09-07T03:58:22Z claimed by agent/claude-opus-5; lease until 2026-09-07T07:58:22Z
