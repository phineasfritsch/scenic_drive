---
id: T-0105
title: a duplicate task id is invisible until the merge, so all three of today's were found by hand
state: done
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T10:18:01Z
lease_expires_at: 2026-09-08T13:18:01Z
worktree: null
branch: task/T-0105
exclusive: []
touches: [ops/lib/queue.py, ops/queue-ids, ops/lib/check-ids-floor, ops/agent-preflight]
pins_affected: []
reviewer: agent/reviewer-final-pr66
depends_on: [T-0101]
verify: [ops/test, ops/check-pins]
acceptance:
  - "bash ops/lib/check-ids-floor -> IDS-FLOOR ok (4 cases), exit 0: the vacuity floor refuses a scan that found no ids (A), and one that found ids on only one ref (B), while a real collision is still exit 1 (C) and a healthy pair still exit 0 (D)"
  - "RED for the floor: change `if with_ids < 2:` in cmd_ids to `< 0` -> check-ids-floor prints A/B FAIL and exits 1; restore -> exit 0"
  - "bash ops/queue-ids -> IDS OK (N ids on M of M refs) + the line saying how old the last fetch was, exit 0"
  - "RED for the detector: commit a second T-0105-<other-slug>.md onto a throwaway refs/remotes/origin/zz-* -> IDS FAIL naming both slugs, exit 1; bash ops/agent-preflight -> ids COLLISION + PREFLIGHT FAIL, exit 1; delete the ref -> both exit 0"
  - "python ops/lib/queue.py <unknown> -> the printed commands: block lists ids (it is built from OPTS, not written by hand)"
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

- 2026-09-08 — **green, on live data, after the collision it found was repaired.**

        RED    IDS FAIL: 1 id(s) name different work on different refs   (T-0076)   real exit 1
        GREEN  IDS OK (105 ids across 75 refs; no id names two different tasks)     real exit 0

  The repair was `task/T-0071`'s new task being renumbered `T-0076 -> T-0106`. So the cycle here is not a
  fixture: the check found a real collision, a real branch was corrected because of it, and the same command
  then went green across all 75 refs. It is also the first of the three collisions found by a tool rather
  than by a human reading two agents' output side by side.

  Worth stating what the green does NOT prove: 75 refs carry 105 ids and the vast majority of those ids
  appear on many refs at once. `IDS OK` means no id carries two different slugs — it says nothing about
  whether the work behind any id is correct, and the count is large because branches share history, not
  because 105 tasks are healthy.

