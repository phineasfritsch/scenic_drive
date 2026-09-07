---
id: T-0007
title: CI: linux-core.yml (swift test + check-pins --source-only), Xcode Cloud nightly + device/* TestFlight, ci_scripts
state: review
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: 2026-09-07T03:53:05Z
lease_expires_at: 2026-09-07T07:53:05Z
worktree: ../wt/T-0007
branch: task/T-0007
exclusive: []
touches: [.github/workflows/, apps/ios/ci_scripts/]
pins_affected: []
reviewer: agent/reviewer-1
depends_on: [T-0002, T-0004]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "a push to main runs linux-core.yml in <5 min and prints the TESTS line in the job log"
  - "RED: a PR adding import SwiftUI to Sources/ScenicKit fails the source-only pin job"
  - "apps/ios/ci_scripts/ci_post_clone.sh exists and is executable; the Xcode Cloud nightly + device/* workflows themselves are configured in App Store Connect once the project exists (T-0010) and proven by T-0009"
---
## Brief

Pin the swift image by digest. Linux job must never need a Mac or any secret.

## Log
- 2026-09-07T03:53:05Z claimed by agent/claude-opus-5; lease until 2026-09-07T07:53:05Z
- 2026-09-07T04:05:00Z GREEN: run 34081219977 on PR #3 - pins-source-only 6s success; core success; job log shows PREFLIGHT OK, TESTS linux=3/3 ios=skipped failed=0, PINS ok=7 pending=4, QUEUE OK (13 tasks), source-only PINS ok=2
- 2026-09-07T04:05:00Z RED: throwaway branch tmp/ci-red-demo (draft PR, closed) adding import SwiftUI to Sources/ScenicKit/Tmp.swift -> pins-source-only FAILURE, core FAILURE; log names P-SRC-01 (PINS ok=1 failed=1 source-only)
- 2026-09-07T04:05:00Z swift image pinned by digest sha256:98ee3a84...; the Worker tier (node 22 + npm ci) is conditional on services/api/package.json and is exercised on this PR after merging main (T-0005 merged)
- 2026-09-07T04:05:00Z acceptance line 3 narrowed: App Store Connect workflows need the xcodeproj (T-0010) and are proven by T-0009; ci_post_clone.sh delivered here
- 2026-09-07T04:05:00Z moved to review/, reviewer agent/reviewer-1
- 2026-09-07T04:23:12Z reviewed by agent/reviewer-2: FAIL — .github/workflows/linux-core.yml:51 `run: cd services/api && npm ci --no-audit --no-fund 2>&1 | tail -3` has no `shell:` set, so GitHub Actions uses the unspecified-shell default `bash -e {0}` (no pipefail; pipefail is only added when `shell: bash` is explicit) — confirmed by fetching GitHub's own docs and by local repro (`bash -e -c 'false | tail -3'; echo $?` → 0). A failing `npm ci` would be masked by `tail -3` succeeding and the `core` job would report green with no worker deps installed. Fix: add `shell: bash` to that step (or `defaults: run: {shell: bash}` at job level), or drop the pipe and tee to a file instead. Separately, apps/ios/ci_scripts/ci_post_clone.sh is committed with mode 100644, not 100755 (`git ls-files -s apps/ios/ci_scripts/ci_post_clone.sh` → `100644 d0404a1...`) — Xcode Cloud requires ci_scripts to be executable, so acceptance line 3 ("exists and is executable") is not met as committed. Fix: `chmod +x apps/ios/ci_scripts/ci_post_clone.sh`, re-add, re-commit. Acceptance lines 1 and 2 do check out: run 34081433612 (sha 48a7391) both jobs success in 78s with TESTS linux=37/3 failed=0, PINS ok=7 pending=4, QUEUE OK (14 tasks), PREFLIGHT OK; run 34081318363 (tmp/ci-red-demo) both jobs failure, pins-source-only names P-SRC-01. Also noted, non-blocking: `gh api repos/.../branches/main/protection` returns 403 (private repo, not Pro) not 404, so whether linux-core actually gates merges to main is unverifiable, not confirmed either way; and `concurrency: {group: linux-core-${{ github.ref }}, cancel-in-progress: true}` on the `push: branches: [main]` trigger can cancel an in-flight run for an earlier main commit if two pushes land close together, leaving that commit's required check un-reported — worth a follow-up task but not this task's scope. Leaving in review/ per protocol; owner should apply the two FAIL-worthy fixes above and resubmit.
- 2026-09-07T05:30:00Z FIX for reviewer-2 finding 1 (pipefail): added job-level `defaults: run: shell: bash` so every run: step is `bash -e -o pipefail`; GitHub's unspecified-shell default is `bash -e` without pipefail, so `npm ci ... | tail -3` could report success on a failed install. Verified locally: `bash -e -c 'false | tail -3'` exits 0, `bash -eo pipefail -c 'false | tail -3'` exits 1.
- 2026-09-07T05:30:00Z FIX for reviewer-2 finding 2 (exec bit): git update-index --chmod=+x apps/ios/ci_scripts/ci_post_clone.sh -> mode 100755. NOTE: every ops/* and .githooks/* file is also committed 100644 (core.filemode is false on this Windows checkout); that is repo-wide and outside this task's touches, so it is filed as T-0015.
- 2026-09-07T05:30:00Z FIX for reviewer-2 finding 3 (concurrency): cancel-in-progress now only applies to pull_request events, so a main commit never loses its check to a later push.
- 2026-09-07T05:30:00Z branch protection could not be checked (403: private repo on a free plan). Filed as T-0016 - until it exists, green CI does not mechanically gate a merge; the queue review gate does.
- 2026-09-07T05:30:00Z re-review requested from agent/reviewer-2
