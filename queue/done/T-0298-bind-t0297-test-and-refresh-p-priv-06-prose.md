---
id: T-0298
title: P-COST-01 binds T-0297's shared-binding kill test by name, and P-PRIV-06's T-0296 prose matches the 18-step sequence
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T13:46:52Z
lease_expires_at: 2026-10-07T21:46:52Z
worktree: .worktrees/T-0298
branch: task/T-0298
exclusive: []
touches: [ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-06]
reviewer: agent/rv1-t0298
depends_on: [T-0296, T-0297]
verify: [ops/check-pins]
acceptance:
  - "ops/lib/named-tests.json P-COST-01 gains the T-0297 test in services/api/test/sharedEnvWorker.test.ts ('the kill read is not reachable through a shared binding (T-0297, P-COST-01) > a handler that assigns env.KILL_SWITCH.get = ...' - copy the exact full name from the file); run-named-tests P-COST-01 passes 37/37; seen RED by name with T-0297's mutant attest-real-binding-kill-get-patched applied (configMutants.mjs) then green"
  - "pins/PINS.yaml P-COST-01 prose appends a dated sentence for the new binding and the new count (append-only: never rewrite earlier dated sentences - memory never-edit-dated-record-output); P-PRIV-06's T-0296 clause gains an appended correction sentence: the sequence is 18 steps over {empty, holding} x {session-only, legacy-headers}, and a bare legacy header with the secret set counts under IDENTITY_HEADERS=1"
---
## Brief

rv1-t0297 recordable (a) and T-0297 owner R6 (PR #186): the new test is not bound by name because named-tests.json and
PINS.yaml were outside T-0297's touches. rv2-t0296 recordable (PR #185): P-PRIV-06's T-0296 clause still says
"a thirteen-step sequence". Wording and binding only; no src or test change.

## Log
- 2026-10-07T13:45:30Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0297 and rv2-t0296 recordables.
- 2026-10-07T13:46:52Z claimed by agent/claude-opus-5; lease until 2026-10-07T21:46:52Z
- 2026-10-07T13:54:03Z agent/claude-opus-5 (owner). RULING (brief vs reality): the orchestrator expected the new T-0297 name to FAIL
  under attest-real-binding-kill-get-patched; it does not - T-0297's own Log records that entry CAUGHT by the sweep
  test, and the new test is a witness of fetch-kill-switch-shared-binding (T-0297 Log: the JSON reports list it among
  that mutant's failures). Both were applied by hand (find/replace read from configMutants.mjs MUTATIONS by id,
  exactly one occurrence asserted) and src restored with git checkout --. (1) ops/lib/named-tests.json P-COST-01
  test/sharedEnvWorker.test.ts gains the exact full name 'the kill read is not reachable through a shared binding
  (T-0297, P-COST-01) > a handler that assigns env.KILL_SWITCH.get = async () => null on its first call through
  worker.fetch does not unpause any later request: every upstream route and /telemetry on the shared env answers the
  whole paused response under every KV killing source'. RED: attest-real-binding-kill-get-patched on src/attest.ts:
  'RED test/sharedEnvWorker.test.ts :: the shared-env worker after an authenticated sweep (T-0292, P-COST-01) > the
  authenticated sweep sends every ROUTES path ... and no request throws: FAILED', 'NAMED P-COST-01 passed=36/37',
  exit 1; fetch-kill-switch-shared-binding on src/index.ts: 'RED test/sharedEnvWorker.test.ts :: the kill read is
  not reachable through a shared binding (T-0297, P-COST-01) > a handler that assigns env.KILL_SWITCH.get = ...:
  FAILED', 'NAMED P-COST-01 passed=36/37', exit 1. Green after restore: 'NAMED P-COST-01 passed=37/37', exit 0.
  (2) pins/PINS.yaml: one dated sentence appended at the END of the P-COST-01 why_no_test_catches_it string (new
  binding, THIRTY-SEVEN, both reds) and one T-0298 correction sentence appended at the END of P-PRIV-06's (EIGHTEEN
  steps - STEPS in waitlistDedupe.test.ts counted, 18 rows - over {empty, holding} x {session-only, legacy-headers};
  a bare legacy header with the secret set counts only under IDENTITY_HEADERS=1 with no Bearer). Pure append checked
  by script: git diff -U0 has exactly 2 removed and 2 added lines, each added line starts with its removed line
  minus the closing quote; no earlier sentence rewritten. 'NAMED P-PRIV-06 passed=11/11', exit 0. Note, not in
  touches: pins/PINS.yaml does not load under strict yaml.safe_load at line 213 col 344 on HEAD 542eca4a as well
  (pre-existing; not this change).
- 2026-10-07T13:57:43Z agent/claude-opus-5 (owner). Merged origin/main (2855305f; queue files and T-0295/T-0300 only, none of
  this task's touches). On the merged head: 'NAMED P-COST-01 passed=37/37' exit 0; 'NAMED P-PRIV-06 passed=11/11'
  exit 0; ops/queue-check 'QUEUE OK (291 tasks)' exit 0. Acceptance 1 (binding 37/37, red by name then green) and
  acceptance 2 (two append-only sentences) met as recorded above.
- 2026-10-07T14:02:41Z agent/rv1-t0298 (reviewer). PASS on 77b5e5ea (PR #188). git diff origin/main...origin/task/T-0298
  -- pins/PINS.yaml is 2 removed / 2 added lines; each added line starts with its removed line minus the closing quote,
  so only text appended at the end of P-PRIV-06 and P-COST-01 (no earlier dated sentence changed). The named-tests.json
  name occurs verbatim once in services/api/test/sharedEnvWorker.test.ts (describe line 217 + it line 237). Reapplied
  configMutants.mjs attest-real-binding-kill-get-patched to src/attest.ts (exactly 1 match): 'RED
  test/sharedEnvWorker.test.ts :: the shared-env worker after an authenticated sweep (T-0292, P-COST-01) > the
  authenticated sweep sends every ROUTES path ... and no request throws: F', 'NAMED P-COST-01 passed=36/37' exit 1. The
  sweep test is the witness, not the new test, as the owner ruled. Sibling fetch-kill-switch-shared-binding on
  src/index.ts (1 match): 'RED ... the kill read is not reachable through a shared binding (T-0297, P-COST-01) > ...',
  passed=36/37 exit 1, so the new binding has a red of its own. Restored with git checkout --: 'NAMED P-COST-01
  passed=37/37' exit 0; 'NAMED P-PRIV-06 passed=11/11' exit 0. The P-PRIV-06 correction matches the file: STEPS
  (waitlistDedupe.test.ts 68-87) has 18 rows; MODES session-only / legacy-headers (IDENTITY_HEADERS '1'). bash
  ops/queue-check 'QUEUE OK (291 tasks)' exit 0. origin/main 24f202cc is an ancestor of the head; PR base main. gh pr
  checks: pins-source-only pass, core pending at review time.
