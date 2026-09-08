---
id: T-0081
title: the oracle guard needs a structural property, not more enumerated routes
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T04:10:02Z
lease_expires_at: 2026-09-08T10:10:02Z
worktree: wt/T-0081
branch: task/T-0081
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, services/etl/pyproject.toml, ops/etl-mutation, ops/lib/etl_mutation.py, ops/lib/etl_mutation_rules.py]
pins_affected: []
reviewer: null
depends_on: [T-0079]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

[[T-0074]] was given seven named routes and closed all seven, verified. The round-two adversary then executed
**ten more that pass**, and every one is the adjacent form of a route that was closed:

    X1   the size dodge, one power of two up            (E5 was `< (1 << 20)`; this is `< (2 << 20)`)
    X3   the partial read, at a bigger block            (E6 read 1 MB; this reads 2 MB)
    X2   the refusal keyed on the directory the real oracle lives in, instead of on size
    X4   the pinned constant kept, the call site ignoring it
    X5   `random.Random(seed).shuffle` -> `random.shuffle`; the fixture stops being reproducible
    X6   `cap: int = 400` -> `cap: int = 4`; round 5's "subset of itself" reached through the cap
    X7   the arity floor on condition 2's precondition
    X11  narrow the TABLE not the code - delete one entry from NODE_TAGS
    X12  keep the one value the new test uses, drop the other five

Plus the one round-one route that was explicitly out of scope and remains open: rewriting
`inputs/manifest.yaml`'s `sha256:` and the fixture's `source_sha256` to the same fabricated value, `186 passed`.

**The finding is not any single one of these. It is that the list does not terminate.** Three rounds of
T-0025, then T-0069, then T-0074, have each closed the routes they were shown and been beaten by the next
variant of the same idea. Writing an eleventh test for X1 buys nothing: X1 is E5 with a different constant.

**What a structural property would look like**, instead of a longer list:

- **Mutation testing over `etl/oracle_select.py` and `etl/oracle.py`.** Every route above is a source
  mutation, and every one leaves the suite green - that is the definition of a gap in mutation coverage. A
  mutation run answers the whole class at once and keeps answering it for mutations nobody has thought of.
  `mutmut` or `cosmic-ray` on those two modules, with a coverage floor, run in CI rather than per commit.
- **Property tests rather than fixtures for the funnel.** Every exclusion condition has a shape: given an
  input that violates condition N, `build()` must exclude it. Generate those inputs instead of hand-writing
  one KMZ per condition; the hand-written ones are what X11 and X12 walked around by narrowing the table.
- **The provenance chain needs to leave the repo.** Two co-editable literals compared with each other cannot
  be fixed inside a pytest suite, because the real oracle is gitignored and a test cannot hash a file that is
  not in the tree. The containment is `ops/etl-fetch-inputs` failing at fetch time, which is outside
  `ops/test`. That half belongs in `ops/sane` or the fetch path - file it separately, do not attempt it here.

Do not simply add ten more tests. If that is the chosen route anyway, say in the log why mutation testing was
rejected, because the next adversary will find X13.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-two adversarial verification of T-0074. All ten
  mutations were executed and reverted; the verifier's tree ended clean.
- 2026-09-08T04:10:02Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:10:02Z

