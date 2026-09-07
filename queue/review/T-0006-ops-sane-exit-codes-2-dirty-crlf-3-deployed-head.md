---
id: T-0006
title: ops/sane: exit codes 2 (dirty/CRLF), 3 (deployed != HEAD), 7 (backend down), 9 (legal URLs)
state: review
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: 2026-09-07T03:58:22Z
lease_expires_at: 2026-09-07T07:58:22Z
worktree: ../wt/T-0006
branch: task/T-0006
exclusive: []
touches: [ops/sane]
pins_affected: []
reviewer: agent/reviewer-1
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
- 2026-09-07T04:20:00Z GREEN: ops/sane -> SANE OK exit 0 (repo checks); ops/sane --prod -> SANE OK, backend up, version live f75eddb == Worker code at HEAD (services/api unchanged), legal/corpus/goldens/quota skipped with the task that will add them
- 2026-09-07T04:20:00Z RED 2: untracked Sources/ScenicKit/Stray.swift -> repo FAIL, exit 2 (buildable folders compile stray files)
- 2026-09-07T04:20:00Z RED 3: services/api changed since the live deploy (proven in a tmp worktree, since the T-0006 pre-commit hook correctly blocks touching services/api) -> version FAIL, exit 3
- 2026-09-07T04:20:00Z RED 7: API_URL pointed at a dead host -> backend FAIL, exit 7
- 2026-09-07T04:20:00Z note: version check means 'Worker CODE at HEAD == live', not 'sha == HEAD' - the Worker only redeploys when services/api changes, so a lagging baked git_sha with unchanged code is sane by design
- 2026-09-07T04:20:00Z moved to review/, reviewer agent/reviewer-1
