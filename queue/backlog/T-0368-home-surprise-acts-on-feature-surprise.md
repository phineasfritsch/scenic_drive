---
id: T-0368
title: The home's Surprise Me chip acts on /config's feature_surprise - hidden or its typed line when false, and the plan sheet's post-tap Surprise action follows it
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/, ops/mutate/, queue/]
pins_affected: []
reviewer: null
depends_on: [T-0364]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0364 decodes feature_surprise (RemoteConfig.featureSurprise, per field, default true) and acts on it only in the
plan sheet's pre-tap pause notice (ConfigDegrade.pausedSurpriseOff, R4). The home's SurpriseToggle (home.surprise)
and SurpriseCard are composed by the shell apps/ios/ScenicDrive/ScenicDriveApp.swift, outside T-0364's touches, and
FeatureScenicHome may import no adapter - so the chip still shows under feature_surprise=false, and the post-tap
PlanFailureCopy rows (quotaExhausted, planningPaused, attestUnsupported) still offer "Surprise me instead".

MEASURE first (the shell's composition, whether ScenicDriveApp.swift is frozen by check-safety-disclaimer-frozen,
how the home could receive the config without a feature-to-adapter import). RULE hide vs typed line, and whether
PlanFailureCopy takes the flag. Surprise Me sends the Worker nothing (no /surprise route), so the flag is advisory.

## Log
- 2026-10-16T00:26:47Z filed by agent/claude-opus-5 as T-0364's follow-up (T-0364 R6). Ids checked on origin/main and every
  origin/task/* branch: highest T-0366, so T-0367.
- 2026-10-16T01:20:31Z renumbered T-0367 -> T-0368 by agent/claude-opus-5: main took T-0367 (telemetry-install-id-per-request)
  in the T-0358 merge; ids rechecked on origin/main and every origin/task/* branch, highest T-0367.
