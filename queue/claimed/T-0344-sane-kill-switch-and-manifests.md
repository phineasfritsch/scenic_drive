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
  - "A1 Fake-Worker table, through the SHIPPED ops/sane --prod: `bash ops/lib/check-sane-prod` exits 0 printing `SANE-PROD ok` with every case passed - a local python fake Worker on 127.0.0.1 (never prod) serving /__health, /__version (live git_sha = HEAD) and a corpus manifest; cases: quota green, kill_switch true, upstream_calls at trip_at, at the near bound (calls*10 == trip_at*9), one below the near bound (green), null, absent, boolean and negative calls, kill_switch a string, null, 0 and the empty string (every non-boolean is cannot-tell, falsy included), trip_at 0; manifest green, not an object, missing key, extra key, schema_version 2 (older, SV - 1) and 4 (newer, SV + 1) and the string 3, version empty, sha256 uppercase and 63 chars, bytes 0, boolean min_app_build, manifest 404; no manifest URL (skip); precedence 6 over 8, 7 over 6 and 8 (health 503). Each red case asserts the exact exit code (6, 8 or 7) and the FAIL row's check name; each green case asserts the ok row and exit 0 exactly (SANE_SCOPE=prod skips the local checks 2/4/10, R8)."
  - "A2 Never mutates: every check-sane-prod case asserts the fake received only GET requests and that `git status --porcelain` and HEAD are byte-identical before and after the ops/sane run."
  - "A3 RED first: check-sane-prod against the pre-change ops/sane FAILS (quoted in the Log), then green; and three one-line mutants of ops/sane's verdict helper ops/lib/sane_prod.py (near bound `>=` -> `>`, the schema_version compare dropped, the kill_switch arm dropped) each turn it red by case name, restored green."
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
- 2026-10-09T14:21:53Z R8 (ruled during the build, before the acceptance re-run): ops/sane gains SANE_SCOPE=prod,
  which skips the local checks 2, 4 and 10 with a skip row each. Measured: one pre-change ops/sane --prod run costs
  ~60 s on this box (check-worktrees over 97 worktrees), and its exit is 10 here whatever 6/8 say, so the green
  cases could only assert "not 6/8"; under SANE_SCOPE=prod they assert exit 0 exactly. The --prod checks run the
  same code either way; the acceptance's A1/A3 wording was amended to match (exit 0; the mutants are of
  ops/lib/sane_prod.py, the verdict helper ops/sane calls).
