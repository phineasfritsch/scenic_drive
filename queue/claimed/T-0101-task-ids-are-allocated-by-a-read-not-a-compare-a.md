---
id: T-0101
title: task ids are allocated by a read, not a compare-and-swap, and T-0099 was issued twice
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T08:23:05Z
lease_expires_at: 2026-09-08T11:23:05Z
worktree: null
branch: task/T-0101
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python ops/lib/queue.py selftest prints 'RESERVE SELFTEST ok: T-0043 contested by two allocators at one commit, won once' and exits 0"
  - "the red run: revert _reserve_id to push HEAD and to trust the push exit code, and the same command prints 'RESERVE SELFTEST FAIL: two allocators that both read T-0043 before either pushed got True and True' and exits 1"
  - "the red run for the race floor: let A push before B reads, and it prints 'the two allocators did not compute the same id, so the race this checks was never set up' and exits 1"
  - "the red run for the population floor: point the reservation push at a remote that is not there, and it prints 'no id was reserved on the throwaway origin, so nothing was compared and this run proves nothing' and exits 1"
---
## Brief

**`T-0099` was allocated twice on 2026-09-08, minutes apart, on two different branches, and nothing caught
it.** `main` got *"every merge-readiness tool enumerates open PRs, so eleven branches of work are
invisible"*; `task/T-0080` got *"P-SRC-01 greps Sources/ only, so a banned import in Tests/ is invisible"*.
Two unrelated findings, one id. Reconciled by hand and the second renumbered to `T-0100`.

**It happened TWICE in one day, and the second one was worse.** `T-0088` was also allocated twice: `main`
has *"the 69 mutation survivors are five gaps"* (from `task/T-0081`) and `task/T-0087` has *"ops/check-pins
tier with no value prints an index"*. Renumbered to `T-0102`.

That second instance is the one that should decide the priority, because **no gate could see it**.
`ops/queue-check` passes on `main`. It passes on `task/T-0087`. The duplicate exists only in the MERGE of
the two — the merge-time-only class [[T-0063]] was filed for and [[T-0065]]'s rehearsal exists to catch —
and the rehearsal could not see it either, because `task/T-0087` has no open PR and the rehearsal
enumerated pull requests ([[T-0099]]). It surfaced only because an unrelated task happened to branch from
`task/T-0087` and merge `main` into it. That is luck, not a mechanism.

**A THIRD instance, hours after this task was filed, and it came through the other door.** `task/T-0071`'s
agent filed *"core.hooksPath is machine-local and unverified"* as **T-0076**. `T-0076` on `main` and on
every other branch is *"ops/test picks whichever python3 is first on PATH"*.

This one was not the read/push race. `task/T-0071`'s own tree tops out at **T-0075**, `main` is at
**T-0104**, and `next_id()` returned `max(0075) + 1`. That is `_ids_in_refs()` taking its **documented
degraded path** — the one whose own comment says *"a degraded scan means collision protection is off, and
the caller must know"* — and then continuing anyway.

    WARNING: next_id could not ... ; id allocation is falling back to this worktree only,
    so a duplicate id is possible. Verify with ops/queue-check after pushing.

**The warning is the defect, not the mitigation.** It goes to stderr, where an agent running a tool does not
read it; the id it hands back looks ordinary; and `ops/queue-check` cannot see the collision from either
tree, only from the merge. So the fallback produced a duplicate 28 ids away from the real maximum, under
ordinary fleet load, on a normal working day — three for three today.

Whatever this task builds must therefore **refuse** rather than warn when the id space cannot be read. An
allocator that cannot see the other allocators is not degraded, it is wrong, and this is the third piece of
evidence for that in one day.

**This is not a hole in [[T-0017]]'s fix; it is the limit of its shape.** `next_id()` consults
`_ids_in_refs()`, which scans every remote ref precisely to stop this, and the comment there is right about
what it buys. But the sequence is:

    read the refs  ->  pick max+1  ->  write the file  ->  ...work...  ->  commit  ->  push

Two allocators that both READ before either PUSHED get the same number, and the window is not milliseconds —
it is however long the first agent takes to reach its first push. Here it was several minutes, because
`ops/new-task` is typically run at the *start* of a piece of work.