- 2026-09-08 — **fixer pass on PR #66's review. F1 (blocking) fixed, F2/F3/F4 folded in, F6 closed, F5
  confirmed pre-existing and still red. Every finding was reproduced before it was touched.**

  **F1 — the floor counted refs walked past, not the population examined.** The reviewer is right, and the
  mechanism is that `git ls-tree -r <ref> queue/` on a ref with NO `queue/` exits 0 and prints nothing,
  which is byte-identical to a ref whose `queue/` holds no task files. `scanned` cannot tell them apart.
  Reproduced first, in three standalone repos (two remote-tracking refs each, driven through the real
  `ops/queue-ids` wrapper, `.artifacts/f1repro.sh`):

        case                                        BEFORE the fix                       AFTER
        A  no T-NNNN-<slug>.md where the scan looks  IDS OK (0 ids across 2 refs)  exit 0  IDS REFUSED  exit 2
        B  live collision, one side at tasks/        IDS OK (1 ids across 2 refs)  exit 0  IDS REFUSED  exit 2
        C  control: same collision, both in queue/   IDS FAIL naming both slugs    exit 1  unchanged    exit 1

  B is the one that matters: a real duplicate id sat in that tree and the command certified it clean. The
  fix is a second floor on `with_ids` — refs that actually YIELDED an id — next to the `scanned` one, and
  the counted population is now printed in the green line too (`IDS OK (114 ids on 79 of 79 refs)`), so a
  reader can see what was examined rather than what was iterated over.

  **The floor is now itself a check, with its own red.** `ops/lib/check-ids-floor` builds those three
  repos plus a fourth (same id, same slug, two refs — the normal healthy case that must stay exit 0) and
  asserts all four exit codes. A floor can always be made green by refusing everything; case D is what
  stops that. Demonstrated red by disabling the floor it tests:

        # `if with_ids < 2:` -> `if with_ids < 0:` in cmd_ids
        ids-floor  A no ids anywhere          FAIL  expected 2, got 0
        ids-floor  B collision outside queue  FAIL  expected 2, got 0
        ids-floor  C real collision           ok    expected 1, got 1
        ids-floor  D one id, two refs, ok     ok    expected 0, got 0
        IDS-FLOOR FAIL                                                  real exit 1
        # restored
        IDS-FLOOR ok (4 cases)                                          real exit 0

  **F4 — nothing ran the detector; `ops/agent-preflight` now does.** It was a detector with no caller, in a
  repo whose stated failure mode is a command people stop running. Red demo, on live refs: a second
  `T-0105-an-entirely-different-piece-of-work.md` committed onto a throwaway
  `refs/remotes/origin/zz-fixer-t0105-reddemo` with `commit-tree` (nothing pushed, ref deleted in a trap):

        ### RED
        ids          COLLISION - run ops/queue-ids
                       T-0105
                         a-duplicate-task-id-is-invisible-until-the-merge   main, task/T-0021, ... (+9 more)
                         an-entirely-different-piece-of-work                zz-fixer-t0105-reddemo
        PREFLIGHT FAIL                              agent-preflight real exit 1   (queue-ids real exit 1)
        ### RESTORED
        ids          IDS OK (114 ids on 80 of 80 refs; no id names two different tasks)
        PREFLIGHT OK                                agent-preflight real exit 0   (queue-ids real exit 0)

  Exit 1 (a real collision) fails preflight; **exit 2 (the scan refused) is printed and does NOT fail it** —
  a fresh clone or a CI checkout has one ref, and a preflight that goes red there is a preflight people
  stop running. The cost is real and worth stating: `ops/queue-ids` alone measures 3.9–6.2 s (one `ls-tree`
  per remote ref, 82 of them; `ops/queue-check` next to it is 1.2 s, which is why this stays off the
  per-commit path), and preflight went from 14.4 s to 23.3 s back-to-back on this box. Deduping
  by the `queue/` tree oid would save ~6% (77 distinct trees across 82 refs), so it was not worth the
  complexity.

  **F2 — the stated rationale described a cost the code never paid.** `cmd_ids` reads `refs/remotes`, a
  cache, and never fetches; the docstring claimed the network was why it stays out of `queue-check`. The
  docstring now says what is true (per-ref `ls-tree` over every remote ref, ~6 s vs queue-check's ~0.4 s,
  which is why it is not on the per-commit path) and every result line now carries its own staleness:

        IDS OK (114 ids on 79 of 79 refs; no id names two different tasks)
          refs/remotes read as they stand: this command never fetches, so this answer is as old as this
          worktree's last fetch (2.8h ago). `git fetch --all` first if a push since then matters.

  FETCH_HEAD's mtime is a LOWER bound (a fetch from a sibling worktree updates the shared refs without
  touching this file), so the age can read older than the refs are. That is the safe direction here.
  No `--fetch` flag: `_opts` refuses a valueless option by design, and widening the parser every command
  shares is not a change this finding needs.

  **F3 — `ids` was missing from the only usage text a reader gets.** Fixed structurally rather than by
  typing the missing line: the `commands:` block is now BUILT from `OPTS` (`_usage_all()`), the same table
  the dispatch reads, so registration and documentation cannot drift again.

        # before                              # after
        python ops/lib/queue.py bogus         python ops/lib/queue.py bogus
        | grep -c 'queue.py ids'  ->  0       | grep -c 'queue.py ids'  ->  1   (real exit 2 both)

  **F6 — `acceptance:` was empty and is now four commands with their expected exits**, including both reds
  above, so this does not have to be reconstructed from prose a second time.

  **F5 — confirmed, not fixed, still red.** `bash ops/test` -> real exit 1,
  `FAIL: services/api exists but vitest produced no report`, and no `TESTS linux=N/F ios=N/F` line. Run
  again on `main` at e9e00cf: identical message, real exit 1. Pre-existing and environmental; this task
  touches no JS and no test runner, and fixing it belongs to a task that declares `services/api`.

  **`touches:` was widened deliberately** from `[ops/lib/queue.py, ops/queue-ids]` to add
  `ops/lib/check-ids-floor` (the new fixture check) and `ops/agent-preflight` (F4's home). Both are named
  in the findings this pass exists to close; nothing else was staged. `ops/lib/check-ids-floor` is
  committed 100755 (`git update-index --chmod=+x`) and `bash ops/lib/check-exec-bits` -> P-OPS-01: 28
  files, 15 required present, all modes correct, exit 0.

  **verify: on this branch after the fix** — `ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0
  failed=0 tier=linux`, real exit 0. `ops/test` -> real exit 1 (F5, identical on main). Also green:
  `ops/queue-check` -> QUEUE OK (98 tasks) exit 0, `ops/queue-ids` exit 0, `ops/lib/check-ids-floor` exit 0,
  `ops/agent-preflight` -> PREFLIGHT OK exit 0.

- 2026-09-08 — **second review of PR #66, agent/reviewer-final-pr66 (owner is agent/claude-opus-5). PASS,
  transitioned to `queue/done/`.** Reviewed on `task/T-0105` @ 59d917e, worktree `.worktrees/T-0105`,
  scratch under `.artifacts/rvw-final-pr66/`. Every prior finding was re-closed by RUNNING what
  demonstrated it, not by reading the diff. Exit codes taken as `<cmd> >file 2>&1; echo $?`, never after a
  pipe.

  **verify: and acceptance:, every exit code**

        bash ops/check-pins            0   PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        bash ops/test                  1   FAIL: services/api exists but vitest produced no report   (F5)
        bash ops/queue-check           0   QUEUE OK (98 tasks)
        bash ops/lib/check-ids-floor   0   IDS-FLOOR ok (4 cases)                     acceptance 1
        RED: with_ids < 2 -> < 0       1   A FAIL expected 2 got 0; B FAIL expected 2 got 0   acceptance 2
        restored                       0   IDS-FLOOR ok (4 cases)
        bash ops/queue-ids             1   IDS FAIL: T-0117 - see below               acceptance 3, NOT 0
        bash ops/agent-preflight       1   ids COLLISION -> PREFLIGHT FAIL            acceptance 4
        python ops/lib/queue.py bogus  2   `commands:` block lists `queue.py ids`     acceptance 5

  **acceptance 3 and 4 do not reproduce, and the reason is the deliverable working.** `ops/queue-ids` is
  exit 1 on live refs today because there is a FOURTH real collision, which this command found:

        T-0117
          scenickit-routescore-is-this-route-actually-pret   main, task/T-0117, task/T-0118 (+1 more)
          the-review-sheet-captures-no-verdict-and-seeds-f   task/T-0108

  Confirmed by hand with `git ls-tree -r --name-only <ref> queue/` on all four refs. `task/T-0108` committed
  its `T-0117` at 2026-09-08 07:15:06 -0700, **68 seconds after** this task's 59d917e at 07:13:58 — so the
  fixer's `exit 0` was true when written and the queue moved under it. The detector is right and the queue
  is wrong; the repair is to renumber the later one, which belongs to `task/T-0108`, not to this task.
  Recorded rather than fixed: testers find and do not fix.

  **F1 (was blocking) — closed, and proved by disabling it.** The floor is on `with_ids`, refs that actually
  yielded an id, and `ops/lib/check-ids-floor` pins it at exactly 2: A (no ids anywhere) forces >= 1,
  B (collision with one side outside `queue/`) forces >= 2, D (healthy pair) forbids > 2. Setting
  `if with_ids < 2:` to `< 0` reproduced the reviewer's original F1 exactly — A and B fall back to exit 0,
  the confident green over a tree with a live duplicate in it. Restored, `diff` against a pre-run backup
  clean, `git status` clean.

  **F1's guard is not vacuous in either direction — mutation-tested, which the fixer did not do.** I broke
  the DETECTOR (not the floor it tests) two ways and checked the fixture noticed:

        M1  bad = {}                                  never report   -> C FAIL expected 1, got 0   floor exit 1
            same mutation on live refs                               -> IDS OK (117 ids on 85 of 85 refs), exit 0
        M2  bad keyed on ref count, slug ignored      always report  -> D FAIL expected 0, got 1   floor exit 1

  M1 is the important one: with the discriminator gutted the live command printed a clean bill of health
  over the real T-0117 collision, and `check-ids-floor` is the only thing in the tree that caught it. Case D
  is what stops the floor being made green by refusing everything, and M2 shows it earns its place.

  **My own attack, which the author did not run: the queue state directory.** Task files move
  backlog -> claimed -> review -> done constantly here (61 claimed right now), and the author's healthy case D
  puts the SAME path on both refs, so it never proves the state directory is excluded from the slug. If it
  leaked in, every ordinary move would read as a collision and the command would be worthless in this repo.
  Three standalone repos, driven through the real `ops/queue-ids` wrapper
  (`.artifacts/rvw-final-pr66/statedir.sh`):

        E  same id, same slug, queue/backlog on one ref and queue/done on the other   expected 0, got 0
        F  a real collision that ALSO crosses state directories                       expected 1, got 1
        G  one ref carrying the same id+slug under two state dirs (a stale copy)      expected 0, got 0
        STATEDIR ok (3 cases)                                                         real exit 0

  Clean: the regex anchors on the last `/T-NNNN-` so the state directory never reaches the slug, and a
  collision is still found when both sides move.

  **F2 — closed.** The docstring no longer claims a network cost the code never paid, and every result line
  carries its own staleness: `refs/remotes read as they stand: this command never fetches, so this answer is
  as old as this worktree's last fetch (4.8h ago).` Present on the OK line, the FAIL line, and observed on
  both during this review.

  **F3 — closed structurally, not by typing the missing line.** `python ops/lib/queue.py bogus` prints a
  `commands:` block built from `OPTS`; `grep -c 'queue.py ids'` is 1 where it was 0, real exit 2. The
  `_usage`/`_invocation`/`_usage_all` refactor did not regress argument hygiene — `ids extra-operand`,
  `ids --nope`, `ids --nope V`, `claim` with no operand and `check --x` all still refuse with exit 2 and the
  right message.

  **F4 — closed, and I proved BOTH preflight branches, not just the red one.** `grep -rn queue-ids` now hits
  `ops/agent-preflight`. Exit 1 -> `ids COLLISION` + `PREFLIGHT FAIL`, observed live on the T-0117 pair. For
  the exit-2 branch, which had only been asserted in prose, I forced a refused scan (`with_ids < 999`):

        bash ops/queue-ids        2   IDS REFUSED: 117 task id(s) found on 85 of 85 ref(s) scanned.
        bash ops/agent-preflight  0   ids  not checked (IDS REFUSED: ...)   PREFLIGHT OK

  That also isolates the cause: preflight is red today ONLY because of the real collision — every other
  line in it is green. Restored, `git status` clean.

  **F5 — confirmed, still red, still not attributable.** `bash ops/test` -> real exit 1,
  `FAIL: services/api exists but vitest produced no report`, no `TESTS linux=N/F ios=N/F` line. I checked
  the attribution rather than taking it on trust: `git diff --stat origin/main HEAD -- ops/test services/api`
  shows this branch is BEHIND main (main added `services/api/test/quota.test.ts` and `upstream.test.ts` at
  16a49a0 on 2026-09-07 and extended `ops/test`); no commit in `origin/main..HEAD` deletes them, and none of
  this task's four commits touches JS or a test runner. Environmental, pre-existing.

  **F6 — closed.** `acceptance:` is five lines naming commands and expected exits, including both reds.

  **Mechanical.** Commits touch exactly `ops/lib/queue.py`, `ops/queue-ids`, `ops/lib/check-ids-floor`,
  `ops/agent-preflight` and this task file — all inside `touches:`; `exclusive: []` and none of them is a
  serial-only file; no `git add -A`; no secrets. `git ls-files -s`: `ops/queue-ids` and
  `ops/lib/check-ids-floor` are 100755 (both are bash, so the ops/lib `.py`-is-data carve-out does not
  apply), `ops/agent-preflight` 100755, `ops/lib/queue.py` mode unchanged; `ops/check-pins` P-OPS-01 green.

  **Non-blocking, recorded for whoever picks them up — none of these changed the verdict:**

  1. **`ops/lib/check-ids-floor` has no gate.** Nothing runs it: not `ops/test`, not `ops/sane`, not CI, not
     a pin (`pins_affected: []`). F4 was "nothing runs the detector"; the fix wired the detector into
     preflight and left its guard ungated one level up. [[T-0090]] is already filed for exactly this class
     (`check-brief-required` and `check-lock-lifecycle` are ungated too), so this belongs there rather than
     in a new task. It is at least named in `acceptance:`, so a reviewer re-runs it by hand.
  2. **`IDS-FLOOR ok (4 cases)` is a hard-coded literal**, not a count of cases that ran — the same
     "state the population you examined" discipline the green `IDS OK (N ids on M of M refs)` line was fixed
     to follow, missing thirty lines away in the check that guards it. Not reachable today (the four
     `expect` calls are straight-line), so a note, not a finding.
  3. **`if scanned < 2` is now dead.** `with_ids <= scanned`, so `with_ids < 2` subsumes it; no fixture case
     distinguishes them. Harmless — it produces a clearer message for the one-ref case — but it is untested.
  4. **A collision is still invisible if a task file lives outside `queue/` while other refs are healthy.**
     Fixture B only refuses because it drove `with_ids` to 1; with 80 healthy refs alongside, the same shape
     passes. Inherent to scanning `queue/`, out of scope for this task.
  5. **`ops/lib/queue.py` is 1244 lines** against CLAUDE.md's 300-line cap. P-SRC-02 scopes its assertion to
     `Sources/`+`Tests/` `.swift`, so nothing enforces it here. Pre-existing and inherited through the stack
     (372 on `origin/main`, 1078 before this task's commits); this task added 166.

  **Verdict: PASS.** Every prior finding closed and verified by execution; my own attacks (two detector
  mutations, three state-directory cases, the preflight exit-2 branch) found nothing disqualifying. Moved
  `queue/claimed/` -> `queue/done/` with `git mv`, `state: done`, `reviewer: agent/reviewer-final-pr66`
  (owner is `agent/claude-opus-5`, so P-PROC-01's inequality holds). No code in this PR was modified by this
  review: every mutation above was reverted with `git checkout --` and `git status` was clean before the
  transition.
