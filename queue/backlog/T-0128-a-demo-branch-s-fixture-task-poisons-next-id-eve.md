---
id: T-0128
title: A demo branch's fixture task poisons next_id; every new task is now T-99xx
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/new-task` now allocates **T-9902** for every new task, and will keep doing so forever.

`next_id()` (`ops/lib/queue.py:272`) takes the max over local task ids **union `_ids_in_refs()`**, which walks
every ref under `refs/remotes` and pulls `T-(\d+)` out of every path under `queue/`. That union is deliberate
and correct in principle - it is what stops two agents on two branches minting the same id. But it does not
distinguish a real task from a **test fixture**, and two remote refs carry one:

```
$ for r in $(git for-each-ref --format='%(refname)' refs/remotes | grep -v HEAD); do
    git ls-tree -r --name-only "$r" queue/ | grep -o 'T-9[0-9]*-[^/]*' | sed "s|^|$r  |"; done | sort -u
refs/remotes/origin/demo/T-9901-mrg  T-9901-demo.md
refs/remotes/origin/task/T-9901      T-9901-demo.md
```

`T-9901` is a demonstration artifact - the deliberately-high id a red/green merge-gate demo used precisely so
it would not collide with real work. It achieved that, and then set the floor for everything after it.

### Reproduced twice, deterministically

```
$ python ops/lib/queue.py new "CLAUDE.md tells agents to commit ops/*.py executable; ..."
queue/backlog/T-9902-claude-md-tells-agents-to-commit-ops-py-executab.md
$ python ops/lib/queue.py new "A demo branch's fixture task poisons next_id; ..."
queue/backlog/T-9902-a-demo-branch-s-fixture-task-poisons-next-id-eve.md
```

The second call returned **the same id**, because the first file was still untracked and `_ids_in_refs()` only
sees refs - so the allocator is not merely shifted, it is now capable of handing the same id to two consecutive
tasks on one machine. Both were renamed by hand to T-0127 and T-0128; the true next real id was T-0127.

### Why this is worse than cosmetic

* Ids stop being ordered, so `T-9902` filed after `T-0126` reads as unrelated to the run of work it belongs to.
* The one thing `_ids_in_refs()` exists to prevent - a duplicate id that surfaces only when two branches merge -
  is exactly what the second call above produced, because the collision window is between *minting* and
  *pushing*, and every new task now starts inside it.
* An agent that does not notice will file at T-9903, T-9904 ... and the real sequence is abandoned silently.

### Do

1. Decide what a fixture id **is**, and make it explicit rather than a convention someone remembers. Options,
   in rough order of preference:
   * Reserve a documented range (e.g. `>= 9000`) as fixture-only, exclude it from `next_id()`, and **refuse**
     to mint into it. Cheap, and it makes the existing `T-9901` choice correct in retrospect rather than
     accidental.
   * Exclude refs whose name matches `refs/remotes/*/demo/*` from the scan. Weaker - a fixture can live on a
     `task/` branch, and `origin/task/T-9901` shows one already does.
2. Whatever the rule is, `next_id()` must still scan real branches - do not "fix" this by deleting the union.
   That would restore the duplicate-id hazard the union was added to close.
3. **Do not delete the `T-9901` demo branches to make the symptom go away.** They are the evidence trail for a
   red/green demonstration. If they should be pruned that is a separate, human-confirmed decision.
4. Demonstrate red then green: with the fixture ref present, show `next_id()` returning the wrong id, then
   returning the right one; and add a case proving the allocator still refuses to reuse an id that exists only
   on a remote task branch.

## Log
- 2026-09-08T19:35:00Z filed by agent/claude-opus-5 after `ops/new-task` handed out T-9902 twice in a row while
  filing T-0127. Both reproductions above are real command output, not reconstructions.
