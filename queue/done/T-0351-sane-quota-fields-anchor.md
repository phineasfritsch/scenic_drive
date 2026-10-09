---
id: T-0351
title: ops/lib/sane_prod.py names its quota fields once (QUOTA_FIELDS), quota() reads through it, and check_sane_prod's R10 meta-check compares the generated field list against that shipped symbol - both halves of R10 seen red
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T19:47:24Z
lease_expires_at: 2026-10-10T03:47:24Z
worktree: .worktrees/T-0351
branch: task/T-0351
exclusive: []
touches: [ops/lib/sane_prod.py, ops/lib/check_sane_prod.py, ops/lib/check-sane-prod, queue/]
pins_affected: [P-OPS-08]
reviewer: agent/rv1-t-0351
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
- 2026-10-09T19:47:24Z claimed by agent/claude-opus-5; lease until 2026-10-10T03:47:24Z
- 2026-10-09T19:50:12Z MEASURED (before code, on b048be30): check_sane_prod.CASES = 138 (41 hand-written + 97
  generated, 43 of them quota rows x-kill_switch/x-upstream_*); HEALTH fixture keys = db, git_sha, kill_switch, ok,
  upstream_calls, upstream_month, upstream_trip_at; QUOTA_KINDS = the four quota keys; sane_prod has no QUOTA_FIELDS;
  quota() reads the four keys as four string literals (sane_prod.py lines 41-44); meta_problems() line 191 compares
  set(QUOTA_KINDS) to set(HEALTH) - {ok, db, git_sha} - the generator's table against the generator's own fixture;
  meta_problems() today = []. The Worker writes the four keys in services/api/src/index.ts lines 83-86 in the order
  kill_switch, upstream_month, upstream_calls, upstream_trip_at. check_sane_prod.py is 300 lines (at the cap).
  RULINGS:
  R1 sane_prod.QUOTA_FIELDS = ("kill_switch", "upstream_month", "upstream_calls", "upstream_trip_at"), the Worker's
     order; quota() binds kill, month, calls, trip by unpacking `h.get(k) for k in QUOTA_FIELDS`, so no quota key is
     spelled anywhere else in quota(); a field added to or dropped from QUOTA_FIELDS without quota() raises at the
     unpack (uncaught -> exit 1 -> ops/sane exit 6, fail closed) and the meta-check refuses first in the check.
  R2 The quota half of R10 compares set(QUOTA_KINDS) to set(sane_prod.QUOTA_FIELDS) and NOTHING else - the HEALTH
     comparison is removed (acceptance 1: "never to its own HEALTH fixture"). The fixture still has to hold every
     field because variants() reads each field's good value from it (a KeyError at import, not an anchor). Both
     shipped symbols are read with getattr(sane_prod, NAME, ()), so a sane_prod without the symbol (the pre-change
     file) refuses with exit 2 by the meta line instead of an AttributeError traceback.
  R3 Sets, not order, as the manifest side already does; the order is quota()'s business (R1's unpack).
  R4 check_sane_prod.py stays <= 300: the change is in place (the condition and message lines of the quota half).
  R5 pins/PINS.yaml is not in touches; P-OPS-08's text ("the shipped sane_prod.MANIFEST_FIELDS plus the /__health
     quota keys") stays true - QUOTA_FIELDS IS those keys - and the case count 138 does not change; not edited.
  R6 Red, by name, each refusing exit 2 with zero "SANE-PROD pass" lines (before any case runs), driven by a
     restore-checked script under .build-t0351/ (gitignored) that purges ops/lib/__pycache__ and sleeps 1.1 s
     before restoring: anchor half - (a) "upstream_month" dropped from shipped QUOTA_FIELDS, (b) "bytes" dropped
     from shipped MANIFEST_FIELDS, (c) the new check against the pre-change sane_prod.py (no QUOTA_FIELDS);
     coverage half - (d) the "negative" variant dropped from the generator's int branch; then the full table green.