- 2026-10-09T14:21:53Z BUILT + SEEN RED THEN GREEN (agent/claude-opus-5):
  - A3 red first, harness against the PRE-CHANGE ops/sane (`--only q-kill,q-near-bound,m-schema-other,m-404`):
    `SANE-PROD FAIL q-kill: exit 10, want 6; row quota ['skip'], want [FAIL]; row manifest None, want [ok]` (same
    shape for the other three) -> `SANE-PROD FAIL 4 of 4 cases failed (sane=ops/sane)`, rc=1.
  - A4 P-OPS-05 red: new fail() 6/8 in place, EXIT_ORDER unchanged -> `SANE-EXIT-ORDER FAIL ... EXIT_ORDER
    (documented) = 2,7,3,9,4,10; fail() calls, file order = 2,7,3,6,9,8,4,10; first divergence at position 4:
    documented 9, code 6.` rc=1. Green after EXIT_ORDER=(2 7 3 6 9 8 4 10): `SANE-EXIT-ORDER ok
    documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=18` rc=0.
  - A1 green: `bash ops/lib/check-sane-prod` -> 37 `SANE-PROD pass` rows (q-green ... p-7-over-6-and-8 exit=7) and
    `SANE-PROD ok 37/37 cases passed`, rc=0 (7m50s on this box).
  - A3 mutants of ops/lib/sane_prod.py (.artifacts/t0344_mutants.py, restored byte-identical: `restored: True`):
    near-bound `>=` -> `>`: `FAIL q-near-bound: exit 0, want 6` and `FAIL q-near-bound-small-trip: exit 0, want 6`
    (q-below-near still pass) rc=1; schema compare -> `if False:`: `FAIL m-schema-other: exit 0, want 8` rc=1;
    kill arm -> `if False:`: `FAIL q-kill: exit 0, want 6` rc=1.
  - A5 red first by name before the src change: `x the whole /__health answer over every QUOTA reading x every kill
    source, D1 up and down, through the shipped worker.fetch, and the quota state is untouched` (first label `D1 up /
    nothing reserved / no kill source`) and `x upstream_trip_at is the least monthly count killSwitchTripped refuses`
    (trip undefined) -> Tests 2 failed (2). After src: the four touched files `Tests 19 passed (19)`.
  - Full Worker suite then caught two consequences, both ruled and fixed in this diff: (1) sharedEnvWorker.test.ts
    `after the sweep, ...` asserted killed rigs' quota state {} - the sweep's GET /__health now READS the global
    counter, which opens an EMPTY "global" instance in the fake; the expectation is now exactly { global: {} } (a
    reservation would store a record there, so "reserved nothing" still holds by full equality). (2)
    configAnswerPath.test.ts's content pin over index.ts and quota.ts re-approved: index.ts 951d55d9...8551069,
    quota.ts 0e5c24b0...e4817eb (quota.ts: isCount exported, UPSTREAM_TRIP_AT added; no new src import). Full
    suite after: `Test Files 89 passed`, `Tests 2579 passed` (2578 + the re-approved pin).
  - P-OPS-08 added (assertion `bash ops/lib/check-sane-prod`, linux); P-OPS-05's why extended; check-pins-yaml
    `PINS-YAML ok pins=50 fields=403`; check-exec-bits `P-OPS-01: 202 files, 23 required present, all modes correct`
    (ops/lib/check-sane-prod committed 100755; sane_prod.py and check_sane_prod.py data 100644).
  - Follow-up filed: queue/backlog/T-0345 (tiles manifest shape + its exit-8 arm, R5).
- 2026-10-09T15:03:49Z ACCEPTANCE re-run on the merged head 079a1835 (origin/main 58f66b4a, T-0325, merged clean; no src overlap):
  - A1 + A2: `bash ops/lib/check-sane-prod` -> 37 pass rows, `SANE-PROD ok 37/37 cases passed`, rc=0 (GET-only and
    git status/HEAD unchanged are asserted inside every case).
  - A3: red-first and the three mutants as quoted above (2026-10-09T14:21:53Z); sane_prod.py unchanged since.
  - A4: `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=18` rc=0.
  - A5: `npx vitest run test/healthQuota.test.ts test/routes.test.ts test/sharedEnvWorker.test.ts
    test/killSwitchRoutes.test.ts test/configAnswerPath.test.ts` -> Test Files 5 passed, Tests 22 passed. Full Worker
    suite on 2d289a41: Test Files 89 passed, Tests 2579 passed.
  - A6: `bash ops/sane` repo-only: repo/crlf/autocrlf/gitattrs ok, bounds skip, `worktrees FAIL 4 of 98`
    (environmental, R7: other agents' worktrees, plus this branch's merge commit before its push) -> exit 10;
    check-pins-yaml `PINS-YAML ok pins=50 fields=403`; check-exec-bits `P-OPS-01: 202 files, 23 required present, all
    modes correct`; queue-check `QUEUE OK (336 tasks)`; `ops/check-pins --source-only` on 2d289a41 `PINS ok=21
    skipped=28 pending=1 expired=0 failed=0` rc=0. PR #228 CI on 2d289a41: core pass, pins-source-only pass.
