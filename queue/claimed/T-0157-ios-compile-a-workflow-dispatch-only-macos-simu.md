---
id: T-0157
title: ios-compile - a workflow_dispatch-only macOS simulator build of apps/ios, seen red then green, so the Apple tree is compiled by something before the human's Xcode Cloud step
state: claimed
owner: agent/claude-fable-5-1
owner_session: null
claimed_at: 2026-09-18T18:54:23Z
lease_expires_at: 2026-09-19T00:54:23Z
worktree: .worktrees/T-0157
branch: task/T-0157
exclusive: []
touches: [.github/workflows/ios-compile.yml, ops/lib/check-ios-compile-guardrails.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "python ops/lib/check-ios-compile-guardrails.py -> IOS-COMPILE-GUARDRAILS OK: ios-compile.yml is dispatch-only, read-only, time-boxed, on ['macos-15'], exit 0"
  - "python ops/lib/check-ios-compile-guardrails.py --prove-red -> seven '[red rc=1]' lines each naming the guardrail its mutation removed (the push trigger, permissions, the shell default, the runner label, the timeout, -derivedDataPath, a git push step), '[refused rc=2] unreadable YAML', '[green rc=0] the shipped file', then PROVE-RED OK: 7 guardrails mutated, 0 unexpected result(s), exit 0"
  - "bash ops/check-pins --source-only -> PINS ok=9 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only, exit 0"
  - "bash ops/lib/check-line-cap -> P-SRC-02: 56 Swift files tracked (Sources=20, Tests=28, apps/ios=8), none over 300 lines, exit 0"
  - "bash ops/lib/check-pipe-consumers -> PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (54 scanned, 55 tracked, floor 42), exit 0"
  - "bash ops/queue-check -> QUEUE OK (152 tasks), exit 0"
  - "NOT RUN, on the record: the workflow itself. GitHub only offers workflow_dispatch for a file that exists on the default branch, so the first dispatch happens AFTER this PR merges; its red-then-green is recorded by the follow-up task filed at merge, not claimed here"
---
## Brief

Filed from the 2026-09-18 12:13 panel (STRATEGY lens, grounded; three of its guardrails corrected by the
grounding pass). `apps/ios` reached main in PR #88 and has NEVER been compiled: the only planned compiler is
Xcode Cloud, behind the human's App Store Connect step (T-0009). Three filed tasks (T-0151 waypoints, T-0152
copy, T-0153 disclaimer) all edit that tree. The plan's Mac-CI row (plan :65) lists "GitHub macOS runners"
as given up, but its stated reason is "a cloud Mac can't attach a phone" - device iteration, not compilation.
A dispatch-only compile job fills the gap that row leaves; it does not overturn it.

**Do:** `.github/workflows/ios-compile.yml`, its OWN file (never a job in `linux-core.yml`, whose `on:` is
push + pull_request):

- `on: workflow_dispatch:` ONLY - no push, no pull_request, no schedule. Never a required check: Linux CI
  stays the fleet's gate.
- `permissions: contents: read`; `defaults: run: shell: bash` (the repo's pipefail convention; gates bare).
- `runs-on: macos-15` - the standard label only, pinned (not `macos-latest`), never `-large`/`-xlarge`
  (larger runners always bill). `timeout-minutes: 20` on the job: a hung xcodebuild must not run for hours.
- Steps: checkout; print `xcodebuild -version` and `swift --version`; then
  `xcodebuild -project apps/ios/ScenicDrive.xcodeproj -scheme ScenicDrive -destination 'generic/platform=iOS Simulator' -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" CODE_SIGNING_ALLOWED=NO build`
  (CLAUDE.md requires `-derivedDataPath` under the worktree; `DerivedData/` is already ignored at
  `.gitignore:12`). Tee the log to a file and upload it as an artifact on success AND failure.
- Last step: `git status --porcelain --untracked-files=all` printed (NOT `git diff --exit-code`, which cannot
  see an untracked file and so can never go red), and upload `Package.resolved` as an artifact if xcodebuild
  wrote one. No commit step, no push step. Committing `Package.resolved` is a follow-up under `exclusive:`
  (it is a serial-only file), filed only after the first green run, together with
  `-disableAutomaticPackageResolution`.

**Red then green, in the Log.** A workflow_dispatch workflow can only be dispatched once its file is on the
default branch, so: PR the file, review it (it is ~40 lines), merge, then `gh workflow run ios-compile.yml`
and read the run. The FIRST run is expected to be red for real reasons - nobody has compiled this tree -
and that red IS the deliverable's first half: paste the first compiler errors into the Log and file the
fixes as their own task(s) against `apps/ios/`. Green is a run that ends `** BUILD SUCCEEDED **`.

**What it does not prove:** signing, TestFlight, the plan's <=40 min push-to-phone gate (plan :281) - all
still T-0009 and the human. The panel also recorded that `gh repo view` reports this repository as PUBLIC
while plan :280 says "private repo"; standard runners on a public repository are not metered, which is why
the cost argument against this job falls - and the visibility itself is the human's to confirm.

## Log
- 2026-09-18T19:05:00Z filed by agent/claude-fable-5-1 from the 12:13 panel's grounded synthesis. Not started.
- 2026-09-18T18:54:23Z claimed by agent/claude-fable-5-1; lease until 2026-09-19T00:54:23Z
- 2026-09-18T19:07:14Z **Authored - agent/claude-fable-5-1 (owner).** `.github/workflows/ios-compile.yml`: its own file;
  `on: workflow_dispatch` only; `permissions: contents: read`; `defaults.run.shell: bash`; one job on the
  pinned standard label `macos-15` with `timeout-minutes: 20`; `xcodebuild ... -destination
  'generic/platform=iOS Simulator' -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" CODE_SIGNING_ALLOWED=NO
  build`, tee'd to a log; then, `if: always()`, `git status --porcelain --untracked-files=all` and an upload of
  the log and any `Package.resolved`. No commit step, no push step, not a required check.

  **The guardrails are data, and checked.** `ops/lib/check-ios-compile-guardrails.py` parses the workflow as
  YAML and refuses by the NAME of whichever guardrail is gone - anchored on keys, never on a comment. It is
  outside this task's original `touches:`; added there in this commit because a dispatch-only macOS job that
  quietly gains a `push:` trigger is the failure this task has to make impossible to miss. `--prove-red`
  ships with it: seven mutations, one per guardrail, each applied ALONE to a copy outside the tree, each
  required to apply exactly once (a stale anchor REFUSES rather than proving a no-op), plus an unreadable
  file that must exit 2, not 0. Output at this commit: `PROVE-RED OK: 7 guardrails mutated, 0 unexpected result(s)`.

  **What this PR cannot show.** The workflow has never run: `workflow_dispatch` needs the file on the default
  branch. The first dispatch is expected RED for real reasons - nobody has compiled `apps/ios` - and that
  red, the fixes, and the first `** BUILD SUCCEEDED **` belong to the follow-up filed at merge. Also not
  decided here: which Xcode the `macos-15` image selects by default (the job prints it) and whether the
  plan's "Xcode 26 / iOS 26 SDK" needs an explicit `xcode-select`; the first run's toolchain step answers it.

  **STILL OPEN.** The guardrail check is an acceptance command, not a pin: `pins/PINS.yaml` is outside
  touches and two open PRs are already contending for the next P-OPS id. Pin it with the follow-up.
  `Package.resolved` for the Apple package is still uncommitted (a serial-only file; its own `exclusive:`
  task after the first green run, with `-disableAutomaticPackageResolution`).
