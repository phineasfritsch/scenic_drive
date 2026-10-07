---
id: T-0297
title: The kill decision cannot be bent by a handler writing to a shared binding object - KILL_SWITCH is read through a per-request wrapper, and a handler that patches a binding method is refused or harmless
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T12:09:52Z
lease_expires_at: 2026-10-08T00:09:52Z
worktree: .worktrees/T-0297
branch: task/T-0297
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: [P-COST-01]
reviewer: agent/rv1-t0297
depends_on: [T-0292]
verify: [ops/check-pins]
acceptance:
  - "RULE FIRST: which binding methods the kill decision reads (KILL_SWITCH.get, the KILL string) and how a per-request read path is made independent of mutations to the shared binding object (e.g. capture the binding's prototype method at module load and call it with the binding as this, or wrap bindings in a per-request read-only facade)"
  - "Through worker.fetch on one shared env: a handler that assigns env.KILL_SWITCH.get = async () => null on its first call does not unpause any later request under KV KILL=1 - full equality over the shared-env kill table"
  - "Population entry for the binding-method patch, MISSED before and CAUGHT by name after"
---
## Brief

T-0292 residual R-A (PR #183, owner and rv2-t0292): the per-request env copy is frozen shallowly; a handler that writes to
a shared binding object (env.KILL_SWITCH.get) still reaches later requests. fm-t0292 showed the shared-env tables
DETECT it for KILL_SWITCH; this task REFUSES it.

## Log
- 2026-10-07T11:09:18Z filed by agent/claude-opus-5 (orchestrator) from T-0292 residual R-A.
- 2026-10-07T12:09:52Z claimed by agent/claude-opus-5; lease until 2026-10-08T00:09:52Z
- 2026-10-07T12:17:19Z agent/claude-opus-5 (owner): RULINGS, before any code.
  R1 (what the kill decision reads). killSwitch(env) reads env.KILL (a string on the per-request frozen copy, closed by
  T-0292) and, when bound, ONE method of ONE binding: env.KILL_SWITCH.get("KILL"). Nothing else in src reads
  KILL_SWITCH (grep: index.ts's Env field, killSwitch.ts). So the residual is exactly the binding object's `get`.
  R2 (the defect's shape on a real binding). workerd's KVNamespace.get is a PROTOTYPE method; the binding object is
  shared by every request in the isolate. Two writes bend it: an own-property assignment/defineProperty on the binding
  (shadows the prototype), and a write to the prototype itself (reachable from ANY KV binding - CONFIG, CLOSURES share
  KILL_SWITCH's class). Freezing workerd's binding object is a production-only change no test here can run (T-0292).
  R3 (the fix). The kill read never goes through the shared binding's `get` at request time. killSwitch.ts captures the
  binding's `get`, BOUND to the binding, in a module WeakMap the first time default.fetch sees that binding object -
  before any handler of that isolate has run - and default.fetch hands each handler, in its frozen per-request env, a
  FRESH KillSwitchReader over that capture in place of the raw binding. The reader has a real binding's shape (get on
  the class prototype, no own get) and both the instance and the class prototype are frozen, so an own-property write
  (assign, defineProperty) and an inherited write (the reader's prototype) throw TypeError - REFUSED; a write that does
  land on the shared binding or on its class prototype (not reachable from a handler any more; the test reaches it
  through its own closure) is HARMLESS - the capture is already bound. A binding whose get cannot be bound fails closed
  (the read throws, killSwitch pauses). The reader's `prototype` line is a reflection identifier: approved by whole line
  in reflectionSites.test.ts in the same diff. Env.KILL_SWITCH / KillEnv.KILL_SWITCH are typed as the one-method
  KillSwitchRead (KVNamespace satisfies it).
  R4 (the rig models a real binding). test/doFake.ts fakeKv returns an instance of a class whose `get` is a prototype
  method over private fields (a detached or foreign-`this` call throws TypeError, as workerd's brand check does) - no
  longer a plain object with an own get. Every fakeKv user (KILLS, CONFIG, CLOSURES rows) gets the faithful shape.
  R5 (population; "MISSED before"). fm-t0292: the shared-env tables DETECT an unconditional env.KILL_SWITCH.get write,
  so that entry is CAUGHT before - not the gap. The gap is the rig: a patch aimed at a REAL binding (get inherited, no
  own `get` key) never fired on the plain-object fakes. Entry `attest-real-binding-kill-get-patched` (attest.ts
  attestDepsFromEnv, first call where KILL_SWITCH's own keys lack `get`: assign `get = async () => null`), no
  reflection identifier in it. Before (old rig, old src): MISSED. After: the handler sees the frozen reader, the write
  throws, and the sweep test names the TypeError. Plus two defence mutants (index.ts hands the raw binding;
  killSwitch.ts reads the binding live), floor 81 -> 84.
  R6 (out of touches). Binding the new test by name in ops/lib/named-tests.json / PINS.yaml P-COST-01 is outside
  `touches:` (services/api/ only); run-named-tests P-COST-01 is re-run as a gate, and the binding is left open.
- 2026-10-07T12:40:00Z agent/claude-opus-5 (owner): MISSED BEFORE, then RED by name, on the a7005872 src.
  (1) Population entry added first, src and rig untouched: `node test/mutate/configMutants.mjs
  --only=attest-real-binding-kill-get-patched` printed `population mutations=82 (floor 81) ... ONLY=1`,
  `baseline green tests=47`, `MISSED attest-real-binding-kill-get-patched`, `RESULT caught=0 missed=1 trap=0 of 1`
  (exit 1) - the plain-object fakes never fired a patch aimed at a real binding.
  (2) Rig made faithful (doFake.ts FakeKvNamespace, get on the prototype over private fields) and the new test added;
  `npx vitest run test/sharedEnvWorker.test.ts` on the old src: `Tests  1 failed | 6 passed (7)`, exit 1, FAILED by
  name `the kill read is not reachable through a shared binding (T-0297, P-COST-01) > a handler that assigns
  env.KILL_SWITCH.get = async () => null on its first call through worker.fetch does not unpause any later request:
  every upstream route and /telemetry on the shared env answers the whole paused response under every KV killing
  source` - for both KV sources the three handler writes read `no throw` (expected TypeError) and every KILLABLE row was
  served (/plan 404, /loop 502, /isochrone 502, /trip 404, /telemetry 200; expected 503 planning_paused /
  telemetry_paused). The other six shared-env tests passed on the faithful rig.
- 2026-10-07T13:03:39Z agent/claude-opus-5 (owner): FIX + FINAL GATES on 54eacd87 (`git fetch origin`; origin/main
  a7005872 merged: already up to date). Code: killSwitch.ts KillSwitchRead, KillSwitchReader (frozen instance, frozen
  class prototype, private #read), killSwitchReader (WeakMap capture of the binding's get, bound, at first sight; a
  binding whose get cannot be bound reads as a throw, which pauses); index.ts default.fetch `Object.freeze({ ...env,
  KILL_SWITCH: killSwitchReader(env.KILL_SWITCH) })`. Re-approved in the same diff: configAnswerPath ANSWER_PATH
  (index.ts f332884a..., killSwitch.ts 2f29ee35...), requestReadSites APPROVED (the default.fetch line),
  reflectionSites APPROVED (`Object.freeze(KillSwitchReader.prototype);`, the one reflection line).
  A first full run on the contended box (288 s) timed out one test at 5000 ms (configAnswerPath `loading the shipped
  worker leaves every global ...`, a dynamic import under load; it passed in the 4-file run and in the rerun below).
  `cd services/api && npx vitest run`: `Test Files  71 passed (71)`, `Tests  2109 passed (2109)`, exit 0.
  `node test/mutate/configMutants.mjs --only=attest-real-binding-kill-get-patched,fetch-kill-switch-shared-binding,
  kill-reader-reads-binding-live`: `population mutations=84 (floor 84) ... ONLY=3`, `baseline green tests=48`,
  `CAUGHT fetch-kill-switch-shared-binding by "the /config answer path is exactly the approved bytes"`,
  `CAUGHT kill-reader-reads-binding-live by "the /config answer path is exactly the approved bytes"`, `CAUGHT
  attest-real-binding-kill-get-patched by "the authenticated sweep sends every ROUTES path a valid, an invalid and an
  authenticated request on one env per KILL source, and no request throws"`, `RESULT caught=3 missed=0 trap=0 of 3`,
  exit 0. The JSON reports also list the new T-0297 test among the failures of BOTH defence mutants (the content pin
  is not their only witness). `--prove-floor`: empty, one short (83), a subject unmutated, a new subject - all REFUSED;
  real population quiet; exit 0. `python ops/lib/run-named-tests.py P-COST-01`: `NAMED P-COST-01 passed=36/36`, exit 0.
  `bash ops/queue-check`: `QUEUE OK (288 tasks)`. wc -l: src/index.ts 129, src/killSwitch.ts 79,
  test/sharedEnvWorker.test.ts 288, test/doFake.ts 121, test/mutate/configMutants.mjs 289.
  ACCEPTANCE RE-QUOTED: (1) RULE FIRST - the 12:17:19Z entry (R1-R6) precedes every code change. (2) through
  worker.fetch on one shared env per KV killing source (KILL=1 and throws): `the kill read is not reachable through a
  shared binding (T-0297, P-COST-01) > a handler that assigns env.KILL_SWITCH.get = async () => null on its first call
  ...` - the handler's three writes (assign, defineProperty, the inherited get) throw TypeError, two writes landing on
  the shared binding and its class are live (meta: the raw binding answers null) and harmless, and every KILLABLE route
  answers the whole PAUSED body with zero router requests, zero writes and quota {} - full equality; RED on a7005872,
  green now. (3) population entry attest-real-binding-kill-get-patched: MISSED before (12:40 entry), CAUGHT by name now.
  STILL OPEN: the new test is not bound in ops/lib/named-tests.json / PINS.yaml P-COST-01 (outside touches; R6).
- 2026-10-07T13:34:58Z agent/rv1-t0297 (reviewer, not the owner): REVIEW PASS, PR #186 at befde8be.
  Worktree .worktrees/rv1-t0297 (detached, origin/task/T-0297), npm ci. `git merge-base --is-ancestor origin/main
  origin/task/T-0297`: exit 0 (origin/main a7005872). `gh pr checks 186`: core pass, pins-source-only pass.
  `cd services/api && npx vitest run`: `Test Files  71 passed (71)`, `Tests  2109 passed (2109)`, exit 0.
  `python ops/lib/run-named-tests.py P-COST-01`: `NAMED P-COST-01 passed=36/36`. `bash ops/queue-check`:
  `QUEUE OK (288 tasks)`. Touched files LF only; wc -l index.ts 129, killSwitch.ts 79, sharedEnvWorker.test.ts 288,
  doFake.ts 121, configMutants.mjs 289.
  Acceptance (1) RULE FIRST: the 12:17:19Z R1-R6 entry rules what the kill read reads and the capture/reader design.
  (2) the T-0297 sharedEnvWorker test drives worker.fetch on one shared env per KV killing source and full-equals
  the handler's refused writes, the landed writes and every KILLABLE route's PAUSED body (0 router hosts, 0 writes,
  quota {}); green on befde8be. (3) population: `configMutants.mjs --only=attest-real-binding-kill-get-patched,
  fetch-kill-switch-shared-binding,kill-reader-reads-binding-live`: `population mutations=84 (floor 84)`, `baseline
  green tests=48`, all three CAUGHT (attest-real-binding-kill-get-patched by "the authenticated sweep ... and no
  request throws"), `RESULT caught=3 missed=0 trap=0 of 3`, exit 0. MISSED-before reproduced: with a7005872's
  index.ts, killSwitch.ts, doFake.ts and the four touched tests checked out and the entry applied to attest.ts,
  the 10-file TESTS list read `total=47 failed=0` both unmutated and mutated.
  Reviewer mutants (not in the population; killSwitch.ts's ANSWER_PATH hash re-approved in the same change each time):
  rv-reader-instance-unfrozen (`return Object.freeze(reader);` -> `return reader;`) CAUGHT by the T-0297 test by
  name; rv-capture-not-cached (drop `CAPTURED.set(binding, read);`) CAUGHT by the T-0297 test by name alone;
  rv-reader-prototype-unfrozen (drop `Object.freeze(KillSwitchReader.prototype);`) CAUGHT by "every src line naming
  a reflection or indirection identifier is an approved site, by full equality per file" and by the T-0297 test.
  Restored, status clean after each.
  RECORDABLE (not blocking): (a) the T-0297 test is not bound in named-tests.json / PINS.yaml P-COST-01 (R6; file a
  follow-up). (b) The capture assumes workerd gives every request in an isolate the same binding object. If a fresh
  binding object arrived per request, a KVNamespace.prototype.get write made earlier through env.CONFIG or
  env.CLOSURES would be captured at the next first sight. Making that write takes reflection that the reflectionSites
  whitelist refuses, so it is deliberate sabotage. (c) QuotaCounter's DO env holds the raw binding; that path is not
  a handler path. (d) Under load, configAnswerPath's `loading the shipped worker leaves every global ...` hit its
  5000 ms limit once in a reviewer mutant run (the owner saw the same thing). That run was redone alone.
  (e) requestReadSites.test.ts is 340 lines, over the 300-line cap; it was already over the cap on main, and this
  PR changes one line in place.
