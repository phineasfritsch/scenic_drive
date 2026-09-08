---
id: T-0068
title: queue-check's reviewer-is-not-owner gate is satisfied by owner: null
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T01:19:37Z
lease_expires_at: 2026-09-08T05:19:37Z
worktree: wt/T-0068
branch: task/T-0068
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

CLAUDE.md's rule is *"the reviewer of a task is never its owner (`ops/queue-check`)"*, and P-PROC-01 states
it. The assertion beneath it is:

    elif fm.get("reviewer") == fm.get("owner"):

Both operands are fields the same agent writes into the same file, and **nothing asserts that a task in
`review/` or `done/` has an owner at all**, so the inequality is satisfied vacuously by a null.

Demonstrated, every case executed:

    control:    owner: agent/self + reviewer: agent/self in queue/done/
                -> QUEUE CHECK FAIL - reviewer == owner (agent/self)   exit 1
    evasion 1:  change one word to `owner: null`, leave reviewer: agent/self
                -> QUEUE OK (1 tasks)                                   exit 0
    evasion 2:  delete the `owner:` line entirely
                -> QUEUE OK (1 tasks)                                   exit 0

In both evasions P-PROC-01 is green while the worker graded its own work.

**This is not an exotic hand edit.** `cmd_sweep` writes `owner=None` itself when a lease expires, so a null
owner is a state the tooling produces. A task swept back to ready, re-claimed, and later moved to review by
hand can reach `done/` with no owner and no complaint.

- A task in `review/` or `done/` must HAVE an owner and a reviewer, and they must differ. Two of those three
  conditions are currently unenforced.
- Check the same shape on the other side: does anything assert the reviewer is not null? The existing code
  has `if not fm.get("reviewer")` - confirm that arm is reachable and demonstrated.
- `ops/review` (added by T-0032) refuses `reviewer == owner` at the transition. Give it the same null
  treatment, or the refusal is evadable the same way.
