---
id: T-0079
title: the MIN_ ratchet constants have no commit-msg protection, unlike the test floors
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:59:05Z
lease_expires_at: 2026-09-08T08:59:05Z
worktree: wt/T-0079
branch: task/T-0079
exclusive: []
touches: [.githooks/commit-msg]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`.githooks/commit-msg` refuses a commit that LOWERS any `pins/floor_*.txt` without a `floor-lower: <reason>`
line. Nothing protects the other ratchets, which are ordinary module constants:

    ops/lib/pins.py            MIN_PINS, MIN_RAN, MIN_RAN_SOURCE_ONLY, REQUIRED, REQUIRED_RAN
    ops/lib/check-exec-bits    MIN_FILES, REQUIRED
    ops/lib/check-line-cap     MIN_FILES, MIN_CAPPED, EXEMPT

`MIN_RAN = 9` -> `MIN_RAN = 6` is a one-line edit, no justification required, nothing red - and after
[[T-0072]] re-ratcheted the floors to today's counts, that one line restores exactly the headroom T-0072 was
filed to remove. **A ratchet whose notch can be moved silently is a suggestion again, one commit later.**

Noted by the T-0072 fix agent, which could not fix it: `.githooks/commit-msg` was outside that task's
`touches:`.

The asymmetry is the whole point. Raising a floor is free. Lowering one is sometimes correct - a pin is
genuinely retired, a suite is genuinely split - and the hook does not forbid it, it forbids doing it without
saying why. The constants deserve the same treatment and currently get none.

- Extend `.githooks/commit-msg` to the constants. They are integers on a line matching a known name in a known
  file, so the same `old > new` comparison works; parse them out of the staged blob the way the floors are
  parsed out of theirs.
- Removing an entry from `REQUIRED`, `REQUIRED_RAN` or `EXEMPT` is a lowering too, and is the more likely
  evasion: it needs no number to change. Count the entries.
- Anchor on the identifier, never on a comment - the names are the anchor and they are stable.
- Consider whether this wants to be a check rather than a hook. A hook is bypassable with `--no-verify` and is
  not run in CI; `ops/check-pins` runs on every push. The honest answer may be both, and the reason belongs in
  the file.
- Demonstrate red for each: lower one constant per file with no justification and show the refusal, then with
  a justification and show it accepted, then remove one `REQUIRED` entry and show that counted as a lowering.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the T-0072 fix agent's report, which identified it while
  re-ratcheting the floors it had just been asked to tighten.
- 2026-09-08T02:59:05Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:59:05Z