- 2026-09-08 agent/claude-opus-5 — mutation coverage, built rather than installed, and it reproduced the
  adversary mechanically.

  **The argument for doing this at all.** T-0025, T-0069 and T-0074 each closed the routes they were shown and
  were beaten by the next variant of the same idea. T-0074 closed seven and an adversary executed ten more that
  pass. The list does not terminate, so a test per route is the wrong shape.

  **Why not `mutmut` or `cosmic-ray`, which this brief names.** Both would work. Neither is pinned in
  `services/etl/inputs/manifest.yaml`, and the ETL's whole discipline is that every input is pinned and
  digest-verified — adding an unpinned dependency in order to produce a *trust signal* is the wrong trade, and
  a framework nobody here can audit sits badly in a repository whose founding premise is that checks lie. The
  harness is stdlib `ast`, it enumerates its mutations explicitly, and it runs anywhere the suite runs. If a
  reviewer disagrees, the counter-argument is short and this paragraph is where to attack it.

  **RUN 1 — 121 mutants, and it found the adversary's own holes without being told them:**

        MUTATION 84 killed, 37 survived, of 121 run in 389s

        SURVIVED  etl/oracle_select.py:86   continue  `continue` -> `pass`
        SURVIVED  etl/oracle_select.py:90   continue  `continue` -> `pass`
        SURVIVED  etl/oracle_select.py:154  continue  `continue` -> `pass`
        SURVIVED  etl/oracle_select.py:68   constant  20 -> 21
        SURVIVED  etl/oracle_select.py:167  constant  7 -> 8
        SURVIVED  etl/oracle.py:170         constant  400 -> 401

  Those three `continue` survivors are **exactly** the guard deletions evasions E8 and E9 used against T-0074,
  and `20 -> 21` at line 68 is E5's size dodge. A mechanical pass reproduced in six minutes what an adversary
  took a session to enumerate by hand. That is the whole argument, measured.

  **THE RULE SET WAS AUDITED AGAINST THOSE TEN EVASIONS, and it had gaps.** Checking a mutation tool against a
  textbook list would have missed this:

        E4   delete `or near_tagged_node(ours, grid)`   operand deletion   MISSING - and it is the FIRST
                                                                           evasion that ever beat T-0074
        X11  drop one entry from NODE_TAGS              collection element MISSING
        E6   _sha256 loop -> one fh.read(1 << 20)       statement swap     DELIBERATELY NOT MODELLED

  Two were added (`operand`, `dictkey`, `setmember`): **121 -> 186 mutants**. E6 is not, and the file says so
  rather than faking coverage: replacing an arbitrary statement with an arbitrary other one is not an
  enumerable mutation, it is writing a different program, and a rule that tried would produce noise. That
  shape belongs to a test that reads a file larger than one block — T-0074's own outstanding correction.

  **RUN 2 — 186 mutants, and the two new rules found X11 verbatim:**

        MUTATION 117 killed, 69 survived, of 186 run in 661s

        SURVIVED  etl/oracle_select.py:37  dictkey    drop key 'traffic_calming'
        SURVIVED  etl/oracle_select.py:38  setmember  drop member 'crossing'
        SURVIVED  etl/oracle_select.py:38  setmember  drop member 'give_way'
        SURVIVED  etl/oracle_select.py:38  setmember  drop member 'mini_roundabout'
        SURVIVED  etl/oracle.py:166        operand    drop operand 0 of Or
        SURVIVED  etl/oracle.py:170        operand    drop operand 1 of Or

  X11 was *"delete `traffic_calming` from NODE_TAGS"* and X12 was *"keep the one value the new test uses, drop
  the other five"*. The harness produced both without being told they existed. That is what a rule set buys
  over a test per route: it covers the mutation nobody has thought of yet, which is the only kind that matters.

  `MAX_SURVIVORS = 69`, the measured number. **It is a ratchet in the safe direction: lower it as tests land,
  never raise it.** `.githooks/commit-msg` guards `MAX_*` bindings (T-0079), so raising it costs a stated
  reason. 63% is not a good mutation score and this file does not pretend otherwise — it is the honest floor
  under a suite that had none, and the 69 names exactly where the next adversary will go.

  > **CORRECTED 2026-09-08 (PR #56 review, F1 below).** The sentence about `.githooks/commit-msg` was false
  > when written: that guard is T-0079's and T-0079 is unmerged. `grep -c "MAX_" .githooks/commit-msg` on this
  > branch and on main returns 0, and the reviewer took 69 -> 999 through the hook in silence. Left in place
  > rather than edited away, because the entry is the record of what I claimed. `depends_on: [T-0079]` now
  > carries the dependency the sentence assumed.

  **THREE DEFECTS IN MY OWN HARNESS, ALL FOUND BY OPERATING IT RATHER THAN BY READING IT.**

  1. **A killed run leaves a mutant on disk** — and because `ast.unparse` does not preserve comments, it leaves
     a COMMENT-STRIPPED module, which is far more damage than one flipped operator. It happened for real: a
     `tee` into a directory that did not exist closed the pipe and killed the run mid-mutant. The clean-tree
     guard, written an hour earlier for a case I called unlikely, refused to start:

            MUTATION FAIL: these modules are not clean, and this harness rewrites them in place:
                services/etl/etl/oracle.py

  2. **Two runs can race.** Python survived that broken pipe and kept mutating invisibly while I started a
     second run; both rewrote the same two modules at once. Added an `O_EXCL` lock, demonstrated red
     (`another run holds .artifacts/etl-mutation.lock (pid 99999)`) and green.

  3. **`import ast` was dropped in the split** and the runner still calls `ast.parse`/`ast.unparse`. Caught
     because I ran a two-mutant control after the split instead of trusting it — the traceback was on the last
     line of the file.

  **Split, not exempted.** The harness reached 332 lines against the 300-line cap. `ops/lib/check-line-cap` on
  this branch is still the Swift-only version, so nothing would have reported it — which is precisely the
  reasoning [[T-0059]] records as wrong ("the check cannot see it is not a reason"), and [[T-0058]] brings the
  Python cap that will. Split at the real seam: `etl_mutation_rules.py` (188) knows what a mutation IS and
  needs only `ast`; `etl_mutation.py` (220) knows how to apply one, run a suite and decide whether the result
  can be trusted. They change for different reasons.

  **NOT wired into `ops/test`**, deliberately: a full pass restores and re-runs the suite once per mutant —
  661 seconds — and `ops/test` is the per-commit gate. This belongs in CI on its own schedule. Said here so
  the omission is a decision rather than something a reviewer has to notice.

  **What this does NOT do**, since a tool that oversells itself is the thing this repo exists to catch: it
  does not decide which of the 69 survivors are genuinely equivalent mutations, and some certainly are. It
  ranks nothing. It is a floor and a map, not a verdict.

- 2026-09-08 agent/claude-opus-5 — **PR #56's CI is red, and it is the T-0036 ordering constraint, not a
  defect in this work.** Recorded here so a reviewer does not spend time on it.

        core / check-pins
          P-OPS-01: wrong git file mode:
            ops/lib/etl_mutation.py       (script, should be 100755, is 100644)
            ops/lib/etl_mutation_rules.py (script, should be 100755, is 100644)

  This branch adds two `ops/lib/*.py`, and `task/T-0036` — unmerged — is what reclassifies those from script
  to data, because they are only ever invoked as `"$PY" ops/lib/x.py`. Whichever mode they carry, ONE of the
  two merge orders fails. Measured both ways:

        on this branch's base (T-0036 absent):   should be 100755, is 100644          exit 1
        main + task/T-0036 + task/T-0081:        P-OPS-01: 31 files, 20 required present, all modes correct

  100644 is the correct END state, so it stays, exactly as `task/T-0021` and `task/T-0049` did before it.

  **The tool written in this session derives the edge for this very branch**, which is the check that matters:

        git diff --name-only --diff-filter=A origin/main...origin/task/T-0081 -- 'ops/lib/*.py'
          ops/lib/etl_mutation.py
          ops/lib/etl_mutation_rules.py

  `ops/merge-rehearse` (T-0065) asks exactly that question and emits
  `ordering: task/T-0081 ... must follow task/T-0036`. So this is the third branch the derived rule covers,
  and the first one it covers that did not exist when the rule was written — which was the whole argument for
  deriving it rather than listing T-0021 by hand.
- 2026-09-08 agent/claude-opus-5 — **PR #56's review was right on every count, and all four attacks are
  closed.** I reproduced each finding before changing anything; not one of them turned out to be wrong.

  **F1 [high] the ratchet was unprotected, and the file said otherwise.** RED, on this branch:

        $ grep -c "MAX_" .githooks/commit-msg
        0
        $ python .artifacts/toggle_budget.py up      # MAX_SURVIVORS = 69 -> 999
        $ git add ops/lib/etl_mutation.py
        $ bash .githooks/commit-msg .artifacts/msg.txt ; echo "HOOK_EXIT=$?"
        HOOK_EXIT=0

  The hook here guards `pins/floor_linux.txt` and `pins/floor_ios.txt` and nothing else. The `MAX_*` rule is
  T-0079's and is unmerged. I cannot fix that from here — `.githooks/` is outside this task's `touches:` —
  so the fix is to stop claiming it: the comment now states plainly that nothing guards the constant on this
  branch, and `depends_on: [T-0079]` records the ordering the way the log records T-0036's. GREEN is the
  same staged index under the hook the dependency brings:

        $ bash .artifacts/commit-msg-T0079 .artifacts/msg.txt ; echo "HOOK_EXIT=$?"
        commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line in the commit body:
          ops/lib/etl_mutation.py: MAX_SURVIVORS 69 -> 999
        HOOK_EXIT=1

  **F2 [high] nothing bounded the mutant set.** RED — the two rules this PR added, turned off by renaming
  their visitors, and no check anywhere objects:

        $ python .artifacts/toggle_rules.py off
        $ python ops/lib/etl_mutation.py --list | tail -1 ; echo "LIST_EXIT=$?"
        MUTANTS 154
        LIST_EXIT=0
        $ python ops/lib/etl_mutation.py --limit 4 ; echo "RUN_EXIT=$?"
        MUTATION 3 killed, 1 survived, of 4 run in 9s
        RUN_EXIT=0

  (The reviewer ran the full pass at 154 mutants and got 54 survivors — a fifteen-survivor "improvement".)
  GREEN — `MIN_MUTANTS_ORACLE = 66` and `MIN_MUTANTS_ORACLE_SELECT = 120` in the rules module, checked before
  `--list` and before any run, because `--list` is how you would confirm the rule set is intact:

        $ python .artifacts/toggle_rules.py off
        $ python ops/lib/etl_mutation.py --list ; echo "LIST_EXIT=$?"
        MUTATION FAIL: the mutant set shrank, so the survivor count falls for a reason that is not
          better tests. Raise the bar by killing mutants, never by generating fewer of them.
            etl/oracle.py: 63 mutants, floor MIN_MUTANTS is 66
            etl/oracle_select.py: 91 mutants, floor MIN_MUTANTS is 120
          If the module really did get smaller: lower the floor in ops/lib/etl_mutation_rules.py with
          a `ratchet-lower: <reason>` line in the commit body.
        LIST_EXIT=2

  They are two scalars rather than one dict on purpose, and that was checked rather than assumed: T-0079's
  parser classifies a dict literal as `opaque` and skips it, so a dict would have looked like a ratchet and
  been none. With the floors committed, its hook reads them:

        $ # MIN_MUTANTS_ORACLE_SELECT = 120 -> 12, staged
        $ bash .artifacts/commit-msg-T0079 .artifacts/msg.txt ; echo "HOOK_EXIT=$?"
        commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line in the commit body:
          ops/lib/etl_mutation_rules.py: MIN_MUTANTS_ORACLE_SELECT 120 -> 12
        HOOK_EXIT=1

  **F3 [high] the vacuity guard sat on the planned count, not the executed one.** RED:

        $ python ops/lib/etl_mutation.py --limit -1 ; echo "EXIT=$?"
        baseline: suite passes

        MUTATION 0 killed, 0 survived, of 0 run in 0s
        EXIT=0

  GREEN, both halves — refused at the door, and a truncated run is no longer a pass:

        $ python ops/lib/etl_mutation.py --limit -1 ; echo "EXIT=$?"
        MUTATION FAIL: --limit must be >= 0 (0 means no limit), not -1
        EXIT=2

        $ python ops/lib/etl_mutation.py --limit 4 ; echo "EXIT=$?"
        baseline: suite passes
        unparse control: suite passes
          SURVIVED  etl/oracle.py:47  operand   drop operand 0 of Or

        MUTATION 3 killed, 1 survived, of 4 run in 9s
          PARTIAL, so not a verdict: only 4 of 186 mutants ran.
          The budget of 69 only means anything over the whole floored set. Exit 3, not 0.
        EXIT=3

  A subset can still FAIL — the budget is applied first, so a sample that blows it exits 1 — but it can never
  pass. The same rule covers a module with no floor, which was the other way to get a small denominator:

        $ PYTHON=python ops/etl-mutation --module etl/counts.py --limit 2 ; echo "EXIT=$?"
          PARTIAL, so not a verdict: only 2 of 33 mutants ran; no MIN_MUTANTS floor for etl/counts.py.
        EXIT=3

  **F4 [medium] the clean-tree guard asked git about the wrong files.** RED — the exact disaster the
  docstring describes, sitting in the tree while the harness reports numbers:

        $ python .artifacts/corrupt_select.py corrupt      # ast.unparse, comments stripped, behaviour same
        $ git status --porcelain
         M services/etl/etl/oracle_select.py
        $ python ops/lib/etl_mutation.py --module etl/oracle.py --limit 2 ; echo "EXIT=$?"
        baseline: suite passes

        MUTATION 2 killed, 0 survived, of 2 run in 2s
        EXIT=0

  GREEN — `dirty()` now asks about the whole `etl` package, not this run's module list:

        $ python ops/lib/etl_mutation.py --module etl/oracle.py --limit 2 ; echo "EXIT=$?"
        MUTATION FAIL: these modules are not clean, and this harness rewrites them in place:
            services/etl/etl/oracle_select.py
        EXIT=2

  **F5 [medium] "every one of the ten evasions is in this file's rule set" was false.** Confirmed: X5's site
  produces no mutant at all (`--list | grep "oracle_select.py:196"` is empty), and X2 and X4 are the same
  shape — a call site rewritten, not a node edited. The docstring now says SIX, names the three that no rule
  can generate, and says what that means: zero survivors would still not close the class. That sentence was
  load-bearing — it is what licensed "so a survivor is where the next adversary will go".

  **F6 [low] `mutants_for` was defined twice**, the first dead. Removed; the rules module is 199 lines.

  **F7 [low] there was no unparse-only control**, and this one was not latent — it is a fail-open in the
  flattering direction, so I demonstrated it rather than reasoning about it. A temporary probe test that
  reads the module SOURCE (any docstring, licence-header or line-budget assertion has this shape) passes
  normally and fails on unparsed output. RED, against the committed runner:

        $ python ops/lib/_old_runner.py --module etl/oracle.py --limit 3 ; echo "EXIT=$?"
        baseline: suite passes

        MUTATION 3 killed, 0 survived, of 3 run in 5s
        EXIT=0

  A perfect score, produced entirely by `ast.unparse` stripping comments. GREEN:

        $ python ops/lib/etl_mutation.py --module etl/oracle.py --limit 3 ; echo "EXIT=$?"
        baseline: suite passes
        unparse control: FAIL
        MUTATION FAIL: the suite fails on the UNMUTATED ast.unparse of these modules, so every mutant
          would be scored as killed by that alone and the run would look perfect. Refusing.
        EXIT=2

  **F8 (mine, found while closing F3) a mutant could be counted in "of N run" without ever running.** A
  mutant whose applier matches nothing was skipped silently and counted anyway. RED — every applier degraded
  to a no-op, against the committed runner:

        $ python .artifacts/toggle_noop.py off
        $ python ops/lib/_old_runner.py --limit 3 ; echo "EXIT=$?"
        baseline: suite passes

        MUTATION 0 killed, 0 survived, of 3 run in 0s
        EXIT=0

  GREEN:

        $ python ops/lib/etl_mutation.py --limit 3 ; echo "EXIT=$?"
        MUTATION 0 killed, 0 survived, of 0 run in 0s
        MUTATION FAIL: 3 mutants were reached and 0 of them actually ran. A mutant whose
          applier matched nothing, or whose tree would not unparse, is not a tested mutant - and a
          run that executed nothing must never read as clean. An enumeration is not coverage.
        EXIT=2

  **THE FULL PASS AFTER ALL OF IT**, to show the guards cost nothing and the headline numbers still stand:

        $ python ops/lib/etl_mutation.py ; echo "FULL_EXIT=$?"
        baseline: suite passes
        unparse control: suite passes
          SURVIVED  etl/oracle.py:166        operand   drop operand 0 of Or
          SURVIVED  etl/oracle.py:170        operand   drop operand 1 of Or
          SURVIVED  etl/oracle_select.py:37  dictkey   drop key 'traffic_calming'
          SURVIVED  etl/oracle_select.py:38  setmember drop member 'crossing'
          ... 65 more ...

        MUTATION 117 killed, 69 survived, of 186 run in 664s
        FULL_EXIT=0

  The same 117/69/186 as the PR body (661s) and as the reviewer's independent run (657s), with the same
  survivors at the same lines. The new guards cost one extra suite run: 664s against 661s. Tree clean
  afterwards, lock removed.

  **NOT FIXED, and why.** The review's other medium is that nothing in the tree invokes `ops/etl-mutation`,
  so `MAX_SURVIVORS` gates only a human's own run. Wiring it needs `.github/workflows/`, outside this task's
  `touches:`, and the instruction for this round was not to widen it. It is stated in the wrapper header now
  instead of implied away.

  I tried the one route that WAS inside `touches:` — a pytest test in `services/etl/tests/` asserting the
  MIN_MUTANTS floors, which `ops/test` and therefore CI already run — and rejected it, because it is a trap:
  the harness rewrites the modules in place while the suite runs, so a test that enumerates mutants of the
  working tree would see the MUTATED module. Every `dictkey`/`setmember` mutation drops an entry, the count
  falls below the floor, that test fails, and the mutant is scored KILLED by its own floor check. It would
  have inflated the kill count and looked like an improvement. Filed here rather than committed.

  **FOR WHOEVER MERGES THIS UNDER task/T-0088.** Two things, both mechanical:
  1. The `MAX_SURVIVORS` comment block is edited on both branches and will conflict. The resolution is
     T-0088's value and history list, plus this branch's sentence about the constant being unguarded until
     T-0079 lands — the two say different things and both are true.
  2. `ops/lib/etl_mutation.py` is 294 lines here against the 300-line cap, and T-0088 adds ~35. The merged
     file is over the cap and needs the next split — the run-integrity guards (clean tree, unparse control,
     vacuity, floors) are a different reason-to-change from applying a mutant and running a suite.