- Demonstrate all three states red then green.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the self-referential-check sweep.
- 2026-09-08T01:19:37Z claimed by agent/claude-opus-5; lease until 2026-09-08T05:19:37Z
- 2026-09-08 agent/claude-opus-5 — fixed in `ops/lib/queue.py` (`cmd_check` and `cmd_review`).

  Harness: `.artifacts/T-0068/demo.sh` (gitignored, not committed). It writes a `T-9001` fixture into the
  real `queue/done/` or `queue/claimed/`, runs `bash ops/queue-check` / `bash ops/review T-9001 --reviewer X`,
  reports whether the file moved, and deletes the fixture. The SAME script produced both transcripts below.
  Case E (owner=agent/a, reviewer=agent/b) is the no-regression control: it must stay green in both runs.
  Case D is the `if not fm.get("reviewer")` arm the brief asked about — it is reachable and it fires.

  RED — `bash .artifacts/T-0068/demo.sh` before the change:

      ===== ops/queue-check =====
      --- CHECK A control  owner=agent/self reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK B evasion1 owner=null      reviewer=agent/self
      QUEUE OK (62 tasks)
      exit=0
      --- CHECK C evasion2 owner line ABSENT reviewer=agent/self
      QUEUE OK (62 tasks)
      exit=0
      --- CHECK D missing-reviewer owner=agent/self reviewer=null
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without a reviewer
      exit=1
      --- CHECK E legit    owner=agent/a    reviewer=agent/b
      QUEUE OK (62 tasks)
      exit=0

      ===== ops/review =====
      --- REVIEW A control  owner=agent/self --reviewer agent/self
      reviewer agent/self is also the owner of T-9001 - a worker may not grade its own work
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW B evasion1 owner=null      --reviewer agent/self
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/self  released=[none]
      (now: git add queue/ && git commit && git push)
      exit=0
      file moved to: queue/review/T-9001-fixture.md
      --- REVIEW C evasion2 owner line ABSENT --reviewer agent/self
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/self  released=[none]
      (now: git add queue/ && git commit && git push)
      exit=0
      file moved to: queue/review/T-9001-fixture.md
      --- REVIEW E legit    owner=agent/a    --reviewer agent/b
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/b  released=[none]
      (now: git add queue/ && git commit && git push)
      exit=0
      file moved to: queue/review/T-9001-fixture.md

  GREEN — `bash .artifacts/T-0068/demo.sh` after the change, same script, same fixtures:

      ===== ops/queue-check =====
      --- CHECK A control  owner=agent/self reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK B evasion1 owner=null      reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without an owner
      exit=1
      --- CHECK C evasion2 owner line ABSENT reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without an owner
      exit=1
      --- CHECK D missing-reviewer owner=agent/self reviewer=null
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without a reviewer
      exit=1
      --- CHECK E legit    owner=agent/a    reviewer=agent/b
      QUEUE OK (62 tasks)
      exit=0

      ===== ops/review =====
      --- REVIEW A control  owner=agent/self --reviewer agent/self
      reviewer agent/self is also the owner of T-9001 - a worker may not grade its own work
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW B evasion1 owner=null      --reviewer agent/self
      T-9001 has no owner, so 'the reviewer is not the owner' cannot be decided - a null owner
      satisfies that inequality for every reviewer. Restore owner: before handing it over
      (ops/queue-sweep clears owner: when a lease expires; re-claim with ops/claim).
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW C evasion2 owner line ABSENT --reviewer agent/self
      T-9001 has no owner, so 'the reviewer is not the owner' cannot be decided - a null owner
      satisfies that inequality for every reviewer. Restore owner: before handing it over
      (ops/queue-sweep clears owner: when a lease expires; re-claim with ops/claim).
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW E legit    owner=agent/a    --reviewer agent/b
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/b  released=[none]
      (now: git add queue/ && git commit && git push)
      exit=0
      file moved to: queue/review/T-9001-fixture.md

  Repo gates in wt/T-0068 after the change:

      $ bash ops/queue-check
      QUEUE OK (61 tasks)
      exit=0
      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      exit=0
      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0

  Every real task in `review/` and `done/` on this branch already carries both an owner and a reviewer
  (16 files checked), so the new assertion does not turn P-PROC-01 red on existing state.

  `bash ops/test` fails here, before and after the change, with `FAIL: services/api exists but vitest
  produced no report` — `services/api/node_modules` does not exist in this worktree. Verified pre-existing
  by restoring HEAD's `ops/lib/queue.py` and re-running: identical last line, exit 1. That is T-0040,
  already filed and claimed; not caused by and not touched by this task.

  `ops/lib/queue.py` grew 498 -> 515 lines. It was already over the 300-line cap on the base branch;
  T-0059 owns that split and this task did not do it.