- 2026-09-08 agent/claude-opus-5 — the ratchet constants now need a reason, and one of my own fixes was
  defeated by its adjacent form before it was tightened.

  **Where the demonstrations were run, and why not on this branch.** The constants the brief names do not all
  exist on `main` or on `task/T-0079`: `ops/lib/pins.py`'s `MIN_PINS/MIN_RAN/REQUIRED*` live on
  `task/T-0066`, and `check-line-cap`'s `MIN_CAPPED/EXEMPT` on `task/T-0058`. Measured, not assumed:

        for b in $(git branch --format=%(refname:short)); do
          c=$(git show "$b:ops/lib/pins.py" | grep -c MIN_RAN); [ "$c" != 0 ] && echo "$b: $c"; done
        task/T-0066: MIN_RAN x4
        task/T-0077: MIN_RAN x4

  So every red/green below is a REAL `git commit` in a throwaway clone under the gitignored `.artifacts/`,
  on branch `demo` (= this branch) and `demo66` (= this branch merged with `origin/task/T-0066`, which has
  pins.py's constants). A throwaway branch name also switches off `pre-commit`'s `touches:` enforcement, so
  the commit reaches `commit-msg` and the refusal that gets recorded is this hook's, not the other one's -
  a demonstration that dies in `pre-commit` proves nothing about the guard under test. `git status --short`
  was clean at every reset; no `git reset --hard` was used anywhere (T-0071's log says why).

  **Anchoring.** Bindings are found by identifier only: `^` optional declarator keywords, then a name matching
  `(MIN|MAX|REQUIRED|EXEMPT)[A-Z0-9_]*`, then `=` (or `: type =`). Comments are stripped before parsing, so no
  guard rests on one. Files are found from the staged path list, never from a hard-coded list of filenames -
  the failure T-0071 had just removed from the floors half.

  --------------------------------------------------------------------------------------------------
  **ROUTE A — lower a numeric constant (`ops/lib/check-exec-bits` `MIN_FILES` 17 -> 10).**

        RED    sed -i s/^MIN_FILES=17$/MIN_FILES=10/ ops/lib/check-exec-bits
               git add ops/lib/check-exec-bits && git commit -m "tidy up check-exec-bits"
               [demo 66f7664] tidy up check-exec-bits
                1 file changed, 1 insertion(+), 1 deletion(-)
               --- exit: 0 ---            commit ACCEPTED, nothing said

        GREEN  identical two commands, fixed hook
               commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line in the commit body:
                 ops/lib/check-exec-bits: MIN_FILES 17 -> 10
               --- exit: 1 ---            HEAD unchanged
               and with `-m "ratchet-lower: demonstrating the guard accepts a stated reason"`:
               commit-msg: ratchet lowered (justified: ratchet-lower: demonstrating ...)  --- exit: 0 ---

        SELF-ATTACK, six adjacent forms, all executed:
          A1  the same value one notation over, `MIN_FILES=0x0a`
              -> MIN_FILES changed shape (num -> opaque) - the old value can no longer be compared   exit 1
          A2  leave 17 alone and REBIND it lower down the file (`sed -i 14a MIN_FILES=10`)
              -> MIN_FILES 17 -> 10   exit 1     (the weakest binding in a file wins, not the first)
          A3  comment the binding out: `#MIN_FILES=17`
              -> MIN_FILES is gone - no binding of that name at ops/lib/check-exec-bits   exit 1
          A4  one directory over: `git mv ops/lib/check-exec-bits ops/lib/check-modes` AND lower it
              -> MIN_FILES 17 -> 10 (followed the rename to ops/lib/check-modes)   exit 1
          A5  CONTROL, the same rename WITHOUT lowering - must not cry wolf
              -> rename ops/lib/{check-exec-bits => check-modes} (100%)   exit 0, silent
          A6  leave the constant and invert the TEST that uses it: `-lt` -> `-gt`
              -> [demo ce6bd57] check-exec-bits: flip   exit 0   **NOT CAUGHT** - see "still open" below

  --------------------------------------------------------------------------------------------------
  **ROUTE B — lower `ops/lib/check-line-cap` `MIN_FILES` 5 -> 2.**

        RED    [demo 0bf87f3] check-line-cap: relax   --- exit: 0 ---   ACCEPTED
        GREEN  commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line ...
                 ops/lib/check-line-cap: MIN_FILES 5 -> 2                  --- exit: 1 ---

        SELF-ATTACK B1 — **this one broke my own fix, and is why the fix changed.** Rename the CONSTANT and
        lower it in one edit: `MIN_FILES` -> `MIN_FILE_COUNT`, `=5` -> `=2`. Against the first version of the
        fix:

               17:MIN_FILE_COUNT=2
               [demo e1bbbeb] check-line-cap: rename the constant
               --- exit: 0 ---            ACCEPTED

        Cause, found by reading my own comparison rather than guessing: when a name left its file I rescued it
        with "does any file still bind that name at least this strongly?" - and `check-exec-bits` binds an
        UNRELATED `MIN_FILES=17`, which is >= 5, so the disappearance read as a move. Two constants that share
        a name in different files are not the same ratchet. Fixed by following moves through git's own rename
        detection (`git diff -M --name-status --diff-filter=R`, fed to the comparator as `@rename` records)
        and deleting the name-global rescue entirely. Re-run, identical command:

               commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line in the commit body:
                 ops/lib/check-line-cap: MIN_FILES is gone - no binding of that name at
                 ops/lib/check-line-cap, so nothing constrains it any more          --- exit: 1 ---

        The cost of that tightening is stated in the hook: moving a ratchet to a genuinely new home without
        renaming the file is now reported and needs one `ratchet-lower:` line. That is the safe direction.

  --------------------------------------------------------------------------------------------------
  **ROUTE C — remove an entry from `REQUIRED` (`ops/queue-next`, the entry T-0019 had to add by hand).**

        RED    [demo 34747cb] check-exec-bits: shorten REQUIRED   --- exit: 0 ---   ACCEPTED
        GREEN  commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line in the commit body:
                 ops/lib/check-exec-bits: REQUIRED lost ops/queue-next             --- exit: 1 ---

        SELF-ATTACK:
          C1  **cardinality is not identity** - swap `ops/queue-next` for a DUPLICATE of `ops/claim`, so the
              entry count is unchanged. The brief asked for a count; a count would have passed this.
              -> REQUIRED lost ops/queue-next   exit 1   (entries are compared as a set, not counted)
          C2  reflow the whole array onto one line while dropping the entry, so the diff looks like a format
              change -> REQUIRED lost ops/queue-next   exit 1
          C3  a different entry point - delete the file instead of editing it (`git rm`)
              -> MIN_FILES is gone ... / REQUIRED is gone ...   exit 1

  --------------------------------------------------------------------------------------------------
  **ROUTE D — the constants the brief actually names, on `demo66` where they exist.**

        RED    sed -i s/^MIN_RAN = 9$/MIN_RAN = 6/ ops/lib/pins.py ; git add ; git commit -m "pins: relax"
               [demo66 0ff1525] pins: relax MIN_RAN   --- exit: 0 ---   ACCEPTED
        RED2   REQUIRED_RAN loses "P-OPS-01"
               [demo66 f464877] pins: trim REQUIRED_RAN   --- exit: 0 ---   ACCEPTED

        GREEN  ops/lib/pins.py: MIN_RAN 9 -> 6                                     --- exit: 1 ---
               with `-m "ratchet-lower: P-SAFE-05 was retired, so nine pins can no longer run"` -> exit 0
        GREEN2 ops/lib/pins.py: REQUIRED_RAN lost P-OPS-01                          --- exit: 1 ---

        SELF-ATTACK:
          D3  the same value in a different TYPE: `MIN_RAN: int = 6`  -> MIN_RAN 9 -> 6            exit 1
          D4  the same value at a different SCALE: `MIN_RAN = 6.0`    -> MIN_RAN 9 -> 6.0          exit 1
          D5  a different ENTRY POINT: delete the line from pins.py and put `MIN_RAN = 6` in a brand-new
              `ops/lib/thresholds.py` -> MIN_RAN is gone - no binding of that name at ops/lib/pins.py exit 1
          D6  duplicate swap inside `REQUIRED_RAN` (`"P-OPS-01"` -> a second `"P-SRC-01"`, count unchanged)
              -> REQUIRED_RAN lost P-OPS-01                                                        exit 1

  --------------------------------------------------------------------------------------------------
  **ROUTE MAX — the family the brief did not name, found while surveying what the pattern would cover.**
  `git grep` for binding-shaped lines turned up `MAX_SQL_LENGTH = 4000` in BOTH `ops/lib/ro_grammar.py` and
  `services/api/src/ro.ts`. That is a ratchet whose weak direction is UP, and it guards the read-only SQL
  gate. It was unprotected in exactly the same way, so it is covered.

        RED    [demo 1aa6055] ro_grammar: allow longer statements  (4000 -> 400000)  --- exit: 0 ---
        GREEN  ops/lib/ro_grammar.py: MAX_SQL_LENGTH 4000 -> 400000                  --- exit: 1 ---
        SELF-ATTACK MAX1  `4_000_000`, a legal Python literal my integer regex does not accept
                          -> MAX_SQL_LENGTH changed shape (num -> opaque)             exit 1
        SELF-ATTACK MAX2  the TS twin one directory over, services/api/src/ro.ts 4000 -> 400000
                          -> services/api/src/ro.ts: MAX_SQL_LENGTH 4000 -> 400000    exit 1

  --------------------------------------------------------------------------------------------------
  **ROUTE E — the entry points a commit-msg hook does not see. One closed, one NOT.**

        E4  `git merge` DOES run commit-msg here (git 2.54.0.windows.1), measured, not assumed:
              git merge --no-ff --no-edit evil     # evil carries MIN_RAN 9 -> 6
              commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line in the commit body:
                ops/lib/pins.py: MIN_RAN 9 -> 6
              Not committing merge; use 'git commit' to complete the merge.     --- merge exit: 1 ---
            and HEAD:ops/lib/pins.py still reads `MIN_RAN = 9`. Closed.

        F3  partial commit - lower it in the WORKTREE only, leave the index clean, and name the path:
              git status --short          ->  " M ops/lib/check-exec-bits"
              git diff --cached --name-only ->  (empty)
              git commit ops/lib/check-exec-bits -m "check-exec-bits: partial commit"
              commit-msg: ... ops/lib/check-exec-bits: MIN_FILES 17 -> 10          --- exit: 1 ---
            git points the hook at its temporary index, so `git diff --cached` sees the partial commit.
            Closed - and worth recording, because it was not obvious and I expected it to leak.

        E1  `git commit --no-verify`  -> **NOT CLOSED**, and cannot be by anything in this file:
              [demo66 fce75d8] pins: relax MIN_RAN
               1 file changed, 1 insertion(+), 1 deletion(-)
              --- exit: 0 ---

            The durable half is the new `--audit <base>` mode - the same comparison between two refs, with the
            justification looked for in every commit message in the range. Demonstrated red then green over
            exactly the commit `--no-verify` slipped through:

              bash .githooks/commit-msg --audit $BASE
              commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line in the commit body:
                ops/lib/pins.py: MIN_RAN 9 -> 6                              --- audit exit: 1 ---
              git commit --amend --no-verify -m "pins: relax MIN_RAN" -m "ratchet-lower: P-SAFE-05 retired ..."
              bash .githooks/commit-msg --audit $BASE
              commit-msg: ratchet lowered (justified: ratchet-lower: P-SAFE-05 retired, ...)
                                                                             --- audit exit: 0 ---

            **The mode is not wired into CI**, because that needs a pin and `pins/PINS.yaml` is outside this
            task's `touches:`. Until a pin runs `bash .githooks/commit-msg --audit origin/main`, `--no-verify`
            still lowers any of these constants in one line. Filed as a follow-up rather than claimed as done.

  --------------------------------------------------------------------------------------------------
  **REGRESSION — the floors half, which this task rewrote the hook around.** Rerun of T-0071's own
  demonstration, on the current file:

        F1  printf 10 > pins/floor_linux_swift.txt ; git add ; git commit -m "lower a floor with no reason"
            commit-msg: pins/floor_linux_swift.txt lowered 16 -> 10 without a 'floor-lower: <reason>' line
            --- exit: 1 ---
        F2  identical staged change with `-m "floor-lower: ..."`
            commit-msg: pins/floor_linux_swift.txt lowered 16 -> 10 (justified: floor-lower: ...)
            --- exit: 0 ---

  The floors loop is byte-for-byte the T-0071 logic; the only change is that it now sets `fail=1` instead of
  exiting immediately, so a commit that lowers a floor AND a constant reports both.

  --------------------------------------------------------------------------------------------------
  **COST, measured, because a slow hook is a hook someone turns off.** The first version scanned the whole
  tree on both sides: `time bash .githooks/commit-msg /tmp/msg.txt` -> `real 0m10.034s` on a clean tree, on
  this Windows box. The scan is now restricted to the paths the commit actually changes (`--no-renames`, so a
  rename contributes both of its names) - a path the commit does not touch has the same blob in HEAD and in
  the index, so it cannot have moved its own ratchet. Same command after: `real 0m1.790s`. Every red, green
  and self-attack above was then RE-RUN end to end against the narrowed version and is quoted from that run.

  **STILL OPEN, stated plainly.**
  1. `git commit --no-verify` (E1 above). Open until `--audit` is wired into `ops/check-pins`.
  2. A6: the guard watches the ratchet's VALUE, not the code that reads it. `if [[ "$n" -lt "$MIN_FILES" ]]`
     -> `-gt` leaves `MIN_FILES=17` untouched and disables the check completely, and commits clean. No
     value-comparison guard can see that; it needs the check's own behaviour to be tested (the `check-pins`
     self-test class). Filed.
  3. The guard cannot tell a program from a document: a markdown file containing `MIN_X = 3` at the start of a
     line registers a ratchet. Direction is safe (it can only add a demand for a reason, never remove one),
     but it means transcripts in queue files must not paste a bare binding at column 0. The lines in THIS log
     that would otherwise parse are prefixed, and that is the reason.

  **Gates, in this worktree, last line of each:**

        bash ops/queue-check                 QUEUE OK (76 tasks)                                    exit 0
        bash ops/check-pins                  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        bash ops/check-pins --source-only    PINS ok=3 skipped=8 pending=1 expired=0 failed=0 ... source-only
        PYTHON=$(command -v python) bash ops/test
                                             TESTS linux=50/50 (swift=16/16 ts=34/34 py=-/0) ios=skipped
                                             failed=0 skipped=0   OK
        git ls-files -s .githooks            100755 .githooks/commit-msg   (mode unchanged)

  `ops/test` needed `npm ci` in `services/api` first - without it the run ends `FAIL: services/api exists but
  vitest produced no report`, which blames services/api for a missing install. Same shape as the interpreter
  bug T-0071 found and T-0076 owns.