**The queue already solves this exact problem one step over, and the contrast is the whole brief.** Claiming
is safe because it is a compare-and-swap: `git mv` + push, and *a rejected push means someone else claimed
it* — `queue/README.md` step 3 says so in as many words. Allocation has the read and no second step. So the
repository's own safety mechanism exists, is documented, and is not applied to the one operation that
invents a unique name.

**What it costs when it is not caught.** `ops/queue-check` fails on `duplicate id` — but only once both
files are in one tree, i.e. after the merge, on a branch neither author is looking at. That is the same
merge-time-only class as the stale `claimed/` copy [[T-0063]] was filed for, and the reason
[[T-0065]]'s rehearsal exists. Here it was caught by a human reading two agents' reports side by side,
which is not a mechanism.

Do:

1. Make allocation a compare-and-swap. The cheapest form that fits this repo: `ops/new-task` writes the
   file, commits **just that file**, and pushes immediately — a rejected push means the id was taken, so it
   re-reads and retries with the next free id. The task file at that point is `ops/new-task`'s placeholder,
   which `brief_is_unwritten()` already recognises ([[T-0056]], [[T-0070]]), so an unwritten brief on `main`
   for a few minutes is a state the rest of the system already understands.
2. If pushing at allocation is judged too eager, the alternative is to stop pretending ids are dense:
   allocate `T-` plus a short hash of (title, owner, timestamp) and let `queue-check` enforce uniqueness.
   That trades readable ordering for correctness by construction. **Pick one and say why in the log** —
   the failure mode of choosing neither is the one already measured.
3. Either way, `ops/new-task` must print the id it actually got, and must refuse silently reusing one.

**Red demo:** two allocations from two worktrees with no push between them currently produce the same id.
That is a two-line reproduction and it should be in the log before the fix.

**Do not** make this depend on the network at read time only — a scan that is more thorough is still a
read, and this task exists because a read is not enough.

## Log
- 2026-09-08T08:23:05Z claimed by agent/claude-opus-5; lease until 2026-09-08T11:23:05Z

- 2026-09-08 — **the id is now reserved by pushing a ref whose NAME is the id, which is the missing second
  step.**

  `git push origin HEAD:refs/tags/id/T-0103` is rejected when the ref already exists — no `--force`, no
  lease — so the push either wins the id or says who has it. It commits nothing, touches no branch, and
  reserves globally rather than per-branch, so it works from any worktree.

  **The sentence this task was filed against is corrected in place**, because it was the load-bearing part
  of the mistake. `_ids_in_refs()` said *"the push is the compare-and-swap that settles that, exactly as for
  claims."* For a CLAIM that is true — the moved file goes to `main` and a rejected push means somebody else
  moved it first. For an ALLOCATION nothing is pushed at allocation time and the task file's eventual push
  goes to a task BRANCH, where it can never conflict with another branch's push. There was no second step,
  only a longer read, and the comment asserting otherwise is why nobody looked.

  **RED** (`.artifacts/demo-reserve.py`, two module instances, nothing pushed between them):

        allocator A -> T-0103
        allocator B -> T-0103     (nothing was pushed in between)
        SAME ID: True

  **GREEN:**

        reservations on origin before: ['T-0103', 'T-0104']
        allocator C -> T-0105
        allocator D -> T-0106     (again nothing was committed or pushed by the caller)
        SAME ID: False
        reservations on origin after: ['T-0103', 'T-0104', 'T-0105', 'T-0106']

        $ ops/queue-check   QUEUE OK (95 tasks)   exit 0
        $ ops/check-pins --source-only   ok=3 failed=0   exit 0

  **Two defects of my own, both found by the demo rather than by reading:**

  1. The first RED printed `T-0001`. The before-copy had been written to `.artifacts/`, so its
     `ROOT = Path(__file__).parents[2]` resolved outside the repository — it saw no tasks and no git, and
     the "red" was an artifact of the harness. Moved to `ops/lib/queue_before.py` and re-run. A red that
     comes from the harness proves nothing, and this one would have read as proof.
  2. `--reserve no` skipped *reading* the reservations as well as writing them, and handed out `T-0103`
     while `T-0103` was already reserved. The escape hatch exists because a box may not be able to PUSH;
     that does not make reading free-er to skip. It now always reads and only the push is conditional.

  **Failure modes, deliberately:** if the reservations cannot be READ, it warns loudly and continues, because
  that is exactly the old behaviour and refusing would make an offline box unable to file a task at all. If
  the reservation cannot be WRITTEN, it **refuses** — allocating unreserved is what issued two ids twice, so
  it is not something to do by accident. `--reserve no` is the deliberate version and prints what it costs.

  **Left as it is, on purpose:** `T-0103`–`T-0106` are now reserved with no task behind them, burned by this
  demo. Deleting a reservation is the one operation that reintroduces the collision, so it should be a
  deliberate act and not a cleanup step in a demo script. A future `queue-check` rule could report
  reservations with no task file; that is not this task.

