---
id: T-0253
title: ScenicKit Surprise - the selector picks one reachable, open, safe, novel place and says why
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, Tests/Fixtures/surprise/, ops/mutate/]
pins_affected: [P-PROD-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "Sources/ScenicKit/Surprise/ (Foundation only, one type per file, 300-line cap) exposes one entry point, Surprise.pick(candidates:reach:history:context:seed:) -> SurprisePick? (or a closed SurpriseOutcome enum with a typed 'nothing reachable' case); every Swift test below calls THAT entry point, never a helper"
  - "the plan's hard filters, each its own named test that FAILS by name when that filter alone is deleted from the shipping entry point: (1) outside the reach (round-trip minutes > budget, from a per-candidate travel-time input), (2) shown within 90 days, (3) same category x corridor within 30 days, (4) a blocklisted brand / chain, (5) not open at arrival + dwell + 45 min unless hours-exempt, (6) an unlit unpaved viewpoint arriving after civil twilight (ScenicKit Solar, not a literal), (7) a red-flag / fire-weather day drops park, trailhead and viewpoint, (8) an approach flagged as crossing private access"
  - "ranking = quality (curation score) + approach-road score + novelty + time-fit with a seeded 20% exploration; P-PROD-02: the pick is a pure function of (user id, local date, seed) - same inputs give the same pick (equality, 100 runs) and >= 90 of 100 consecutive seeds over the committed fixture give distinct picks when >= 100 candidates are eligible"
  - "the pick carries its WHY: a SurpriseReason value naming the hook, the round-trip minutes and the golden-hour line when sunset falls inside the visit (from Solar); a full-equality test pins the whole value for three fixture picks (CLAUDE.md, full-equality oracle)"
  - "a fixture of >= 120 synthetic LA-area candidates under Tests/Fixtures/surprise/ (no raw OSM coordinates beyond 5 dp, no real personal data); 'not this' feedback (four reasons: too far, not my thing, been there, wrong time) is an input that changes the next pick deterministically, each reason with a test"
  - "a mutation population under ops/mutate/surprise*.py with a literal floor, run once in full by the author with its vacuity proof; check-mutate-population, check-line-cap, queue-check and ops/check-pins --source-only green"
---
## Brief

Plan M5 'Surprise me': "Time-budget dial -> one named, curated, public place inside the reachable area; hook line,
round-trip time, golden-hour line, 4-way 'not this'". The engine is missing entirely (no Sources/ScenicKit/Surprise).
This task is the pure, Linux-tested selector only - no Worker endpoint, no isochrone call, no UI. Reach arrives as
a per-candidate round-trip minutes input so the caller (the Worker's /isochrone later, or a cached polygon on the
device) is free to compute it. Weather/red-flag arrives as a Bool in the context. Copy the shapes of
Sources/ScenicKit/RoadTrip (T-0249, merged) and its mutation population ops/mutate/roadtrip*.py.

Population measured before the predicate (CLAUDE.md): there is no curated LA corpus with hours yet (T-0183 is
backlog), so the >= 90% distinct predicate ranges over the committed SYNTHETIC fixture this task writes, whose size
and eligible count the author quotes in the Log before writing that test.

## Log
- 2026-10-05T09:36:52Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map: M5's Surprise
  engine is missing; filed as T-0253 by hand because ops/new-task allocated T-9902 (the T-0128 stray-ref bug).
