---
id: T-0232
title: ops/plan over the Bay Area golden - plan:284's literal clause 3: Mountain View -> SF +25 returns the 280/Canada/Skyline shape against T-0008's Bay Area graph; explicitly NOT on the LA owner's path
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/plan, Tests/Fixtures/, services/routing/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0008, T-0182]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/plan over T-0008's Bay Area graph for Mountain View -> San Francisco at +25: the URL and the per-edge table quoted; the shape asserted as a Linux golden over a recorded response - motorway/trunk length between the first and last scenic episode == 0, and 280, Canada Road and Skyline named in the explanation; RED by name first against a recorded all-101 response"
---
## Brief

From the 14:13 panel (STRATEGY, grounded on plan:209 and plan:53): M3 is ruled in two halves - the LA-owner half
(clause 1 the floor, clause 2 the drive via T-0209 -> T-0221) and this literal clause 3, which belongs to the CI
golden set and needs the Bay Area graph nobody owns yet (T-0008, backlog).

## Log
- 2026-09-19T21:54:54Z filed by agent/claude-opus-5[1m] (14:13 panel, grounded on pins/floor_*.txt, T-0203 Log :34, queue.py:541-548, RouteScore.swift:92-94). Not started; after T-0008.
