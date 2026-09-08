---
id: T-0073
title: queue-check hardened the presence of owner and reviewer, not the comparison between them
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:03:32Z
lease_expires_at: 2026-09-08T06:03:32Z
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

Follow-up to [[T-0068]], which made `queue-check` and `ops/review` require an owner AND a reviewer before
comparing them. A second agent executed sixteen evasions against that fix. **Five went red. Eleven did not.**
Full report in T-0068's `## Log`. The fix hardened the **presence** of the two names; it did not harden the
**comparison**, and that is where every surviving route goes.

**1. A YAML block list defeats the equality, with no funny values.** The module's own front-matter reader
handles "scalars, [flow, lists], and `- ` block lists" — so

        reviewer:
          - agent/self

parses to `['agent/self']`. A list is truthy, so the new presence check passes. Then
`['agent/self'] == 'agent/self'` is **False**, so the inequality passes too. Executed end to end:
`ops/review T-9001` printed `reviewer=['agent/self']` beside an owner spelled identically, exited 0, and moved
the file; `queue-check` then printed `QUEUE OK` in `review/` and again in `done/`, and P-PROC-01's literal
assertion exited 0. The mirror image — owner as the block list, reviewer a plain scalar — is green too.

**2. `owner: "null"` — one pair of quotes.** `_scalar` strips the quotes and yields the *string* `'null'`,
which is truthy, so the presence check passes. Worse at the transition: `ops/review` accepted it, exited 0,
moved the file, and `dump()` rewrote it as `owner: null` — **the transition-time guard manufactured the exact
real null it exists to refuse.** `queue-check` catches the wreckage afterwards, which is the "report, not
prevention" T-0068's own comment argues against.

**3. `agent/self` vs `agent/Self`.** One capital letter, same worker, green. Nothing normalises agent names.

**4. No population floor — the ninth occurrence of this repo's signature bug.** The real module against an
empty `queue/` prints `QUEUE OK (0 tasks)` exit 0; with `queue/review` and `queue/done` deleted outright,
same. Two cheaper variants are also green: a fully self-graded `done/` task named outside `tasks()`'
`rglob("T-*.md")` (`queue/done/selfgraded-fixture.md` — not even counted), and one parked in
`queue/completed/`, a directory outside `STATES`. Already filed as part of [[T-0070]]; repeated here because
the fix for this task must not land without it.

**What the guard did catch**, and should keep catching: a field-name typo (`ownr:`), `owner: []`, and the
`--reviewer=agent/self` flag form. The presence check is not evadable by *absence*; it is evadable by the
*presence of a non-name*.

- Normalise both operands before comparing: require each to be a non-empty string of the `agent/<name>` shape,
  reject lists, reject the literals `null` / `none` / `~`, and casefold before `==`.
- Anything that is not a valid agent name is a failure, not a value to compare. That single rule closes 1, 2
  and 3 together, which is why it is worth doing once rather than three times.
- `tasks()` must not silently ignore files it cannot see: either widen the glob and fail on a task file whose
  name does not match, or assert that every `.md` under a state directory is a task.
- Add the population floor from [[T-0070]] in the same pass; without it the rest is decoration.
- `ops/lib/queue.py` is 515 lines, already over the 300-line cap before this change. [[T-0059]] owns the
  split. Do not split it here, but do not grow it much either.
- Demonstrate each route red then green, and re-run the end-to-end chain the verifier used: one task walked
  `claimed/ -> review/ -> done/` through the real tools with owner and reviewer naming the same worker.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the adversarial verification of T-0068. Every case above was
  executed by an agent that did not write the fix, against the real tools, and the fixtures were removed
  afterwards (`git status --short` empty).
