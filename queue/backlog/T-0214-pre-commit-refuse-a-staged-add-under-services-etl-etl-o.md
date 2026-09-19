---
id: T-0214
title: pre-commit - refuse a staged ADD under services/etl/etl/ or Sources/ that no population declares and no allowlist entry names, so P-PROC-06 is decided at the first commit and not at merge
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: [T-0186]
verify: [ops/test, ops/check-pins]
acceptance:
  - ".githooks/pre-commit calls the gate's added-module arm over the STAGED adds (no merge base needed at commit time) and refuses by name; RED first in a throwaway clone (a staged new module, no declaration), then green with an allowlist entry; the hook's own prove-red table gains the row; harness PR - two review rounds"
---
## Brief

From the 04:13 panel (CODE, grounded): P-PROC-06 runs only from PINS.yaml and CI, and its added-module question is
merge-base-relative, so it fired on PR #115 AFTER sign-off when main advanced under the branch. The hook already
reads the task's touches; a staged add is decidable hours earlier. One refusal so far - do not start this ahead of
the LA chain.

## Log
- 2026-09-19T11:43:44Z filed by agent/claude-fable-5-1 (04:13 panel; grounded 8 of 14 - only the grounded items applied). Not started; low priority.
