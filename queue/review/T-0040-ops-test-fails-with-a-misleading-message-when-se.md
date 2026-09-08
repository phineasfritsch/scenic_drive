---
id: T-0040
title: ops/test fails with a misleading message when services/api/node_modules is absent
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T20:55:20Z
lease_expires_at: 2026-09-07T22:55:20Z
worktree: null
branch: task/T-0040
exclusive: []
touches: [ops/test]
pins_affected: []
reviewer: agent/reviewer-36
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

- 2026-09-07T23:05Z claimed and fixed by agent/claude-opus-5, stacked on task/T-0023, which owns ops/test.

  Two unrelated failures printed the same line. `produced no report` is written for the case this runner
  exists to catch - vitest RAN and its reporter wrote nothing, which is what a reporter broken to make the
  suite green looks like. An absent `npm ci` produces an identical symptom and is a different thing entirely:
  one command away, and hit by every fresh worktree precisely because CI never hits it (the workflow runs
  `npm ci` first). They are now separate messages and each says what to do rather than what was observed.

  A third case is now caught that the brief did not ask for, because looking at it turned it up: node_modules
  present but vitest not in it. Without a check, `npx` DOWNLOADS vitest from the registry and runs that - an
  unpinned version, and a suite whose result depends on the network. That is a worse outcome than either
  message, and it was reachable from any interrupted `npm ci`.

  RED then GREEN, all four states, real output:

      1. OLD ops/test, node_modules absent
         FAIL: services/api exists but vitest produced no report            exit=1
      2. NEW ops/test, node_modules absent
         FAIL: services/api/node_modules is absent - the Worker's dependencies were never installed here.
               Run: (cd services/api && npm ci)                             exit=1
      3. NEW ops/test after npm ci
         TESTS linux=86/76 ios=skipped failed=0 skipped=0 / OK
      4. NEW ops/test, node_modules present but vitest removed
         FAIL: services/api/node_modules exists but vitest is not in it - the install is incomplete.
               Run: (cd services/api && npm ci)                             exit=1

  **Then the check that mattered more: is the ORIGINAL message still reachable?** A guard that can no longer
  fire is worse than the confusing message it replaced, and I had just put two early exits in front of it.
  Stubbed vitest to run and write nothing:

      vitest present, runs, produces no report
      FAIL: services/api exists but vitest produced no report               exit=1

  It is alive. Worth recording HOW that went, because the first attempt at it reported the opposite: I
  replaced only `.bin/vitest`, the suite came back `TESTS linux=86/76 OK`, and it looked exactly like I had
  killed the guard. I had not - on Windows `npx` dispatches to `.bin/vitest.cmd`, so the real vitest ran and
  my stub was never touched. Stubbing all three shims (`vitest`, `.cmd`, `.ps1`) gives the real answer. A
  demonstration that quietly does not do what it claims is the same failure as a test that quietly does not
  assert what it claims, and it nearly went into this log as a finding.

  NOT DONE, per the brief: `ops/test` does not run `npm ci` itself. A test runner that mutates the tree to
  make itself pass is the beginning of a runner that mutates the tree to make everything pass.

  Verification: `ops/test` -> `TESTS linux=86/76 ios=skipped failed=0 skipped=0` / `OK`; `ops/check-pins` ->
  `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`; `ops/queue-check` -> `QUEUE OK`. The two
  demonstration scripts were deliberately not committed - they mutate node_modules and exist to be run once.
  GitHub Actions is still billing-blocked; this is local.

  **What to attack.** The vitest-binary check hard-codes `.bin/vitest` and `.bin/vitest.cmd` and does not
  look at `.ps1`, which is the shim my own demo needed - so an install with only the PowerShell shim would
  pass the check and then behave unpredictably. I judged that unreachable from `npm ci` and did not guard it;
  argue with that. Second: both new messages assume `npm ci` is the right command, which is true for this
  repo and would be wrong for a worktree deliberately using `npm install`.