- 2026-09-08 — **a third collision, hours after this task was filed, through the other door — so the
  degraded path now REFUSES instead of warning.**

  `task/T-0071`'s agent filed *"core.hooksPath is machine-local and unverified"* as **T-0076**. `T-0076` on
  `main` and on every other branch is *"ops/test picks whichever python3 is first on PATH"*.

  **This one was not the read/push race this task was filed for.** `task/T-0071`'s own tree tops out at
  `T-0075`, `main` is at `T-0104`, and `next_id()` returned `max + 1` from the worktree alone — 28 ids below
  the real maximum. That is `_ids_in_refs()` taking its own documented degraded path, the one whose comment
  reads *"a degraded scan means collision protection is off, and the caller must know"*, and then
  continuing.

  **The warning is the defect, not the mitigation.** It goes to stderr, where an agent running a tool does
  not read it; the id comes back looking ordinary; and `ops/queue-check` cannot see the duplicate from
  either tree — only from the merge, on a branch neither author is watching. Three for three today.

  So `SCAN_DEGRADED` now makes the degradation observable to the caller, and `next_id()` raises:

        cannot allocate an id: the id reservations on origin could not be read. Allocating without
        seeing the other allocators is what issued T-0076, T-0088 and T-0099 twice each, so this
        refuses instead of warning. Fix the remote, or pass `--reserve no` to take an id you know
        may collide.

  It is a module global rather than a return value on purpose: every existing caller reads the set and none
  of them asked about its quality, so a tuple would simply have let them keep ignoring it — which is what
  happened.

  **Why the reservation tag alone would NOT have caught T-0076**, which is the reason this needed a second
  change rather than more of the first: the tag reserves the id it is *given*. A degraded scan computes a
  low maximum, the push of `refs/tags/id/T-0076` succeeds because nobody had reserved that number, and the
  allocation still collides with a **task** called T-0076 that the scan never saw. Reservation protects
  against another allocator; it cannot protect against an id space you did not read.

  **On the red, honestly.** `.artifacts/demo-refuse.py` points the module's `ROOT` at a directory that is not
  a git worktree, so every git query fails as it would with no network. Under that simulation the *previous*
  version also refuses — but at the reservation push, not at the read, because in that scenario the push
  fails too. So it is not a clean isolation of this change, and I am not presenting it as one:

        RED    (previous)  refused: cannot reserve T-0001 ... the push could not be made at all
        GREEN  (this)      refused: cannot allocate an id: the id reservations ... could not be read
        CONTROL --reserve no -> T-0001, with the warning saying exactly what it costs

  **The real red is T-0076**: a live duplicate, produced by this exact path, under ordinary fleet load,
  hours after the task describing the race was filed. A simulation that says the same thing would add
  nothing to that.

  Renumbering `T-0076` is deferred while an agent is still finishing on `task/T-0071`; committing to a
  branch under a live agent is the rule this session already broke once.

