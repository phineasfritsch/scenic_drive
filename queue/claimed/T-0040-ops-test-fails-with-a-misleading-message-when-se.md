---
id: T-0040
title: ops/test fails with a misleading message when services/api/node_modules is absent
state: claimed
owner: agent/unknown
owner_session: null
claimed_at: 2026-09-07T20:55:20Z
lease_expires_at: 2026-09-07T22:55:20Z
worktree: null
branch: task/T-0040
exclusive: []
touches: [ops/test]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

On a fresh clone `ops/test` prints:

    FAIL: services/api exists but vitest produced no report

and exits 1. The actual cause is that `services/api/node_modules` does not exist, so `npx vitest` cannot run.
The message names the symptom the runner checks for, not the thing the operator has to do, and it reads exactly
like the "reporter was broken to make the suite green" failure it was written to catch. Found by
agent/reviewer-16 while reviewing T-0035, who correctly reproduced it on a clean `main` checkout and ruled it
out as a regression - but only after spending the time to do so.

CI does not hit this because `.github/workflows/linux-core.yml` runs `npm ci` first. Every human and every
agent on a new worktree does hit it, and each one has to rediscover why.

- Detect the missing install and say so: if `services/api/package.json` exists but `services/api/node_modules`
  does not, fail with the command to run (`cd services/api && npm ci`), not with a report-missing message.
- Keep the existing message for the case it was actually written for: deps installed, vitest ran, no report
  produced. Those are different failures and must not share a line.
- Demonstrate red: `mv services/api/node_modules /tmp/nm && bash ops/test` before and after the change.

Deliberately NOT in scope: having `ops/test` run `npm ci` itself. A test runner that mutates the tree to make
itself pass is the beginning of a runner that mutates the tree to make everything pass.

## Log
- 2026-09-07T20:55:20Z claimed by agent/unknown; lease until 2026-09-07T22:55:20Z
