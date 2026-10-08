---
id: T-0321
title: NavAdapter - the app's only Ferrostar importer, pinned to an exact version, drives turn-by-turn on the planned scenic route through a custom RouteProvider and calls ScenicKit DriveSession for every decision (off-route, reroute with remaining waypoints + same lambda, offline rejoin, motion gate)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T11:51:00Z
lease_expires_at: 2026-10-08T21:51:00Z
worktree: .worktrees/T-0321
branch: task/T-0321
exclusive: [package-swift]
touches: [apps/ios/Packages/ScenicApp/Package.swift, apps/ios/Packages/ScenicApp/Package.resolved, apps/ios/Packages/ScenicApp/Sources/, apps/ios/Packages/ScenicApp/Tests/, apps/ios/ScenicDrive/, Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-NAV-01, P-SAFE-09, P-ATTR-01]
reviewer: null
depends_on: [T-0317]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the Ferrostar release to pin (exact version, its Swift package URL and products, its license, its minimum iOS - must be <= 18.4), how its RouteProvider / custom route adapter accepts a pre-computed route (our GraphHopper polyline + instructions via ScenicKit Guidance), what its off-route and location hooks expose, and how they map onto ScenicKit DriveSession (T-0317) - every decision stays in DriveSession, NavAdapter is a thin shell; the CLAUDE.md rule that NavAdapter is the ONLY importer of Ferrostar"
  - "apps/ios/Packages/ScenicApp/Package.swift gains Ferrostar pinned with exact: and a NavAdapter target; Package.resolved committed; a source guard (whitelist of import sites, CLAUDE.md) refuses 'import Ferrostar' anywhere but NavAdapter, seen red then green"
  - "NavAdapter feeds every location fix and connectivity edge into DriveSession and acts only on its outputs; when the connection drops it cancels the in-flight reroute and drops a late reply/failure (rv2-t0317 recordable 4); offline -> rejoin banner, zero requests; the >4.5 m/s minimal surface is what the drive screen shows; attribution stays visible on the drive map (P-ATTR-01)"
  - "ios-compile + ios-screenshot pass on the branch (the drive screen in the screenshot set if ruled feasible on the simulator); digests re-approved; population entries for the adapter's own wiring (e.g. a fix not forwarded, the late reply not dropped) MISSED before and CAUGHT by name after, or EQUIVALENT with a witness where only device runs can observe them"
---
## Brief

Plan: Navigation on the scenic path (Ferrostar) + M7 + the Turn-by-turn decision row ("pinned to an exact version,
custom RouteProvider"). T-0317 put every decision into Linux-tested ScenicKit DriveSession; this task is the Apple
shell. The Worker reroute wire (/plan carrying remaining waypoints + lambda) is T-0319; until it lands, NavAdapter
rules what a reroute does online (e.g. hand off, or rejoin) and records it. TTS (spoken guidance + audio background
mode) and Live Activity are separate follow-ups; Live Activity needs the xcodeproj lock (held by T-0180).

## Log
- 2026-10-08T11:50:51Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M7 NavAdapter) and rv2-t0317's recordable 4.
- 2026-10-08T11:51:00Z claimed by agent/claude-opus-5; lease until 2026-10-08T21:51:00Z
