---
id: T-0158
title: Worker custom model - buildCustomModel(lambda, closures) and rejectCustomModel - the per-request model never carries road_access or surface, and its multipliers are monotone in lambda
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
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
