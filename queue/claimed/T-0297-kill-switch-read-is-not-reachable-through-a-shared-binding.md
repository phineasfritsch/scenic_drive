---
id: T-0297
title: The kill decision cannot be bent by a handler writing to a shared binding object - KILL_SWITCH is read through a per-request wrapper, and a handler that patches a binding method is refused or harmless
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T12:09:52Z
lease_expires_at: 2026-10-08T00:09:52Z
worktree: .worktrees/T-0297
branch: task/T-0297
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: [P-COST-01]
reviewer: null
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
