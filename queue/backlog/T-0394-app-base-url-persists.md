---
id: T-0394
title: The app's API base URL only comes from a -plan.base.url launch argument - a TestFlight or home-screen launch shows routingOffline; read it from Info.plist (build setting) with the launch argument as a debug override
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, ops/lib/, Tests/]
pins_affected: [P-SAFE-03]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The pilot audit found that plan.base.url is set only by a -plan.base.url launch argument, which applies only when Xcode launches the app. An app launched from the home screen or TestFlight has no base URL and shows routingOffline everywhere.

MEASURE every reader of the base URL (planner, telemetry, waitlist, config, search, account, attest, ledger). RULE one binding:
- an Info.plist key, e.g. SCENIC_API_BASE_URL, set from a build setting in the app target's build configuration. If that needs project.pbxproj, which is serial-only and holds the xcodeproj lock, STOP and say so. Prefer an Info.plist value that buildable folders pick up without a pbxproj edit;
- the launch argument kept as a DEBUG-only override;
- one Linux-testable resolver in ScenicKit or ScenicAPIClient that every client reads (shipped-value-single-binding), table-tested over: absent, empty, non-https, trailing slash, the override precedence, and a malformed URL.

The value for the pilot is https://scenic-api.phineas-fritsch.workers.dev. Re-approve P-SAFE-03 digests and the frozen shell lines. ios-compile must succeed, with a whitelist guard so that no client reads the base URL any other way.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the pilot runbook audit (owner authorised the pilot backend 2026-10-17).