- 2026-10-09T19:52:19Z CODE: sane_prod.py gains QUOTA_FIELDS and quota() reads `kill, month, calls, trip = (h.get(k)
  for k in QUOTA_FIELDS)`; check_sane_prod.meta_problems() compares set(QUOTA_KINDS) to
  set(getattr(sane_prod, "QUOTA_FIELDS", ())) only (the HEALTH-fixture comparison is gone) and the manifest side to
  getattr(sane_prod, "MANIFEST_FIELDS", ()) (plus MANIFEST, unchanged). `wc -l`: sane_prod.py 113,
  check_sane_prod.py 300 (the R10 comment folded to one line to make room). RED, `python .build-t0351/drive.py`
  (each mutant alone, ops/lib/__pycache__ purged, 1.1 s before a byte-checked restore):
    MUTANT a-anchor-quota-field-dropped: exit=2 pass_lines=0 RED-AS-REQUIRED
       SANE-PROD refuse   meta: quota fields ['kill_switch', 'upstream_calls', 'upstream_month', 'upstream_trip_at'] != shipped QUOTA_FIELDS ['kill_switch', 'upstream_calls', 'upstream_trip_at']
    MUTANT b-anchor-manifest-field-dropped: exit=2 pass_lines=0 RED-AS-REQUIRED
       SANE-PROD refuse   meta: manifest fields ['bytes', 'min_app_build', 'schema_version', 'sha256', 'version'] != shipped MANIFEST_FIELDS ['min_app_build', 'schema_version', 'sha256', 'version']
    MUTANT c-anchor-pre-change-sane-prod: exit=2 pass_lines=0 RED-AS-REQUIRED
       SANE-PROD refuse   meta: quota fields ['kill_switch', 'upstream_calls', 'upstream_month', 'upstream_trip_at'] != shipped QUOTA_FIELDS []
    MUTANT d-coverage-variant-dropped: exit=2 pass_lines=0 RED-AS-REQUIRED
       SANE-PROD refuse   meta: field upstream_calls has no row for ['negative']; field upstream_trip_at has no row for ['negative']; field schema_version has no row for ['negative']; field min_app_build has no row for ['negative']; field bytes has no row for ['negative']
    DRIVER 4/4 mutants red as required
  Each refused by the meta line with exit 2 and zero `SANE-PROD pass` lines - before any case ran.
- 2026-10-09T20:55:07Z FIRST full run (19:53:02Z-20:55:07Z, 62 min on a loaded box) is NOT counted: I edited this
  file and committed e1282696 while it ran, and the table's own never-mutates guard refused the two cases running at
  those moments - `SANE-PROD FAIL x-upstream_trip_at-number: git status or HEAD changed across the run` and
  `x-upstream_trip_at-negative` (same), each with the right exit 6 and quota FAIL row; 136 passed, rc=1. Re-run clean.
- 2026-10-09T21:52:14Z GREEN on e1282696, tree untouched for the whole run (20:57:32Z-21:52:14Z), origin/main ==
  b048be30 (fetched 20:56Z, nothing to merge): `bash ops/lib/check-sane-prod` rc=0, 138 `SANE-PROD pass` lines,
  `SANE-PROD ok       138/138 cases passed (sane=ops/sane, fake=http://127.0.0.1:57269)`; the meta-check passed
  (no refuse); the two rows above `SANE-PROD pass x-upstream_trip_at-number exit=6` and `...-negative exit=6`.
  ACCEPTANCE re-quoted:
  1 "sane_prod.py gains QUOTA_FIELDS ... quota() reads every key through it; the generator's quota field list is
    compared to sane_prod.QUOTA_FIELDS ..., never to its own HEALTH fixture" - MET: QUOTA_FIELDS at sane_prod.py
    line 23, quota()'s only key reads are the one unpack over it; meta_problems() has no HEALTH reference (R2).
  2 "Both halves of the R10 meta-check seen red by name ... each refusing with exit 2 before any case runs; then the
    full table green" - MET: mutants a/b/c (anchor) and d (coverage) above, exit 2, 0 pass lines; green 138/138.
- 2026-10-09T22:44:30Z REVIEW PASS by agent/rv1-t-0351 (not the owner) on 2fddff63 (PR #236). Read the diff: QUOTA_FIELDS
  at sane_prod.py line 23, quota() reads the four keys by one unpack over it; meta_problems() compares set(QUOTA_KINDS)
  to getattr(sane_prod, QUOTA_FIELDS, ()) only, no HEALTH comparison; wc -l 300 / 113. Reviewer mutants
  (.build-rv1-t0351/drive.py, pycache purged, 1.1 s before a byte-checked restore, DRIVER 5/5 as expected):
    m1a quota() reads upstream_trip_at by a literal h.get, QUOTA_FIELDS drops it: exit=2 pass_lines=0
       SANE-PROD refuse   meta: quota fields [...4] != shipped QUOTA_FIELDS ['kill_switch', 'upstream_calls', 'upstream_month']
    m1b quota() reads trip by a literal h.get of a key outside QUOTA_FIELDS (upstream_trip): exit=1
       SANE-PROD FAIL     q-green: exit 6, want 0; row quota ['FAIL'], want [ok]
    m1c quota() reads upstream_trip_at by a literal h.get, QUOTA_FIELDS unchanged: exit=0 (behaviourally
       equivalent; "every key through QUOTA_FIELDS" is a source property no check holds - recordable)
    m2a QUOTA_FIELDS gains upstream_limit the generator lacks: exit=2 pass_lines=0
       SANE-PROD refuse   meta: quota fields [...4] != shipped QUOTA_FIELDS [..., 'upstream_limit', ...]
    m2b the same with quota()'s unpack widened to five: exit=2 pass_lines=0, same meta line
  Gates bare: check-exec-bits rc=0 (202 files); check-pins-yaml rc=0 (pins=50 fields=403); queue-check rc=0 (340);
  check-sane-prod --only 6 quota cases rc=0 6/6 (full 138 not re-run: no ops/ or services/api change since the
  owner's green e1282696, merge 2fddff63 brought none); gh pr checks: core pass, pins-source-only pass;
  merge-base --is-ancestor origin/main origin/task/T-0351 rc=0.
