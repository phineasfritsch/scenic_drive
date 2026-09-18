---
id: T-0158
title: Worker custom model - buildCustomModel(lambda, closures) and rejectCustomModel - the per-request model never carries road_access or surface, and its multipliers are monotone in lambda
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T19:13:08Z
lease_expires_at: 2026-09-19T03:13:08Z
worktree: .worktrees/T-0158
branch: task/T-0158
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "SETUP and CONTROL, in this worktree: `cd services/api && npm ci` -> `added 85 packages, and audited 86 packages in 30s` (node_modules is gitignored and was absent on this box - T-0040; still present in this worktree for round 2). The CONTROL re-derived at THIS head with both new test files excluded: `npx vitest run --exclude 'test/customModel.test.ts' --exclude 'test/customModelGate.test.ts'` -> `Test Files  4 passed (4)` / `Tests  71 passed (71)`. At the final commit, bare: `npx vitest run` -> `Test Files  6 passed (6)` / `Tests  125 passed (125)`, exit 0. 54 new tests over two new test files: 37 in round 1, 17 added in round 2 for the review's B1, B2 and B3"
  - "`bash ops/test` was NOT re-run in round 2: the harness forbade it and full `bash ops/check-pins` in this session, so this line is the owner's round-1 run at a05a70d and nothing more - bare -> `RO-GRAMMAR OK 30 cases`, `TESTS linux=810/76 ios=skipped failed=0 skipped=0`, `OK`, exit 0, with `.artifacts/vitest.json` numTotalTests 108, numFailedTests 0. The Worker count ops/test:32-40 parses is 125 at this head, not 108, so the linux total moves up by 17; that arithmetic is NOT a run. CI does run it (`npm ci` for services/api, .github/workflows/linux-core.yml:61), so `gh pr checks 91` is what stands behind this line at the pushed head. STILL OPEN"
  - "strict typecheck of the THREE files: `npx tsc --noEmit --ignoreConfig --strict --target es2022 --module es2022 --moduleResolution bundler --skipLibCheck --lib es2022 --types vitest src/customModel.ts test/customModel.test.ts test/customModelGate.test.ts` -> no output, `tsc-exit=0`. The package HAS a tsconfig.json and a `typecheck` script, and `npx tsc --noEmit` exits 1 on `error TS2688: Cannot find type definition file for '@cloudflare/workers-types/2023-07-01'` - which is NOT this task's: with the new files moved out of the tree, that same command prints that same single error and exits 1 (control run recorded in the Log, round 1; not re-run in round 2). tsconfig.json is outside touches:; STILL OPEN"
  - "the 300-line cap: `wc -l services/api/src/customModel.ts services/api/test/customModel.test.ts services/api/test/customModelGate.test.ts` -> `287`, `294`, `211`, all under 300. `bash ops/lib/check-line-cap` bare -> `P-SRC-02: 64 Swift files tracked (Sources=24, Tests=32, apps/ios=8), none over 300 lines`, exit 0 - and that gate reads Swift only, so it covers none of the three; the cap is held here by the wc count, not by it (the gap is T-0058's, still in queue/claimed). Headroom is now 13 and 6 lines: the next change to either file splits the closures validation out into src/closureAreas.ts. STILL OPEN"
  - "`bash ops/check-pins --source-only` bare -> `PINS ok=9 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only`, `pins-exit=0`. `bash ops/queue-check` bare -> `QUEUE OK (153 tasks)`, `queue-exit=0`. Neither piped: a pipe would swallow the exit status"
  - "RED 1, re-run at the final tree: the >= 4 band made to GROW with lambda (`mid: 1 + 0.5 * lambda` in scenicBandMultipliers) -> `Tests  8 failed | 117 passed (125)`. By name: `(c) ... > mid band (scenic_score >= 4) is monotone non-increasing over the grid`, `(c) ... > the built model's multipliers are monotone non-increasing over the grid`, `(c) ... > both falling bands stay monotone non-increasing across the grid's interval midpoints` (the new N1 test), `(c) ... > matches the plan's multipliers at lambda 1`, `at lambda 2`, `at lambda 8`, `(c) ... > matches 1/(1+0.5*lambda) and 1/(1+lambda) as doubles at lambda 0, 1, 2 and 8`, `(a) ... > emits the plan's clause shape: if / else_if / else with string multiply_by`. Restored"
  - "RED 2, re-run at the final tree: a `surface` clause smuggled into the built model (`{ if: 'surface == ASPHALT', multiply_by: '1' }` appended to priority) -> `Tests  13 failed | 112 passed (125)`. By name: the seven `(a) ... > built model never mentions road_access or surface at lambda 0 / 0.25 / 0.5 / 1 / 2 / 4 / 8`, `(a) ... > drops closure feature properties so a poisoned KV feed cannot smuggle surface in`, `(a) ... > emits the plan's clause shape`, `(a) ... > keys areas the way the closure clause references them`, `(b) ... > accepts the built model, with and without closures`, and the two new `(h) ... > drops foreign members on the closure geometry instead of forwarding them` and `(h) ... > shares no array with the feed, so poisoning the feed after the build changes nothing`. Restored"
  - "RED 3, re-run at the final tree: rejectCustomModel made to check only top-level keys (no recursion, no string values) -> `Tests  13 failed | 112 passed (125)`. By name: the five round-1 ones (`(b) ... > refuses road_access in a top-level condition`, `... nested else_if clause`, `... surface hidden in an areas feature property`, `... used as an object KEY, not only as a value`, `... refuses ROAD_ACCESS whatever its case`), all five new `(f)` tests, and `(g) ... > refuses a body nested past 64 levels, naming the depth`, `(g) ... > refuses at 65 levels even when the deep leaf is the forbidden token itself`, `(g) ... > walks a body just under the cap to the bottom and refuses it by the TOKEN, not the depth`. Restored"
  - "RED 4 = the reviewer's B1 mutant, `mentioned()`: `lowered.includes(word)` -> `lowered.startsWith(word)`. REPRODUCED first at a05a70d, alone: `Tests  108 passed (108)`, exit 0, nothing red. At the final tree -> `Tests  5 failed | 120 passed (125)`, by name all five new ones: `(f) ... > refuses road_access in the MIDDLE of a condition, not only at its start`, `(f) ... > refuses a key that merely CONTAINS a forbidden token`, `(f) ... > refuses a forbidden token that only ENDS a string value`, `(f) ... > refuses a forbidden token mid-string inside an areas property value, several levels down`, `(f) ... > refuses an upper-case token in the MIDDLE of a condition`. Restored"
  - "RED 5 = the reviewer's B2 mutant, the MAX_WALK_DEPTH branch: the depth refusal -> `return null`. REPRODUCED first at a05a70d, alone: `Tests  108 passed (108)`, exit 0, nothing red. At the final tree -> `Tests  2 failed | 123 passed (125)`: `(g) ... > refuses a body nested past 64 levels, naming the depth` and `(g) ... > refuses at 65 levels even when the deep leaf is the forbidden token itself`. The third `(g)` test stays green under it by design - a body just under the cap must be refused by the token, not the depth. Restored"
  - "RED 6 and RED 7 = the two halves of B3. (6) `{ ...geometry, type, coordinates }` spread into the emitted geometry: REPRODUCED at a05a70d, alone, `Tests  108 passed (108)`; at the final tree -> `Tests  1 failed | 124 passed (125)`: `(h) ... > drops foreign members on the closure geometry instead of forwarding them`. (7) the coordinates pass-through (rebuild called and discarded, `coordinates: geometry.coordinates` returned) -> `Tests  1 failed | 124 passed (125)`: `(h) ... > shares no array with the feed, so poisoning the feed after the build changes nothing`. Both restored. At the UNFIXED head the six remaining `(h)` tests are red on their own, no mutant needed - that is B3 reproduced as a false claim, not as a survived mutant"
  - "TWO NEIGHBOURING MUTANTS nobody asked for, each alone, each restored. (i) case folding removed, `const lowered = text.toLowerCase()` -> `const lowered = text` -> `Tests  2 failed | 123 passed (125)`: `(b) ... > refuses ROAD_ACCESS whatever its case` and `(f) ... > refuses an upper-case token in the MIDDLE of a condition`. (ii) the areas walk skipping array elements (the Array.isArray branch never recursing) -> `Tests  9 failed | 116 passed (125)`: the five round-1 `(b)` refusal tests and four of the five `(f)` tests - everything that reaches a token through `priority[0]` or `features[0]`. `git status --short` clean of src after every one of the nine mutants"
  - "the plan's literals are TYPED OUT, never computed from the code under test: test/customModel.test.ts PLAN_MULTIPLIERS holds lambda 0 -> 1/1/1, lambda 1 -> 1/0.666667/0.5, lambda 2 -> 1/0.5/0.333333, lambda 8 -> 1/0.2/0.111111 for the (>= 7, >= 4, else) bands, and a second test pins the unrounded doubles 0.6666666666666666, 0.3333333333333333, 0.1111111111111111. test/customModelGate.test.ts writes out every refusal string by hand - `custom model mentions road_access at priority[0].if`, `custom model mentions surface at custom_model.areas.features[0].properties.why`, `closure feature 0 ring 0 position 0 is not two finite numbers (string, number)`, `closure feature 0 ring 0 does not close on its first position`, `closure feature 0 ring 0 needs at least 4 positions (3)` - and the emitted ring as literal pairs. Recordable N1 taken: the midpoint sample is pinned as `[0, 0.125, 0.25, 0.375, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8]`, typed out"
  - "NOT IN THIS TASK, on the record: nothing is wired. index.ts is untouched, no /plan route exists, no upstream call carries the model and rejectCustomModel is called by no route yet (the Brief's instruction). services/routing/profiles/ and pins/PINS.yaml are untouched - T-0012 and T-0149 own them, so P-SAFE-01 gains no pin assertion here. At the final commit `git diff --stat $(git merge-base origin/main HEAD) HEAD -- services/api` -> `3 files changed, 792 insertions(+)` (287 + 294 + 211) and `git diff --name-only $(git merge-base origin/main HEAD) HEAD` lists those three plus this task file, nothing else. The branch is still based on 91c78ef and has NOT been rebased"