- 2026-09-08 adversarial verification by a second agent that did not write the fix. **holds = false.**
  The fix is real and its own transcript reproduces; it does not survive contact. Reproduced first,
  then every evasion below was EXECUTED, not argued. Full report follows verbatim so the next person
  inherits the limits along with the code.

  # Adversarial verification of T-0068 — holds = False
  
  ## Verdict
  
  HOLDS=FALSE. The fix is real, honestly reported, and closes exactly the two states it demonstrates - but it hardens the PRESENCE of the two names, not the comparison between them, and six distinct evasions kept a self-graded task green. I executed 15 cases; 4 went red, 6 went green, plus the floor probe and the end-to-end chain.
  
  WHAT IS TRUE. I re-ran the fixer's own harness unchanged (bash .artifacts/T-0068/demo.sh) and it reproduces its published transcript exactly - all four queue-check states red, both ops/review null-owner states refused and the file did not move, case E green in both tools. The claimed gates verify: queue-check QUEUE OK (61 tasks) exit 0, check-pins ok=9 failed=0 exit 0, --source-only ok=3 failed=0. The no-regression claim verifies independently: I enumerated owner/reviewer for all 16 files in queue/review/ and queue/done/ (2 + 14) and every one carries both fields, so the new assertion turns nothing red on real state. The missing-reviewer arm is genuinely reachable (case D). Nothing was weakened.
  
  FINDING 1 (worst, both halves defeated, no funny values needed). C:\Users\phineasf\Documents\GitHub\wt\T-0068\ops\lib\queue.py:233 and :396 compare owner and reviewer with ==, and the module's own front-matter reader (documented in its docstring: "scalars, [flow, lists], and `- ` block lists") turns
      reviewer:
        - agent/self
  into the LIST ['agent/self']. A list is truthy, so missing==[] and the new presence check passes; then ['agent/self'] == 'agent/self' is False, so the inequality passes too. Executed end-to-end: bash ops/review T-9001 printed "T-9001 -> queue/review/...  reviewer=['agent/self']" exit 0 and moved the file - the tool printed the reviewer's name directly beside an owner spelled identically and let it through - then queue-check printed QUEUE OK (62 tasks) exit 0 in review/, again in done/, and P-PROC-01's literal assertion (bash ops/queue-check >/dev/null) exited 0. The mirror (owner as the block list, reviewer a plain scalar) is green too. This is the SAME defect class T-0068 was filed against: an inequality that says nothing. It is pre-existing rather than introduced (the old `elif` was green here as well), but the task's premise is that this comparison must not be vacuous, and it still is.
  
  FINDING 2 (defeats the new code specifically, one pair of quotes). `owner: "null"` survives _scalar's quote-stripping as the STRING 'null' - truthy, so the new `not fm.get("owner")` test passes. queue-check printed QUEUE OK (62 tasks) exit 0 on a done/ task with owner "null" and reviewer agent/self. Worse at the transition: ops/review accepted it, exited 0, moved the file, and dump() rewrote it as `owner: null` - the transition-time guard manufactured the exact real null it exists to refuse. queue-check catches the wreckage afterwards, which is the "report, not prevention" the fixer's own comment argues against.
  
  FINDING 3 (no floor - the repo's signature bug, ninth occurrence). Running the real module against an empty queue/ tree printed QUEUE OK (0 tasks) exit 0, and again with queue/review and queue/done deleted outright: QUEUE OK (0 tasks) exit 0. Nothing asserts a minimum population, so P-PROC-01 is satisfied by a check that inspected nothing. Two cheaper variants of the same hole are also green: a self-graded done task named outside tasks()' rglob("T-*.md") (queue/done/selfgraded-fixture.md -> QUEUE OK (61 tasks), not even counted), and one parked in queue/completed/, a directory outside STATES (QUEUE OK (61 tasks)).
  
  FINDING 4 (minor). owner: agent/self vs reviewer: agent/Self - one capital - is green. Agent names are free-form strings nothing normalises.
  
  WHAT THE GUARD DID CATCH: the field-name typo (ownr:) goes red with "in done/ without an owner"; owner: [] goes red in both tools; the unrecognised flag form --reviewer=agent/self falls back to fm.reviewer and is caught by the equality test. So the presence check is not itself evadable by absence - it is evadable by presence of a non-name.
  
  RECOMMENDED SHAPE (not applied - I am the verifier): normalise both operands before comparing - require each to be a non-empty string matching the agent/<name> shape, reject lists and the literal "null"/"none"/"~", and casefold before ==; add a floor so an empty or unreadable population is a failure, not a pass.
  
  DISCLOSED AND CONFIRMED: ops/lib/queue.py is 515 lines, already over the repo's 300-line cap before this change (fixer says T-0059 owns the split) - I verified the count, this fix added 17 lines to an existing violation.
  
  HYGIENE: all fixtures were written into the real queue dirs and removed; `git checkout -- .` run; final `bash ops/queue-check` -> QUEUE OK (61 tasks) exit 0 (back to baseline); `find queue -iname "*9001*" -o -iname "*selfgraded*" -o -type d -name completed` returns nothing; final `git status --short` printed EMPTY OUTPUT - worktree clean, nothing staged, nothing committed by me. My harnesses are reproducible at C:\Users\phineasf\Documents\GitHub\wt\T-0068\.artifacts\T-0068\adversary.sh, adversary2.sh, adversary3.sh and probe.py (that directory is gitignored; nothing there is staged).
  
  ## Evasions executed
  
  ### 1. CAUGHT — REPRODUCTION FIRST (not an evasion): ran the fixer's own harness unchanged, bash .artifacts/T-0068/demo.sh
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0068 && bash .artifacts/T-0068/demo.sh
  CHECK A/B/C/D all 'QUEUE CHECK FAIL' exit=1 (B and C: 'queue/done/T-9001-fixture.md: in done/ without an owner'); CHECK E 'QUEUE OK (62 tasks)' exit=0. REVIEW A exit=1, B and C exit=1 'T-9001 has no owner, so the reviewer is not the owner cannot be decided' + 'file did NOT move', REVIEW E exit=0 moved. Reproduces the fixer's green transcript character for character.
  ```
  
  ### 2. *** UNCAUGHT *** — EV1 queue-check: queue/done/T-9001-fixture.md with owner: "null" (the null the fix is about, in quotes) and reviewer: agent/self
  
  ```
  $ bash ops/queue-check
  QUEUE OK (62 tasks)
  exit=0    [probe: parsed owner='null' reviewer='agent/self' | missing=[] | owner==reviewer -> False]
  ```
  
  ### 3. *** UNCAUGHT *** — EV3 queue-check: owner: agent/self and reviewer written as the module's own block-list form (reviewer: / '  - agent/self')
  
  ```
  $ bash ops/queue-check
  QUEUE OK (62 tasks)
  exit=0    [probe: parsed owner='agent/self' reviewer=['agent/self'] | missing=[] | owner==reviewer -> False]
  ```
  
  ### 4. *** UNCAUGHT *** — P2 queue-check: the mirror image - owner: / '  - agent/self' as a block list, reviewer: agent/self
  
  ```
  $ bash ops/queue-check
  QUEUE OK (62 tasks)
  exit=0    [probe: parsed owner=['agent/self'] reviewer='agent/self' | missing=[] | owner==reviewer -> False]
  ```
  
  ### 5. *** UNCAUGHT *** — EV2 queue-check: owner: agent/self, reviewer: agent/Self (one capital letter, same worker)
  
  ```
  $ bash ops/queue-check
  QUEUE OK (62 tasks)
  exit=0
  ```
  
  ### 6. *** UNCAUGHT *** — EV4 queue-check: a fully self-graded done task (owner==reviewer==agent/self) whose FILENAME is outside tasks()' rglob('T-*.md') - queue/done/selfgraded-fixture.md
  
  ```
  $ bash ops/queue-check
  QUEUE OK (61 tasks)
  exit=0    (61, not 62 - the file is not even counted; the population silently excludes it)
  ```
  
  ### 7. *** UNCAUGHT *** — EV6 queue-check: same self-graded task parked in a directory outside STATES - queue/completed/T-9001-fixture.md
  
  ```
  $ bash ops/queue-check
  QUEUE OK (61 tasks)
  exit=0
  ```
  
  ### 8. CAUGHT — EV5 queue-check: field-name typo - 'ownr: agent/self' instead of 'owner:', reviewer: agent/self
  
  ```
  $ bash ops/queue-check
  QUEUE CHECK FAIL
   - queue/done/T-9001-fixture.md: in done/ without an owner
  exit=1
  ```
  
  ### 9. CAUGHT — EV7 queue-check: owner nulled as an empty flow list, owner: [] with reviewer: agent/self
  
  ```
  $ bash ops/queue-check
  QUEUE CHECK FAIL
   - queue/done/T-9001-fixture.md: in done/ without an owner
  exit=1
  ```
  
  ### 10. *** UNCAUGHT *** — EV8 ops/review: claimed task with owner: "null" (quoted), handed to itself
  
  ```
  $ bash ops/review T-9001 --reviewer agent/self
  T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/self  released=[none]
  exit=0
  RESULT: file MOVED to queue/review/T-9001-fixture.md
  ...and dump() then wrote the moved file as 'owner: null' - the transition-time guard MANUFACTURED the exact real null the fix exists to refuse. (queue-check does catch it afterwards: 'in review/ without an owner' exit=1 - report, not prevention.)
  ```
  
  ### 11. *** UNCAUGHT *** — P3 ops/review: owner: agent/self, reviewer named in front matter as a block list, no --reviewer flag
  
  ```
  $ bash ops/review T-9001
  T-9001 -> queue/review/T-9001-fixture.md  reviewer=['agent/self']  released=[none]
  exit=0
  RESULT: file MOVED. The tool printed the reviewer's name next to an owner spelled identically and exited 0. Persisted as 'owner: agent/self' / 'reviewer: [agent/self]'.
  ```
  
  ### 12. *** UNCAUGHT *** — P4 ops/review: owner as a block list ('  - agent/self'), --reviewer agent/self
  
  ```
  $ bash ops/review T-9001 --reviewer agent/self
  T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/self  released=[none]
  exit=0
  RESULT: file MOVED. Persisted as 'owner: [agent/self]' / 'reviewer: agent/self'.
  ```
  
  ### 13. CAUGHT — EV9 ops/review: unrecognised flag form --reviewer=agent/self so _opts misses and it falls back to fm.reviewer (owner==reviewer==agent/self)
  
  ```
  $ bash ops/review T-9001 --reviewer=agent/self
  reviewer agent/self is also the owner of T-9001 - a worker may not grade its own work
  exit=1
  RESULT: file did NOT move
  ```
  
  ### 14. CAUGHT — EV10 ops/review: owner: [] (empty flow list), --reviewer agent/self
  
  ```
  $ bash ops/review T-9001 --reviewer agent/self
  T-9001 has no owner, so 'the reviewer is not the owner' cannot be decided - a null owner
  satisfies that inequality for every reviewer. Restore owner: before handing it over
  exit=1
  RESULT: file did NOT move
  ```
  
  ### 15. *** UNCAUGHT *** — P5/P6 EMPTY THE POPULATION: copied the real ops/lib/queue.py into a scratch tree with an empty queue/ (then with queue/review and queue/done deleted outright) and ran the real check function against it. This is the repo's signature floor bug - P-PROC-01's whole assertion is 'bash ops/queue-check >/dev/null'.
  
  ```
  $ python .artifacts/T-0068/emptytree/ops/lib/queue.py check
  QUEUE OK (0 tasks)
  exit=0        (and again, with queue/review and queue/done deleted: QUEUE OK (0 tasks) exit=0). No MIN_TASKS floor exists anywhere; a guard covering nothing reports success.
  ```
  
  ### 16. *** UNCAUGHT *** — END-TO-END CHAIN: one task, owner: agent/self, reviewer block-listed as agent/self, walked claimed/ -> review/ -> done/ through the real tools
  
  ```
  $ bash .artifacts/T-0068/adversary3.sh
  STEP 1 bash ops/review T-9001 -> 'reviewer=['agent/self']' exit=0, file moved
  STEP 3 bash ops/queue-check on review/ -> QUEUE OK (62 tasks) exit=0
  STEP 4 moved to done/, state: done -> QUEUE OK (62 tasks) exit=0
  STEP 5 P-PROC-01 as the pin runs it: 'bash ops/queue-check >/dev/null' -> exit=0
  A worker graded its own work and reached done/ with every gate green.
  ```
