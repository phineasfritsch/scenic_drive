---
id: T-0327
title: ops/route-autopsy - one command dumps a bad drive's per-edge GATE / M / E terms and the lambda trace, so a reported rat-run or dull route becomes a pinned negative fixture before any weight changes (the plan's gate-failure playbook)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T17:16:10Z
lease_expires_at: 2026-10-09T03:16:10Z
worktree: .worktrees/T-0327
branch: task/T-0327
exclusive: []
touches: [ops/route-autopsy, ops/lib/, Sources/ScenicPlanCLI/, Sources/ScenicKit/, Tests/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: what ops/plan / scenic-plan already print (the per-edge term table, the bisection trace), what a 'plan id' can be when the server keeps no plans (T-0319's plan_token lives 12 h in KV and holds pins + lambda, not edges; a recorded fixture dir; or O/D/budget/departs-at re-planned against a recorded router) - rule the input honestly, never invent a server-side plan store; and where the per-edge GATE, M and E terms come from (ScenicKit scoring over the corpus segment ids, or GraphHopper path details)"
  - "ops/route-autopsy prints, for a recorded plan, every edge with its gate verdict (and which safety rule), M and E terms, scenic_score and length, plus the lambda trace (each bisection step's lambda and duration) and the RouteScore terms - full-equality golden over one recorded fixture; a --fixture flag writes the plan as a pinned NEGATIVE fixture under Tests/ (the playbook's 'a bad drive becomes a pinned negative fixture before any weight changes')"
  - "Wrapper discipline as ops/plan: no decision in bash, the engine is the Swift CLI; committed executable (P-OPS-01); usage on no args; seen red (a golden row changed) then green; a mutation population for any new Swift numeric code"
---
## Brief

Plan: Runtime lifecycles, Gate-failure playbook (`ops/route-autopsy <plan-id>` dumps per-edge GATE/M/E terms + lambda
trace; a bad drive becomes a pinned negative fixture before any weight changes) and M3's list. Owner intent (memory
owner-route-intent): one residential rat-run ends the relationship - this is the tool that turns that report into a
fixture. Measured 2026-10-08: ops/ has plan, score-review and etl-* but no route-autopsy; no task named it.

## Log
- 2026-10-08T17:15:53Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M3 ops/route-autopsy).
- 2026-10-08T17:16:10Z claimed by agent/claude-opus-5; lease until 2026-10-09T03:16:10Z
- 2026-10-08T17:20:41Z MEASURE then RULE (agent/claude-opus-5, before any code).
  MEASURED. (m1) `ops/plan 34.0669,-118.4399 34.0356,-118.6894 25 --recorded Tests/Fixtures/t0221/westwood-malibu`
  at 9e910336 printed `LAMBDA 3.25 evaluations=6 used-budget=false monotonicity-violated=false`,
  `ETA fastest=27m47s returned=31m44s ceiling=52m47s distance=29214.7m`, `TABLE rows=166 columns=way,highway,
  scenic_score,metres,seconds (seconds apportioned by metres; the scoring terms are not in the graph)`, 166 rows
  (49 of them `trunk 0`, PCH), `WAYPOINTS 9 of max 9`, exit 0. It prints NO bisection trace (only the winner and
  `evaluations=`), NO gate verdict, NO M/E, NO RouteScore. (m2) `LambdaSearch.search` keeps its samples in a local
  `seen` and returns `BudgetOutcome` without them; `ScenicPlanner.plan` calls `source.scenic(...)` once per
  evaluation, in evaluation order. (m3) Every recorded fixture's `recorded.details` is
  `scenic_score,road_class,osm_way_id` (t0221 headers; t0182/t0213-pair: 18/3/26 runs): the graph and the
  recordings carry the QUANTISED 0..10 score, never a term, a tag or a gate. (m4) The ETL's tagwriter
  (services/etl/etl/tagwriter.py `tags_for_row`) writes `scenic_<term>` + `scenic_gate` onto the PBF; no per-way
  terms table for any LA way is in the tree. (m5) services/api/src/planToken.ts:17 `PLAN_TOKEN_TTL_SECONDS =
  43_200`; index.ts:45 `PLANS` KV holds "each /plan answer's pins + lambda" - no edges. (m6) `SegmentScore.score`
  computes M and E as locals and exposes neither; ops/mutate/segmentscore.py anchors span the `let m` block, a
  blank line and `var e` at 8/12-space indentation.
  RULED. R1 (the plan id): there is no server plan store and this task builds none. A "plan" is what ops/plan
  takes - `<O> <D> <extra-minutes> --recorded <dir>` (or `--router <url>` for a live graph) - re-planned by the
  shipping `ScenicPlanner` against the recorded router. A plan_token is NOT an input: it holds pins + lambda for
  12 h and no edges, so it cannot reproduce per-edge terms. R2 (GATE/M/E source): ScenicKit over per-way input,
  never the graph: GATE = `Gates.decide(tags)`, M and E = `SegmentScore`'s own arithmetic, score =
  `SegmentScore.score(for:)`. The per-way input is `--terms <json>` (`{"source":..,"ways":{"<osm_way_id>":
  {"tags":{..},"terms":{..}}}}`, SegmentTerms' field names; highway/surface read from `tags`). A way with no
  entry prints `-` in GATE/M/E/score, never a default. Converting the ETL's tagged output into that file is a
  follow-up task, not built here. R3 (M and E exposed, not re-derived): `SegmentScore.axes(for:)` returns
  `(drive, scenery)` holding the existing `let m`/`var e`/byway lines verbatim at the same indentation (m6's
  anchors keep matching); `score(for:)` calls it. One formula in the tree. R4 (lambda trace): a recording
  `RouteSource` wrapper in ScenicPlanCLI logs each `scenic(lambda)` call and duration in order; the fit verdict
  per step is `duration <= plan.ceiling`. No change to LambdaSearch. R5 (RouteScore terms): `RouteScore(edges:)`
  over the chosen route's table rows as `ScoredEdge(length: metres, score: scenic_score/10)` (ScoredEdge.swift's
  own normalisation); rows with no score are excluded and their metres printed. R6 (--fixture <dir>): refused
  unless `--recorded`, unless a path component of `<dir>` is `Tests`, and if `<dir>` exists; it copies fastest.json
  + exactly the traced lambda files + the terms file, writes `fixture.json` (verdict "negative", the arguments,
  the chosen lambda, the chosen way ids) and `autopsy.txt` = the autopsy RE-RUN against the written dir (so the
  pinned text is what the fixture itself reproduces). R7 (golden): full equality of `AutopsyCommand.run` over
  t0221/westwood-malibu + a committed terms file `Tests/Fixtures/t0327/westwood-malibu-terms.json` that is
  SYNTHETIC (its `source` says so): four way ids of that route with hand-chosen terms, one carrying
  `access=private` so a refused verdict is exercised. No real terms are invented as measured. R8 (wrapper):
  `ops/route-autopsy` execs `scenic-plan --autopsy "$@"`, usage on no args, exit 2; committed 100755. R9: the
  first REAL negative fixture lands with the owner's first bad-drive report; a replay test over
  Tests/Fixtures/negative/ is not added now because its population is empty (a vacuous test). R10 (population):
  new numeric Swift (AutopsyReport/AutopsyCommand) gets ops/mutate/autopsy*.py with a literal floor.
  P-PROD-01 (pins_affected) stays TODO: it is the three-implementation parity pin (pending T-0012); this tool
  prints the ScenicKit leg only and does not satisfy it.