---
## Brief

Filed from the 2026-09-18 12:13 panel (CODE lens, grounded; its profiles-and-pin half was ruled out of
scope by the grounding pass - see the end). The lambda -> GraphHopper-request seam is owned by nothing today:
`LambdaSearch.search` takes an injected `measure: (Double) throws -> TimeInterval`
(`Sources/ScenicKit/Budget/LambdaSearch.swift:57`), and a case-insensitive grep of `services/api/src` for
`custom_model|road_access|surface` returns zero hits. The plan puts both halves in the Worker: the
per-request custom model (plan :105-109, `ch.disable=true`, lambda from the budget search, closures as
`areas`) and the refusal ("Worker rejects custom models touching road_access/surface", plan :98).

It is testable on the Windows box today with no container and no graph: `ops/test:33-36` runs
`npx vitest run` for `services/api` whenever its `package.json` exists, and `vitest.config.ts` plus four test
files are on main. (`node_modules` is absent on this box today - T-0040 - so the fixer installs locally or
runs in CI; say which in the Log.)

**Do, RED first:**
1. `services/api/src/customModel.ts`: `buildCustomModel(lambda: number, closures: GeoJSON | null)` returning
   the plan's per-request model - priority rules for `scenic_score >= 7` (x1), `>= 4` (x `1/(1+0.5*lambda)`),
   else (x `1/(1+lambda)`), the residential anti-rat-run rule (`road_class == RESIDENTIAL && scenic_score < 7`
   x0.5), and the closures rule over at most 50 polygons - and `rejectCustomModel(body)` refusing any
   request-supplied model whose serialised form mentions `road_access` or `surface`.
