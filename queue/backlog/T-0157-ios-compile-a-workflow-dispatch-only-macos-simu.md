---
id: T-0157
title: ios-compile - a workflow_dispatch-only macOS simulator build of apps/ios, seen red then green, so the Apple tree is compiled by something before the human's Xcode Cloud step
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.github/workflows/ios-compile.yml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
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
