---
id: T-0083
title: the read-only SQL grammar's length cap is the one rule the shared cases never reach, and its constant is duplicated
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:46:43Z
lease_expires_at: 2026-09-08T09:46:43Z
worktree: wt/T-0083
branch: task/T-0083
exclusive: []
touches: [ops/lib/ro_cases.json, ops/lib/ro_grammar.py, services/api/src/ro.ts, services/api/test/ro.test.ts, ops/test]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`services/api/src/ro.ts:4` says of itself:

    Mirrored in ops/lib/ro_grammar.py; both are tested against ops/lib/ro_cases.json so they cannot drift.

**That is true for five of the six rules and false for the sixth**, which is the one guarding a duplicated
constant. Measured:

    shared cases: 8 accept + 18 reject = 26
    longest case: 62 chars
    MAX_SQL_LENGTH: 4000
    cases that exercise the length rule: 0

    empty                      covered  ('' and '   ')
    longer than N chars        NOT COVERED
    must start with SELECT...  covered
    comments not allowed       covered  ('-- INSERT later', '/* DELETE */')
    exactly one statement      covered  ('SELECT 1; SELECT 2')
    write keyword              covered

And the constant lives in two places with nothing comparing them:

    ops/lib/ro_grammar.py:17    MAX_SQL_LENGTH = 4000
    services/api/src/ro.ts:10   export const MAX_SQL_LENGTH = 4000;

So either side's cap can be changed alone, in either direction, and both suites stay green. **The weak
direction is UP**: a larger cap admits more, and this is the read-only SQL gate that `ops/prod-read` sends
through and the Worker `/__ro` enforces again on arrival — the plan's own design says the grammar is
"enforced **again** by Worker `/__ro`", which is only a second line of defence while the two agree.

This is not hypothetical drift. [[T-0079]] found `MAX_SQL_LENGTH` while surveying ratchet constants precisely
because nothing protected it, and raised it 4000 -> 400000 in a one-line edit as its own demonstration.

- Add length cases to `ops/lib/ro_cases.json`: one accepted at exactly the cap, one rejected at cap+1. That
  single pair closes the coverage half on both sides at once, which is the whole point of the shared file.
- Assert the two constants are equal. The shared JSON is the natural home - put the number in it and have
  both implementations read it, so there is one definition rather than two that agree by luck. If that is too
  invasive for the Worker, a test that reads both files and compares is acceptable and is one assertion.
- **Fix the comment in `ro.ts` either way.** "so they cannot drift" is a claim about coverage that the
  coverage does not support, and a false comment is worse than no comment - it is the reason nobody looked.
  P-SRC/P-COST pins are anchored on identifiers and config precisely because comments get stripped; this one
  did not get stripped, it got believed.
- Check the same shape on the other duplicated safety constant: the plan pins
  `MAX_MONTHLY_UPSTREAM_CALLS` compile-time == `PINS.yaml` (P-COST-02). Confirm that pin actually compares
  them rather than reading one of them twice - the failure mode here is exactly that.

## Log
- 2026-09-08 filed by agent/claude-opus-5. Found while verifying a finding reported by the T-0079 fix agent,
  whose summary line misattributed the constant to `ops/lib/check-exec-bits`; its own log had the right file.
  Every number above was measured on `main`, not taken from that report.
- 2026-09-08T03:46:43Z claimed by agent/claude-opus-5; lease until 2026-09-08T09:46:43Z

- 2026-09-08 agent/claude-opus-5 — **CORRECTION TO THIS BRIEF, BEFORE ANY FIX.** I filed it and half of it is
  wrong. Executed, both ways:

        RED 1 (as filed): raise MAX_SQL_LENGTH in services/api/src/ro.ts only, 4000 -> 40000
          vitest:  Tests  1 failed | 33 passed (34)
          FAIL  test/ro.test.ts > "rejects anything over the length cap"

  **The TypeScript side IS covered.** `ro.test.ts:16` builds `"SELECT " + "1,".repeat(3000) + "1"` — about
  6007 characters — and asserts it is rejected. I checked `ro_cases.json` for a long case, found none
  correctly, and never opened `ro.test.ts`. The brief's claim that "either side's cap can be changed alone and
  both suites stay green" is false for the TS side and I should not have written it without looking.

  **RED 2 is the real defect, and it is worse than the one I filed.**

        references to ro_grammar in ops/test:     0
        references to ro_grammar in pins/PINS.yaml: 0

        make read_only_problem() return None for everything:
          read_only_problem('DROP TABLE users') -> None
          vitest:  Tests  34 passed (34)

  **The Python mirror is executed by nothing automatic.** `ro_grammar.py --self-test` exists, runs the 26
  shared cases and prints `RO-GRAMMAR OK 26 cases` — and no workflow, no pin and `ops/test` itself never call
  it. So `ops/lib/ro_grammar.py` can be made to accept `DROP TABLE users` with the entire suite green.

  That matters because of who runs it: `ops/prod-read` is the tool a human points at **production**, and its
  only gate is `"$PY" ops/lib/ro_grammar.py "$sql"`. The Worker's `/__ro` is the second line of defence and is
  well tested; the first line is tested by nothing.

  So the corrected work is:
  1. `ops/test` must run the Python self-test. That is the structural fix and it is one line.
  2. A long case belongs in `ro_cases.json` so the length rule is covered on BOTH sides from one place —
     currently the TS side covers it in a test the Python side cannot see.
  3. The two `MAX_SQL_LENGTH` constants still have nothing comparing them.
  4. `ro.ts`'s "so they cannot drift" comment is still an overclaim: the shared cases constrain only what is
     in them, and the Python side was not being run at all.

  `touches:` widened to include `ops/test` for item 1, which the original scope did not cover.
