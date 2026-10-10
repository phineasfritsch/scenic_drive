---
id: T-0359
title: Photon address search, everything but the deploy - services/search (pinned image, California index config), a Worker /search proxy that sends at most one 2-dp coordinate, and a ScenicAPIClient search client, all tested locally
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/search/, services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-COST-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10 (M4 "corpus FTS5 + Photon"; P-PRIV-06 typed address): services/ holds api, etl, routing, tiles -
no search; PlanPlaceSearch.swift says "Photon is not deployed and typed street addresses are a later task". The VPS
deploy is the owner's; everything else is buildable.

MEASURE FIRST: Photon's request/response shape at a pinned version (cite the source, pin the image by digest),
the Worker's existing proxy pattern for the router (secret header, quota decrement before upstream, kill switch,
route table enumerations - see memory parallel-worker-prs-conflict), and how the app's plan sheet would call it.
RULE: the query the Worker forwards (the typed text plus at most one bias coordinate at 2 decimals - CLAUDE.md
privacy invariant), quota/kill behaviour (P-COST-01: every route in the router table), the answer the client decodes
(fail-closed), and what stays out (the app wiring is a follow-up task if apps/ios digests are refused). Tests:
Worker vitest through the shipping handler with a fake upstream; client whole-body equality; P-COST-01's table gains
/search. Do NOT deploy or create Cloudflare/VPS resources.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-5).
