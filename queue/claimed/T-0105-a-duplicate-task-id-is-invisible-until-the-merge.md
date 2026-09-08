---
id: T-0105
title: a duplicate task id is invisible until the merge, so all three of today's were found by hand
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T10:18:01Z
lease_expires_at: 2026-09-08T13:18:01Z
worktree: null
branch: task/T-0105
exclusive: []
touches: [ops/lib/queue.py, ops/queue-ids]
pins_affected: []
reviewer: null
depends_on: [T-0101]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**Three task ids were issued twice on 2026-09-08, and a human found all three.** `ops/queue-check` has a
duplicate-id rule; it did not fire once, and it could not have.

    T-0099   main "merge-readiness tools enumerate open PRs"  vs  task/T-0080 "P-SRC-01 greps Sources/ only"
    T-0088   main "the 69 mutation survivors"                 vs  task/T-0087 "check-pins tier with no value"
    T-0076   main "ops/test picks whichever python3"          vs  task/T-0071 "core.hooksPath is machine-local"

`queue-check`'s rule compares ids **within one tree**. Every one of these is a pair across two branches, so
it passes on `main`, passes on the branch, and fails only once both files are in the same tree — after the
merge, on a branch neither author is watching. That is the merge-time-only class [[T-0063]] was filed for.

**How each was actually found**, which is the part that should not be repeated:

  * `T-0088` — an unrelated task happened to branch from `task/T-0087` and merge `main` into it.
  * `T-0099` — I reconciled two agents' reports side by side and noticed the same number twice.
  * `T-0076` — I read a fixer's commit list and recognised an id that already meant something else.

None of that is a mechanism. [[T-0065]]'s rehearsal is the tool that should catch merge-time defects, and it
missed all three: two of the branches had no open PR, so it never merged them ([[T-0099]]), and its
`gates()` keeps only `tail -1` of `queue-check`, so a *new* duplicate reads as INHERITED and does not count
([[T-0104]]).

[[T-0101]] stops new collisions being *created*. This task is the other half: **detecting the ones that
exist**, and there are three in the tree right now.

Do:

1. A cross-branch id check. The data is one query — `_ids_in_refs()` already walks every remote ref for
   exactly this population, and it is what `next_id()` consults. Compare the ids on THIS branch against the
   ids on every other ref, and report a pair whose id matches while the FILENAME SLUG differs — same id,
   different work, which is the shape all three had.
2. **Do not put it in `ops/queue-check`'s default path.** That command runs in CI, in the pre-commit hook
   and in the rehearsal's gates; making it reach the network makes it a command people stop running, which
   is the failure mode this repository keeps meeting. Give it its own entry point, or a flag that is off by
   default, and say in the output when it was skipped.
3. Report the pair with both slugs and both refs, not just the id — `T-0076` needs the reader to see
   *"ops/test picks whichever python3"* against *"core.hooksPath is machine-local"* to know it is a real
   collision and not the same task on two branches, which is the normal and healthy case.
4. **The discriminator matters and is easy to get wrong.** The same task file legitimately appears on dozens
   of branches; that is not a duplicate. Only a differing slug for the same id is. Get this wrong in the
   permissive direction and it reports nothing; get it wrong in the strict direction and it reports 60 false
   pairs and gets ignored.
5. Red demo: the three real pairs above, if they are still unrepaired when this is claimed — and if they
   have been renumbered by then, reconstruct one in a throwaway rather than skipping the red.

**Vacuity guard:** if the ref scan is degraded, the check must say so and fail rather than report no
duplicates. That is precisely the mistake `next_id()` made ([[T-0101]]): the same degraded scan that issued
`T-0076` would otherwise let this check report a clean bill of health.

## Log
- 2026-09-08T10:18:01Z claimed by agent/claude-opus-5; lease until 2026-09-08T13:18:01Z

- 2026-09-08 — **`ops/queue-ids`. It found the live collision on its first run, which is the only evidence
  that counts here.**

        IDS FAIL: 1 id(s) name different work on different refs
          T-0076
            core-hookspath-is-machine-local-and-unverified-s   task/T-0071
            ops-test-picks-whichever-python3-is-first-on-pat   main, task/T-0045, task/T-0060 (+22 more)
          Same id, different slug: two pieces of work were given one name. Renumber the LATER one and
          record why in its log - the id is referenced from other task files by [[T-nnnn]].
        real exit 1

  **The discriminator is the SLUG, and getting it wrong in either direction makes the check worthless.**
  The same task file legitimately appears on 25 refs — that is the normal, healthy case, and reporting it
  would produce sixty false pairs and get this ignored within a day. Only the same id carrying two different
  slugs is a collision. The run above is the proof in both directions at once: it named the one real pair
  and stayed silent about the 25 refs carrying the *same* T-0076.

  **Deliberately not part of `ops/queue-check`.** That command runs in CI, in the pre-commit hook and inside
  `merge-rehearse`'s gates. Making it reach the network would make it a command people stop running, which
  is the failure mode this repository keeps meeting — so this is its own entry point.

  **Vacuity floors, because this check is about a scan that lied.** A failed `for-each-ref` or a single
  unreadable `queue/` refuses with exit 2 rather than reporting no duplicates, and fewer than two refs
  scanned refuses too: *cross-branch* means at least two. That is exactly the mistake `next_id()` made — the
  same degraded scan that issued `T-0076` would otherwise let this report a clean bill of health.

  **Two implementation notes worth keeping.** `COMMANDS` is derived from `OPTS` on this branch ([[T-0087]]),
  so adding the option entry is the whole registration and there is no second list to forget. And `_git()`
  here collapses *"could not run"* and *"ran and failed"* into one `False`, which is acceptable only because
  both answers lead to the same action — refuse. If a caller ever needs to tell them apart, that helper is
  the wrong one to use.

  **What this does not do:** it detects, it does not prevent. [[T-0101]] is the prevention half. Both are
  needed, and today proved it — the third collision happened *after* T-0101 was filed, because the fix is
  not merged.
