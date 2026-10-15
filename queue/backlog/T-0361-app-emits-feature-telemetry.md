---
id: T-0361
title: The app emits the ten feature-side telemetry cases T-0355 left pending - a seam per feature target plus the shell, so each has its one emit site
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-SAFE-03]
reviewer: null
depends_on: [T-0355]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0355 shipped Sources/Telemetry/TelemetryClient and PlanAdapter/LiveTelemetry, and emits plan_requested, plan_result
and surprise_shown (the moments PlanAdapter already owns). ops/lib/check-telemetry-emit-sites.txt holds the other
ten as `pending T-0361`: preview_shown, handoff_tapped, drive_started, drive_completed, drive_abandoned,
surprise_not_this, surprise_take_me_there, surprise_arrived, corpus_activated, paywall (post_drive_answer is T-0358).

Measured by T-0355 (its Log M3/M4): each moment sits in a target that may not import Telemetry or PlanAdapter -
FeaturePlanSheet (preview card), FeatureScenicHome (GatedHandoffButton.swift:94, DriveScreen.swift:117 End),
FeatureSurpriseMe (SurpriseCard.swift:125 take me there, :186 not this), Entitlements (PaywallScreen), NavAdapter
(DriveHost.swift:23 start). So each needs a feature-owned seam (a closure or environment value of the feature's own
types) that the shell (apps/ios/ScenicDrive/ScenicDriveApp.swift) wires to a LiveTelemetry function - the shell file
is in this task's touches. OPEN QUESTIONS TO MEASURE AND RULE FIRST: drive_completed/abandoned need a whole-percent
progress fraction and a deviation count that DriveDisplay does not carry (ScenicKit DriveSession may); surprise_arrived
has NO moment today (the Surprise opens Apple Maps; the app never learns of an arrival) - rule whether it is
measurable at all or the case stays pending with a reason; corpus_activated needs an Int version but
CorpusActivation.activated carries none and CorpusManifest.version is a String - rule the mapping or the gap.

Acceptance shape (T-0355's): every wired case moves from a pending row to exactly one emit row in the same diff; the
guard's --prove-red stays red row by row; every apps/ios edit re-approves its P-SAFE-03 digest; ios-compile and
ios-screenshot succeed with the touched screens looked at.

## Log
- 2026-10-10T04:10:00Z filed by agent/claude-opus-5 (T-0355 owner) from T-0355 R5.
