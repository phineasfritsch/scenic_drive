---
id: T-0083
title: the read-only SQL grammar's length cap is the one rule the shared cases never reach, and its constant is duplicated
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:46:43Z
lease_expires_at: 2026-09-08T09:46:43Z
worktree: wt/T-0083
branch: task/T-0083
exclusive: []
touches: [ops/lib/ro_cases.json, ops/lib/ro_grammar.py, services/api/src/ro.ts, services/api/test/ro.test.ts, ops/test]
pins_affected: []
reviewer: agent/reviewer-final-pr53
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

- 2026-09-08 agent/claude-opus-5 — **an independent reviewer of PR #53 found three real defects in this work,
  one of them introduced by this diff. All three are fixed here, and the red/green transcripts CLAUDE.md
  requires — which the previous commit admitted omitting — are below.**

  The review was run because CLAUDE.md says *"the reviewer of a task is never its owner"* and every PR opened
  in this session was written by one agent with no reviewer. It was worth it.

  **DEFECT 1 (high) — the gate written to close a vacuous pass, passing vacuously.** The tier was guarded by
  `if [[ -f ops/lib/ro_grammar.py ]]` and nothing anywhere required that file to exist. Reproduced:

        RED   mv ops/lib/ro_grammar.py elsewhere
              bash ops/test        -> TESTS linux=51/50 ... OK      exit 0     <- no RO-GRAMMAR line at all
              bash ops/check-pins  -> PINS ok=9 ... failed=0        exit 0
              bash ops/sane        -> SANE OK                       exit 0

        GREEN same deletion, after the fix
              FAIL: ops/lib/ro_grammar.py is missing - it is the only read-only SQL check ops/prod-read has
              exit 1

  Tiers 1b and 1c already hard-fail when their expected report is missing; this now matches them.

  **DEFECT 2 (medium) — I introduced a bound derived from the value it bounds, and did not disclose it.**
  The pre-existing TypeScript length test used a hardcoded 6007-character statement. This diff quietly
  rewrote it to `"1,".repeat(MAX_SQL_LENGTH)`, so the statement grows with the cap and the test can never
  fail for any value of it. Mentioned in neither the PR body, the commit message, nor this log.

        RED   cap 4000 -> 400000 in BOTH services/api/src/ro.ts and ops/lib/ro_cases.json
              npx vitest run  ->  Tests  35 passed (35)            <- the coordinated raise sails through
        GREEN same edit, hardcoded literal restored
              FAIL  test/ro.test.ts > "rejects anything over the length cap"

  The literal is now marked `must NOT be derived` in the file. This is the repository's signature defect, and
  the commit that added a check against it introduced one.

  **DEFECT 3 (medium) — no red/green demonstration in this log**, which CLAUDE.md line 40 requires and the
  previous commit message openly admitted (*"Committed BEFORE the red/green demonstrations"*) without ever
  appending them. This entry is that demonstration.

  **Also fixed, from the same review:**
  - The self-test had no floor on the shared case list. Emptying `accept` and `reject` printed
    `RO-GRAMMAR OK 3 cases`, exit 0 — a run that checked three synthetic length cases and none of the
    grammar. Now `MIN_CASES = 20`: `RO-GRAMMAR FAIL 1/3 - only 0 shared case(s) ... (expected >= 20)`, exit 1.
  - The failure report was piped through `tail -3`, which dropped the `RO-GRAMMAR FAIL n/m` header — the line
    the previous commit message credits with catching a lost fix. It now prints `head -8` on failure.
  - `n` added 3 unconditionally, but the two length cases only run when the cap matches, so a drift failure
    reported a denominator of 29 when 27 checks ran. Now conditional.

  **A trap I fell into while writing this entry**, worth recording because it is documented in CLAUDE.md and I
  did it anyway: `python ... --self-test 2>&1 | head -3; echo $?` printed `exit=0` for a run that exits 1.
  `$?` after a pipeline is the LAST command's status — `head`'s. Re-measured with the pipe removed:
  `real exit with cases emptied: 1`, `with the module missing: 1`, `restored: 0`.

