---
id: T-0362
title: The plan sheet searches typed addresses through SearchClient and plans to one - rule how a searched address reaches /plan under P-PRIV-05 first, then wire PlanPlaceSearch, debounce to one request per submit, and carry the paid search allowance
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T01:06:49Z
lease_expires_at: 2026-10-17T01:06:49Z
worktree: .worktrees/T-0362
branch: task/T-0362
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
- 2026-10-16T01:06:49Z claimed by agent/claude-opus-5; lease until 2026-10-17T01:06:49Z
- 2026-10-16T01:12:21Z MEASURED (main 42d049fb) and RULED before code.
  Measured: planRequest.ts takes `destination: {place}` only (DESTINATION_KEYS = ["place"], PLACE_ID
  /^[A-Za-z0-9:._-]+$/, <=128); plan.ts resolves it with deps.resolvePlace (D1) BEFORE identify; planPrivacy.test.ts
  refuses "a destination carried as a coordinate - a second coordinate". Corpus place ids are segid.place_id =
  fnv1a64 & MASK63 or 1, so ALWAYS >= 1; the app's whole plan path carries the destination as Int64 (PlanPlace.id,
  PlanClient.plan(to: Int64), PlanRequestBody encodes String(place), PlanRerouter). /search answers
  {results:[{label,lat,lon}]}; SearchClient sends IdentityHeaders.json(device, account: nil, bearer: nil) - no account,
  no session, no 401 retry. PLANS (KV, plan tokens keyed `plan:<who.userId>:<token>`, swept per device by planSweep's
  key WHITELIST prefix+PLAN_TOKEN) is declared in index.ts Env and NOT bound in wrangler.jsonc. FeaturePlanSheet may not
  import ScenicAPIClient; PlanSheetScreen is built only by apps/ios/ScenicDrive/ScenicDriveApp.swift (outside touches)
  from LivePlanner.make(); the sheet never sees the map.
  R1 DESTINATION. The invariant (CLAUDE.md): "The server never receives more than one coordinate per user action,
  never more than 2 decimal places." Candidates: (a) the searched coordinate as the destination beside the origin -
  TWO coordinates in one action: REFUSED (and planPrivacy refuses it). (b) snap the result to the nearest corpus place
  on the device - one coordinate, but plans to a place the user did not pick: REFUSED (dishonest). (c) shown and
  handed off only - satisfies, plans nothing: the fallback for a row with no place. (d) CHOSEN: a server-issued opaque
  place id. /search remembers each result's {lat, lon} in PLANS under `plan:<who.userId>:<id>` for
  SEARCH_PLACE_TTL_SECONDS (86400: a search, then a plan, then the plan token's 12 h of reroutes) and answers the id as
  the row's `place`; the id is a NEGATIVE integer string in [-(2^53-1), -1] (SEARCH_PLACE_ID /^-[1-9][0-9]{0,15}$/,
  value checked), the namespace corpus ids never use, so it rides the existing Int64 path and the existing
  `destination: {place}` - the /plan whitelist is UNCHANGED. Per action: submit a search = q + at most one `near`
  at 2 dp (T-0359, unchanged); plan to a searched row = `origin` (1 coordinate, 2 dp) + place id; reroute of it =
  origin + token + place id. No action carries a second coordinate; the device never sends the result's coordinate.
  R2 IDENTITY + PAID HEADERS. The id is recalled under the identity /plan computes, so SearchClient sends EXACTLY
  /plan's header set by the same code: PlanFamilySend (IdentityHeaders.json with the install id, the StoreKit account
  token when held, the session Bearer whose act is that purchase, one re-send after a 401 to that Bearer). That set is
  what makes who.tier "paid" and so DAILY_SEARCH_QUOTA.paid. No install id -> refusedOnDevice, zero requests.
  R3 RECALL. In /plan an id matching SEARCH_PLACE_ID identifies first (that branch only; a corpus id keeps its order),
  then reads PLANS for that identity: PLANS unbound, a miss, another identity's id, or a value that is not exactly
  {lat, lon} finite in range -> 404 unknown_place with zero upstream calls; a KV throw -> 503 planning_unavailable
  (D1's rule). R4 SWEEP. DELETE /account's plan sweep also deletes prefix+SEARCH_PLACE_ID keys (P-PRIV-04 parity).
  R5 WRITE FAILURE. A row whose KV put fails, or every row when PLANS is unbound, carries no `place`; the app does not
  offer a row with no place (R1 c: not plannable). R6 ONCE PER SUBMIT. ScenicKit PlaceSearchSubmit: typing calls
  nothing; a submit calls the searcher exactly once; a blank submit calls nothing. The corpus FTS list stays per
  keystroke (on device, no request). R7 BIAS (Brief says "map centre": the sheet cannot see the map and the shell is
  outside touches) - the sheet's chosen start's coordinate, else the chosen destination's, else none; SearchRequestBody
  rounds it to 2 dp. R8 COPY: PlaceSearchCopy maps every SearchOutcome to the table in A5. R9 WIRING: the searcher
  rides on the sheet's planner value (WaitlistRoutePlanner gains PlaceSearching; LivePlanner builds ClientPlaceSearch)
  so ScenicDriveApp.swift is unchanged. A searched row picked as START plans from its coordinate rounded to 2 dp, as a
  corpus start does.

## Acceptance
A1 `npx vitest run test/searchPlace.test.ts`: through the shipped worker.fetch ROUTES['/search'] with PLANS bound, the
   200 body EQUALS {results: photon rows each with place = the id written}, each KV put EQUALS
   [`plan:<DEVICE>:<place>`, JSON {lat, lon}, {expirationTtl: 86400}], ids distinct and SEARCH_PLACE_ID; PLANS unbound
   -> the T-0359 body exactly (no place); a failing put -> that row without place.
A2 same file, /plan through the shipped worker.fetch: a searched id from the same identity plans to the remembered
   coordinate (router points EQUAL [[origin], [remembered lon, lat]]); another device's, unknown, unbound, and every
   malformed stored value (lat/lon at each bound accepted, nextafter outside refused, string/bool/null/missing/extra
   key/not JSON) -> 404 unknown_place, zero upstream calls; KV throw -> 503 planning_unavailable.
A3 `npx vitest run test/accountDeletePlans.test.ts`: the sweep deletes prefix+search-id keys and keeps near-misses.
A4 `swift test --filter SearchClientIdentityTests`: the request EQUALS PlanHTTPRequest(url .../search, POST, headers
   IdentityHeaders.json(device, account, bearer), body) for {no account, account, account+session}; a 401 to the Bearer
   re-sends once; no install id -> zero requests.
A5 `swift test --filter PlaceSearchCopyTests`: every SearchOutcome case -> its exact PlaceSearchAnswer; the reader's
   `place` table (valid -1 and -(2^53-1); 0, -0, 1, -01, -(2^53), " -1", number, bool, null, "" -> unreadable).
A6 `swift test --filter PlaceSearchSubmitTests`: typing -> 0 calls, submit -> exactly 1 call (query, bias), blank -> 0;
   bias = start ?? destination ?? nil.
A7 privacy: `swift test --filter PlanClientSearchedPlaceTests`: the /plan body for a searched place EQUALS the
   recomputed bytes and holds exactly one coordinate at <= 2 dp (also for its reroute).
A8 ios-compile + ios-screenshot success; the plan-sheet search shot looked at. A9 the bare gates in the Brief green.
