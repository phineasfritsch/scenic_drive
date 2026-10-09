---
id: T-0351
title: ops/lib/sane_prod.py names its quota fields once (QUOTA_FIELDS), quota() reads through it, and check_sane_prod's R10 meta-check compares the generated field list against that shipped symbol - both halves of R10 seen red
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/sane_prod.py, ops/lib/check_sane_prod.py, ops/lib/check-sane-prod, queue/]
pins_affected: [P-OPS-08]
reviewer: null
depends_on: [T-0344]
verify: [ops/check-pins]
acceptance:
  - "sane_prod.py gains QUOTA_FIELDS (the four /__health quota keys) and quota() reads every key through it; the generator's quota field list is compared to sane_prod.QUOTA_FIELDS (as the manifest side already compares to MANIFEST_FIELDS), never to its own HEALTH fixture"
  - "Both halves of the R10 meta-check seen red by name: a field dropped from the shipped list (anchor half) and a variant dropped from the generator (coverage half), each refusing with exit 2 before any case runs; then the full table green"
---
## Brief

rv2-t0344 recordables 1 and 2 (PR #228, harness PR at its two-round limit - filed per CLAUDE.md): the quota half of
R10 compares QUOTA_KINDS to the generator's own HEALTH fixture, not to a shipped symbol (it still fails closed via
q-green, but the anchor compares a table to itself), and the field-list half of R10 was never seen red.

## Log
- 2026-10-09T18:54:55Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0344 recordables 1-2.
