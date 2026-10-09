---
id: T-0325
title: Learned corridor speeds reach the ETA - completed drive legs feed LearnedCorridorSpeeds.record with an H3-8 cell, and the preview's ETA and estimate badge come from retime, so the badge goes away after 5 drives on a corridor (M7 exit)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T10:44:52Z
lease_expires_at: 2026-10-09T22:44:52Z
worktree: .worktrees/T-0325
branch: task/T-0325
exclusive: []
touches: [Sources/ScenicKit/, Sources/ScenicAPIClient/, Sources/PlaceStore/, Tests/, apps/ios/Packages/ScenicApp/Sources/, services/api/src/, services/api/test/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-07, P-PRIV-05]
reviewer: null
depends_on: [T-0320, T-0317]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0320 owner stillOpen 1 (PR #207): LearnedCorridorSpeeds exists but nothing feeds it or reads it. Open questions
the claimer MEASURES and RULES before writing acceptance (CLAUDE.md: measure the population first):
(a) where an H3-8 index comes from - Telemetry builds resolution 5 only, internal, and ScenicKit cannot import it
without a Package.swift change (serial file);
(b) per-edge free-flow times - PlanResponse carries only etaSeconds; does the Worker pass GraphHopper details=time
through (a Worker change) or does the device split the ETA by edge length (ruled honestly);
(c) where completed legs come from - DriveSession (T-0317) progress + fix timestamps, recorded on device only,
persisted across launches (PlaceStore, no Codable path to the server per P-PRIV-05);
(d) the preview's etaIsEstimate becomes retime's isEstimate; the "estimate · no traffic data" badge stays until every
edge is learned (product invariant).

## Log
- 2026-10-08T13:58:47Z filed by agent/claude-opus-5 (orchestrator) from T-0320's stillOpen 1.
- 2026-10-08T13:59:22Z renumbered T-0324 -> T-0325 by agent/claude-opus-5 (orchestrator): task/T-0321 already holds a T-0324.
- 2026-10-09T10:44:52Z claimed by agent/claude-opus-5; lease until 2026-10-09T22:44:52Z
