---
id: T-0377
title: Bind P-PRIV-05's named-tests.json entry to a check-named-table.py digest and count
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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

## Log
- 2026-10-16 filed by agent/claude-opus-5 from T-0375 R2 / stillOpen 2, after T-0318 merged.
