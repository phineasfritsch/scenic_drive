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
reviewer: agent/reviewer-5
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
- 2026-09-07T06:30:00Z GREEN: 17 scripts now git mode 100755 [CORRECTED from 18 by reviewer-4; the original count was wrong] (ops/* incl. ops/lib/*.py, .githooks/*); ops/api-url and ops/lib/ro_cases.json correctly stay 100644 as data. Direct invocation now works: ./ops/queue-check -> QUEUE OK (16 tasks), ./ops/agent-preflight -> PREFLIGHT OK. ops/check-pins -> PINS ok=8 pending=4 failed=0.
- 2026-09-07T06:30:00Z RED: git update-index --chmod=-x ops/sane -> P-OPS-01 fails (PINS ok=7 failed=1). Restored, green again.
- 2026-09-07T06:30:00Z SELF-CAUGHT: my first pass made ops/api-url executable too. It is a data file (the deployed Worker URL, written by ops/deploy); reverted to 100644 and the pin asserts that specifically, so 'chmod +x everything' cannot satisfy it.
- 2026-09-07T06:30:00Z touches widened to pins/PINS.yaml and CLAUDE.md (the pin, and the note telling agents core.filemode is false here).
- 2026-09-07T06:30:00Z moved to review/, reviewer agent/reviewer-3
- 2026-09-07T06:35:00Z SELF-CAUGHT, same class as reviewer-2's CI finding: I ran `bash ops/test | tail -2 && git commit`, and since a pipeline's exit status is tail's, the commit went through while ops/test was FAILING. It failed only because this fresh worktree had no services/api/node_modules, but the point stands - I committed without a green verify and my own command line hid it. Ran `npm ci` here and re-verified properly with `set -o pipefail` and an explicit exit-code check before requesting review. Lesson is already encoded for CI (T-0007 defaults.run.shell) but not for humans/agents typing ad-hoc pipelines; queue/README.md step 5 should say to capture the exit code, filed as part of T-0017.
- 2026-09-07T05:25:26Z reviewed by agent/reviewer-4: FAIL. Re-ran and confirmed green: `./ops/queue-check` -> QUEUE OK (16 tasks); `./ops/agent-preflight` -> PREFLIGHT OK; `./ops/check-pins` -> PINS ok=8 skipped=0 pending=4 expired=0 failed=0; `bash ops/test >/tmp/x.log 2>&1; echo $?` -> 0, log tail shows `TESTS linux=37/3 ios=skipped failed=0 skipped=0`/`OK`. Confirmed P-OPS-01 goes red on `git update-index --chmod=-x ops/sane` (failed=1, restored) and on `git update-index --chmod=+x ops/api-url` (failed=1, restored). But pins/PINS.yaml:31's assertion does NOT enforce "data files are not [executable]" for ops/lib/ro_cases.json, only for the hardcoded ops/api-url. Proof: `git update-index --chmod=+x ops/lib/ro_cases.json && bash ops/check-pins` -> still `PINS ok=8 skipped=0 pending=4 expired=0 failed=0` (should have failed); restored with `--chmod=-x`, `git status --short` clean again. Root cause: the first awk clause `$4 ~ /\.(json|txt|md)$/ || $4 == "ops/api-url" {next}` skips mode-checking for every excluded path instead of requiring 100644 on them, and the second `test` re-checks only the single literal path `ops/api-url` - ro_cases.json, named as data in this task's own Brief, is left completely unguarded, as would any future ops/*.json|*.txt|*.md file. This contradicts both the pin's own statement ("data files are not [executable]") and commit b3218b6's message ("P-OPS-01 pins both halves, so neither a new 100644 script nor a blanket chmod +x satisfies it") - a targeted `chmod +x` on ro_cases.json alone satisfies it. Fix: collapse both checks into one awk pass that requires 100644 on excluded/data paths and 100755 otherwise, e.g. `git ls-files -s ops .githooks | awk '$4 ~ /\.(json|txt|md)$/ || $4 == "ops/api-url" {if ($1 != "100644") print $4; next} $1 != "100755" {print $4}'`, dropping the separate ops/api-url-only test. Secondary, non-blocking: this file's 2026-09-07T06:30:00Z GREEN line and commit b3218b6's message both say "18 scripts now git mode 100755"; actual count on 7840a41 is 17 (`git ls-files -s ops .githooks | awk '$1=="100755"' {c++} END{print c}'` = 17) - self-reported counts should be corrected. All other checks in this review (file classification, direct-invocation, CRLF/.gitattributes coverage incl. subdirectories, ops/test exit code, the two self-reported slips) held up and are not blocking.
- 2026-09-07T07:40:00Z reviewer-4 FAILED this task, correctly, on two counts. Both fixed:
- 2026-09-07T07:40:00Z FIX 1 (high): P-OPS-01 did not enforce the "data files are not executable" half of its own statement - only ops/api-url was re-checked, so `git update-index --chmod=+x ops/lib/ro_cases.json` passed. My commit message claimed "neither a new 100644 script nor a blanket chmod +x satisfies it", which was an OVERCLAIM the reviewer disproved with a runnable demo. Applied reviewer-4's exact fix: one awk pass that requires 100644 on data paths and 100755 on everything else. I re-ran the hole first to see it pass (ok=9 failed=0) before fixing, so the regression is documented, not just asserted.
- 2026-09-07T07:40:00Z FIX 2 (low): "18 scripts" corrected to 17 in the log above. git ls-files -s ops .githooks | awk '$1=="100755"' | wc -l -> 17.
- 2026-09-07T07:40:00Z RED x3 against the fixed pin: (a) chmod -x ops/sane -> failed=1; (b) chmod +x ops/lib/ro_cases.json -> failed=1 (was passing before the fix); (c) chmod +x ops/api-url -> failed=1. GREEN between and after each: ok=9 failed=0.
- 2026-09-07T07:40:00Z merged origin/main (T-0018's P-SAFE-05 fix) so this branch carries a green pin set: PINS ok=9 pending=3 failed=0.
- 2026-09-07T07:40:00Z re-review requested from agent/reviewer-5
