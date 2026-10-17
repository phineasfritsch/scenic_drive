---
id: T-0385
title: ops/plan's body gate (ScenicPlanCLI GraphHopperRouteSource.forbiddenEncodedValues) still lists only road_access and surface - bind it to the shipped base profile like the Worker
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicPlanCLI/, Tests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/mutate/]
pins_affected: [P-SAFE-01]
reviewer: null
depends_on: [T-0382]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0382 (PR #276) bound the Worker's FORBIDDEN_ENCODED_VALUES to the shipped car_scenic_base.json by full
equality: the identifiers of every multiply_by-0 clause minus the builder's own (road_class), which is eight names
(car_access, road_access, surface, track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way).
Its author recorded the Swift copy left behind: Sources/ScenicPlanCLI/GraphHopperRouteSource.swift
`forbiddenEncodedValues = ["road_access", "surface"]`, the plan CLI's body gate, which still lacks six of them.

Bind the Swift list the same way. A Linux test reads the SHIPPED profile JSON, derives the list and asserts
equality, and the overlap with the CLI builder's identifiers must equal exactly what the builder reads. Drive a
generated near-miss corpus per name (memory generated-near-miss-corpus) through the CLI's shipping body gate:
refused iff the name occurs, forwarded unchanged otherwise. Show red before the list changes and green after.
Re-approve the digest row, and add mutation population entries if the gate is a numeric/decision module.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0382 stillOpen 1.
