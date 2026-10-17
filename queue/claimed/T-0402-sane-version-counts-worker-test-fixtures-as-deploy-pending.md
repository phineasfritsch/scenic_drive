---
id: T-0402
title: ops/sane --prod exit 3 counts a services/api/test fixture change as a pending deploy - compare only the files the deployed Worker is built from
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T17:18:06Z
lease_expires_at: 2026-10-18T17:18:06Z
worktree: .worktrees/T-0402
branch: task/T-0402
exclusive: []
touches: [ops/sane, ops/lib/, queue/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Measured 2026-10-17 (T-0395): after T-0393 merged (c6f2da75) with only new files under
services/api/test/fixtures/seed-places/, `ops/sane --prod` printed
`version FAIL services/api changed since live 5e4150a0 -> deploy pending: services/api/test/fixtures/seed-places/places-0001.sql ...`
and exited 3. Nothing the deployed Worker is built from had changed. ops/sane:77 runs
`git diff --quiet "$live" "$head" -- services/api ops/deploy`, so every test file, fixture and README counts.

Fix by WHITELIST, not by excluding test/: the version row compares only the paths the bundle is built from
(what wrangler bundles - services/api/src/, wrangler.jsonc, package.json, package-lock.json, tsconfig - plus
ops/deploy). Read the list from wrangler's own config/entry, or pin it, so that a new source directory cannot be
missed silently. Demonstrate on a scratch repo or with a fixture git history: a fixture-only change -> ok; a
src/ change -> exit 3; a wrangler.jsonc var change -> exit 3; an unlisted new top-level directory under
services/api that wrangler bundles -> exit 3 (fail closed). Each shown red on today's ops/sane, then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0395's ops/sane --prod run.
- 2026-10-17T17:18:06Z claimed by agent/claude-opus-5; lease until 2026-10-18T17:18:06Z
- 2026-10-17T17:22:39Z rulings (author rule, before code) by agent/claude-opus-5:
  - R1 what wrangler builds from. ops/deploy runs `npx wrangler deploy` in services/api; wrangler.jsonc `main` is
    `src/index.ts`, so esbuild bundles src/ and whatever src imports; wrangler.jsonc itself is the deploy config (vars,
    bindings, crons); package.json + package-lock.json pin wrangler/esbuild/workerd; tsconfig.json is read by
    esbuild. Tracked today under services/api: src/, test/ (122 files, incl. test/fixtures/seed-places, test/mutate),
    migrations/, package.json, package-lock.json, tsconfig.json, vitest.config.ts, wrangler.jsonc. test/ and
    vitest.config.ts are read only by `vitest run`; nothing in src/ is the reason they exist.
  - R1b Brief vs reality: the bundle is NOT confined to services/api. `git grep` over services/api/src finds
    src/servedRegion.ts:8-9 `import la from "../../etl/regions/la/region.json"` and the sfbay twin - esbuild inlines
    both into the deployed Worker, and main's `git diff -- services/api ops/deploy` has never seen them change.
    Ruled: the version row reads every relative import in src/ at HEAD (one `git grep`), resolves it against the
    importing file, and counts any changed path the import names (prefix match, so an extensionless import covers
    x.ts and x/index.ts). An import target outranks WORKER_NOT_BUNDLE, so src/ importing from test/ also counts
    (closes the hole R6 below would otherwise leave).
  - R2 Brief vs Brief: "compare ONLY the bundle paths" and "a new unlisted directory ... -> exit 3 (fail closed)"
    cannot both hold - a path list that is compared alone ignores every directory it does not name. Ruled: a TWO-list
    classification. WORKER_BUNDLE (src/, wrangler.jsonc, package.json, package-lock.json, tsconfig.json,
    migrations/, ops/deploy) counts; WORKER_NOT_BUNDLE (test/, vitest.config.ts) is ignored; any changed path in
    NEITHER list counts as pending and is reported as unclassified. The whitelist is the set of approved IGNORE sites,
    each named exactly; it is pinned in ops/lib/sane_version.py (R6), not derived from wrangler.jsonc - `main` names one file, not the set
    esbuild follows, so deriving from it would add nothing the fail-closed residual does not already give.
  - R3 migrations/ is not bundled (ops/deploy never runs `d1 migrations apply`) but it is production state no other
    ops/sane row watches; it stays counted, as it is today. Ignoring it would be the fail-open direction.
  - R4 how the version row is tested today: it is not. check_sane_prod.py's fake answers /__version with this
    checkout's HEAD, so the `git diff` arm never sees a difference; no fixture git history exists. New
    ops/lib/sane_version_cases.py builds a scratch repo per case (live commit + one change commit, with this
    checkout's ops/lib/sane_prod.py committed so the quota row can answer), points the fake's /__version at the live
    commit, and runs the SHIPPED ops/sane (`--sane`, default this checkout's) with cwd in the scratch repo. Called from
    check_sane_prod.py, so P-OPS-08's existing assertion `bash ops/lib/check-sane-prod` runs it (PINS.yaml is outside
    touches:). Each row compares the exit code and the WHOLE printed version line to a recomputation.
  - R5 a row over the real tree: v-real-tree commits every path `git ls-files services/api` lists (empty contents)
    on top of an empty live commit and requires 0 unclassified - a new tracked directory fails it until it is put
    in one of the two lists.
  - R6 where the decision lives: ops/lib/sane_version.py (lists, import scan, classification, the row's message;
    exit 0 ok / 1 pending / 2 cannot tell). ops/sane locates it from its OWN path (BASH_SOURCE), not the checkout's,
    so the test drives the shipped script and the shipped module against a scratch repo; any non-zero exit,
    traceback included, is `version FAIL` exit 3. Changes outside every Worker input (services/etl/other.py) are
    not counted.

- 2026-10-17T19:51:40Z acceptance re-quoted by agent/claude-opus-5 (code afc83309; origin/main merged as e2c135a0, the
  merge touched no ops/sane, check_sane_prod.py or sane_* file):
  1. `bash ops/lib/check-sane-prod` (on afc83309, 2 h on a loaded box) ->
     `SANE-PROD ok       347/347 cases passed (77 b-/c- rows through sane_prod.tiles at a fixed clock; sane=ops/sane, ...)`,
     all 19 v- rows `pass`: v-none/v-fixture/v-test/v-vitest/v-outside exit=0, the other 14 exit=3.
  2. Red on main (`--sane` = `git show main:ops/sane`): `19 of 19 cases failed` on the whole-line compare; on EXIT
     code exactly v-fixture, v-test, v-vitest (`exit 3, want 0`) and v-region (`exit 0, want 3`) - e.g.
     `v-fixture: exit 3, want 0; version line ['version   FAIL   services/api changed since live 3f0c611 -> deploy
     pending: services/api/test/fixtures/seed-places/places-0001.sql ']`. Correction to the acceptance's prediction:
     v-imported-test exits 3 on main too (main counts all of services/api); its red is M3 below, and it is what
     would catch a fix that merely excluded test/.
  3. Mutants of sane_version.py, each red then restored (`git diff --quiet` clean after): M1 unclassified->outside
     `v-newdir: exit 0, want 3`, `v-newfile: exit 0, want 3`; M2 test/ dropped `v-fixture: exit 3, want 0`,
     `v-test: exit 3, want 0`; M3 imports never read `v-region: exit 0, want 3`, `v-imported-test: exit 0, want 3`;
     M4 package-lock dropped `v-lock: ... (0 bundle, 1 unclassified, 0 not bundled)` vs want `(1 bundle, 0 ...)`.
  4. wc -l: ops/sane 214, check_sane_prod.py 279, sane_version.py 116, sane_version_cases.py 146.
  5. Gates bare on e2c135a0: `P-PROC-06: every added module is covered or allowlisted; the floor of 173 holds`;
     `NAME-PAIRS OK: 242318 pair tokens ...`; `PINS-YAML ok pins=53 fields=426`; `P-OPS-01: 255 files, 23 required
     present, all modes correct`; `QUEUE OK (394 tasks)`; check-safety-disclaimer quoted in the PR body.

## Acceptance
1. `bash ops/lib/check-sane-prod` -> `SANE-PROD ok N/N cases passed`, N including the v- rows, each compared on exit
   code and the WHOLE version line: v-none, v-fixture, v-test, v-vitest, v-outside -> version ok, exit 0; v-src,
   v-src-new, v-wrangler-var, v-package, v-lock, v-tsconfig, v-deploy, v-migration, v-fixture-and-src, v-region
   (services/etl/regions/la/region.json, imported by src), v-imported-test (a test/ file src imports) -> FAIL, exit 3;
   v-newdir (services/api/lib/), v-newfile (services/api/worker-configuration.d.ts) -> exit 3, 1 unclassified;
   v-real-tree -> exit 3, 0 unclassified.
2. Red on main: `bash ops/lib/check-sane-prod --sane <main's ops/sane> --only <v- rows>` -> v-fixture, v-test,
   v-vitest fail on `exit 3, want 0`; v-region and v-imported-test fail on `exit 0, want 3`.
3. Mutants of ops/lib/sane_version.py, each red then restored: M1 unclassified paths ignored -> v-newdir, v-newfile
   red; M2 services/api/test/ dropped from WORKER_NOT_BUNDLE -> v-fixture, v-test red; M3 imports never read ->
   v-region, v-imported-test red; M4 package-lock.json dropped from WORKER_BUNDLE -> v-lock red (unclassified count).
4. `wc -l ops/sane ops/lib/check_sane_prod.py ops/lib/sane_version.py ops/lib/sane_version_cases.py` each <= 300.
5. Gates bare: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-pins-yaml.py,
   check-exec-bits, queue-check.