- 2026-10-08T17:50:37Z RED, GREEN, GOLDEN RED->GREEN (agent/claude-opus-5).
  RED FIRST, by name: with `AutopsyCommand.run` a stub returning `[]` (real AutopsyArguments/Terms/Fixture/
  Tracer), `swift test --filter RouteAutopsy` printed 6 of 7 named failures - "the autopsy of westwood-malibu
  equals its golden, every line", "a way the terms file does not carry prints dashes, never a default",
  "--fixture writes the traced recordings, the terms, fixture.json and an autopsy that replays", "each way in
  the terms file prints its gate, M, E and score from ScenicKit", "every trace step is a lambda the search
  measured, at the raw time of its recording", "--fixture refuses outside Tests/, over an existing directory,
  and without --recorded" - `Test run with 7 tests in 2 suites failed ... with 14 issues`. The 7th ("no
  arguments is a usage refusal") was green because the parser was already real.
  GREEN: `ops/route-autopsy` with no args printed its usage + example, exit 2. `ops/route-autopsy
  34.0669,-118.4399 34.0356,-118.6894 25 --recorded Tests/Fixtures/t0221/westwood-malibu --terms
  Tests/Fixtures/t0327/westwood-malibu-terms.json` exit 0, 183 lines, committed as the golden
  Tests/Fixtures/t0327/westwood-malibu.autopsy.txt (no CR). Its trace: `STEP 1 0 1623.696 yes`, `STEP 2 4 3578.870
  no`, `STEP 3 2 1667.261 yes`, `STEP 4 3 1667.261 yes`, `STEP 5 3.5 3578.870 no`, `STEP 6 3.25 1904.238 yes`;
  `ROUTESCORE value=0.226 mean=0.251 p90=0.600 dud=0.500 episodes=0 honest-failure=true scored=29214.4m
  unscored=0.0m`; terms rows `909518997 ... allowed 0.433 0.266 0.315`, `399156621 ... allowed 0.763 0.644 0.683`,
  `675540508 trunk 0 allowed 0.110 0.491 0.000`, `1073769540 ... refused:noAccess 0.313 0.310 0.218`.
  `swift test --filter "RouteAutopsy|SegmentScore|PlanCLI|ScenicPlan"`: `Test run with 84 tests in 15 suites
  passed`. FINDING (not fixed here, owner-intent memory): the engine ISSUES this plan although its own
  RouteScore calls it an honest failure (0.226 < 0.45) - half its metres are PCH trunk at score 0; ops/plan
  never consults RouteScore. That is exactly the "dull route" report this tool exists to turn into a fixture.
  GOLDEN SEEN RED THEN GREEN: row `399156621` M changed 0.763 -> 0.764 in the golden file -> `the autopsy of
  westwood-malibu equals its golden, every line` recorded 2 issues (`line 81: printed ... golden ...`), `Test run
  with 7 tests in 2 suites failed ... with 2 issues`; restored (git diff empty) -> `Test run with 7 tests in 2
  suites passed`.
  DIGESTS: PINNED_ROOT_SOURCES re-approved in place (table order kept, no trailing newline kept):
  SegmentScore.swift 42cc8f0f31cd -> 03db04e14e81, main.swift b83829e5b33d -> 704d401c8cb4, NEW AutopsyArguments
  1d439fc1a254, AutopsyCommand b57669ec5a7f, AutopsyFixture 38ee3e58e302, AutopsyReport b6c3c33a1b17, AutopsyTerms
  90c3fc9d2635, TracingRouteSource c5219fbecfc1. ops/route-autopsy committed 100755.
  POPULATION: ops/mutate/autopsy.py (+ _mutations, _run; menu.py's shape) - 17 mutations over all six new files,
  1 EQUIVALENT with witness, floors 17/1/2; `--prove-floor`: `FLOOR PROOF OK: 7 of 7 arms refused and the
  control did not`; `check-mutate-population.py`: `P-PROC-06: every added module is covered or allowlisted; the
  floor of 143 holds`.
- 2026-10-08T18:40:00Z MUTATION RUNS at 2de50b0b (agent/claude-opus-5). `python ops/mutate/autopsy.py`: BASELINE
  exit=0, `caught by the test that names it: 17 of 17 (wrong killer 0, trapped 0, compile-only 0, MISSED 0,
  skipped 0)`, the EQUIVALENT entry MISSED as required, `MUTATE OK caught=17/17 equivalent_caught=0`, exit 0.
  `--prove-vacuity`: `VACUITY PROOF OK: with the 2 test file(s) emptied, caught=0 (need 0) and MISSED=17 of 17`.
  SegmentScore.swift's existing population (ops/mutate/segmentscore.py, 64+2 entries, >1 h on this box) was
  started and STOPPED by me after ~10 min under the owner's faster-verification rule (the change is an extract
  with every moved line kept verbatim at the same indentation, R3); the stop left one mutant in SegmentTerms.swift,
  restored with `git checkout --` (git status clean but for this file). In its place a static check: every
  `old` anchor of segmentscore.py's MUTATIONS + EQUIVALENT found verbatim in the current files - `ANCHORS 66 of
  66 found verbatim (0 gone)` - so no entry would SKIP; the SegmentScore suites are green in the 84-test run
  above. A full segmentscore.py run is the reviewer's to buy if it wants one.
