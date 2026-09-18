---
id: T-0130
title: A reviewer's red-demo rewrote a tracked file inside another agent's worktree
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/, queue/README.md]
pins_affected: [P-PROC-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Two agents were working at the same time. One was fixing PR #78 in `.worktrees/T-0122`. The other was
reviewing the same task and, to demonstrate a pin going red, ran `.artifacts/rvw2/pinred.sh`, which:

* **overwrites the tracked file** `ops/lib/check-touches-merge.py` with a deliberately-failing stub (line 9),
* runs the check,
* restores it (line 16),

**inside the first agent's worktree.**

The fixer noticed only because their own verification produced an impossible result - `TOUCHES-MERGE FAIL
(stubbed by reviewer)` in the middle of a run that should have been green. They re-ran with a guard that
hashed the subject against `HEAD` before and after, confirmed both matched, and correctly concluded the false
red was not theirs. It restored byte-identically that time.

### Why this is a real hazard and not a near-miss story

The window between the stub being written and restored is a window in which **any commit by the other agent
would have committed the stub**. What kept it out was one habit: CLAUDE.md's *"Never `git add -A`. Stage
explicit paths"*. That is a good rule and it held, but the fleet should not depend on every agent, in every
worktree, remembering it during someone else's unannounced write.

It also silently corrupts evidence. The fixer's first GREEN run reported a failure that had nothing to do with
their change. Had they been less careful, the plausible conclusions were both wrong: "my fix does not work" or
"the check is flaky". Either would have produced a task log describing something that never happened - which
is precisely the failure mode `ops/`, `pins/` and `queue/` exist to prevent.

### The general shape

`queue/LOCKS` and `exclusive:` protect **serial files**. Nothing currently states that a **worktree** is owned
by the agent that claimed its task, and that another agent may read it but must not write in it. Reviewers
legitimately need to mutate files to demonstrate red - CLAUDE.md requires it: *"A check that has never been
seen red is untested"* - so the answer is not "reviewers must not mutate", it is "reviewers mutate in a
worktree of their own".

Note the reviewers who did this correctly today did exactly that: PR #70's reviewer worked in
`.worktrees/rvw3-T0114` with its own `--scratch-path`, and said so in their report.

### Do

1. State the rule where an agent will actually meet it - `CLAUDE.md` and `queue/README.md`: **a worktree
   belongs to the task that claimed it. Create your own (`git worktree add`) to run any demonstration that
   writes to a tracked file.** A reviewer reads the owner's worktree; it never writes there.
2. Make it mechanical rather than remembered. Options worth weighing in the task log before choosing:
   * a `.githooks/pre-commit` refusal when the worktree's checked-out branch does not match the `branch:` of
     any task naming this worktree - cheap, and it fires at the moment damage would be committed;
   * `ops/agent-preflight` printing the worktree's owning task and warning when the current session is not
     that owner;
   * an `ops/` helper that makes "give me a scratch worktree at this ref" a one-liner, so the correct thing is
     also the easy thing. The absence of that helper is probably why the shortcut was taken.
3. Whichever is built: **demonstrate it red then green.** The red case is a write to a tracked file inside a
   worktree the session does not own; the green case is the same write inside its own.
4. Do not weaken anything to accommodate this. `git add -A` stays banned, and reviewers still have to show red.

## Log
- 2026-09-08T20:40:00Z filed by agent/claude-opus-5 from the PR #78 fixer's own report, which flagged it as
  "worth escalating, not mine to fix". Their guard - hashing the subject blob against HEAD before and after a
  verification run - is worth keeping as a technique regardless of what this task builds.
- 2026-09-15T05:00:00Z **A SECOND SOURCE OF THE SAME HAZARD, and it hit twice in one interruption.** The first instance was a reviewer writing into another agent's worktree. This one needs no second agent at all: a red demo mutates a tracked file, and the **session dies before the `finally` that restores it**.

  Two fixer agents were interrupted mid-demonstration when the session ended. Both had left their mutation in
  the shipping source:

  * `.worktrees/T-0114` - `Sources/Handoff/AppleMapsDirections.swift` carried
    `let point = NumberFormatter().decimalSeparator ?? "."`, the reviewer's own reproduction. That is a live
    locale defect: on a German device every coordinate becomes `34,06890` inside a comma-separated pair. Two
    tests were failing, which was the *demonstration working* - but anyone reading `git status` next session
    sees a modified source file and failing tests, and the obvious reading is "the fix is broken".
  * `.worktrees/T-0116` - `Sources/ScenicKit/Budget/LambdaSearch.swift` had the `routerReturnedNonsense`
    guard replaced by `// guard removed`. Four failing tests, same shape.

  Both restored with `git checkout --`, and both branches then went green: 51 tests in 8 suites and 46 in 6.
  Nothing was lost, because neither agent had committed. But the window between "mutate" and "restore" is
  open for the whole length of a build-and-test cycle - minutes - and a session can end inside it.

  **This changes what the task should build.** A rule about worktree ownership does not help here; the agent
  owned the worktree. The options worth weighing:

  * **Red demos run against a COPY, never the branch's own checkout.** The strongest fix, and it removes both
    sources of the hazard at once. Costs a worktree or a temp tree per demo.
  * **A marker the next session cannot miss.** A demo writes `.artifacts/DEMO-IN-PROGRESS` naming the file and
    its original blob, removes it on restore, and `ops/agent-preflight` refuses while one exists. Cheap, and
    it turns a silent dirty tree into a stated condition.
  * **`.githooks/pre-commit` refusing a commit whose staged diff reinstates a known-bad pattern** - the
    locale spellings, a deleted guard. Narrow, and it only catches the commit, not the confusion.

  The preflight marker is probably the right first move: it is small, it fails closed, and it addresses the
  actual damage, which was not a bad commit but **fifteen minutes of a new session reading a deliberate
  mutation as a defect**.

  **AND A WORKING REFERENCE ALREADY EXISTS.** The agent fixing PR #71 had reached the same conclusion
  independently and built the marker into `ops/mutate/budget.py` before it was interrupted - so this session
  met the guard doing its job rather than the damage. Starting the harness produced:

  ```
  REFUSING: .../.artifacts/budget-mutation-in-flight exists, so the previous run was killed while a
    mutation was on disk.
    The subject files may still be mutated. A run starting now would snapshot a MUTATED file
    as `pristine`, measure every verdict against it, and restore the mutant afterwards.
    Check them - `git diff -- Sources/ScenicKit/Budget/` - restore, then delete the sentinel.
  exit 2
  ```

  That names a **worse** failure than the one this task was filed for, and I had not thought of it: not just
  a confusing dirty tree, but a harness that adopts the mutant as its baseline, scores every mutation against
  it, reports a clean sheet, and writes the mutant back on "restore". Silent, self-consistent, and it
  corrupts the source.

  So the shape is settled and the argument is over: **a sentinel written before the mutation and removed
  after the restore, with the harness refusing while one exists.** What remains is to lift it out of one
  harness into the shared place the rest of [[T-0132]] is heading, and to have `ops/agent-preflight` refuse
  on it too so a human session meets it at the start rather than on the next harness run.

- 2026-09-15T19:30:00Z **IT ALREADY PRODUCED A FALSE GREEN, in a real run, and nobody noticed at the time.** Everything above was written about a *window*. The agent fixing PR #71 closed it and, in doing so, showed the window had already been walked through:

  A subject file was left mutated on disk. A later harness run snapshotted that MUTANT as `pristine`,
  measured all 34 mutations against it, printed **`34 of 34 caught`, exit 0**, and restored the mutant. A
  clean bill of health over corrupted source, self-consistent, with nothing anywhere to contradict it. The
  md5 of the file it measured (`d08228d8`) is not the md5 of `HEAD` (`2e420d88`).

  So this is no longer a hazard with a plausible story attached. It is a defect with a reproduction.

  **The guard that closes it is stronger than the sentinel**, and both are now wanted for different reasons:

  * the **sentinel** (`.artifacts/<name>-mutation-in-flight`) catches *this run was killed mid-mutation*, and
    it is the only thing that can speak before the next run starts;
  * the **HEAD comparison** catches *the subject differs from `git show HEAD:` for ANY reason* - a killed
    run, a hand-edit, a half-applied patch, another agent's demo - and it fires before a single build.

  `ops/mutate/budget.py` now does the second and REFUSES with
  `REFUSING: LambdaSearch.swift does not match \`git show HEAD:\`` and exit 2, with `--allow-dirty-subject`
  as the escape hatch, which announces that it is measuring disk rather than HEAD. Demonstrated end to end
  by hand-planting the exact mutation and getting the refusal where the earlier run had printed 34 of 34.

  **TEST files are deliberately excluded from the comparison**, and the reason is written down rather than
  left implicit: a fix pass edits tests by design, so refusing on them would refuse the ordinary case - and a
  test file left emptied by a killed `--prove-vacuity` makes every mutation report MISSED, which fails
  loudly (`caught 0 of 38`) instead of reading as a clean sheet. The asymmetry is the point: a dirty SUBJECT
  fails silently, a dirty TEST file fails loudly, so only the subject needs the guard.

  Both guards belong in the shared place [[T-0132]] is heading, and `ops/agent-preflight` should refuse on a
  live sentinel so a human session meets it at the start rather than on the next harness run.
