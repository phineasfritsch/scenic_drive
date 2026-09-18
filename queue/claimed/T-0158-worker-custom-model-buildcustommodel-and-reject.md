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
  - "SETUP and CONTROL, in this worktree: `cd services/api && npm ci` -> `added 85 packages, and audited 86 packages in 30s` (node_modules is gitignored and was absent on this box - T-0040). The EXISTING suite, before a line of this task was written: `npx vitest run` -> `Test Files  4 passed (4)` / `Tests  71 passed (71)`. At the final commit the same command bare -> `Test Files  5 passed (5)` / `Tests  108 passed (108)`, exit 0. 37 new tests, one new file"
  - "`bash ops/test` bare -> `RO-GRAMMAR OK 30 cases`, `TESTS linux=810/76 ios=skipped failed=0 skipped=0`, `OK`, exit 0. The Worker tier is inside that total: ops/test:32-40 parses `.artifacts/vitest.json`, which reports numTotalTests 108, numFailedTests 0. ops/test got through the Worker tier on this box today only because node_modules now exists in this worktree; .github/workflows/linux-core.yml:61 runs `npm ci` for services/api, so CI runs these 37 too"
  - "strict typecheck of the two new files: `npx tsc --noEmit --ignoreConfig --strict --target es2022 --module es2022 --moduleResolution bundler --skipLibCheck --lib es2022 --types vitest src/customModel.ts test/customModel.test.ts` -> no output, exit 0. The package HAS a tsconfig.json and a `typecheck` script, and `npx tsc --noEmit` exits 1 on `error TS2688: Cannot find type definition file for '@cloudflare/workers-types/2023-07-01'` - which is NOT this task's: with both new files moved out of the tree, that same command prints that same single error and exits 1 (control run recorded in the Log). tsconfig.json is outside touches:; STILL OPEN"
  - "the 300-line cap: `wc -l services/api/src/customModel.ts services/api/test/customModel.test.ts` -> `224` and `278`, both under 300. `bash ops/lib/check-line-cap` bare -> `P-SRC-02: 64 Swift files tracked (Sources=24, Tests=32, apps/ios=8), none over 300 lines`, exit 0 - and that gate reads Swift only, so it does not cover either new file; the cap is held here by the wc count, not by it (the gap is T-0058's, still in queue/claimed)"
  - "`bash ops/check-pins --source-only` bare -> `PINS ok=9 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only`, exit 0. `bash ops/queue-check` bare -> `QUEUE OK (153 tasks)`, exit 0. Neither piped: a pipe would swallow the exit status"
  - "RED 1, the >= 4 band made to GROW with lambda (`mid: 1 + 0.5 * lambda` in scenicBandMultipliers) -> `Tests  7 failed | 101 passed (108)`. By name: `(c) ... > mid band (scenic_score >= 4) is monotone non-increasing over the grid`, `(c) ... > the built model's multipliers are monotone non-increasing over the grid`, `(c) ... > matches the plan's multipliers at lambda 1`, `at lambda 2`, `at lambda 8`, `(c) ... > matches 1/(1+0.5*lambda) and 1/(1+lambda) as doubles at lambda 0, 1, 2 and 8`, `(a) ... > emits the plan's clause shape: if / else_if / else with string multiply_by`. Restored"
  - "RED 2, a `surface` clause smuggled into the built model (`{ if: 'surface == ASPHALT', multiply_by: '1' }` appended to priority) -> `Tests  11 failed | 97 passed (108)`. By name: the seven `(a) ... > built model never mentions road_access or surface at lambda 0 / 0.25 / 0.5 / 1 / 2 / 4 / 8`, plus `(a) ... > drops closure feature properties so a poisoned KV feed cannot smuggle surface in`, `(a) ... > emits the plan's clause shape`, `(a) ... > keys areas the way the closure clause references them`, and `(b) ... > accepts the built model, with and without closures` - the last one is rejectCustomModel refusing what buildCustomModel produced, which is the property the two halves share. Restored"
  - "RED 3, rejectCustomModel made to check only top-level keys (no recursion, no string values) -> `Tests  5 failed | 103 passed (108)`. By name: `(b) ... > refuses road_access in a top-level condition`, `(b) ... > refuses road_access hidden in a nested else_if clause`, `(b) ... > refuses surface hidden in an areas feature property`, `(b) ... > refuses a forbidden encoded value used as an object KEY, not only as a value`, `(b) ... > refuses ROAD_ACCESS whatever its case`. Restored"
  - "the plan's literals are TYPED OUT, never computed from the code under test: test/customModel.test.ts PLAN_MULTIPLIERS holds lambda 0 -> 1/1/1, lambda 1 -> 1/0.666667/0.5, lambda 2 -> 1/0.5/0.333333, lambda 8 -> 1/0.2/0.111111 for the (>= 7, >= 4, else) bands, and a second test pins the unrounded doubles 0.6666666666666666, 0.3333333333333333, 0.1111111111111111. The monotonicity test compares consecutive grid points - that is a property, not an expectation derived from the function"
  - "NOT IN THIS TASK, on the record: nothing is wired. index.ts is untouched, no /plan route exists, no upstream call carries the model and rejectCustomModel is called by no route yet (the Brief's instruction). services/routing/profiles/ and pins/PINS.yaml are untouched - T-0012 and T-0149 own them, so P-SAFE-01 gains no pin assertion here. At the final commit `git diff --stat $(git merge-base origin/main HEAD) HEAD -- services/api` -> `2 files changed, 502 insertions(+)` and `git diff --name-only $(git merge-base origin/main HEAD) HEAD` lists those two plus this task file, nothing else"
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