2. `services/api/test/customModel.test.ts`: (a) the built model, serialised, NEVER contains `road_access` or
   `surface`, for lambda across a grid including 0 and 8; (b) `rejectCustomModel` refuses a model that
   mentions either, in a condition or a nested clause, and accepts the built one; (c) for each scenic_score
   band the multiplier is monotone NON-INCREASING in lambda over the grid and equals 1 at lambda = 0 - the
   static half of "T(lambda) monotone" before any graph exists; (d) lambda outside [0, 8], NaN and negative
   are refused, not clamped silently; (e) more than 50 closure polygons is refused by name. Literals typed
   out from the plan, never computed from the function under test.
3. Red demonstrations by name: the >= 4 band's factor changed to grow with lambda -> (c) fails; a `surface`
   clause smuggled into the built model -> (a) fails.

**NOT in this task (ruled by the grounding pass):** `services/routing/profiles/*.json` - serial-only files
already in T-0012's touches (`queue/backlog/T-0012-*.md:12`), and P-PROD-01 is pending T-0012; and any pin
in `pins/PINS.yaml` - the safety-gate pin is T-0149's, behind PR #82. What stays blocked on a real graph:
measured duration monotonicity, the bisection's 12-request cap against a live router, `scenic_score` as an
encoded value (T-0031), closures geometry.

Sequenced after T-0154 (the scorer contract) and the T-0024/T-0027 fix passes, and after T-0157.

