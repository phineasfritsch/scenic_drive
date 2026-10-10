---
id: T-0357
title: The app reads /config - a ConfigClient fetches the Worker's remote config with cached defaults, and the kill switch and min build degrade the UI to the typed PlanError copy instead of failing
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-10T05:16:25Z
lease_expires_at: 2026-10-10T13:16:25Z
worktree: .worktrees/T-0357
branch: task/T-0357
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml, .github/workflows/ios-screenshot.yml, queue/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 MEASURE (Log, before code): the Worker's /config body and every field quoted from services/api/src/config.ts; what the app does on planning_paused today; which fields the app could act on"
  - "A2 ConfigClient.fetch() (the shipping client) sends exactly ONE request equal to PlanHTTPRequest(url: base/config, method GET, headers [:], body empty) and never retries; no reply is nil after exactly one request"
  - "A3 Whole-answer equality: for the Worker's full answer body with min_app_build in {1, 2, 41, 2147483646, 2147483647} x planning_paused in {false, true}, fetch() == RemoteConfig(minAppBuild:planningPaused:) exactly; fields the app does not read (supported_regions, feature_*, quota, config_warnings, an unknown key) dropped, garbled or added never change the answer"
  - "A4 Decode-failure table, rows as functions of two variants (build 7 paused / build 3 unpaused) with a meta-test that every body row differs across the variants: min_app_build 0, -1, 2147483648, 1.5, 1e20, \"7\", true, null, missing; planning_paused \"true\", 1, 0, null, missing; body not an object ([], \"x\", 7, null, empty, invalid JSON); status 201, 204, 304, 404, 500, 503 with a good body -> fetch() is nil"
  - "A5 ConfigCache.refresh(): a good answer is returned and stored; a refused answer or no reply returns the stored last good answer, else RemoteConfig.bundled (== the Worker's DEFAULTS: 1, false), as a cross product over stored {none, paused build 7, unpaused build 3, garbage bytes} x failure {no reply, 503, malformed}; a refusal never rewrites the stored bytes"
  - "A6 ScenicKit ConfigDegrade.of(config, appBuild:) equals a literal table over planning_paused {false,true} x min_app_build {1, 41, 42, 43, 2147483647} x appBuild {nil, 1, 42, 2147483647}: updateRequired iff appBuild != nil and min > appBuild, else planningPaused iff paused, else none; AppBuild.parse reads only a positive ASCII-decimal Int within 1...2147483647 (table over every bound and \"\", \"+1\", \"-1\", \" 1\", \"1.0\", \"0\", nil)"
  - "A7 The gate: PlanSheet.startPlanning() issues no ticket under planningPaused or updateRequired and one under none; the notice is PlanFailureCopy.of(.planningPaused).line for planningPaused, the update line for updateRequired, nil for none; ConfiguredPlanner.degrade() through ScriptedTransport is ConfigDegrade.of(the refreshed answer, our build)"
  - "A8 Each new test named in the Log seen RED on the pre-code tree (missing symbols) and on a planted mutant, then GREEN: swift test --filter ConfigClientTests|ConfigCacheTests|ConfigDegradeTests|ConfiguredPlannerTests"
  - "A9 ops/mutate/config.py: population with a literal floor over every added Sources module, run in full: caught = all, equivalents MISSED; --prove-vacuity OK; --prove-floor OK"
  - "A10 Apple half: P-SAFE-03 digests re-approved for every edited apps/ios and Sources file; ios-compile success and ios-screenshot success with the new plan-paused and plan-update shots looked at"
  - "A11 Final head (after merging origin/main last): bare check-safety-disclaimer, check-mutate-population, check-line-cap, check-pins-yaml, queue-check each exit 0; every touched file <= 300 lines"
---
## Brief

Survey 2026-10-10 (M6 exit: "kill switch by hand -> typed degrade, no 500s"): the Worker serves /config
(services/api/src index.ts, T-0288), but no client in Sources or apps/ios reads it.

