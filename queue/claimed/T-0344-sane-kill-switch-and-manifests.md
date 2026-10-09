---
id: T-0344
title: ops/sane --prod gains its reserved exit codes 6 (quota / kill switch tripped or near its trip) and 8 (the R2 corpus/tiles manifests disagree with this checkout's config), read-only, against the deployed Worker's own read-only endpoints
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T13:50:37Z
lease_expires_at: 2026-10-09T23:50:37Z
worktree: .worktrees/T-0344
branch: task/T-0344
exclusive: []
touches: [ops/sane, ops/lib/, ops/mutate/, services/api/src/, services/api/test/, pins/PINS.yaml]
pins_affected: [P-OPS-05, P-COST-01, P-COST-02, P-PROD-05]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "A1 Fake-Worker table, through the SHIPPED ops/sane --prod: `bash ops/lib/check-sane-prod` exits 0 printing `SANE-PROD ok` with every case passed - a local python fake Worker on 127.0.0.1 (never prod) serving /__health, /__version (live git_sha = HEAD) and a corpus manifest; cases: quota green, kill_switch true, upstream_calls at trip_at, at the near bound (calls*10 == trip_at*9), one below the near bound (green), null, absent, boolean and negative calls, kill_switch a string, trip_at 0; manifest green, not an object, missing key, extra key, schema_version 2 and the string 3, version empty, sha256 uppercase and 63 chars, bytes 0, boolean min_app_build, manifest 404; no manifest URL (skip); precedence 6 over 8, 7 over 6 and 8 (health 503). Each red case asserts the exact exit code (6, 8 or 7) and the FAIL row's check name; each green case asserts the ok row and an exit outside {3,6,7,8,9}."
  - "A2 Never mutates: every check-sane-prod case asserts the fake received only GET requests and that `git status --porcelain` and HEAD are byte-identical before and after the ops/sane run."
  - "A3 RED first: check-sane-prod against the pre-change ops/sane FAILS (quoted in the Log), then green; and three one-line ops/sane mutants (near bound `>=` -> `>`, the schema_version compare dropped, the kill_switch arm dropped) each turn it red by case name, restored green."
  - "A4 P-OPS-05: EXIT_ORDER becomes (2 7 3 6 9 8 4 10); `bash ops/lib/check-sane-exit-order` seen exit 1 with the new fail() 6/8 calls in place and EXIT_ORDER unchanged, then exit 0."
  - "A5 Worker read-only fields, whole-answer: services/api/test/healthQuota.test.ts asserts the WHOLE /__health answer (status and body by toEqual) through the shipped worker.fetch over {QUOTA with 0 and with N reserved, QUOTA absent, QUOTA readMonthly throwing, QUOTA readMonthly a non-count} x {no kill, env KILL=1, KV KILL=1, KV get throwing} plus D1 down (503, ok false, quota fields still present), and that upstream_trip_at is the least count killSwitchTripped refuses; seen RED by name before the src change; `npx vitest run test/healthQuota.test.ts test/routes.test.ts test/sharedEnvWorker.test.ts test/killSwitchRoutes.test.ts` green."
  - "A6 Pin P-OPS-08 runs check-sane-prod; on the merged head: `bash ops/sane` (repo-only) prints no FAIL row but the environmental worktrees row (other agents' worktrees, quoted), and check-sane-exit-order, check-exec-bits, check-pins-yaml, queue-check and `ops/check-pins --source-only` are green."
---
## Brief

The plan's harness table: `ops/sane [--prod]` exit 6 = quota/kill switch, 8 = R2 manifest != config. ops/sane reserves
both ("5/6/8 reserved ... added with T-0008/T-0014"); exit 5 (golden routes live against the router) needs the
deployed router and stays out of scope here. MEASURE FIRST: what the deployed Worker exposes read-only today
(/__health, /__version, /config, /__ro - which of them can answer "is KILL set / how close is the monthly upstream
counter to MAX_MONTHLY_UPSTREAM_CALLS" and "which corpus/tiles manifest version is live" without a new write path),
what this checkout's config pins (corpus schema_version, tiles manifest, MAX_MONTHLY_UPSTREAM_CALLS), and how
ops/sane's EXIT_ORDER / check-sane-exit-order (P-OPS-05) must move. Then write the acceptance: each new check seen
red then green against a LOCAL fake Worker (never prod from CI; never a deploy), EXIT_ORDER updated with P-OPS-05
seen red then green, never mutates, distinct exit codes, a near-trip threshold ruled (e.g. 90% as the plan's kill
switch). If the Worker lacks a read-only field the check needs, add it read-only (no location data, P-PRIV-05) with
a whole-answer test.

## Log
- 2026-10-09T13:50:14Z filed by agent/claude-opus-5 (orchestrator) from the plan's harness table (M1 ops/sane 6/8).
- 2026-10-09T13:50:37Z claimed by agent/claude-opus-5; lease until 2026-10-09T23:50:37Z
- 2026-10-09T13:55:55Z MEASURED (agent/claude-opus-5), before any code:
  - Worker read-only answers today: /__health = {ok, db, git_sha} (D1 SELECT 1); /__version = {git_sha, built_at,
    schema_version: 3}; /config = the closed whitelist answer whose planning_paused = killSwitch(env) OR the KV
    config record's own planning_paused (public, max-age 300); /__ro = token-gated SQL over D1 ONLY. The monthly
    upstream counter lives in the QuotaCounter Durable Object (idFromName "global", MonthlyRecord {month, calls}),
    which NO endpoint reads; /__ro cannot (D1 only). So "how close is the counter" has no read-only answer today.
  - Limits: quota.ts MAX_MONTHLY_UPSTREAM_CALLS = 250_000, KILL_SWITCH_THRESHOLD = 0.9; killSwitchTripped(n) is
    n >= 250000*0.9, so the counter trips at 225000 and reserveMonthly refuses from there.
  - Manifests: the Worker has NO R2 binding (wrangler.jsonc binds the QUOTA DO, TELEMETRY and D1 only). The corpus
    manifest shape is Sources/PlaceStore/CorpusManifest.swift: exactly {version, schema_version, min_app_build,
    sha256, bytes}, version non-empty, bytes >= 1, sha256 64 lowercase hex, ints typed; downloaded only when
    schema_version == PlaceStore.schemaVersion. Its URL is NOT in the checkout: LiveCorpus reads UserDefaults
    `corpus.manifest.url`. Checkout schema pins: services/etl/etl/schema.py SCHEMA_VERSION = 3 and index.ts
    SCHEMA_VERSION = 3 (held equal by P-PROD-05). No TILES manifest exists anywhere: BasemapResolver reads
    tiles/la.pmtiles and services/tiles has no manifest. App build: project.pbxproj CURRENT_PROJECT_VERSION = 1
    (both configs), but Xcode Cloud stamps CI_BUILD_NUMBER (ci_post_clone.sh), so the checkout does not pin the
    shipped build.
  - ops/sane: EXIT_ORDER=(2 7 3 9 4 10); check-sane-exit-order `ok documented=2,7,3,9,4,10 code=2,7,3,9,4,10
    calls=15`; no ops/legal-urls (legal skips). `bash ops/sane` (repo-only) at b92f9b26: every row ok/skip but
    `worktrees FAIL 3 of 97 need attention` (rv2-mutA, rv2-mutX modified; T-0104 no origin branch) -> `SANE FAIL
    exit=10`. Environmental: other agents' worktrees.
- 2026-10-09T13:55:55Z RULINGS (agent/claude-opus-5), before code:
  - R1 Exit 6 reads ONE endpoint, /__health - already fetched once by check 7, uncached, and no new route, so the
    ROUTES whitelist tables, the shared-env sweep and P-COST-01's killable derivation are untouched. /__health gains
    four read-only fields: kill_switch (killSwitch(env), the very function every killable route calls: env KILL or
    the KV KILL_SWITCH key), upstream_month (monthKey(now)), upstream_calls (the global DO's readMonthly, or null
    when QUOTA is unbound, the read throws, or it returns a non-count) and upstream_trip_at (the least integer
    count killSwitchTripped refuses: 225000). `ok` and the status stay D1-only: quota is not health, and exit 7
    keeps its meaning. No location data and no per-user data - one global aggregate (P-PRIV-05 untouched). Public,
    ruled: one aggregate integer; the kill state is already public via /config; the cost is one DO read per call.
  - R2 /config's planning_paused is NOT read: it also folds in the owner's deliberate KV config pause, a product
    setting; exit 6 is the kill switch and the counter, which kill_switch states without that conflation.
  - R3 Near-trip: FAIL 6 when upstream_calls*10 >= upstream_trip_at*9 (90% of the trip point = 202500 of 225000,
    81% of MAX). Tripped (calls >= trip_at) and kill_switch true are FAIL 6; a missing, null or mistyped field is
    FAIL 6 "cannot tell" - never ok. Exit 6 runs inside the backend-up branch after the version check.
  - R4 Exit 8 cannot be answered by the Worker (no R2 binding; binding one would create a Cloudflare resource,
    which this task may not). It reads the manifest from its own public URL - the one the app fetches - named by
    CORPUS_MANIFEST_URL or the file ops/corpus-manifest-url; neither present -> skip (nothing published yet);
    present but unreachable -> FAIL 8. "Disagrees", field by field, mirroring CorpusManifest.parse + decide: key
    set exactly the five; version a non-empty string; schema_version an int (not bool) EQUAL to the checkout's
    services/etl/etl/schema.py SCHEMA_VERSION (exactly one such line, else cannot tell -> 8); min_app_build an
    int >= 1, NOT compared (the shipped build is stamped by Xcode Cloud, not pinned by the checkout); sha256 64
    lowercase hex; bytes an int >= 1. Parsed by ops/lib/sane_manifest.py (data, 100644).
  - R5 Tiles manifest: OUT OF SCOPE - no shape exists to disagree with; ops/sane prints a skip row naming that,
    and the gap is filed as a follow-up task.
  - R6 Precedence: EXIT_ORDER (2 7 3 6 9 8 4 10). Tests run against a local python fake Worker only; the fake serves
    files from a temp directory and logs every request's method.
  - R7 `bash ops/sane` repo-only cannot exit 0 on this box while other agents' worktrees are dirty (exit 10,
    measured above; testers find and do not fix). Green = no FAIL row except that environmental worktrees row.