- 2026-09-08 — **fixer pass on the PR #61 review. The blocking finding is real, reproduced, and fixed;
  findings 2 and 3 were reproduced and were the stale base plus two stale caches; finding 4 is half fixed
  and half handed on.**

  **1. BLOCKING — reproduced.** The reviewer is right and the mechanism is exactly as described.
  `git push origin HEAD:refs/tags/id/T-XXXX` is rejected only when the ref exists at a DIFFERENT object;
  at the SAME object git prints "Everything up-to-date" and exits 0, and `_reserve_id()` read that 0 as
  "we created the tag". Two clones at one commit, driven through the shipped `_reserve_id`
  (`.artifacts/fix61/cas.py`, throwaway origin, the real one never contacted):

        same HEAD       : True
        clone A: _reserve_id(600) -> True
        clone B: _reserve_id(600) -> True
        VERDICT: COMPARE-AND-SWAP DEFEATED (A=True B=True)        exit 1

  End to end, both allocators reading before either pushes — the interleaving in the brief —
  against the pre-change module (`git show 50126a0:ops/lib/queue.py`):

        allocator A READ -> would take T-0043
        allocator B READ -> would take T-0043
        allocator A PUSH T-0043 -> _reserve_id returned True   (KEEPS the id)
        allocator B PUSH T-0043 -> _reserve_id returned True   (KEEPS the id)
        VERDICT: DUPLICATE - T-0043 was allocated twice          exit 1

  The reviewer's "common case, not edge case" reading is also right, and it is worse than an accident of
  this branch: `ops/new-task` runs at the *start* of a piece of work, when a fresh worktree has no commits
  of its own, so two agents who branch off `main` have identical HEADs. The same-object condition and the
  collision condition coincide. `T-0103`–`T-0106`, reserved by this task's own demo, all sit on `4305be5`,
  which is the evidence in this branch's own history.

  **The fix removes two inferences rather than adding a third.**

  `_reservation_object()` builds a parentless commit over an empty tree carrying a per-call nonce, and that
  is what gets pushed. The remote cannot already be at an object invented a millisecond ago, so "already
  there" and "we put it there" stop being confusable. The object is never read; only its uniqueness is
  load-bearing.

  `_reserve_id()` then asks the remote what the ref actually holds, and *that* decides: our object means we
  won, another object means somebody else holds the id, no ref at all means the push did not land. This
  also removes the stderr grep the reviewer flagged in the same breath — `already exists` / `rejected` /
  `cannot lock ref` / `non-fast-forward` are gone. Wording is not an interface, and it was the mirror of the
  bug: the success side trusted an exit code that did not mean what it was taken to mean, the failure side
  distrusted exit codes and read prose. `_remote_ref_object()` keeps "asked, and it is not there" separate
  from "could not ask", because collapsing them is how a failed push reads as a lost race. The exit code
  survives only as the fallback for when the remote cannot be asked a second time, and only in the one
  direction the unique object makes sound.

  **GREEN, same two probes, same labs:**

        clone A: _reserve_id(600) -> True
        clone B: _reserve_id(600) -> False
        VERDICT: compare-and-swap HELD                            exit 0

        allocator A PUSH T-0043 -> _reserve_id returned True   (KEEPS the id)
        allocator B PUSH T-0043 -> _reserve_id returned False  (backs off)
        VERDICT: the compare-and-swap held                       exit 0

  The differing-HEAD control still holds on both versions (exit 0), so the change did not simply move the
  failure.

  **The demo is now a committed check, because a gitignored probe is how this shipped believed.** The first
  version of `_reserve_id()` was reviewed, believed and merged on a prose argument plus a demo nobody else
  could run. `queue.py selftest` builds its own throwaway bare repo, forces the read-before-push
  interleaving, and refuses two ways a green could be empty:

  * `landed` — the reservations that actually reached the throwaway origin must be non-empty. Without it,
    "the second allocator backed off" is indistinguishable from "no push ever worked".
  * `na != nb` — both allocators must have computed the SAME id, or the race was never set up and the pass
    says nothing about a race. This is the floor that counts the right population: what is examined is
    *contested* allocations, not allocations.

  **RED, then GREEN, on the real file** (`.artifacts/fix61/red.py` applies each break, runs, and restores
  from a byte-for-byte snapshot; it asserts the restore):

        GREEN (unmodified)  exit=0
          RESERVE SELFTEST ok: T-0043 contested by two allocators at one commit, won once

        RED 1  push HEAD again, and believe the push exit code           exit=1
          A-reserve=True B-reserve=True landed=['T-0043']
          FAIL: ... got True and True; exactly one must win.

        RED 2  let A push before B reads, so the run is sequential       exit=1
          A-read=T-0043 B-read=T-0044 landed=['T-0043', 'T-0044']
          FAIL: the two allocators did not compute the same id, so the race this checks was never set up.

        RED 3  send the reservations to a remote that is not there       exit=1
          A-reserve=None B-reserve=None landed=[]
          FAIL: no id was reserved on the throwaway origin ... A green here would be vacuous.

        GREEN (restored)    exit=0

  Note that RED 1 fails *because both halves were reverted together*. Reverting either half alone still
  passes — a unique object defeats the same-sha push on its own, and asking the remote defeats it on its
  own. That is deliberate belt and braces on the operation that invents unique names, not an accident, and
  it is stated here so a future reader does not delete one half as dead weight.

  **2. The log's GREEN line — reproduced, and the number in it was wrong.** On the branch as reviewed:
  `ops/check-pins --source-only` → `PINS ok=2 skipped=8 pending=1 expired=0 failed=1`, **exit 1**, P-SAFE-05
  failing. The earlier log said `ok=3 failed=0 exit 0`; that is not a number this branch ever produced and
  it should not have been written. Two causes, both outside the diff: the branch was 70 commits behind
  `origin/main` (now merged, clean, no conflicts), and this worktree's `.build/` held a Swift module cache
  compiled when the worktree lived at `C:\Users\phineasf\Documents\GitHub\wt\T-0101`, so every Swift
  invocation died with `could not build module 'vcruntime'` before running a test. After the merge and
  `rm -rf .build`: `PINS ok=4 skipped=9 pending=0 expired=0 failed=0`, **exit 0**, which is `main`'s
  baseline today (`ok=4 failed=0`, exit 0) exactly. Full `ops/check-pins`: `ok=11 skipped=0 pending=2
  expired=0 failed=0`, exit 0.

  **3. `verify:` — reproduced, and it passes now.** `ops/test` on the branch as reviewed exited 1 at
  `FAIL: swift test produced no JUnit report`, same stale module cache. With that cleared it exited 1 one
  tier later at `FAIL: services/api exists but vitest produced no report`, which is precisely where `main`
  failed for the reviewer — `services/api/node_modules` was absent, so `npx vitest` could not run. After
  `npm ci` in `services/api` (host state; nothing committed, `node_modules` is gitignored):

        TESTS linux=119/76 ios=skipped failed=0 skipped=0
        OK                                                        exit 0

  Both `verify:` entries are green on this branch now. The honest caveat: the vitest tier's greenness is
  host state, not a property of the tree, and on a box without `services/api/node_modules` `ops/test` still
  exits 1 the same way it does on `main`. That is a pre-existing gap in `ops/test`, not something this task
  introduced or fixed.

  **4. `acceptance: []` — half fixed here, half not mine to fix.** The list is now four entries: the
  command and its expected line, and the three red runs with the non-zero exit each produces. The other
  half of the reviewer's point — that *nothing mechanical* refuses an empty `acceptance` on a claimed task,
  and `ops/queue-check` prints `QUEUE OK` regardless — is a change to `ops/queue-check`, outside this task's
  `touches: [ops/lib/queue.py]`. Widening `touches` to smuggle in a queue-wide gate under a task about id
  allocation is the shape this repo files tasks against, so it is left for a task of its own and named here
  rather than quietly done or quietly dropped.

  **And against the real origin, read-only, on the reservations this branch itself made.** Both pushes are
  `--dry-run`; nothing was written and `refs/tags/id/T-0103..T-0107` are unchanged.

        $ git ls-remote --refs origin 'refs/tags/id/T-010*'
        4305be5...  refs/tags/id/T-0103      (T-0104, T-0105, T-0106 all at the same commit)
        d9cea6f...  refs/tags/id/T-0107

        $ git push --dry-run origin 4305be5:refs/tags/id/T-0103     # what the old code pushed
        Everything up-to-date                                        exit 0   -> old code: "we won it"

        $ git push --dry-run origin <fresh commit-tree>:refs/tags/id/T-0103    # what this code pushes
         ! [rejected]  ... -> id/T-0103 (already exists)              exit 1   -> new code: False

  **State:** not transitioned. Still `claimed`, reviewer still null, for the same reviewer to look again.