MEASURE FIRST: /config's body and every field (quote the Worker), what the app already does on planningPaused
(503 from /plan under KILL=1), and which fields the app could act on. RULE the fields read (fail-closed decoding:
unknown or malformed -> cached defaults, never a crash), the cache (last good answer, bundled defaults), and what the
UI does per field (kill -> planningPaused copy before the user taps Plan; min build above ours -> an update prompt).
Tests through the shipping client: whole-answer equality over every field and bound, decode-failure rows, and the
degrade mapping as a table. Every apps/ios Swift edit needs the P-SAFE-03 digest re-approval; if refused, ship the
Linux slice and say so.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-3).
- 2026-10-10T05:16:25Z claimed by agent/claude-opus-5; lease until 2026-10-10T13:16:25Z
- 2026-10-10T05:30:16Z MEASURE (A1), from services/api/src/config.ts on this branch's base (8ef9c6c0):
  - GET /config -> `handleConfig(env)` (index.ts: `"/config": (_req, env) => handleConfig(env)` - the request is never
    read), status 200, `content-type: application/json; charset=utf-8`, `cache-control: public, max-age=300`
    (CONFIG_MAX_AGE_S). The body is `{...DEFAULTS, ...valid KV overlay, planning_paused: killed || merged, quota,
    config_warnings}`; with no KV record and no kill it is exactly
    `{"min_app_build":1,"planning_paused":false,"supported_regions":["la"],"feature_loop":true,"feature_trip":true,"feature_surprise":true,"quota":{"anon":{"plan":3,"loop":1,"surprise":3,"trip":1},"free":{"plan":10,"loop":1,"surprise":3,"trip":1},"paid":{"plan":200,"loop":200,"surprise":200,"trip":200}},"config_warnings":[]}`
    (quota = dailyQuota(kind, tier) over DAILY_PLAN_QUOTA's tiers anon/free/paid and DISPLAY_KINDS plan/loop/surprise/trip).
  - Fields and the Worker's own whitelist (FIELDS): `min_app_build` Number.isInteger and 1..MAX_APP_BUILD=2147483647;
    `planning_paused` boolean, and the kill switch (env KILL=1 or KV KILL_SWITCH "1" or a throwing KV read) forces it
    true - KV can never unpause; `supported_regions` non-empty unique subset of ["la"]; `feature_loop|trip|surprise`
    booleans; `quota` the tier x kind numbers; `config_warnings` the names of KV fields that fell to defaults.
  - The app today: nothing under Sources/ or apps/ios reads /config (grep "config" in Sources/ScenicAPIClient: none).
    Under KILL=1 /plan, /loop and /trip answer 503 `{"error":"planning_paused"}` before the body is read (plan.ts :72,
    :87; loop.ts :50, :62; trip.ts :53, :71); PlanResponseReader maps it to PlanError.planningPaused ->
    PlanSheetFailure.planningPaused -> PlanFailureCopy "Planning is paused right now. Surprise Me still works." with
    action surpriseMe - shown only AFTER the user taps Plan and a request has gone out.
  - Fields the app could act on: planning_paused (say so before the tap, send nothing), min_app_build (an update
    prompt; our CFBundleVersion is CURRENT_PROJECT_VERSION = 1 in both configurations of project.pbxproj).
    supported_regions is ["la"] only and /plan already answers 422 region_unsupported; feature_* have no switch in the
    UI to drive; quota is display-only and no screen shows allowances; config_warnings is an operator diagnostic.
- 2026-10-10T05:30:16Z RULINGS (before code):
  - R1 Fields read: `min_app_build` and `planning_paused` ONLY. Every other key the Worker sends (supported_regions,
    feature_*, quota, config_warnings) and any unknown key is ignored: present, absent or garbled, it never changes the
    answer (the Worker always sends them, so refusing unknown keys would make every answer the defaults). Acting on
    feature_* and on /loop and /trip is the follow-up filed at the end of this task, not this slice.
  - R2 Fail-closed decoding (ConfigReader): an answer is accepted only when the status is 200, the body is a JSON
    object, `min_app_build` is a JSON integer in 1...2147483647 (the Worker's MAX_APP_BUILD) and `planning_paused` is
    a JSON boolean. Anything else refuses the WHOLE answer (no per-field overlay: the Worker already did that, so a
    malformed answer is a protocol disagreement). No force unwrap, no `try!`: a refusal is nil, never a crash.
  - R3 The request: GET {base}/config with NO headers and an empty body - the handler takes env only, so nothing
    identifying the device is sent. One request per refresh, never retried; a throwing transport is nil.
  - R4 The cache (ConfigCache over a ConfigStorage): the last good answer is stored re-encoded as the two-field object
    and read back through the same ConfigReader.decode; stored bytes that do not decode are as if absent. A refused
    answer or no reply returns the stored answer, else RemoteConfig.bundled = the Worker's DEFAULTS for the two
    fields (min 1, not paused); a refusal never rewrites the store. The bundled defaults never pause: the server's
    503 stays authoritative, the config is advance notice.
  - R5 The degrade (ScenicKit ConfigDegrade.of(config, appBuild:)): `updateRequired` iff appBuild is known and
    min_app_build > appBuild; else `planningPaused` iff planning_paused; else `none`. Update outranks pause (an old
    build cannot plan once unpaused either). An unknown build (CFBundleVersion absent or not a positive decimal
    within Int32, AppBuild.parse) never prompts an update: we cannot claim one is needed, and the Worker enforces no
    build - pause is still honoured.
  - R6 The UI: PlanSheet carries the degrade; THE GATE issues no ticket unless it is `none`, so under a known pause no
    /plan is sent. The form shows the notice in place of the Plan button: planningPaused -> PlanFailureCopy.of(
    .planningPaused).line (the typed PlanError copy, by reference, never a second literal); updateRequired -> "This
    version can't plan drives anymore. Update Scenic Drive from the App Store to keep planning."
  - R7 The wiring: RoutePlanning gains `func degrade() async -> ConfigDegrade` with NO default implementation, so every
    conformer states its answer (ClientPlanner, UnreachablePlanner and the test fakes: none - they read no config;
    RetimingPlanner: its inner's). ScenicAPIClient's ConfiguredPlanner wraps a ClientPlanner with a ConfigCache and
    our build; LivePlanner.make() returns it, its store is UserDefaults (PlanAdapter, the only ScenicAPIClient
    importer). PlanSheetScreen asks the planner once per appearance (`.task`), skipped under a DEBUG rehearsal.
    ScenicDriveApp.swift (outside touches) is unchanged.
  - R8 Seeing it: two DEBUG rehearsals, `-screen paused|update`, and ios-screenshot shoots them (touches widened to
    .github/workflows/ios-screenshot.yml; ops/lib/ios_screenshot_pinned.py moves in the same commit).
  - R9 Population: ops/mutate/config.py (config_mutations.py, config_run.py, ledger's three-file shape) covers every
    added Sources module that holds logic; pure declarations (ConfigStorage protocol, ConfigWire Codable shape,
    RemoteConfig value) go to the allowlist with one reason each.
- 2026-10-10T06:46:39Z R9 revised as built: ConfigWire and RemoteConfig hold mutable logic-bearing literals (the wire
  keys, the bundled defaults, MAX_APP_BUILD), so both are config.py SUBJECTS; only the ConfigStorage protocol is
  allowlisted. A test file written as a table of 26 closure literals sent the type checker past 30 min on this box
  (killed; rows rewritten as plain data with "$" = the variant's value) - recorded so nobody re-tries the shape.
- 2026-10-10T06:46:39Z A8 RED, on the tree with the four test files and no code (`swift build --build-tests
  --scratch-path .build/t0357`): `error: cannot find 'RemoteConfig' in scope`, `error: cannot find type
  'ConfigDegrade' in scope`, `error: cannot find 'AppBuild' in scope`, `error: value of type 'PlanSheet' has no member
  'setDegrade'` (and the ConfigClient/ConfigCache/ConfiguredPlanner names). Then GREEN with the code: `swift test
  --filter "ConfigClientTests|ConfigCacheTests|ConfiguredPlannerTests|ConfigDegradeTests|CorridorLearnerTests|
  OnboardingPlanGateTests"` -> the first run had ConfiguredPlannerTests.plan red (a PlanClient with no install id
  refuses on the device - a test-fixture fault, fixed by PlanWire.install), then `Test run with 2 tests in 1 suite
  passed`; the whole root suite `swift test` -> `Test run with 796 tests in 158 suites passed after 30.754 seconds.`
  exit 0. The planted-mutant half of A8 is the config.py run (A9), each mutant red by the test it names.
