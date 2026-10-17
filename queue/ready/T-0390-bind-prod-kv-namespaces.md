---
id: T-0390
title: Bind the production KV namespaces (PLANS, CONFIG, KILL_SWITCH, CLOSURES) in services/api/wrangler.jsonc - the owner created them 2026-10-17
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/wrangler.jsonc, services/api/test/, services/api/src/index.ts, pins/PINS.yaml]
pins_affected: [P-SAFE-08, P-COST-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The owner authorised the pilot backend on 2026-10-17. The orchestrator then created these Cloudflare KV namespaces
on the owner's account. The ids are not secrets.
- scenic-plans       33e411b3b03246a19cda166c0c05cfd6  -> binding PLANS
- scenic-config      8dd224a7fb554dc4a270f67162d28bb6  -> binding CONFIG
- scenic-kill-switch 8946404cc991458196d195c65ea15d7b  -> binding KILL_SWITCH
- scenic-closures    5e3eb553f16c4e4ba4d5297e001ef5ea  -> binding CLOSURES
It also created the R2 bucket scenic-data. That bucket is for tiles and corpus published by ops/publish-*, and the Worker does not bind it.
D1 'scenic' has every migration through 0010 applied remotely. The secrets SESSION_JWT_SECRET, ROUTER_SECRET,
SEARCH_SECRET and RO_TOKEN are set. ROUTER_URL stays the placeholder until the VPS router exists (separate step).

Bind the four namespaces in wrangler.jsonc using exactly these ids and binding names: the binding names the shipped
src/index.ts Env reads.
- Update closuresCron.test.ts. It currently asserts that CLOSURES is NOT bound. It should now assert that the CLOSURES
  binding exists with this id and that the cron is still every 15 minutes.
- Update every comment and pin sentence that says "not bound in wrangler.jsonc". In PINS.yaml, append a dated
  sentence. Never edit dated text.
- Add one test that reads wrangler.jsonc and checks the binding set against the Env bindings the shipped Worker
  reads. Compare whole: a binding added or dropped on either side must fail.

No deploy in this task. The deploy is T-0391, holding exclusive [prod].

## Log
- 2026-10-17 filed by agent/claude-opus-5 after the owner authorised backend setup.
