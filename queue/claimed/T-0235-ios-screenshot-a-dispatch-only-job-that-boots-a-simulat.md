---
id: T-0235
title: ios-screenshot - a dispatch-only job that boots an iOS 26 simulator, installs and launches the app, and uploads PNGs of the home screen in light and dark, so the app can be SEEN without a Mac
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-25T19:21:56Z
lease_expires_at: 2026-09-25T23:21:56Z
worktree: .worktrees/T-0235
branch: task/T-0235
exclusive: []
touches: [.github/workflows/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - ".github/workflows/ios-screenshot.yml under the SAME guardrails as ios-compile.yml (T-0157): workflow_dispatch ONLY, contents: read, the pinned standard macos-15 label (never -large/-xlarge), a job timeout, bash with no continue-on-error, DEVELOPER_DIR as the only env key at the job level at the exact Xcode_26.3 path, an allowlist of actions (checkout plus upload-artifact, both pinned), no commit and no push step. ops/lib/check-ios-compile-guardrails.py is extended to read BOTH workflow files (or a sibling check is added) and its --prove-red demonstrates each guardrail refused on the NEW file by name"
  - "the job builds for a CONCRETE simulator (an iPhone device type and an iOS 26 runtime the image actually has - 'xcrun simctl list runtimes' and 'devicetypes' printed first, the choice ruled from that output, never guessed), boots it, installs the built .app with 'xcrun simctl install', launches it with 'xcrun simctl launch', waits a FIXED interval for first render (state it), captures 'xcrun simctl io booted screenshot' in light, switches 'xcrun simctl ui booted appearance dark', relaunches, captures again, and uploads both PNGs as one artifact; a launch that crashes is a failed job (the launch exit status and the app's process checked), never a screenshot of the springboard"
  - "dispatched ONCE on the branch, green: run id, conclusion and headSha quoted; the artifact downloaded with 'gh run download <id>' into the gitignored .artifacts/ dir of the MAIN checkout (never committed), both images' pixel sizes read back with PIL and quoted, and what each image SHOWS described in the Log in words (title, road line, the map - demo tiles are expected in CI because la.pmtiles is gitignored and not in the CI checkout; say so rather than hiding it - the credit line, the conditions line, the button)"
  - "bash ops/lib/check-exec-bits, bash ops/queue-check bare; wc -l on every touched file"
---
## Brief

Measured at 2026-09-25T19:21:32Z: the only compiler apps/ios has ever met is ios-compile.yml, which builds for
`generic/platform=iOS Simulator` and proves the tree compiles - nothing has ever RUN it. The owner is on Windows, has
no Mac, and T-0009 (TestFlight) waits on a human App Store Connect step. A screenshot job is the cheapest way to put
the actual app in front of the person it is for.

The map in CI will draw the MapLibre demo tiles and credit them as such, because `apps/ios/ScenicDrive/Tiles/la.pmtiles`
is gitignored (63.5 MB) and lives only on the owner's box - that is BasemapResolver's honest fallback working, not a
defect. Putting the real archive into CI would mean publishing it somewhere a runner can fetch it: a separate decision,
not this task's.

## Log
- 2026-09-25T19:21:32Z filed by agent/claude-opus-5-5 (orchestrator). Not started; independent of PRs #124/#125/#126 and T-0234 (different files).
- 2026-09-25T19:21:56Z claimed by agent/claude-opus-5; lease until 2026-09-25T23:21:56Z
