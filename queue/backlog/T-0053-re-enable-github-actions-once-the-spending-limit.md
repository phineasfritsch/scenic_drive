---
id: T-0053
title: re-enable GitHub Actions once the spending limit is raised
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.github/, queue/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**GitHub Actions is DISABLED for this repository right now.** `gh api repos/phineasfritsch/scenic_drive/
actions/permissions` returns `{"enabled": false}`. It was disabled deliberately on 2026-09-07 at the owner's
request, because the account's Actions spending limit was exhausted: every push produced a run that failed
instantly with "The job was not started because recent account payments have failed or your spending limit
needs to be increased", and each failure sent the owner an email. Nothing was wrong with the workflows.

This is recorded as a task rather than left as a setting somebody stumbles on later, because a repository
whose CI is off looks exactly like a repository whose CI is passing if you only read the PR list. Eighteen
open PRs were already unmergeable before this - `ops/merge` refuses a PR whose checks have not all concluded
successfully, and it also refuses a PR with NO checks at all, so disabling Actions does not make anything
mergeable that was not already stuck. It only stops the noise.

To restore, after raising the spending limit at github.com/settings/billing:

    gh api -X PUT repos/phineasfritsch/scenic_drive/actions/permissions -F enabled=true

Note `-F`, not `-f`: `-f` sends the string "false" and the API rejects it with
`For 'properties/enabled', "false" is not a boolean`.

Then verify, in this order, and do not call it done before all three:
- `gh api repos/phineasfritsch/scenic_drive/actions/permissions` reports `"enabled": true`
- a push to a throwaway branch produces a run that actually EXECUTES - `gh run view <id>` showing a real job
  log, not an annotation about billing
- `linux-core` concludes success on `main`, which it has not done since ~15:11 UTC on 2026-09-07

Until all three hold, every "verified locally" note in the task logs from that window stays exactly that:
local. Several tasks in `queue/done/` were signed off on local runs alone and say so.

## Log
- 2026-09-07 filed by agent/claude-opus-5 immediately after disabling Actions, so the setting is not silently
  carried. The disable is reversible and affects no repository content.
