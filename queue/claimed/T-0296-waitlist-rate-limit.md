---
id: T-0296
title: POST /waitlist counts one device once per cell per day - a rate limit so anyone cannot inflate a cell's count
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T09:30:08Z
lease_expires_at: 2026-10-07T21:30:08Z
worktree: .worktrees/T-0296
branch: task/T-0296
exclusive: []
touches: [services/api/src/waitlist.ts, services/api/test/, services/api/migrations/, ops/lib/named-tests.json, pins/PINS.yaml, queue/]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0293]
verify: [ops/check-pins]
acceptance:
  - "RULE FIRST: the identity a waitlist write is bound to (the attested session / install id the quota already uses), and how a per-device-per-cell-per-day dedupe is stored without keeping the device id next to the cell (e.g. a keyed hash that expires daily) - P-PRIV-05 DDL test extended"
  - "Through worker.fetch: the same device posting the same cell twice in one UTC day increments once; a second device increments again; the next day increments again - full-equality table"
  - "Population entries for the dedupe key and the day boundary, MISSED before and CAUGHT by name after"
---
## Brief

T-0293 author stillOpen 4 (PR #182): /waitlist has no rate limit, so anyone can inflate a cell's count. The waitlist
must stay free of personal data (memory user-lives-in-la; plan Launch scope).

## Log
- 2026-10-07T07:17:54Z filed by agent/claude-opus-5 (orchestrator) from T-0293's stillOpen 4.
- 2026-10-07T09:30:08Z claimed by agent/claude-opus-5; lease until 2026-10-07T21:30:08Z
- 2026-10-07T09:38:35Z RULINGS (author rule, before any code):
  - R1 identity. A waitlist write is bound to identifyCaller's userId - the bucket /telemetry and the quota use
    (sessionIdentity.ts): the verified session JWT's sub when SESSION_JWT_SECRET is set, the x-scenic-device install
    bucket (routerDeps deviceIdentity) only on the legacy/IDENTITY_HEADERS=1 path. The tier is never read. Every caller
    without a valid identity shares UNIDENTIFIED_SESSION and so counts as ONE device: at most +1 per cell per day for
    all of them together. LIMIT (recorded, not closed): while IDENTITY_HEADERS=1 a header id is as forgeable for the
    waitlist as it is for the quota; with the secret set and the flag unset only an attested session counts.
  - R2 key. day = now.toISOString().slice(0, 10) (the UTC day, the quota's dayKey). K_day =
    HMAC-SHA256(SESSION_JWT_SECRET, "scenic-waitlist/v1/" + day), computed per request, never stored, logged or
    returned. tag = lowercase hex HMAC-SHA256(K_day, userId + "\n" + cell) - 64 chars. The cell is IN the message, so two
    cells of one device give unrelated tags; the day is in the KEY, so one device's tags on two days are unrelated.
    The secret is read through sessionSecret() (>= 32 chars, MIN_SECRET_LENGTH); reusing SESSION_JWT_SECRET is ruled
    over a new owner secret: the domain prefix separates the uses, and identity is attested only when it is set anyway.
  - R3 fail closed. sessionSecret(env.SESSION_JWT_SECRET) === null (unbound, empty, 31 chars) is 503
    waitlist_unavailable with NO write - never an unlimited count. Checked after the body is valid (400s unchanged).
  - R4 storage. New migration 0007_waitlist_seen.sql (0006 is shipped; a D1 migration once applied is never re-run):
    waitlist_seen (tag TEXT PRIMARY KEY CHECK length 64, day TEXT CHECK length 10). No device, account, cell or instant
    column. Every accepted write first runs DELETE FROM waitlist_seen WHERE day <> today, so no tag outlives its UTC
    day; then INSERT ... ON CONFLICT (tag) DO NOTHING; the waitlist count moves only when that insert's
    meta.changes === 1. Two statements, not one transaction: a failure between them under-counts by one, the safe
    direction. The answer is 200 {waitlisted: true} whether or not the count moved (no membership oracle).
  - R5 kill-switch and quota exemption by ruling unchanged (no upstream, no quota touch). The deletion whitelist
    (accountDelete.test.ts TABLES) gains waitlist_seen as not user-keyed (a tag cannot be mapped back to a device
    without the day key and the cell, and is gone at the next UTC day).
  - R6 tests. New waitlistDedupe.test.ts through worker.fetch: a sequence table (same device same cell twice; second
    device; second cell; unidentified twice; next day; the day bound at 23:59:59.999Z / 00:00:00.000Z) over the
    empty and holding variants, waitlist AND waitlist_seen compared WHOLE against an independent WebCrypto oracle of
    the tag; secret unbound / "" / 31 chars -> 503 with both tables unchanged, 32 chars accepted. The T-0293 tests keep
    their names (P-PRIV-06 binds them); their bodies send with a session and use two devices where they counted two.
    migrationColumns.test.ts gains `waitlist_seen is exactly (tag, day)` for P-PRIV-05's DDL clause.
  - R7 touches widened by ruling to ops/lib/named-tests.json and pins/PINS.yaml: binding the new tests BY NAME under
    P-PRIV-05 / P-PRIV-06 is the only way the acceptance's "P-PRIV-05 DDL test extended" is enforced.
