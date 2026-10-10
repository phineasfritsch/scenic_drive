---
id: T-0362
title: The plan sheet searches typed addresses through SearchClient and plans to one - rule how a searched address reaches /plan under P-PRIV-05 first, then wire PlanPlaceSearch, debounce to one request per submit, and carry the paid search allowance
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, services/api/src/, services/api/test/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-COST-01]
reviewer: null
depends_on: [T-0359]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed by T-0359 (R9). T-0359 shipped POST /search (Worker, through a pinned Photon the owner deploys) and
ScenicAPIClient's SearchClient; the app does not call it yet - apps/ios/.../FeaturePlanSheet/PlanPlaceSearch.swift
still says Photon is not deployed.

MEASURE FIRST: how /plan takes a destination today (planRequest.ts: a corpus place id; planPrivacy.test.ts refuses "a
destination carried as a coordinate - a second coordinate"), and what a SearchResult can become without the server
receiving a second coordinate in one action. RULE that before any code - candidates: the origin stays the one 2-dp
coordinate and the searched place is resolved server-side from an opaque result token /search issued (no coordinate
from the device), or a searched result is only shown and handed off. Then: PlanPlaceSearch calls SearchClient once per
submit (never per keystroke), with the map centre's 2-dp bias; every SearchOutcome has copy; the paid tier's search
allowance (DAILY_SEARCH_QUOTA.paid) needs the account token / session headers SearchClient does not send yet.

## Log
- 2026-10-10T04:48:36Z filed by agent/claude-opus-5 from T-0359 R9 (id checked against main and every task/* branch:
  highest was T-0361).