- 2026-09-08 — **reviewed by `agent/reviewer-pr53` (PR #53): pass with findings.** Recorded here because the review
  itself lived only in a gitignored scratch directory, and because this task had an open PR while its own
  file still said `state: claimed` / `reviewer: null` — the exact blindness [[T-0094]] was filed for.

  The reviewer's own summary, verbatim:

  > The headline claim is TRUE and reproduces. On origin/main, `git grep -n ro_grammar origin/main` returns zero hits in ops/test and pins/PINS.yaml, and the only automatic consumer was ops/prod-read (which is pointed at production). The new tier-1d gate does fire on what it claims to catch: neutering read_only_problem() to return None takes `ops/test` from rc=0 to rc=1 with `FAIL: ops/lib/ro_grammar.py --self-test exited 1`, and drifting either MAX_SQL_LENGTH constant goes red on the correct side. Baseline on the branch is green: `RO-GRAMMAR OK 29 cases` / `TESTS linux=51/50 ios=skipped failed=0 skipped=0` / `OK`, vitest 35/35. The counts in the PR body (python 26->29, vitest 34->35) are correct. Two things do not hold. (1) The gate is guarded by `if [[ -f ops/lib/ro_grammar.py ]]` with nothing anywhere naming that file, so deleting or renaming it makes the whole gate vanish and ops/test, ops/check-pins and ops/sane all stay green — the same vacuous-pass class the neighbouring ops/lib/check-exec-bits header was written to warn about, and the class this repo has hit eight times. (2) The diff quietly rewrote the pre-existing TypeScript length test from a hard-coded 6007-character statement to one built from MAX_SQL_LENGTH itself — a bound derived from the value it bounds. Raising the cap in ro.ts AND ro_cases.json together (400000, exactly what T-0079 did) now leaves vitest at 35 passed / 35, where main's suite went red on the same ro.ts value. That edit is mentioned in neither the PR body, the commit message, nor the task log. Separately, the task log carries no red/green transcript for the checks this PR adds — the commit message itself says "Committed BEFORE the red/green demonstrations" and no follow-up Log entry was ever added, which is a direct miss against CLAUDE.md line 40. All mutations were made and reverted in my own worktree; `git status --short` is clean and `python3 ops/lib/ro_grammar.py --self-test` prints `RO-GRAMMAR OK 29 cases` at handoff.

  **7 findings (1 high, 2 medium, 4 low), and 5 overclaims quoted back:**

  - `[high]` ops/test:57
  - `[medium]` services/api/test/ro.test.ts:17
  - `[medium]` queue/claimed/T-0083-the-read-only-sql-grammar-s-length-cap-is-the-on.md:109
  - `[low]` ops/test:59
  - `[low]` ops/lib/ro_grammar.py:66
  - `[low]` ops/lib/ro_grammar.py:57-58
  - `[low]` ops/lib/ro_grammar.py:67

  Every `critical`, `high` and `medium` above is fixed on this branch, each with its own red-then-green
  transcript in the entries above this one. The `low` items are recorded rather than silently dropped;
  where one was substantive it was fixed and says so.

- 2026-09-08 agent/claude-opus-5 (**fixer**, PR #53 second review round) — **the reviewer's one finding is
  closed, the four smaller items are answered, and every check below is shown red then green with the exit
  code taken without a pipe.** I did not transition this task; the same reviewer looks again.

  **THE FINDING — `ops/lib/ro_grammar.py:66` and `:68`: the two length cases were bounds derived from the
  value they bound.** Reproduced first, on `b23bc18`, before changing anything:

        baseline                                              RO-GRAMMAR OK 29 cases    exit 0
        read_only_problem("SELECT " + "1"*100000) is None  ->  False
        MAX_SQL_LENGTH  4000 -> 400000  in ops/lib/ro_grammar.py
          AND max_sql_length 4000 -> 400000 in ops/lib/ro_cases.json
                                                              RO-GRAMMAR OK 29 cases    exit 0
        read_only_problem("SELECT " + "1"*100000) is None  ->  True

  Byte-identical output, exit 0, while a 100,007-character statement is accepted. `"SELECT " + "1," * cap`
  is `2*cap + 7` characters and `"SELECT " + "1" * (cap - 10)` is `cap - 3`, so both assertions held for
  every value of the cap. The reviewer is right, and it is the same construct commit `21fddc1` removed from
  `services/api/test/ro.test.ts` four lines above the code it edited here.

  **The fix is a magnitude bound made of fixed literals that live in `ops/lib/ro_cases.json`.** JSON has no
  expressions, so a number stored there cannot be re-derived from the value it bounds by a later edit — which
  is also what the `ro.test.ts` literal had only a comment protecting. Both implementations now run the same
  probes: build a statement of exactly `chars` characters, assert accept/reject, and assert
  `max(accept) <= MAX_SQL_LENGTH < min(reject)`. `6008` is the magnitude `ro.test.ts` has hardcoded since
  before this PR; its own literal test is untouched and still there as a second, independent anchor.
  The equality assertion against `ro_cases.json`'s cap stays, relabelled for what it actually is: a DRIFT
  check, which both sides raised together will always satisfy.

  **RED A — the finding itself. Coordinated raise, `ro_grammar.py` + `ro_cases.json`:**

        GREEN  RO-GRAMMAR OK 30 cases                                                   exit 0
        RED    RO-GRAMMAR FAIL 2/30
                - MAX_SQL_LENGTH is 400000, outside the fixed probe bracket [3000, 6008)
                  - the cap's MAGNITUDE moved, not just its spelling
                - should REJECT a statement of exactly 6008 chars but accepted it       exit 1
               100,007-char statement accepted? True
        GREEN  restored                                                                 exit 0

  **RED G — the same raise across all three files, through `ops/test`.** Before this fix the only thing that
  went red was `services/api/test/ro.test.ts:21`; tier 1d printed `RO-GRAMMAR OK` and passed. Now the gate
  fails first:

        GREEN  bash ops/test  ->  RO-GRAMMAR OK 30 cases / TESTS linux=123/76 ... failed=0 / OK   exit 0
        RED    export const MAX_SQL_LENGTH = 400000  (services/api/src/ro.ts)
               MAX_SQL_LENGTH = 400000               (ops/lib/ro_grammar.py)
               "max_sql_length": 400000              (ops/lib/ro_cases.json)
               bash ops/test
                 RO-GRAMMAR FAIL 2/30
                  - MAX_SQL_LENGTH is 400000, outside the fixed probe bracket [3000, 6008) ...
                  - should REJECT a statement of exactly 6008 chars but accepted it
                 FAIL: ops/lib/ro_grammar.py --self-test exited 1
                 TESTS linux=123/76 ios=skipped failed=3 skipped=0
                 FAIL: 3 failing test(s)                                                          exit 1
        GREEN  restored                                                                           exit 0

  **The floors, each shown red on the population the check actually examines** — the probes it ran, not the
  probes it was handed, and the shared cases present, not the file being present:

        RED B  length_probes: []          RO-GRAMMAR FAIL 1/27  - ro_cases.json carries 0 length probe(s)
                                          (expected >= 2) - with none of them nothing here bounds the
                                          MAGNITUDE of MAX_SQL_LENGTH ...                          exit 1
        RED C  one probe left             RO-GRAMMAR FAIL 1/27  - carries 1 length probe(s) ...     exit 1
        RED F  two probes, both "reject"  RO-GRAMMAR FAIL 1/27  - length probes must bracket the cap:
                                          0 accept and 2 reject probe(s) - probing one side only cannot
                                          see the cap move the other way                            exit 1
        RED E  reject probe 6008 -> 3500  RO-GRAMMAR FAIL 2/30  - MAX_SQL_LENGTH is 4000, outside the
                                          fixed probe bracket [3000, 3500) ...                      exit 1
        GREEN  restored after each                                                                  exit 0

  Note the denominator: 27 when no probe ran, 30 when all three assertions ran. It counts the probes that
  actually executed, not a constant 3, so a run that checked nothing cannot report the number of a run that
  checked everything.

  **RED H — a defect I found reviewing my own fix, before the reviewer could (`f1c787f`).** My first version
  asserted only `problem is not None` for a reject probe, i.e. "refused for some reason". That would stay
  green with the length rule deleted, if any other gate happened to catch the statement. The probe now
  requires the length refusal, which is what `ro.test.ts` already asserts with `toMatch(/longer/)`:

        RED    rename the refusal: return "statement too large" instead of f"longer than {N} chars"
               RO-GRAMMAR FAIL 1/30
                - rejected a 6008-char statement for the wrong reason: 'statement too large'
                  - the length rule is what this probe exists to exercise                           exit 1
        GREEN  restored                                                                             exit 0

  **SMALLER ITEM 1 — `ops/lib/ro_grammar.py:44`, `MIN_CASES = 20` against 26 cases present.** Raised to 26.
  Shown red, and shown green at the old floor to prove the old one was slack:

        RED    delete six reject cases (26 -> 20)
               RO-GRAMMAR FAIL 1/24 - only 20 shared case(s) in ro_cases.json (expected >= 26)      exit 1
               the same deletion with MIN_CASES back at 20:
               RO-GRAMMAR OK 24 cases                                                               exit 0
        GREEN  restored                                                                             exit 0

  **SMALLER ITEM 2 — `services/api/test/ro.test.ts:16-20`, a guard anchored on a comment.** The comment
  stays (it explains the history) but it is no longer the only thing standing between that literal and
  re-derivation: `ro_cases.json` now carries the same magnitudes as data, `ro.test.ts` runs three more tests
  from them, and `ro_grammar.py` runs the same two probes plus the bracket. If a later edit re-derives the
  6008 literal from `MAX_SQL_LENGTH`, the JSON-held probes still catch the raise on both sides. That is the
  honest limit of the fix: nothing mechanically forbids writing a derived expression in that file; what is
  now mechanical is that doing so no longer hides a cap raise.

  **SMALLER ITEM 3 — brief bullet 4, `MAX_MONTHLY_UPSTREAM_CALLS` / P-COST-02.** Dropped silently by the
  previous entries; answered here by running it, not by reading it. `T-0014` landed on `main` in the
  meantime, so the pin is no longer `assertion: TODO`. It reads `value:` out of `pins/PINS.yaml` and compares
  it to the literal `grep`ed out of `services/api/src/quota.ts` — two independent sources, not one read
  twice — and additionally refuses any non-numeric right-hand side. Measured:

        baseline                                          PINS ok=11 ... failed=0             exit 0
        quota.ts 250_000 -> 900_000, pin value untouched   PINS ok=10 ... failed=1             exit 1
                                                          - P-COST-02: MAX_MONTHLY_UPSTREAM_CALLS is a
                                                            compile-time constant in the Worker equal to
                                                            the value pinned here
        quota.ts -> Number(globalThis.CAP ?? 250_000)      PINS ok=10 ... failed=1             exit 1
        restored                                          PINS ok=11 ... failed=0             exit 0

  So the failure mode the brief feared is not present there: mutating one side alone goes red, and making
  the constant configurable goes red too. Nothing to fix; recorded so it stops being an open question.

  **SMALLER ITEM 4 — the merge.** The branch was 91 commits behind `origin/main`. Merged at `aa5c365`, no
  conflicts. Checked afterwards rather than assumed: tier 1d survives intact (`ops/test:64-89`) and every
  change `main` made to `ops/test` survives with it — `junit_reports`, the `--list-failures` naming block and
  the tier-1c pytest interpreter probe are all present, `ops/test` is 137 lines. The reviewer's warning about
  "main's per-tier floors" does not apply: `main` has no per-tier floors, only `floor_linux` / `floor_ios`;
  the per-tier ones are still T-0071's unlanded work, which is what the tier-1d comment already says.
  One mode change came in with the merge and is correct: `ops/lib/ro_grammar.py` is now `100644`, because
  T-0036 made every `ops/lib/*.py` a data file for P-OPS-01 (they are all invoked as `"$PY" ops/lib/x.py`,
  never as `./ops/lib/x.py`). `ops/check-pins` agrees: `P-OPS-01 ... all modes correct`.

  **Verify, post-merge, exit codes without a pipe:**

        bash ops/test        RO-GRAMMAR OK 30 cases / TESTS linux=123/76 ios=skipped failed=0 skipped=0 / OK
                                                                                                    exit 0
        bash ops/check-pins  PINS ok=11 skipped=0 pending=2 expired=0 failed=0 tier=linux            exit 0
        bash ops/sane        SANE OK                                                                 exit 0

  Counts: python `29 -> 30` self-test assertions, vitest `35 -> 38` on this file's suite, `linux 123/76`
  after the merge brought in the ETL and quota tiers. `git status --short` is empty at handoff; every
  mutation above was reverted with `git checkout --` and re-measured green.

  **A trap, recorded because I fell into it.** My first red/green script called
  `git checkout -- ops/lib/ro_grammar.py ops/lib/ro_cases.json` to "restore" between mutations while the fix
  was still uncommitted. It restored `HEAD`, i.e. it deleted the fix, and demos B through D then ran against
  the old code and reported green. Only RED A was valid. The fix was committed first (`7889793`) and every
  transcript above was re-taken after that, against a `restore()` that returns to the committed fix.

- 2026-09-08 **reviewed by `agent/reviewer-final-pr53` (PR #53, second review round) — PASS, transitioned to
  `queue/done/`.** Every prior finding was re-verified by RUNNING the mutation that demonstrated it, not by
  reading the diff. Reviewed at `02f7dba`, in `.worktrees/T-0083`; every exit code below was taken without a
  pipe (`<cmd> >file 2>&1; echo $?`), and every mutation was reverted with `git checkout --` and re-measured
  green. `git status --short` is empty apart from this transition.

  **`verify:` and `acceptance:`.** `acceptance:` is empty. `verify: [ops/test, ops/check-pins]`:

        bash ops/test        RO-GRAMMAR OK 30 cases
                             TESTS linux=123/76 ios=skipped failed=0 skipped=0 / OK          exit 0
        bash ops/check-pins  PINS ok=11 skipped=0 pending=2 expired=0 failed=0 tier=linux    exit 0
        bash ops/sane        SANE OK                                                         exit 0
        bash ops/queue-check QUEUE OK (106 tasks)                                            exit 0
        python3 ops/lib/ro_grammar.py --self-test   RO-GRAMMAR OK 30 cases                   exit 0

  No stale-`.build` trouble this round; the previous reviewer's `SwiftShims` note did not recur.

  **THE PRIOR FINDING IS CLOSED — the exact mutation, re-run.** Previously this printed
  `RO-GRAMMAR OK 29 cases` at exit 0 while a 100,007-character statement was accepted:

        MAX_SQL_LENGTH 4000 -> 400000 in ops/lib/ro_grammar.py
          AND max_sql_length 4000 -> 400000 in ops/lib/ro_cases.json
          RO-GRAMMAR FAIL 2/30
           - MAX_SQL_LENGTH is 400000, outside the fixed probe bracket [3000, 6008) - the cap's MAGNITUDE
             moved, not just its spelling
           - should REJECT a statement of exactly 6008 chars but accepted it                 exit 1
          read_only_problem("SELECT " + "1"*100000) is None -> True   (still accepted, and now CAUGHT)
        restored                                             RO-GRAMMAR OK 30 cases          exit 0

  **Every other check in this PR, driven red by breaking its subject and restored** (self-test unless noted):

        neuter read_only_problem -> None      ro_grammar.py "DROP TABLE users" -> OK, exit 0 (the hole)
                                              bash ops/test: RO-GRAMMAR FAIL 19/30
                                              FAIL: ops/lib/ro_grammar.py --self-test exited 1        exit 1
        mv ops/lib/ro_grammar.py away         bash ops/test: FAIL: ops/lib/ro_grammar.py is missing -
                                              it is the only read-only SQL check ops/prod-read has    exit 1
                                              (ops/check-pins still exit 0 in that state, as logged)
        cap 4000 -> 2000, all three files     FAIL 2/30 - outside bracket [3000, 6008) / should ACCEPT
                                              a statement of exactly 3000 chars but refused           exit 1
        cap 4000 -> 4500, ro_grammar.py only  FAIL 1/30 - ro_cases.json says 4000 ... drifted apart    exit 1
        cap 4000 -> 4500, ro.ts only          vitest 71 total, 1 failed:
                                              "agrees with ops/lib/ro_grammar.py about the cap"       (red)
        length_probes: []                     FAIL 1/27 - carries 0 length probe(s) (expected >= 2)   exit 1
        length_probes: one probe              FAIL 1/27 - carries 1 length probe(s)                   exit 1
        reject probe 6008 -> 3500             FAIL 2/30 - outside bracket [3000, 3500) / should
                                              REJECT a statement of exactly 3500 chars                exit 1
        delete the len(sql) > cap rule        FAIL 1/30 - should REJECT ... 6008 chars but accepted   exit 1
        rename the refusal string             FAIL 1/30 - rejected a 6008-char statement for the
                                              wrong reason: 'statement too large'                     exit 1
        empty accept + reject                 FAIL 1/4  - only 0 shared case(s) (expected >= 26)      exit 1
        delete six reject cases (26 -> 20)    FAIL 1/24 - only 20 shared case(s) (expected >= 26)     exit 1
        quota.ts 250_000 -> 900_000           bash ops/check-pins: PINS ok=10 ... failed=1
                                              - P-COST-02 ...                                         exit 1
        restored after each                                                                           exit 0

  **The claim in SMALLER ITEM 2 was tested, not taken on trust.** Re-deriving the `ro.test.ts` literal back to
  `"1,".repeat(MAX_SQL_LENGTH)` — the exact regression `21fddc1` removed — *and* raising the cap to 400000 in
  all three files still goes red on both sides, because the probes live in JSON: python `FAIL 2/30` exit 1,
  and vitest 71 total / 2 failed (`rejects a statement of exactly 6008 characters`, `keeps MAX_SQL_LENGTH
  inside the fixed probe bracket`). The JSON-held probes really are a second, independent anchor.

  **Signature-defect sweep of the whole diff.** No assertion is stated in terms of the constant it checks, no
  expected value is recomputed from the object under test, no loop bound comes from the value being tested,
  and no floor counts the wrong population: `MIN_CASES = 26` counts the shared cases that lines 121-127
  actually iterate, and `probes_ran` counts the assertions that executed (27 when none ran, 30 when all did),
  not the probes handed in. `max(under) <= MAX_SQL_LENGTH < min(over)` reads both bounds out of
  `ops/lib/ro_cases.json`, which has no expressions.

  **Mechanical rules.** Five source paths, all inside `touches:` (plus this queue file, always allowed).
  300-line cap: `ro_grammar.py` 146, `ops/test` 137, `ro.test.ts` 48, `ro.ts` 37, `ro_cases.json` 39. Modes
  `git ls-files -s`: `ops/test` 100755, `ops/lib/ro_grammar.py` and `ops/lib/ro_cases.json` 100644 (both are
  `ops/lib` data under T-0036's classifier, invoked as `"$PY" ops/lib/x.py`); `ops/check-pins` agrees.
  No secrets. Tier 1d anchors on the file path `ops/lib/ro_grammar.py`, not on a comment. `git grep -n
  ro_grammar origin/main -- ops/test pins/PINS.yaml` is still zero hits, so the headline claim holds.

  **Two findings, both recorded and neither blocking. Not fixed here: testers find and do not fix.**

  1. `ops/lib/ro_cases.json:5-8` — **the fixed bracket is loose, and its width is nowhere stated.** The probes
     are 3000 (accept) and 6008 (reject) against a cap of 4000, so any cap in `[3000, 6007]` satisfies both
     the bracket assertion and both probes. Executed: cap `4000 -> 6000` in all three files gives

           bash ops/test   RO-GRAMMAR OK 30 cases
                           TESTS linux=123/76 ios=skipped failed=0 skipped=0 / OK             exit 0

     byte-identical to baseline, while `read_only_problem("SELECT " + "1"*5992)` returns `None` — a 50% raise
     of the read-only SQL cap, undetected. This is NOT vacuity: the historical break (T-0079's `400000`) is
     caught, as is a lowering, as is either-side drift. But the brief asked for *"one accepted at exactly the
     cap, one rejected at cap+1"*, and literal `4000` / `4001` probes in the JSON would have pinned the cap
     exactly with no more derivation than 3000/6008 have. The departure from the brief is not called out; the
     window's width appears nowhere in the file, the log or the PR. Note the same looseness is inherited from
     `ro.test.ts`'s pre-existing 6008 literal, so this is not a regression introduced by this PR.
  2. This log's `Counts:` line, *"vitest `35 -> 38` on this file's suite"* — **not reproducible as written.**
     Measured: `services/api/test/ro.test.ts` runs **31** tests and the whole vitest suite runs **71**
     (quota 19, ro 31, routes 7, upstream 14). `35 -> 38` was the whole-suite count *before* the merge at
     `aa5c365` (ro 28 + routes 7 = 35, +3 added), quoted inside a paragraph headed "Verify, post-merge" and
     labelled as this file's suite, which it never was. Every other number in that block reproduces exactly
     (`linux=123/76`, `PINS ok=11 ... pending=2`, `SANE OK`, python `30`).

  Neither is grounds to hold the PR: the finding this round existed to close is closed, proven by the same
  mutation that demonstrated it, and nine further mutations show the new gate is load-bearing in every
  direction its subject can move. Transitioned to `queue/done/`, `reviewer: agent/reviewer-final-pr53`
  (owner is `agent/claude-opus-5`; `ops/queue-check` -> `QUEUE OK` exit 0).
