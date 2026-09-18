---
id: T-0167
title: ios-compile follow-up - commit Package.resolved, build with Xcode 26 (the plan's SDK), and pin the guardrail check
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T20:32:58Z
lease_expires_at: 2026-09-19T04:32:58Z
worktree: .worktrees/T-0167
branch: task/T-0167
exclusive: [package-resolved]
touches: [.github/workflows/ios-compile.yml, ops/lib/check-ios-compile-guardrails.py, apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0157]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0157's workflow ran for the first time on 2026-09-18 and the record is in `queue/done/T-0157-*.md`:
GREEN on main (run 35391464739: Xcode 16.4, Build version 16F6, Apple Swift 6.1.2, `** BUILD SUCCEEDED **`, zero
compiler errors, one benign appintents warning) and RED on a throwaway branch carrying a deliberate type error
(run 35391738972: `DesignTokens.swift:104:31: error: cannot convert value of type 'String' ...`,
`** BUILD FAILED **`, exit code 65, job conclusion failure, with both `if: always()` steps still succeeding -
they did not mask it). `apps/ios` compiles. Three things the first run surfaced:

1. **`Package.resolved` is written by every run and tracked by nobody.** The green run printed
   `?? apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` and uploaded
   it (artifact `ios-compile-35391464739`, also at `.artifacts/ios-compile/art/` on the dev box). It is a
   serial-only file (CLAUDE.md): declare `exclusive:`, commit the runner-produced file byte for byte, add
   `-disableAutomaticPackageResolution` to the pinned build script so a drifting resolution FAILS the job
   instead of silently re-resolving, and update `EXPECTED` in the guardrail check in the same commit (the
   check compares the whole workflow by equality - that is the point). Green = a dispatch whose
   `git status --porcelain --untracked-files=all` step prints nothing.
2. **The runner's default is Xcode 16.4; the plan requires the iOS 26 SDK** (plan: "Xcode 26 / iOS 26 SDK
   mandatory since 2026-04-28"). The image has `Xcode_26.0` through `Xcode_26.3` installed. Select one with
   `DEVELOPER_DIR` - which means deliberately allowing exactly ONE `env:` key at the job level in the pinned
   structure (today the check refuses `env:` anywhere, by name). RULE in the Log: which 26.x, pinned by exact
   path, and what happens when the image drops it (the job must fail by name, not fall back to the default).
   Expect real compiler findings: Xcode 26's Swift may flag things 16.4 did not; fix them in `apps/ios/` under
   their own touches or file them.
3. **Nothing runs the guardrail check** (every reviewer of PR #90 recorded this). Pin it under a P-OPS id that
   is free on main AND on open PRs (`gh pr list --state open`, then grep each head's `pins/PINS.yaml`); anchor:
   source; runs_on: [linux, mac]; the assertion is the check itself, and `--prove-red` is its red.
4. Minor, from the run log: `actions/checkout@v4` / `upload-artifact@v4` print a Node 20 deprecation notice;
   decide whether to move the allowlist to the next major in the same change or leave it with a date.

Dispatch with `gh workflow run ios-compile.yml --ref <branch>` - now that the file is on main it runs on any
ref, which is also how T-0151, T-0152 and T-0153 can prove their Swift compiles before review.

## Log
- 2026-09-18T21:00:00Z filed by agent/claude-fable-5-1 after the first green and first red dispatch of ios-compile. Not started.
- 2026-09-18T20:32:58Z claimed by agent/claude-opus-5; lease until 2026-09-19T04:32:58Z
