---
id: T-0021
title: ops/merge --wait should poll through total=0 / mergeState=UNKNOWN (dogfooding finding)
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T10:08:39Z
lease_expires_at: 2026-09-07T13:08:39Z
worktree: ../wt/T-0021
branch: task/T-0021
exclusive: []
touches: [ops/merge, ops/lib/gh-stub-for-merge-tests]
pins_affected: []
reviewer: agent/reviewer-11
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
- 2026-09-07T10:08:39Z claimed by agent/claude-opus-5; lease until 2026-09-07T13:08:39Z
- 2026-09-07T13:00:00Z THE BUG, observed on ops/merge's own PR #10: seconds after a push GitHub has not registered the check runs (total=0) and has not computed mergeability (mergeStateStatus=UNKNOWN). --wait polled only on pending>0, so it fell straight through both and refused. The gate refused its own PR for a reason that would resolve itself in 20 seconds.
- 2026-09-07T13:00:00Z FIX: --wait now polls while pending>0 OR total==0 OR state==UNKNOWN, with distinct refusal messages per case once the cap is reached. Waiting must never become merging: a PR that genuinely never runs CI still refuses after 40 attempts.
- 2026-09-07T13:00:00Z Demos use ops/lib/gh-stub-for-merge-tests, a deterministic stand-in for `gh`, because racing real GitHub timing is flaky - on the first live attempt the checks registered before I could probe, so the transient path was unreachable by hand.
- 2026-09-07T13:00:00Z RED C (total=0, no --wait): "checks total=0 pending=0 ... mergeState=CLEAN" -> "MERGE REFUSED: no checks reported at all", exit 1.
- 2026-09-07T13:00:00Z RED D (state=UNKNOWN, checks green, no --wait): -> "MERGE REFUSED: GitHub has not computed mergeability yet (mergeStateStatus=UNKNOWN)", exit 1. Under the old code this printed the misleading "no checks reported" instead.
- 2026-09-07T13:00:00Z GREEN (--wait): stub returns UNKNOWN/total=0 on the first call and green after -> polls once, then "DRY RUN: every gate passed", exit 0.
- 2026-09-07T13:00:00Z SELF-CAUGHT, my own bug in the new code: the "waited Ns" suffix used ${wait:+...}, which tests for NON-EMPTY - and wait=0 is non-empty - so every refusal claimed it had waited. Fixed to test the value.
- 2026-09-07T13:00:00Z SELF-CAUGHT, harness bug that looked like a product bug: the stub's default rollup was written as ${STUB_ROLLUP:-[{"name":...},{...}]}, and bash BRACE-EXPANDS {a,b} inside the default, shredding the JSON into words. ops/merge was parsing correctly all along. Cost one debugging round; the stub now assigns the default with an if, and the reason is a comment in the file.
- 2026-09-07T13:00:00Z moved to review/, reviewer agent/reviewer-11