- 2026-09-08T02:03:32Z claimed by agent/claude-opus-5; lease until 2026-09-08T06:03:32Z
- 2026-09-08 agent/claude-opus-5 — fixed in `ops/lib/queue.py`. Round two: the four routes the adversary
  left open are closed, and the neighbours of each are closed with them.

  ONE RULE does routes 1, 2 and 3: `agent(v)` normalises an operand to a comparable name or returns None.
  Not a `str` -> None (kills every list, block and flow). Stripped, casefolded, rejected against
  `NOT_A_NAME` and required to match `^agent/[a-z0-9][a-z0-9._+-]*$`. `cmd_check` and `cmd_review` both
  run BOTH operands through it, and a value that is not a name is a FAILURE in its own right, never
  something to compare. Route 4 is a separate structural rule: `tasks()` now globs `*` instead of
  `T-*.md`, and `cmd_check` asserts the six state directories exist, refuses a directory under `queue/`
  outside `STATES`, refuses a task-named file anywhere outside a state directory, refuses a file in a
  state directory whose name is not `T-NNNN-slug.md`, and enforces `MIN_TASKS = 40`.

  Harness: `.artifacts/T-0073/routes.sh` (gitignored, not committed). It writes fixtures into the REAL
  `queue/` dirs, runs the real `bash ops/queue-check` / `bash ops/review`, reports whether the file moved
  and what was persisted, then deletes them. The SAME script produced both transcripts below; the diff
  between them is the whole result. `.artifacts/T-0073/smoke.sh` exercises the other subcommands and
  `roundtrip.py` the dump() change.

  RED — `bash .artifacts/T-0073/routes.sh` before the change:

      ===== ROUTE 1  block list defeats the equality =====
      --- CHECK R1a reviewer as block list   owner=agent/self reviewer=[agent/self]
      QUEUE OK (70 tasks)
      exit=0
      --- CHECK R1b MIRROR owner block list  owner=[agent/self] reviewer=agent/self
      QUEUE OK (70 tasks)
      exit=0
      --- CHECK R1e ADJACENT flow list       owner=[agent/self] (flow) reviewer=agent/self
      QUEUE OK (70 tasks)
      exit=0
      --- REVIEW R1c ops/review reviewer block list in fm, NO --reviewer flag
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=['agent/self']  released=[none]
      exit=0
      file MOVED to: queue/review/T-9001-fixture.md
      persisted owner/reviewer:
          owner: agent/self
          reviewer: [agent/self]
      --- REVIEW R1d ops/review owner block list, --reviewer agent/self
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/self  released=[none]
      exit=0
      file MOVED to: queue/review/T-9001-fixture.md
      persisted owner/reviewer:
          owner: [agent/self]
          reviewer: agent/self

      ===== ROUTE 2  quoted null, and every neighbour of it =====
      --- CHECK R2a owner: "null" (quoted) reviewer=agent/self
      QUEUE OK (70 tasks)
      exit=0
      --- CHECK R2c ADJACENT mirror  owner=agent/self reviewer: "null"
      QUEUE OK (70 tasks)
      exit=0
      --- CHECK R2d ADJACENT owner: "~" (quoted tilde) reviewer=agent/self
      QUEUE OK (70 tasks)
      exit=0
      --- CHECK R2g ADJACENT owner: none reviewer=agent/self
      QUEUE OK (70 tasks)
      exit=0
      --- REVIEW R2b ops/review owner: "null" --reviewer agent/self
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/self  released=[none]
      exit=0
      file MOVED to: queue/review/T-9001-fixture.md
      persisted owner/reviewer:
          owner: null                      <-- dump() MANUFACTURED the real null
          reviewer: agent/self
      --- REVIEW R2e ADJACENT ops/review owner=agent/self --reviewer null (writes a null reviewer)
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=null  released=[none]
      exit=0
      file MOVED to: queue/review/T-9001-fixture.md
      persisted owner/reviewer:
          owner: agent/self
          reviewer: null                   <-- a review with no reviewer, made by ops/review
      --- REVIEW R2f ADJACENT ops/review owner=agent/self --reviewer with NO value (_opts yields 'true')
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=true  released=[none]
      exit=0
      file MOVED to: queue/review/T-9001-fixture.md
      persisted owner/reviewer:
          owner: agent/self
          reviewer: true

      ===== ROUTE 3  case =====
      --- CHECK R3a owner=agent/self reviewer=agent/Self
      QUEUE OK (70 tasks)
      exit=0
      --- CHECK R3b owner=Agent/Self reviewer=agent/self
      QUEUE OK (70 tasks)
      exit=0
      --- REVIEW R3c ADJACENT ops/review owner=agent/self --reviewer AGENT/SELF
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=AGENT/SELF  released=[none]
      exit=0
      file MOVED to: queue/review/T-9001-fixture.md

      ===== ROUTE 4  population floor / invisible files =====
      --- CHECK R4c self-graded file named OUTSIDE rglob(T-*.md)
      QUEUE OK (69 tasks)
      exit=0
      --- CHECK R4d self-graded file in queue/completed/ (dir outside STATES)
      QUEUE OK (69 tasks)
      exit=0
      --- CHECK R4f ADJACENT self-graded file with a non-.md extension
      QUEUE OK (69 tasks)
      exit=0
      --- CHECK R4g ADJACENT self-graded file nested in queue/done/archive/
      QUEUE CHECK FAIL
       - queue/done/archive/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK R4a empty queue tree, real module
      QUEUE OK (0 tasks)
      exit=0
      --- CHECK R4b same tree with queue/review and queue/done DELETED outright
      QUEUE OK (0 tasks)
      exit=0
      --- CHECK R4e REAL populated tree with queue/done moved aside (14 real tasks hidden)
      QUEUE CHECK FAIL
        (first 2 other problems, to show WHY it is red:)
       - queue/backlog/T-0008-...: depends_on T-0002 which does not exist
       - queue/backlog/T-0009-...: depends_on T-0007 which does not exist
      exit=1

      ===== REGRESSIONS that round one caught - must stay red =====
      --- CHECK G1 field-name typo ownr: agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without an owner
      exit=1
      --- CHECK G2 owner: [] empty flow list
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without an owner
      exit=1
      --- CHECK G3 owner: null (real null)
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without an owner
      exit=1
      --- CHECK G4 owner line ABSENT
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without an owner
      exit=1
      --- CHECK G5 reviewer: null owner=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without a reviewer
      exit=1
      --- CHECK G6 control owner=agent/self reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- REVIEW G7 ops/review --reviewer=agent/self (unrecognised flag form)
      reviewer agent/self is also the owner of T-9001 - a worker may not grade its own work
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW G8 ops/review owner: [] --reviewer agent/self
      T-9001 has no owner, so 'the reviewer is not the owner' cannot be decided - a null owner
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW G9 ops/review owner: null --reviewer agent/self
      T-9001 has no owner, so 'the reviewer is not the owner' cannot be decided - a null owner
      exit=1
      file did NOT move (still claimed/)

      ===== NO-REGRESSION CONTROLS - must stay green =====
      --- CHECK OK1 owner=agent/a reviewer=agent/b
      QUEUE OK (70 tasks)
      exit=0
      --- REVIEW OK2 ops/review owner=agent/a --reviewer agent/b
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/b  released=[none]
      exit=0
      file MOVED to: queue/review/T-9001-fixture.md

      ===== END-TO-END CHAIN  claimed -> review -> done, owner and reviewer the same worker =====
      STEP 1  bash ops/review T-9001
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=['agent/self']  released=[none]
      exit=0
      STEP 2  file moved to review/; queue-check on review/
      QUEUE OK (70 tasks)
      exit=0
      STEP 3  hand-move to done/, state: done
      QUEUE OK (70 tasks)
      exit=0
      STEP 4  P-PROC-01 exactly as the pin runs it: bash ops/queue-check >/dev/null
      exit=0

      ===== BASELINE  clean tree =====
      QUEUE OK (69 tasks)
      exit=0
      git status --short:            (empty)

  GREEN — `bash .artifacts/T-0073/routes.sh` after the change, same script, same fixtures:

      ===== ROUTE 1  block list defeats the equality =====
      --- CHECK R1a reviewer as block list   owner=agent/self reviewer=[agent/self]
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ with reviewer: ['agent/self'], which is not an agent/<name> - a non-name cannot be compared, so reviewer-is-not-owner is undecidable
      exit=1
      --- CHECK R1b MIRROR owner block list  owner=[agent/self] reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ with owner: ['agent/self'], which is not an agent/<name> - a non-name cannot be compared, so reviewer-is-not-owner is undecidable
      exit=1
      --- CHECK R1e ADJACENT flow list       owner=[agent/self] (flow) reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ with owner: ['agent/self'], which is not an agent/<name> - a non-name cannot be compared, so reviewer-is-not-owner is undecidable
      exit=1
      --- REVIEW R1c ops/review reviewer block list in fm, NO --reviewer flag
      T-9001: reviewer is ['agent/self'], which is not an agent/<name>. A non-name cannot be
      compared, so 'the reviewer is not the owner' cannot be decided - a list, a quoted
      "null" and a bare flag all read as present while meaning nothing.
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW R1d ops/review owner block list, --reviewer agent/self
      T-9001: owner is ['agent/self'], which is not an agent/<name>. A non-name cannot be
      compared, so 'the reviewer is not the owner' cannot be decided - a list, a quoted
      "null" and a bare flag all read as present while meaning nothing.
      exit=1
      file did NOT move (still claimed/)

      ===== ROUTE 2  quoted null, and every neighbour of it =====
      --- CHECK R2a owner: "null" (quoted) reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ with owner: 'null', which is not an agent/<name> - a non-name cannot be compared, so reviewer-is-not-owner is undecidable
      exit=1
      --- CHECK R2c ADJACENT mirror  owner=agent/self reviewer: "null"
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ with reviewer: 'null', which is not an agent/<name> - a non-name cannot be compared, so reviewer-is-not-owner is undecidable
      exit=1
      --- CHECK R2d ADJACENT owner: "~" (quoted tilde) reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ with owner: '~', which is not an agent/<name> - a non-name cannot be compared, so reviewer-is-not-owner is undecidable
      exit=1
      --- CHECK R2g ADJACENT owner: none reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ with owner: 'none', which is not an agent/<name> - a non-name cannot be compared, so reviewer-is-not-owner is undecidable
      exit=1
      --- REVIEW R2b ops/review owner: "null" --reviewer agent/self
      T-9001: owner is 'null', which is not an agent/<name>. A non-name cannot be
      compared, so 'the reviewer is not the owner' cannot be decided - a list, a quoted
      "null" and a bare flag all read as present while meaning nothing.
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW R2e ADJACENT ops/review owner=agent/self --reviewer null (writes a null reviewer)
      T-9001: reviewer is 'null', which is not an agent/<name>. A non-name cannot be
      compared, so 'the reviewer is not the owner' cannot be decided - a list, a quoted
      "null" and a bare flag all read as present while meaning nothing.
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW R2f ADJACENT ops/review owner=agent/self --reviewer with NO value (_opts yields 'true')
      T-9001: reviewer is 'true', which is not an agent/<name>. A non-name cannot be
      compared, so 'the reviewer is not the owner' cannot be decided - a list, a quoted
      "null" and a bare flag all read as present while meaning nothing.
      exit=1
      file did NOT move (still claimed/)

      ===== ROUTE 3  case =====
      --- CHECK R3a owner=agent/self reviewer=agent/Self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK R3b owner=Agent/Self reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- REVIEW R3c ADJACENT ops/review owner=agent/self --reviewer AGENT/SELF
      reviewer AGENT/SELF is also the owner of T-9001 - a worker may not grade its own work
      exit=1
      file did NOT move (still claimed/)

      ===== ROUTE 4  population floor / invisible files =====
      --- CHECK R4c self-graded file named OUTSIDE rglob(T-*.md)
      QUEUE CHECK FAIL
       - queue/done/selfgraded-fixture.md: not a task file (expected T-NNNN-slug.md) - an unnameable file is uncheckable
       - queue/done/selfgraded-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK R4d self-graded file in queue/completed/ (dir outside STATES)
      QUEUE CHECK FAIL
       - queue/completed/ is not a queue state - a task parked there is invisible
      exit=1
      --- CHECK R4f ADJACENT self-graded file with a non-.md extension
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.markdown: not a task file (expected T-NNNN-slug.md) - an unnameable file is uncheckable
       - queue/done/T-9001-fixture.markdown: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK R4g ADJACENT self-graded file nested in queue/done/archive/
      QUEUE CHECK FAIL
       - queue/done/archive/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK R4a empty queue tree, real module
      QUEUE CHECK FAIL
       - only 0 task(s) visible, floor is 40 - a queue-check that inspected nothing still reports success, and that IS P-PROC-01 passing
      exit=1
      --- CHECK R4b same tree with queue/review and queue/done DELETED outright
      QUEUE CHECK FAIL
       - queue/review/ is missing - a deleted state directory silently hides every task in it
       - queue/done/ is missing - a deleted state directory silently hides every task in it
       - only 0 task(s) visible, floor is 40 - a queue-check that inspected nothing still reports success, and that IS P-PROC-01 passing
      exit=1
      --- CHECK R4e REAL populated tree with queue/done moved aside (14 real tasks hidden)
      QUEUE CHECK FAIL
       - queue/done/ is missing - a deleted state directory silently hides every task in it
        (first 2 other problems, to show WHY it is red:)
       - queue/backlog/T-0008-...: depends_on T-0002 which does not exist
       - queue/backlog/T-0009-...: depends_on T-0007 which does not exist
      exit=1

      ===== REGRESSIONS that round one caught - must stay red =====
      (G1..G9 byte-identical to the RED run above: same messages, same exit=1, files did NOT move.)

      ===== NO-REGRESSION CONTROLS - must stay green =====
      --- CHECK OK1 owner=agent/a reviewer=agent/b
      QUEUE OK (70 tasks)
      exit=0
      --- REVIEW OK2 ops/review owner=agent/a --reviewer agent/b
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/b  released=[none]
      exit=0
      file MOVED to: queue/review/T-9001-fixture.md
      persisted owner/reviewer:
          owner: agent/a
          reviewer: agent/b

      ===== END-TO-END CHAIN  claimed -> review -> done, owner and reviewer the same worker =====
      STEP 1  bash ops/review T-9001
      T-9001: reviewer is ['agent/self'], which is not an agent/<name>. A non-name cannot be
      compared, so 'the reviewer is not the owner' cannot be decided - a list, a quoted
      "null" and a bare flag all read as present while meaning nothing.
      exit=1
      STEP 2  chain stopped at the transition - file did NOT move; nothing reached review/ or done/

      ===== BASELINE  clean tree =====
      QUEUE OK (69 tasks)
      exit=0

  ROUTE-BY-ROUTE, all four closed:

      ROUTE 1 block list      R1a R1b R1c R1d   0 -> 1   plus R1e (flow list) found and closed here
      ROUTE 2 quoted null     R2a R2b           0 -> 1   plus R2c R2d R2e R2f R2g, all new, all closed
      ROUTE 3 case            R3a R3b           0 -> 1   plus R3c (--reviewer AGENT/SELF), new, closed
      ROUTE 4 floor/glob      R4a R4b R4c R4d   0 -> 1   plus R4f (.markdown), new, closed

  THE ADJACENT EVASIONS I WENT LOOKING FOR, since round one's lesson was that each fix hardened the exact
  hole it was pointed at. Nine more were green on the shipped module and are red now:

      R1e  owner: [agent/self]  as a FLOW list, not a block list - the other syntax for the same value
      R2c  the mirror of route 2: reviewer: "null" rather than owner: "null"
      R2d  owner: "~"    - the other null literal the parser knows, in quotes
      R2g  owner: none   - the spelling _scalar never handled at all
      R2e  bash ops/review T-9001 --reviewer null   -> ops/review WROTE reviewer: null and moved the file
      R2f  bash ops/review T-9001 --reviewer        -> _opts yields "true"; persisted as reviewer: true
      R3c  bash ops/review T-9001 --reviewer AGENT/SELF against owner: agent/self
      R4f  the self-graded fixture saved as .markdown - invisible to a widened rglob("*.md") too
      R4e  the REAL tree with queue/done moved aside: red before, but only by accident (dangling
           depends_on). It now names the actual cause first: "queue/done/ is missing".

  R4g (a self-graded task nested in queue/done/archive/) was ALREADY red before the change - rglob
  recurses - so it is reported here as a probe that found nothing, not as a route I closed.

  DUMP WAS AN ENTRY POINT, not just cmd_review. Route 2's real damage was that dump() rewrote the string
  'null' as a bare `null`, so the guard manufactured the state it refuses. Every caller that re-dumps a
  file shares that: log(), cmd_sweep, cmd_claim, cmd_lock. dump() now quotes any scalar parse() would not
  read back unchanged. Measured, `.artifacts/T-0073/roundtrip.py`:

      task files re-dumped: 69   files whose bytes would change: 2
        CHANGED: queue/backlog/T-0012-etl-gate-parity-fixture-motorway-trunk-private-u.md
        CHANGED: queue/backlog/T-0013-human-gate-1-developer-drives-5-commute-routes-4.md
      --- null round-trip ---
        owner: "null"            -> parsed 'null' -> dumped/re-parsed 'null'
        owner: null              -> parsed None -> dumped/re-parsed None
        owner: "~"               -> parsed '~' -> dumped/re-parsed '~'
        owner: agent/self        -> parsed 'agent/self' -> dumped/re-parsed 'agent/self'

  Those two files are a PRE-EXISTING asymmetry, not mine. Same measurement against HEAD's queue.py:

      BASELINE (HEAD's queue.py) files whose bytes would change on re-dump: 2
         queue/backlog/T-0012-etl-gate-parity-fixture-motorway-trunk-private-u.md
         queue/backlog/T-0013-human-gate-1-developer-drives-5-commute-routes-4.md

  Identical set. My change adds zero churn; it only ever ADDS quotes. Both are `title:` values that were
  quoted on disk and re-dumped bare — worth a task, not this one.

  agent() behaviour, from the same script:

      'agent/self'   -> 'agent/self'      ['agent/self'] -> None      'null' -> None
      'agent/Self'   -> 'agent/self'      []             -> None      'none' -> None
      'self'         -> None              None           -> None      '~'    -> None
      'agent/'       -> None                                          'true' -> None

  OTHER SUBCOMMANDS. tasks() changed shape, so every caller was exercised — `.artifacts/T-0073/smoke.sh`,
  mutating ones against a COPY of the real tree, never queue/ itself:

      === ops/queue-next (real tree, read-only) ===
      (no unblocked ready task)                                    exit=0
      === check, in the copy ===            QUEUE OK (69 tasks)    exit=0
      === sweep, in the copy ===            SWEEP done (30 moved)  exit=0   (owner: null afterwards)
      === claim, in the copy ===   T-0014 has no brief - ...       exit=1   (the T-0056 brief guard, correct)
      === review, in the copy ===  T-0014 is in ready/, not claimed/  exit=1 (correct)
      === check the copy after three mutations ===  QUEUE OK (69 tasks)  exit=0
      === new, in the copy ===     queue/backlog/T-0075-smoke-test-task.md  exit=0   (next_id still allocates)

  Repo gates in wt/T-0068 after the change:

      $ bash ops/queue-check
      QUEUE OK (69 tasks)
      exit=0
      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      exit=0
      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0
      $ bash ops/sane
      SANE OK
      exit=0

  All 69 real tasks still pass: every owner/reviewer in the tree is already a lowercase `agent/<name>`
  (43 `agent/claude-opus-5`, 2 `agent/unknown`, 8 `agent/builder-*`, 28 `agent/reviewer-*`), so the
  agent/<name> shape rule turns nothing red on existing state.

  DISCLOSURES, all measured:

  1. `ops/lib/queue.py` grew 515 -> 615 lines (+123 / -23). It was already 215 over the 300-line cap
     before this change; T-0059 owns the split and I did not do it here. This is more growth than the
     brief wanted and I am saying so rather than hiding it: 39 of the added lines are comments and
     docstrings, which I trimmed once already (623 -> 610, before disclosure 5 added five back) but did
     not delete, because the whole reason round one's fix was evadable is that the *argument* for the
     rule was not written next to it. I left
     a 3-line dead `if state == "done": for dep ...: pass` loop alone rather than golf the count with an
     unrelated deletion.
  2. `MIN_TASKS = 40` is a constant in the module, not `pins/floor_queue.txt`. `pins/floor_*.txt` is
     serial-only under CLAUDE.md and this task declares `exclusive: []`, so creating one would have needed
     a lock I do not hold and a `touches:` outside my task's. The floor sits far below the real 69 on
     purpose: it exists to catch "inspected nothing", not to track the queue.
  3. `ops/review` now PERSISTS the normalised (casefolded) reviewer name. Deliberate — a canonical
     `agent/<name>` in review/ cannot later be re-read as different from its owner. No real name changes:
     all 38 reviewer values in the tree are already lowercase.
  4. `bash ops/test` fails here, before and after, with `FAIL: services/api exists but vitest produced no
     report` — `services/api/node_modules` does not exist in this worktree. Measured, not assumed: I
     restored HEAD's `ops/lib/queue.py`, re-ran, and got the identical last line and exit 1. `grep -nE
     "queue" ops/test` returns nothing, so ops/test never invokes this module at all. That is T-0040,
     already filed; not caused by and not touched by this task.
  5. `queue/_schema/` and `queue/LOCKS/` are allow-listed in `KNOWN_DIRS`, which re-opened route 4d
     through the back door: a task file dropped in either is invisible for exactly the reason
     `queue/completed/` was. I found this by probing my own fix, and it was green:

         === R4h  self-graded task file in queue/_schema/ (allow-listed dir) ===
         QUEUE OK (69 tasks)
         exit=0

     Closed with four lines - a task-NAMED file only belongs under a state directory. Same probe after:

         === R4h  self-graded task file in queue/_schema/ (allow-listed dir) ===
         QUEUE CHECK FAIL
          - queue/_schema/T-9001-fixture.md: a task file outside backlog/ready/claimed/review/blocked/done
         exit=1
         === R4i  same, in queue/LOCKS/ ===
         QUEUE CHECK FAIL
          - queue/LOCKS/T-9001-fixture.md: a task file outside backlog/ready/claimed/review/blocked/done
         exit=1
         === baseline again ===
         QUEUE OK (69 tasks)
         exit=0

     The test is on the path's FIRST component, not the immediate parent, so nesting inside a state
     directory still works (R4g stays supported and stays caught). `queue/_schema/task.md` is untouched:
     it is a template, not a `T-NNNN-slug.md`.
     RESIDUAL, stated plainly: a task-shaped file with a NON-task filename under `_schema/` or `LOCKS/`
     is still unseen. Closing that means deciding what content may live in those two directories, which
     is a different rule from this task's, and I would rather name it here than half-do it.
  6. Final harness tally after every fix: 32 cases exit 1, and exactly 3 exit 0 - control OK1
     (owner=agent/a reviewer=agent/b), control OK2 (the ops/review happy path, file moved), and the clean
     baseline `QUEUE OK (69 tasks)`. Nothing that should be red is green, and nothing that was green
     before is red now.

  HYGIENE: every fixture was written into the real queue dirs and removed by the harness's own EXIT trap;
  `find queue -iname "*9001*" -o -iname "*selfgraded*" -o -type d -name completed -o -type d -name archive`
  returns nothing; `.artifacts/` is gitignored and nothing in it is staged.
