---
id: T-0377
title: Bind P-PRIV-05's named-tests.json entry to a check-named-table.py digest and count
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T10:29:45Z
lease_expires_at: 2026-10-17T10:29:45Z
worktree: .worktrees/T-0377
branch: task/T-0377
exclusive: []
touches: [pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0375, T-0318]
verify: [ops/check-pins]
acceptance: []
---
## Brief

P-PRIV-05 binds 38 Swift and 32 vitest tests by name through `ops/lib/run-named-tests.py`, and its own
why_no_test_catches_it ends by saying what that does not hold: "this row carries no check-named-table.py
digest, so a name dropped from its table together with its test stays green". `run-named-tests.py` refuses
only an entry that names zero tests, so deleting one privacy test AND its row in `named-tests.json` in the same
diff is green today. T-0375 R2 left this open because T-0318 was editing the same entry; T-0318 merged
(PR #258, 2026-10-16), so the entry is now stable.

P-STORE-02 already shows the shape (`check-named-table.py P-STORE-02 <sha256> <count>` and its `--prove-red`
in the assertion). Do the same for P-PRIV-05:

- MEASURE: the live P-PRIV-05 entry's canonical digest and distinct-name count (`check-named-table.py` prints
  both on a mismatch), quoted in the Log.
- Add `check-named-table.py P-PRIV-05 <sha256> <count>` and its `--prove-red` run to P-PRIV-05's assertion,
  BEFORE the existing run-named-tests call.
- Do NOT add P-STORE-02's exact `passed=N/N` line check: on the Windows box the GRDB-gated
  UserStorePrivacyTests is MISSING by design (passed=75/76 measured 2026-10-16), so the exact line would be
  red there. Rule this in the Log.
- Demonstrate RED: drop one row (with its test) from the entry - the guard exits non-zero naming P-PRIV-05;
  then green. Update the why_no_test_catches_it sentence that says no digest exists (append a dated T-0377
  sentence; do not edit earlier dated record text).
- PINS.yaml stays strict (`python ops/lib/check-pins-yaml.py`).

## Acceptance
1. pins/PINS.yaml P-PRIV-05 `assertion` runs, after check-learned-speeds-sites.py and BEFORE
   `run-named-tests.py P-PRIV-05`, exactly `check-named-table.py P-PRIV-05
   4c879f4d82feb076775b971c0c7ead5730f3c4c5252a5eec84fb8fa5de7f1a45 76` and `check-named-table.py --prove-red
   P-PRIV-05 <same sha> 76 >/dev/null`, each joined by `&&`; nothing else in the assertion changes and no
   `passed=N/N` line check is added (ruling R2).
2. `ops/lib/named-tests.json` is byte-identical to origin/main's (sha256
   a578ae8e9f3753d09376cd927fbf74cf2b9803e9ee6546124f849d3777597695 at fbeb99b8); `python
   ops/lib/check-named-table.py P-PRIV-05 <sha> 76` exits 0 and `--prove-red` prints `PROVE-RED OK: 8 of 8`.
3. Seen RED through the SHIPPED assertion string (read from PINS.yaml by yaml.safe_load, run by `bash -c`): with
   one vitest row dropped from the P-PRIV-05 entry AND that test deleted from its .ts file (neither committed),
   the assertion exits non-zero with `NAMED-TABLE P-PRIV-05 FAILED` and the count/digest refusals, and
   run-named-tests never runs. Both files are then restored and their sha256 equal the committed blobs'.
4. GREEN: the same shipped assertion on the restored tree prints `NAMED-TABLE P-PRIV-05 ok - 76 distinct names`
   and reaches run-named-tests, whose only non-pass on this Windows box is the GRDB-gated UserStorePrivacyTests
   MISSING (passed=75/76, ruling R2); CI's Linux job runs it whole.
5. pins/PINS.yaml P-PRIV-05 `why_no_test_catches_it` gains one appended dated T-0377 sentence; no earlier text
   and no other field or pin changes. Gates `python ops/lib/check-pins-yaml.py`, `bash ops/check-pins
   --source-only`, `bash ops/lib/check-exec-bits`, `bash ops/queue-check` exit 0 on the merged head.

## Log
- 2026-10-16 filed by agent/claude-opus-5 from T-0375 R2 / stillOpen 2, after T-0318 merged.
- 2026-10-16T10:29:45Z claimed by agent/claude-opus-5; lease until 2026-10-17T10:29:45Z
- 2026-10-16T10:31:18Z MEASURE (worktree at fbeb99b8, named-tests.json sha256 a578ae8e...7695, last touched by
  9d5551c9 2026-10-16): `check-named-table.py P-PRIV-05 000...0 0` printed `REFUSED count 76 distinct names !=
  approved 0` and `REFUSED digest 4c879f4d82feb076775b971c0c7ead5730f3c4c5252a5eec84fb8fa5de7f1a45 != approved
  000...0`, exit 1. The entry is {vitest: 15 files, 38 names; swift: filter + 38 tests}. `--prove-red P-PRIV-05
  4c879f4d...1a45 76` printed both CONTROLs green, eight RED rows by name, `PROVE-RED OK: 8 of 8 rows red by name,
  controls green`, exit 0.