## Log
- 2026-09-18T19:05:00Z filed by agent/claude-fable-5-1 from the 12:13 panel's grounded synthesis (CODE lens C4, C6, C7 grounded; C5's cited grep hits did not exist and C8's touches collided with T-0012 and T-0149 - both corrected here). Not started.
- 2026-09-18T19:13:08Z claimed by agent/claude-opus-5; lease until 2026-09-19T03:13:08Z
- 2026-09-18T19:16:00Z READ IN FULL, agent/claude-opus-5: this Brief; CLAUDE.md; the plan's `### GraphHopper
  profiles` block (:95-111, both JSON objects), Problem A (:113-120) and P-SAFE-01 (:242). For house style:
  services/api/src/upstream.ts (one door, injectable `fetchImpl`, typed error classes carrying the verdict),
  src/ro.ts + test/ro.test.ts (`readOnlyProblem(sql): string | null` - a reason or null - and its comment on
  why a bound must never be derived from the value it bounds), src/quota.ts, src/index.ts, package.json,
  tsconfig.json (`strict: true`), vitest.config.ts (@cloudflare/vitest-pool-workers over wrangler.jsonc).
- 2026-09-18T19:16:38Z SETUP + CONTROL. `cd services/api && npm ci` in THIS worktree (node_modules is
  gitignored and was absent - T-0040): `added 85 packages, and audited 86 packages in 30s`. Control run of the
  EXISTING suite, before writing anything: `npx vitest run` ->
  ```
   Test Files  4 passed (4)
        Tests  71 passed (71)
  ```
- 2026-09-18T19:20:14Z GREEN after adding src/customModel.ts + test/customModel.test.ts: `Test Files  5 passed
  (5)` / `Tests  108 passed (108)`. 108 - 71 = 37 new tests.
- 2026-09-18T19:22:00Z RED 1 verbatim, by name. Mutation: scenicBandMultipliers's `>= 4` band changed from
  `1 / (1 + 0.5 * lambda)` to `1 + 0.5 * lambda`, so it GROWS with lambda.
  ```
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > emits the plan's clause shape: if / else_if / else with string multiply_by
   FAIL  test/customModel.test.ts > (c) the band multipliers are monotone non-increasing in lambda > mid band (scenic_score >= 4) is monotone non-increasing over the grid
   FAIL  test/customModel.test.ts > (c) the band multipliers are monotone non-increasing in lambda > the built model's multipliers are monotone non-increasing over the grid
   FAIL  test/customModel.test.ts > (c) the band multipliers are monotone non-increasing in lambda > matches the plan's multipliers at lambda 1
   FAIL  test/customModel.test.ts > (c) the band multipliers are monotone non-increasing in lambda > matches the plan's multipliers at lambda 2
   FAIL  test/customModel.test.ts > (c) the band multipliers are monotone non-increasing in lambda > matches the plan's multipliers at lambda 8
   FAIL  test/customModel.test.ts > (c) the band multipliers are monotone non-increasing in lambda > matches 1/(1+0.5*lambda) and 1/(1+lambda) as doubles at lambda 0, 1, 2 and 8
   Test Files  1 failed | 4 passed (5)
        Tests  7 failed | 101 passed (108)
  ```
  Restored; suite back to 108 passed.
- 2026-09-18T19:24:00Z RED 2 verbatim, by name. Mutation: `{ if: "surface == ASPHALT", multiply_by: "1" }`
  appended to the built model's priority array.
  ```
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > built model never mentions road_access or surface at lambda 0
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > built model never mentions road_access or surface at lambda 0.25
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > built model never mentions road_access or surface at lambda 0.5
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > built model never mentions road_access or surface at lambda 1
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > built model never mentions road_access or surface at lambda 2
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > built model never mentions road_access or surface at lambda 4
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > built model never mentions road_access or surface at lambda 8
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > drops closure feature properties so a poisoned KV feed cannot smuggle surface in
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > emits the plan's clause shape: if / else_if / else with string multiply_by
   FAIL  test/customModel.test.ts > (a) the built model never names a safety encoded value > keys areas the way the closure clause references them
   FAIL  test/customModel.test.ts > (b) rejectCustomModel refuses a request-supplied model that touches the safety gates > accepts the built model, with and without closures
   Test Files  1 failed | 4 passed (5)
        Tests  11 failed | 97 passed (108)
  ```
  Restored. Note the last line: rejectCustomModel refuses what a smuggled buildCustomModel produces, so the
  two halves check each other and not only themselves.
- 2026-09-18T19:26:00Z RED 3 verbatim, by name. Mutation: rejectCustomModel's body replaced by a loop over
  `Object.keys(body)` only - no recursion, no string values.
  ```
   FAIL  test/customModel.test.ts > (b) rejectCustomModel refuses a request-supplied model that touches the safety gates > refuses road_access in a top-level condition
   FAIL  test/customModel.test.ts > (b) rejectCustomModel refuses a request-supplied model that touches the safety gates > refuses road_access hidden in a nested else_if clause
   FAIL  test/customModel.test.ts > (b) rejectCustomModel refuses a request-supplied model that touches the safety gates > refuses surface hidden in an areas feature property
   FAIL  test/customModel.test.ts > (b) rejectCustomModel refuses a request-supplied model that touches the safety gates > refuses a forbidden encoded value used as an object KEY, not only as a value
   FAIL  test/customModel.test.ts > (b) rejectCustomModel refuses a request-supplied model that touches the safety gates > refuses ROAD_ACCESS whatever its case
   Test Files  1 failed | 4 passed (5)
        Tests  5 failed | 103 passed (108)
  ```
  Restored.
- 2026-09-18T19:29:00Z TYPECHECK, and whose failure it is. `npx tsc --noEmit` (the package's `typecheck`
  script; tsconfig.json exists, `strict: true`) -> `error TS2688: Cannot find type definition file for
  '@cloudflare/workers-types/2023-07-01'`, exit 1. CONTROL: both new files moved out of src/ and test/, same
  command -> the same single error, `tsc-exit-control=1`. The installed @cloudflare/workers-types 5.x has no
  dated entrypoint (node_modules/@cloudflare/workers-types/ holds index.d.ts and experimental/ only), so this
  is main's, not mine, and tsconfig.json is outside `touches:` - see STILL OPEN. The two new files DO
  typecheck strict: `npx tsc --noEmit --ignoreConfig --strict --target es2022 --module es2022
  --moduleResolution bundler --skipLibCheck --lib es2022 --types vitest src/customModel.ts
  test/customModel.test.ts` -> no output, `strict-files-exit=0`.
- 2026-09-18T19:33:31Z RULINGS.
  1. `rejectCustomModel(body): string | null` RETURNS the reason (null = may be forwarded), mirroring
     `readOnlyProblem` in src/ro.ts; `buildCustomModel` THROWS `CustomModelError` carrying a `reason` code
     (`lambda_not_finite`, `lambda_out_of_range`, `closures_not_feature_collection`, `closure_not_polygon`,
     `too_many_closure_polygons`). A builder that returned a refusal is ignorable; a gate that threw would
     have to be caught by every route. Tests assert on `.reason`, i.e. by name, not on message text.
  2. Never clamps. lambda outside [0, 8], NaN, +/-Infinity all throw. A clamp would turn a caller bug into a
     route that is silently not the one asked for, and the bisection's feasibility argument (plan :116)
     depends on the bracket being real.
  3. The refusal matches SUBSTRING, case-insensitively, over keys AND string values, at any depth (cap 64
     levels, deeper is refused rather than walked). `ROAD_ACCESS` and `surface_hint` are refused too.
     Over-refusing a client body costs one request; under-refusing routes a driver onto a private dirt track.
     Consequence written into the docstring: the Worker must add its own `details=surface,road_access`
     (plan :120) to the UPSTREAM request after this gate, never to the body it checks.
  4. A non-object body is refused with `custom model must be a JSON object` - including a bare array, which is
     `typeof "object"` but is not a custom model.
  5. `multiply_by` is a STRING, serialised at 6 decimals with trailing zeros trimmed
     (`Number(v.toFixed(6)).toString()`), so the `>= 7` band prints `1` exactly as plan :105 writes it and the
     model is byte-stable across boxes. Rounding cannot break monotonicity (rounding a non-increasing
     sequence leaves it non-increasing) and the doubles test pins the unrounded maths anyway.
  6. The plan's line 107, `{ "else": "multiply_by": "1 / (1 + λ)" }`, is not valid JSON. Emitted as
     `{ else: "", multiply_by: <low> }`, which is GraphHopper's else statement.
  7. `areas` features are REBUILT from geometry alone with `properties: {}` and a generated `id: closure_N`,
     referenced as `in_closure_1 || in_closure_2 || ...` exactly as plan :109-110 keys them. So a KV feed
     whose feature properties or `id` mention a safety encoded value cannot reach the router - asserted by
     `drops closure feature properties so a poisoned KV feed cannot smuggle surface in`.
  8. `ch.disable=true` (plan :104) is a request PARAMETER, not part of the custom model, so the builder does
     not emit it. Nothing is wired into index.ts, per the Brief.
- 2026-09-18T19:33:31Z STILL OPEN (not done here, deliberately or not at all):
  1. `npx tsc --noEmit` for services/api is red on main for a reason that is not this task's (TS2688 above).
     Fixing it means editing services/api/tsconfig.json, outside `touches:`; I did not edit it and I did not
     file a queue task for it (filing is not this task's). Flagged to the parent agent.
  2. Nothing calls either function. No /plan route exists; index.ts, wrangler.jsonc and the routing profiles
     are untouched. The seam is unit-tested and unused until the route lands.
  3. `bash ops/test` needs node_modules for the Worker tier; it passed here because I ran `npm ci` in this
     worktree. On a box without it, ops/test still fails with `FAIL: services/api exists but vitest produced
     no report` - T-0040's, untouched. CI does run `npm ci` (linux-core.yml:61).
  4. `ops/lib/check-line-cap` reads Swift only, so neither new .ts file is under a gate for the 300-line cap;
     224 and 278 by `wc -l`. T-0058 owns that gap.
  5. P-SAFE-01 gains no pin assertion: pins/PINS.yaml is T-0149's (behind PR #82) and out of `touches:`.
  6. Still blocked on a real graph, as the Brief says: measured duration monotonicity, the 12-request cap
     against a live router, `scenic_score` as an encoded value (T-0031), closure geometry correctness. This
     task is the STATIC half of `T(lambda)` monotone - it proves the multipliers are non-increasing, not that
     the returned ETA is.
- 2026-09-18T19:40:20Z EVERY acceptance line re-run at the final commit (1adbd5c, amended with this one Log
  line; src/customModel.ts and test/customModel.test.ts are byte-identical between the two commits, so every
  output below stands for the amended tree too). All identical to what is quoted above:
  `npx vitest run` -> `Test Files  5 passed (5)` / `Tests  108 passed (108)`, exit 0.
  `bash ops/test` -> `RO-GRAMMAR OK 30 cases`, `TESTS linux=810/76 ios=skipped failed=0 skipped=0`, `OK`,
  exit 0, with `.artifacts/vitest.json` numTotalTests 108 numFailedTests 0.
  `npx tsc --noEmit --ignoreConfig --strict ... src/customModel.ts test/customModel.test.ts` -> exit 0;
  `npx tsc --noEmit` -> the same lone TS2688, exit 1 (main's; control recorded above).
  `bash ops/check-pins --source-only` -> `PINS ok=9 skipped=12 pending=1 expired=0 failed=0 tier=linux
  source-only`, exit 0. `bash ops/lib/check-line-cap` -> `P-SRC-02: 64 Swift files tracked (Sources=24,
  Tests=32, apps/ios=8), none over 300 lines`, exit 0. `bash ops/queue-check` -> `QUEUE OK (153 tasks)`,
  exit 0. `wc -l` -> `224` and `278`. `git status --short` -> empty. origin/main moved under me while I worked
  (91c78ef -> ed73969, PR #89 / T-0154 merged), so the diffstat is taken against the merge base, not the
  moving ref: `git diff --stat $(git merge-base origin/main HEAD) HEAD -- services/api` ->
  `2 files changed, 502 insertions(+)`, and `git diff --name-only $(git merge-base origin/main HEAD) HEAD`
  lists exactly those two plus this task file. This branch has NOT been rebased onto ed73969.
- 2026-09-18T22:27:20Z **Record corrections from the read-only verification of this build, closed before review - agent/claude-fable-5-1
  (orchestrator), for the owner. The verifier reproduced the diff (two new files plus this one), the typed-out
  multiplier literals, the recursive walk over keys and string values with its depth cap, `npx vitest run` ->
  `Test Files 5 passed (5)` / `Tests 108 passed (108)`, `wc -l` 224/278, queue-check and the line cap; these are
  text.** (a) The 19:40:20Z entry says the final commit is "1adbd5c, amended with this one Log line"; the reflog
  shows two amends (a0bd082, then a25a2c1), and `git diff 1adbd5c a25a2c1` is this task file only (17+/1-) -
  the two source files are byte-identical across all three. (b) The three RED runs (7/11/5 failing) were not
  re-executed by the verifier - it checked that every failing test it names exists and that the counts fit the
  test structure. (c) `bash ops/test` -> `TESTS linux=810/76`, the pre-task control (`4 files / 71 tests`) and
  the strict `tsc` of the two files with the TS2688 control were the author's runs, not re-run.
- 2026-09-18T22:43:51Z REVIEW ROUND 1, FAIL - agent/rv1-pr91 (reviewer; not the owner agent/claude-opus-5, not the orchestrator agent/claude-fable-5-1). Reviewed at a05a70d == origin/task/T-0158, in a detached worktree .worktrees/rv1-pr91 (removed at the end; repo root `git status --short` empty). Judged `git diff 91c78ef...HEAD` because the branch is behind origin/main (886a8224).
  RE-RAN AT THE HEAD, all bare, all identical to what the acceptance block quotes: `npx vitest run` -> `Test Files  5 passed (5)` / `Tests  108 passed (108)`, exit 0; the CONTROL re-derived by me with `--exclude "test/customModel.test.ts"` -> `Test Files  4 passed (4)` / `Tests  71 passed (71)`, so 37 new tests is right; the strict `npx tsc --noEmit --ignoreConfig --strict ... src/customModel.ts test/customModel.test.ts` -> exit 0; `bash ops/check-pins --source-only` -> `PINS ok=9 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only`, exit 0; `bash ops/queue-check` -> `QUEUE OK (153 tasks)`, exit 0; `bash ops/lib/check-line-cap` -> `P-SRC-02: 64 Swift files tracked (Sources=24, Tests=32, apps/ios=8), none over 300 lines`, exit 0; `wc -l` -> 224 and 278. `gh pr checks 91` -> core pass, pins-source-only pass. NOT re-run by me: `bash ops/test`, full `bash ops/check-pins`, and the three RED runs (harness instruction; the correction entry already admits the verifier did not re-execute the REDs either). I did not fail the round on the pre-existing TS2688.
  RE-DID two typed-out literals by hand against plan :105-107: lambda 1 mid = 1/1.5 = 0.666667 (test:24) and lambda 8 low = 1/9 = 0.111111 (test:26). Both are genuine plan literals, not values computed from the function under test. The (c) block is right.
  THREE MUTATIONS nobody wrote, each alone, restored after each, `git status --short` empty every time. Control 108/108 exit 0 each time.
  M1 `mentioned()`:181 `lowered.includes(word)` -> `lowered.startsWith(word)` -> `Tests  108 passed (108)`, exit 0, NO named test red. Under it, `{priority:[{if:"road_class == MOTORWAY || road_access == PRIVATE",multiply_by:"1"}]}` is FORWARDED. BLOCKING B1: no (b) fixture puts a forbidden token anywhere but at the start of a string or as a whole key, so ruling 3's SUBSTRING half is untested; RED 3 proved recursion, not match position.
  M2 `walk()`:187 depth cap -> `return null` -> `Tests  108 passed (108)`, exit 0, NO named test red; a throwaway probe under the same mutant (created, run, deleted) showed a 70-deep body carrying `road_access == NO` returns null, i.e. forwarded. BLOCKING B2: ruling 3 rules the 64-level cap explicitly and nothing tests it.
  M3 `closureGeometries()`:138 -> `{ ...geometry, ... }` (geometry foreign members reach the router) -> `Tests  108 passed (108)`, exit 0, NO named test red.
  HEAD-LEVEL PROBE, no mutation: a feed with `geometry.coordinates = [[["surface == GRAVEL", 37.7]]]` makes `JSON.stringify(buildCustomModel(2, feed))` match /surface/i. BLOCKING B3: `closureGeometries` checks only `Array.isArray(coordinates)` and passes the array through, so the PR body's "a poisoned KV feed cannot smuggle surface into the router", the docstring at :144-145 and the test name at test:55 all claim more than holds. Ruling 7 as written (properties and id) is true; the wider sentences are not. Not a clause injection - coordinates are not conditions - but it is an overstated safety claim.
  RULINGS: I dispute none. Ruling 3's `details=surface,road_access` reasoning is CORRECT - `details` is a request parameter the Worker composes downstream of the gate (plan :120), so the substring rule cannot refuse the Worker's own request, and the over-refusal direction is right under P-SAFE-01 (plan :242). Rulings 1, 2, 5, 6, 8 all check out against plan :104-116.
  RECORDABLE (no round cost): monotonicity is pinned over 7 literal grid points only while the bisection evaluates arbitrary lambda - sample the interval midpoints; if the route task ever hands rejectCustomModel the whole /plan body, a client place name containing "surface" is refused (note it in that Brief); at lambda 0 the model still carries the residential x0.5 and closures x0 clauses, so "lambda=0 is the fastest route" holds against the scenic profile and not against `car_fast` - a note for the bisection task, not a defect here since the code matches the plan's JSON; the 300-line cap on these two .ts files rests on `wc -l` alone (disclosed, T-0058).
  VERDICT FAIL, round 1. state stays `claimed`, reviewer stays null, the task file stays in queue/claimed/. Nothing in the PR was changed by me.
- 2026-09-18T23:14:56Z ROUND 2 FIX for the owner (agent/claude-opus-5), acting on review round 1 (agent/rv1-pr91, entry
  above, appended verbatim before a line of this was written). All three blocking findings REPRODUCED first,
  then fixed; nine mutants run in this round, each alone, each restored from a copy of the fixed file.
  REPRODUCED AT a05a70d, each mutant alone, `npx vitest run` bare, control `Test Files  5 passed (5)` /
  `Tests  108 passed (108)` exit 0 before each: B1 `lowered.includes(word)` -> `lowered.startsWith(word)` ->
  `Tests  108 passed (108)`, nothing red. B2 the MAX_WALK_DEPTH refusal -> `return null` ->
  `Tests  108 passed (108)`, nothing red. B3 `{ ...geometry, type, coordinates }` -> `Tests  108 passed (108)`,
  nothing red. `git status --short` after each restore showed only this task file, never a source file. All
  three findings stand exactly as the reviewer wrote them; I dispute none of them and none of the rulings.
  WHAT CHANGED. (1) test/customModelGate.test.ts, NEW (211 lines), one concern - the gate. customModel.test.ts
  was at 278 and would have crossed the 300-line cap. `(f)` five tests put a forbidden token in the MIDDLE of a
  condition, in the MIDDLE of a key, at the END of a string, mid-string inside an areas property value four
  levels down, and upper-case mid-condition; each expects the exact refusal string, e.g.
  `custom model mentions surface at custom_model.areas.features[0].properties.why`. `(g)` three tests pin the
  64-level cap: 70 levels -> a refusal containing `custom model nests deeper than 64 levels at deeper.deeper`,
  65 levels with the token at the bottom -> still the depth refusal, 64 levels with the token at the bottom ->
  refused BY THE TOKEN and not by the depth. `(h)` eight tests pin the closure path.
  (2) src/customModel.ts, the B3 CODE fix (224 -> 287 lines). `closureGeometries` no longer returns the feed's
  own arrays. `closureGeometry` constructs `{ type, coordinates }` (never a spread, so geometry foreign members
  are dropped), `rebuildPolygonRings` refuses a Polygon with no rings, `rebuildRing` requires >= 4 positions
  and first == last, `rebuildPosition` copies exactly two finite numbers into a FRESH pair. Two new reason
  codes on CustomModelRefusal: `closure_ring_not_closed`, `closure_position_not_numeric`, plus the exported
  `MIN_RING_POSITIONS = 4`. Error messages name the feature, ring and position and print only element TYPES,
  never the feed's own text, so a poisoned feed cannot get its string quoted back out through an error.
  (3) test/customModel.test.ts gains recordable N1 (278 -> 294): monotonicity sampled at the grid's interval
  midpoints, the sample list `[0, 0.125, 0.25, 0.375, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8]` typed out.
  (4) The src docstring at buildCustomModel no longer claims more than holds: it now says what is rebuilt, says
  BY REFERENCE explicitly, and names round 1's B3 as the reason. The PR body is rewritten to match this head.
  RED BY NAME, every new check, at the final tree (`Tests  125 passed (125)` green first): B1 mutant ->
  `Tests  5 failed | 120 passed (125)`, all five `(f)` tests. B2 mutant -> `Tests  2 failed | 123 passed (125)`,
  the two depth `(g)` tests. B3 spread -> `Tests  1 failed | 124 passed (125)`, `(h) drops foreign members on
  the closure geometry instead of forwarding them`. B3 coordinates pass-through -> `Tests  1 failed | 124
  passed (125)`, `(h) shares no array with the feed, so poisoning the feed after the build changes nothing`.
  Neighbour (i) case folding removed -> `Tests  2 failed | 123 passed (125)`, `(b) refuses ROAD_ACCESS whatever
  its case` and `(f) refuses an upper-case token in the MIDDLE of a condition`. Neighbour (ii) the areas walk
  skipping array elements -> `Tests  9 failed | 116 passed (125)`. Round 1's RED 1/2/3 re-run at this tree ->
  8, 13 and 13 failures of 125; every name is in the acceptance block. Nine mutants, nine restores, `git diff
  --stat services/api/src/customModel.ts` identical before and after the loop.
  ON B3 AND HONESTY: at the unfixed head the six `(h)` refusal and rebuild tests are red WITHOUT any mutant -
  that is the reviewer's point reproduced as a false claim rather than as a survived mutant, and it is the
  reason the code, not only a test, had to change. Observed in this session when a `git checkout --` in my own
  mutant loop reverted the fix mid-run: the run recorded 8 failures, of which 6 were `(h)` at the unfixed head
  and 2 were the B2 mutant's. I re-ran all nine mutants cleanly afterwards, restoring from a saved copy instead
  of from HEAD; only the clean runs are quoted above and in the acceptance block.
  STILL OPEN, unchanged or new. (1) `npx tsc --noEmit` for services/api is still red on main's pre-existing
  TS2688; tsconfig.json is outside `touches:`. (2) Nothing is wired: no /plan route, index.ts untouched, both
  functions still called by no route. (3) P-SAFE-01 gains no pin assertion here - pins/PINS.yaml is T-0149's.
  (4) The 300-line cap on these three .ts files rests on `wc -l` alone (T-0058); headroom is 13 lines on
  src/customModel.ts and 6 on test/customModel.test.ts, so the NEXT change to either splits the closures
  validation into src/closureAreas.ts. I did not split it now: 287 is under the cap and a split the reviewer
  did not ask for would have moved code the review had just read. (5) `bash ops/test` and full
  `bash ops/check-pins` were not run this round (harness instruction); `gh pr checks 91` stands behind them.
  (6) Ring winding, self-intersection and lon/lat range are NOT validated - a well-formed but geographically
  absurd closure is still forwarded. It cannot smuggle an encoded value, which is what P-SAFE-01 rules; the
  geometry-correctness half still waits on a real graph, as the Brief says.
