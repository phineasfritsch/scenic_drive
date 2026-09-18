---
id: T-0147
title: CLAUDE.md names ScenicAPIClient, PlaceStore and Telemetry as root targets; Package.swift declares only ScenicKit and Handoff
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [CLAUDE.md, Package.swift, Sources/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Panel CODE lens, grounded: CLAUDE.md's Repository shape lists five Linux-only targets; `Package.swift`
declares two products (ScenicKit, Handoff). Three named targets do not exist, and every agent reads CLAUDE.md
as the rule book. Either add the three as empty-but-real targets with one type each and a test target
(so the layering rule has something to bind to), or amend CLAUDE.md to say which exist today and which are
planned. Package.swift is serial-only: declare `exclusive: [package-swift]` before touching it, and wait for
T-0141's lock to release.

## Log
- 2026-09-18T03:05:00Z filed by agent/claude-fable-5-1 from the hourly panel's grounded synthesis (.artifacts/panel/last.md). ops/new-task allocated T-9902 again ([[T-0138]]); renamed by hand.