- 2026-10-16T10:31:18Z RULINGS before the change.
  R1: the Brief says the row binds "38 Swift and 32 vitest" tests; measured 38 vitest + 38 Swift = 76 distinct.
  The 32 is T-0318's vitest count from its own dated sentence; later entries added names. Reality wins: the
  approved count is 76, which agrees with the Brief's own passed=75/76 measurement.
  R2: no exact `NAMED P-PRIV-05 passed=76/76` line check, as the Brief directs: UserStorePrivacyTests is
  GRDB-gated and MISSING by design on the Windows box (passed=75/76), so an exact line would be red there.
  run-named-tests' own exit status stays the test gate, as before.
  R3: the two calls use the assertion's existing inline `${PYTHON:-...}` spelling (not P-STORE-02's `py=`
  prefix), so no other part of the assertion changes; the --prove-red output goes to /dev/null as in P-STORE-02.
  R4: `touches:` names named-tests.json, but this task changes it only uncommitted, for the RED demonstration;
  the committed table is unchanged (acceptance 2).
  R5: the pin runs_on [linux]; on this box the assertion is run directly by `bash -c` on the string
  yaml.safe_load reads from PINS.yaml, so the demonstration exercises the shipped text, not a retyped copy.
- 2026-10-16T10:46:59Z CHANGE: pins/PINS.yaml P-PRIV-05 assertion gains, between check-learned-speeds-sites.py and
  run-named-tests.py, `check-named-table.py P-PRIV-05 4c879f4d...1a45 76 && check-named-table.py --prove-red
  P-PRIV-05 4c879f4d...1a45 76 >/dev/null &&` (each with the inline `${PYTHON:-...}`; one replacement asserted by
  the edit script); why_no_test_catches_it gains one appended dated T-0377 sentence. `python
  ops/lib/check-pins-yaml.py`: `PINS-YAML ok pins=51 fields=411`, exit 0.
- 2026-10-16T10:46:59Z RED through the shipped assertion (yaml.safe_load of PINS.yaml -> `PYTHON=python bash -c`):
  dropped the P-PRIV-05 row `POST /search takes ... (T-0359 R3/R4, P-PRIV-05) > a body that is not JSON is 400
  with zero Photon requests` from named-tests.json AND deleted that test (lines 99-103) from
  services/api/test/searchShape.test.ts, neither committed (`git diff --stat`: 1 and 5 deletions). Printed:
  `P-PRIV-05 emit sites: ok ...`, `P-PRIV-05 learned speeds: ok ...`, `REFUSED count 75 distinct names != approved
  76`, `REFUSED digest 63cdaf75e25f9ea39371fc8f831523e8d046e1fadf9e795017169ef4194b742a != approved
  4c879f4d...1a45`, `NAMED-TABLE P-PRIV-05 FAILED - re-approve the digest and count beside the assertion`, rc=1;
  no NAMED line (run-named-tests not reached). Restored: git hash-object equals HEAD's blob for both files
  (named-tests.json 05a0ad8d..., searchShape.test.ts 4ecfd008...).
- 2026-10-16T10:46:59Z GREEN, same shipped assertion on the restored tree (SCENIC_SWIFT_SCRATCH=.build/t0377 of
  the main checkout; the worktree first needed `npm ci` in services/api, whose absence the runner refused by
  name): `NAMED-TABLE P-PRIV-05 ok - 76 distinct names, sha256 4c879f4d82fe`, then `RED
  PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail(): MISSING - no test of this name ran` and
  `NAMED P-PRIV-05 passed=75/76`, rc=1 - the GRDB-gated environment MISSING of ruling R2 and nothing else; CI's
  Linux core job runs it whole.
- 2026-10-16T11:46:02Z ACCEPTANCE re-quoted on the merged head f08d8094 (`git fetch origin` in the main checkout;
  origin/main fbeb99b8 is an ancestor, `merge-base --is-ancestor` yes):
  1. `git diff origin/main -- pins/PINS.yaml`: P-PRIV-05's assertion and why_no_test_catches_it lines only; the
     assertion's new text is exactly `... check-learned-speeds-sites.py && <py> ops/lib/check-named-table.py
     P-PRIV-05 4c879f4d82feb076775b971c0c7ead5730f3c4c5252a5eec84fb8fa5de7f1a45 76 && <py>
     ops/lib/check-named-table.py --prove-red P-PRIV-05 4c879f4d...1a45 76 >/dev/null &&<py>
     ops/lib/run-named-tests.py P-PRIV-05`; no passed= line. PASS.
  2. named-tests.json sha256 a578ae8e9f3753d09376cd927fbf74cf2b9803e9ee6546124f849d3777597695 (unchanged);
     `NAMED-TABLE P-PRIV-05 ok - 76 distinct names, sha256 4c879f4d82fe` [rc=0]; `PROVE-RED OK: 8 of 8 rows red
     by name, controls green` [rc=0]. PASS.
  3. RED: the 10:46:59Z entry above (rc=1, count 75 and digest refused by name, run-named-tests not reached;
     both files restored to HEAD's blobs). PASS.
  4. GREEN: the 10:46:59Z entry above (`NAMED-TABLE P-PRIV-05 ok`, passed=75/76 with only UserStorePrivacyTests
     MISSING). PASS (Windows); CI's Linux job is the whole-green confirmation.
  5. why_no_test_catches_it gains one appended T-0377 sentence, earlier text unchanged. Gates, bare:
     `PINS-YAML ok pins=51 fields=411` [rc=0]; `P-OPS-01: 230 files, 23 required present, all modes correct`
     [rc=0]; `QUEUE OK (368 tasks)` [rc=0]; `PINS ok=22 skipped=28 pending=1 expired=0 failed=0 tier=linux
     source-only` [rc=0]. PASS.
- 2026-10-16 filed by agent/claude-opus-5 from T-0375 R2 / stillOpen 2, after T-0318 merged.
- 2026-10-16T10:29:45Z claimed by agent/claude-opus-5; lease until 2026-10-17T10:29:45Z