- 2026-10-09T16:07:57Z PRE-REVIEW SURVIVORS CLOSED BY CLASS (agent/claude-opus-5). The pre-review mutant pass on ebb9b6e2 found two
  false-greens in ops/lib/sane_prod.py, both survived by the 37-row table:
  - (2) kill_switch parsed loosely: `type(kill) is not bool` -> `kill is None` passed q-kill/q-kill-string/
    q-kill-absent/q-green (the only mistyped value was the TRUTHY "false"). CLASS: R3 makes every non-boolean
    kill_switch "cannot tell", falsy ones included. Rows added: q-kill-null (None), q-kill-zero (0),
    q-kill-empty-string (""), each exit 6 Q6.
  - (3) schema_version compared one-sided: `!=` -> `>` passed m-schema-other (SV + 1 only). CLASS: R4's EQUAL is
    two-sided. Row added: m-schema-older (SV - 1 = 2, which is also A1's named "schema_version 2"), exit 8 M8;
    m-schema-other (SV + 1) kept. A1's case list amended to name the new rows (wording only; no Log line edited).
  - MISSED then CAUGHT by name, six one-line mutants (.artifacts/t0344_mutants_pr.py, each run first on the pre-fix
    rows, then on the new rows; `restored: True`):
    kill-is-none: pre-fix `SANE-PROD ok 4/4 cases passed` rc=0 (MISSED); new rows `FAIL q-kill-zero: exit 0, want
    6; row quota ['ok'], want [FAIL]` + `FAIL q-kill-empty-string: exit 0, want 6` -> `2 of 3 cases failed` rc=1.
    kill-not-in-true-false (`kill not in (True, False)`, 0 == False): pre-fix 4/4 ok rc=0 (MISSED); new rows
    `FAIL q-kill-zero: exit 0, want 6` -> `1 of 3 cases failed` rc=1.
    kill-isinstance-int (`not isinstance(kill, int)`): pre-fix 4/4 ok rc=0 (MISSED); new rows `FAIL q-kill-zero:
    exit 0, want 6` -> `1 of 3` rc=1.
    schema-gt (`>`): pre-fix `SANE-PROD ok 3/3 cases passed` rc=0 (MISSED); new rows `FAIL m-schema-older: exit 0,
    want 8; row manifest ['ok'], want [FAIL]` -> `1 of 2 cases failed` rc=1.
    schema-lt (`<`) and schema-abs-gt-1 (`abs(... - want) > 1`): already CAUGHT by the pre-fix m-schema-other (`FAIL
    m-schema-other: exit 0, want 8`); on the new rows schema-lt fails m-schema-other, abs-gt-1 fails both
    (`2 of 2 cases failed`) rc=1.
    Honest note: q-kill-null fails none of these six (each still refuses None); it binds the key-present-but-null
    reading against a key-presence mutant, beside q-kill-absent.
- 2026-10-09T16:07:57Z ACCEPTANCE re-run on the merged head f15d7f4c (origin/main be0960a8, T-0346 filing only, merged clean):
  - A1 + A2: `bash ops/lib/check-sane-prod` -> 41 `SANE-PROD pass` rows incl. `q-kill-null exit=6`, `q-kill-zero
    exit=6`, `q-kill-empty-string exit=6`, `m-schema-other exit=8`, `m-schema-older exit=8`, then `SANE-PROD ok
    41/41 cases passed`, rc=0 (GET-only and git status/HEAD unchanged asserted inside every case).
  - A3: red-first and the three original mutants as quoted at 2026-10-09T14:21:53Z (sane_prod.py unchanged since);
    plus the six class mutants above.
  - A4: `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=18` rc=0.
  - A5: services/api untouched by this commit; as quoted at 2026-10-09T15:03:49Z.
  - A6: P-OPS-08's why now says 41 cases; check-pins-yaml `PINS-YAML ok pins=50 fields=403` rc=0; check-exec-bits
    `P-OPS-01: 202 files, 23 required present, all modes correct` rc=0; queue-check `QUEUE OK (337 tasks)` rc=0;
    `ops/check-pins --source-only` `PINS ok=21 skipped=28 pending=1 expired=0 failed=0 tier=linux source-only`
    rc=0. `bash ops/sane` repo-only: the only FAIL row is `worktrees FAIL 5 of 97 need attention - untracked:1
    modified:3 unpushed:2` -> `SANE FAIL exit=10` (environmental, R7: other agents' worktrees, plus this branch's
    unpushed merge and this uncommitted Log).
- 2026-10-09T16:36:53Z CORRECTION + RE-RUN (agent/claude-opus-5): the merge 91cfb195 (origin/main dcc63346) is titled "T-0346
  claim, queue move only" but also brought in T-0341's landing (32 files: Sources/ScenicAPIClient, Sources/ScenicKit/
  Hazards, ops/lib hazard-copy guard + digests, ops/mutate/hazardcopy*; none under ops/sane, ops/lib/sane_prod.py,
  ops/lib/check_sane_prod.py, pins/PINS.yaml or services/api). The title is wrong and stays (already pushed; no force
  push); this line is the record. Re-run on 91cfb195: `bash ops/lib/check-sane-prod` -> `SANE-PROD ok 41/41 cases
  passed` rc=0; `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=18` rc=0; `PINS-YAML ok
  pins=50 fields=403`; `P-OPS-01: 202 files, 23 required present, all modes correct` rc=0; `QUEUE OK (337 tasks)`;
  `ops/check-pins --source-only` `PINS ok=21 skipped=28 pending=1 expired=0 failed=0 tier=linux source-only` rc=0.
