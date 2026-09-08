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
depends_on: []
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
