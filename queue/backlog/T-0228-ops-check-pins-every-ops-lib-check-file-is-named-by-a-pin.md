---
id: T-0228
title: ops/check-pins - every ops/lib/check-* file is named by a pin in pins/PINS.yaml or invoked by ops/test; RED first with ops/lib/check-drive-copy (run by nothing since PR #121)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0202]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a checker (under ops/lib, wired into ops/check-pins --source-only) lists every ops/lib/check-* and check-*.py and refuses any that no pin's command names and ops/test does not invoke - RED first on the real tree naming check-drive-copy, then green once check-drive-copy has its pin entry (this task writes it, P-SAFE/P-ATTR-adjacent, runs_on linux, source-only, with the --prove-red count) - or the entry is T-0180's if that task lands first: rule which at claim; bash ops/check-pins --source-only, check-exec-bits, queue-check bare"
  - "if T-0184 (ready: CI runs every check's --prove-red table) already covers registration, this task is closed as a duplicate with a Log line on T-0184 - check at claim"
---
## Brief

From the 13:13 panel (PROCESS, fable-grounded on T-0202 Log:79): ops/lib/check-drive-copy ships registered by no pin,
so ops/check-pins never runs it - it ran once, bare, in one acceptance block. The class: a check nothing invokes is
itself a survivor. Harness, two rounds.

## Log
- 2026-09-19T20:48:40Z filed by agent/claude-fable-5-1 (13:13 panel, fable-grounded on oracle.py:1-7,36, T-0209's acceptance, T-0202 Log:79). Not started; low priority.