- 2026-10-09T17:02:57Z RULING (round 2, agent/claude-opus-5, owner) on rv1-t0344 FAIL (PR #228 at 1da309e3):
  the finding is right and is one class, not three rows: per-field type strictness in ops/lib/sane_prod.py was
  bound only at the sites a hand-written row happened to touch. Survivors (A) sha256 fullmatch -> match (no
  over-long row), (B) upstream_trip_at is_int -> isinstance (bool accepted), (C) bytes is_int -> isinstance (bool
  accepted); recordable 1 (MONTH_RE fullmatch -> match, no garbage row) is closed in the same class. Rulings:
  - R9 (field-by-variant cross product): ops/lib/check_sane_prod.py GENERATES the mistyped rows from one field list
    FIELDS = 4 /__health quota fields (kill_switch, upstream_month, upstream_calls, upstream_trip_at) + the 5
    manifest fields (version, schema_version, min_app_build, sha256, bytes). Each field has a kind (bool, month,
    int>=0, int>=1, int==SV, str, sha256); the row for (field, variant) is named x-<field>-<variant> and its value
    and expected exit are functions of the kind. Every field gets the universal variants absent, null, true, false,
    string, empty-string, list, object, number; int kinds add zero and negative; the regex kinds (month, sha256)
    add over-long, under-long and garbage-suffix (a valid value plus a junk tail). The ruled exit is the field
    side's fail exit (6 for quota, 8 for manifest) with the Q6/M8 rows, EXCEPT where the variant is a valid value
    of the field: kill_switch false and upstream_calls zero are green (exit 0), kill_switch true is the kill (6),
    and version string ("x", non-empty) is green - CorpusManifest.swift:81 asks only !version.isEmpty.
  - R10 (meta-check, fails closed with exit 2 before any case runs): the field list equals the shipped
    sane_prod.MANIFEST_FIELDS plus the quota keys of the HEALTH fixture minus ok/db/git_sha, and every field has a
    case for every variant its kind requires (REQUIRED, a literal per kind). It is demonstrated red by deleting a
    variant from the generator.
  - Hand rows stay under their old names (the Log and P-OPS-08 quote them); the generated rows are additive.
    P-OPS-08's why moves from 41 cases to the new count.
  - Verification per the faster-verification ruling: the four mutants (A, B, C, MONTH_RE fullmatch -> match) run
    on --only of the rows they must fail, each quoted RED by case name, restored byte-identical (sha256 compared,
    __pycache__ purged, 1.1 s sleep); then the full table green once on the merged head.
- 2026-10-09T17:24:06Z ROUND-2 MUTANTS (R9/R10, driver .artifacts/t0344-mutants.py, untracked): each mutant applied to
  one exact anchor, __pycache__ purged + 1.1 s sleep, `bash ops/lib/check-sane-prod --only <rows>`, restored, sha256
  compared (ops/lib/sane_prod.py 23fc609a... == HEAD's blob after all five), purged + slept again:
  - (A) sha256 `SHA256_RE.fullmatch` -> `.match`: `FAIL x-sha256-over-long: exit 0, want 8; row manifest ['ok'],
    want [FAIL]` and `FAIL x-sha256-garbage-suffix: exit 0, want 8`; x-sha256-under-long and m-green pass ->
    `2 of 4 cases failed` rc=1, restored=True.
  - (B) upstream_trip_at `is_int(trip)` -> `isinstance(trip, int)`: `FAIL x-upstream_trip_at-true: exit 0, want 6;
    row quota ['ok'], want [FAIL]`; x-upstream_trip_at-false (False < 1) and q-green pass -> `1 of 3 cases failed`
    rc=1, restored=True.
  - (C) bytes `is_int(m["bytes"])` -> `isinstance(m["bytes"], int)`: `FAIL x-bytes-true: exit 0, want 8; row
    manifest ['ok'], want [FAIL]`; x-bytes-false and m-green pass -> `1 of 3 cases failed` rc=1, restored=True.
  - (D) `MONTH_RE.fullmatch(month)` -> `.match(month)`: `FAIL x-upstream_month-over-long: exit 0, want 6` and
    `FAIL x-upstream_month-garbage-suffix: exit 0, want 6`; x-upstream_month-under-long and q-green pass ->
    `2 of 4 cases failed` rc=1, restored=True.
  - (E) R10 meta-check seen red: the generator's garbage-suffix variant deleted from variants() ->
    `SANE-PROD refuse   meta: field upstream_month has no row for ['garbage-suffix']; field sha256 has no row for
    ['garbage-suffix']` rc=2 (no case ran), restored=True.
  Measured: ops/lib/check_sane_prod.py 300 lines (h() and m() share edited(); cap 300), ops/lib/sane_prod.py 115
  (unchanged). Case count 41 hand + 97 generated = 138 (P-OPS-08 why says 138).
- 2026-10-09T18:21:23Z ACCEPTANCE re-run on the merged head 79e5741e (origin/main 3e9dd748: T-0342 landing in
  services/api index.ts, quota.ts, quotaCounters.ts, scenicPlanner.ts, timeRuns.ts, tests, Sources/ScenicAPIClient;
  T-0343 claim; T-0347 filing; merged without conflicts, merge message amended to name the content):
  - A1 + A2: `bash ops/lib/check-sane-prod` -> 138 `SANE-PROD pass` rows (41 hand-written + 97 generated x-*,
    incl. `x-sha256-over-long exit=8`, `x-upstream_trip_at-true exit=6`, `x-bytes-true exit=8`,
    `x-upstream_month-garbage-suffix exit=6`, `x-kill_switch-false exit=0`, `x-upstream_calls-zero exit=0`,
    `x-version-string exit=0`), then `SANE-PROD ok 138/138 cases passed` rc=0; the R10 meta-check passed (no refuse).
    Also 138/138 rc=0 on the pre-merge commit 9ce59665.
  - A3: round-2 mutants (A)-(E) as quoted at 2026-10-09T17:24:06Z; sane_prod.py and the generator unchanged since.
  - A4: `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=18` rc=0.
  - A5: vitest healthQuota, sharedEnvWorker, configAnswerPath, routes, killSwitchRoutes on the merged services/api:
    `Test Files 5 passed (5)`, `Tests 22 passed (22)`.
  - A6: `PINS-YAML ok pins=50 fields=403`; `P-OPS-01: 202 files, 23 required present, all modes correct` rc=0;
    `QUEUE OK (338 tasks)` rc=0. `ops/check-pins --source-only` was not re-run to completion here (it now runs the
    138-case table, about 15-25 min on this Windows box); CI pins-source-only is the record for it.
