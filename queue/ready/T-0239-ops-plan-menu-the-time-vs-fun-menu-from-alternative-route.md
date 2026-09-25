---
id: T-0239
title: ops/plan --menu - the time-vs-fun menu for one trip, from alternative_route over the lambda ladder (max_exploration_factor 2.0), deduplicated, a Pareto frontier of extra minutes against fun km, recorded and replayed offline
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/Menu/, Sources/ScenicPlanCLI/, Tests/ScenicKitTests/Menu/, Tests/ScenicPlanCLITests/, Tests/Fixtures/t0239/, Tests/Fixtures/t0182-recorder/, ops/plan, ops/mutate/, ops/lib/mutate-population-allowlist.json]
pins_affected: [P-SAFE-04]
reviewer: null
depends_on: [T-0182]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURED population (quoted here, the frontier probe of 2026-09-25, .artifacts/frontier/SUMMARY.md, t0213 canyon-window graph, GraphHopper 11): at alternative_route's default max_exploration_factor 1.0 the T4 trip (Zuma -> Agoura) returns ONLY the fastest path at every lambda; at 2.0 (max_paths 4, max_weight_factor 2.0, max_share_factor 0.7) the five trips yield 6/7/3/6/7 distinct routes (way-id Jaccard >= 0.9 = same). RULED in the Log before code: the hints, the lambda ladder {0,2,4,6,8}, the dedup threshold, and the frontier's axes - DEFAULT extra minutes against fun km (distance on scenic_score >= 6), a route kept only if it adds >= 2 fun km over every quicker kept route, capped at +45 min; fun share and mean score are displayed, not ranked on (the owner's taste: T4's Latigo Canyon route at +16.6 min has the most fun km, 19.7, but a lower share, 56%, than The Snake's 58% at +5.4 min, because 8 km of PCH leads to it)"
  - "the menu is a ScenicKit type (Foundation only) computed from recorded paths: a Linux test over RECORDED fixtures for T1 (Topanga -> Malibu) and T4 (Zuma -> Agoura) asserts the menu rows (extra minutes to 0.1, fun km to 0.1) and that T4's menu contains a row whose roads include Latigo Canyon Road; RED first by name with the frontier rule inverted, then green; the fixtures are recorded by the committed recorder, not the probe's scratch Java"
  - "the budget stays a ceiling: every menu row satisfies ETA <= fastest + its displayed extra minutes, and 'ops/plan --menu <O> <D> --max 20' prints no row above +20 (P-SAFE-04's property, a test by name); each row prints an Apple Maps URL with <= 9 waypoints from the committed handoff builder"
  - "the new numeric module ships its population under ops/mutate/ with a literal floor (frontier comparison, dedup threshold, fun-km threshold, the cap); MUTATE OK and --prove-vacuity quoted"
---
## Brief

The owner asked (2026-09-25): 'could we also have an inverse search where it show (within reason) the most top rated
routes from a to b with also filterable by time?' and 'you know to answer the question, how much more would I have to
drive to have a fun drive'. The lambda sweep alone gives at most 2 distinct routes per trip; the probe showed
alternative_route at exploration factor 2.0 gives the menu. Answers from the probe, free-flow, no traffic:
Topanga -> Malibu: +12 min takes the fun share from 34% to 71%, +17 to +20 min gives Saddle Peak (82-84%).
Topanga -> Agoura: the fastest is already 81% fun, +4.8 min gives Saddle Peak and Stunt (92%).
Zuma -> Agoura: +5.4 min gives Mulholland and The Snake, +16.6 min gives all of Latigo Canyon.
Owner-facing preview of the probe's menus: .artifacts/preview/route-menu.html (gitignored).

## Log
- 2026-09-25T23:39:48Z filed by agent/claude-opus-5 (orchestrator) from the frontier probe (one agent, exploration output only). FOR THE OWNER: rank the menu by fun km (Latigo wins T4) or by fun share (The Snake wins)? Default ruled: fun km.
