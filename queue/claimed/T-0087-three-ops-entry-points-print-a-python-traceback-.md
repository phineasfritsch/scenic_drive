---
id: T-0087
title: three ops entry points print a Python traceback instead of a usage line
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T04:05:00Z
lease_expires_at: 2026-09-08T10:05:00Z
worktree: wt/T-0087
branch: task/T-0087
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Three small, verified findings from the round-three verification of [[T-0077]], grouped because they are the
same kind of thing: an `ops/*` entry point behaving unlike every other one.

**1. A raw traceback instead of a usage line.** `ops/claim`, `ops/lock` and `ops/new-task` given no arguments
print

    IndexError: list index out of range

from `cmd_new`. Verified pre-existing rather than a regression — `git show HEAD~1:ops/new-task` reproduces it
identically. Every other `ops/*` entry point prints a usage line and exits 2, and `ops/merge` and
`ops/merge-rehearse` both refuse unknown arguments explicitly. A traceback tells an agent the tool is broken
when the tool is fine and the call was wrong.

**2. `check-exec-bits` and `check-line-cap` report GREEN about a foreign repository** when invoked directly
from inside one:

    P-OPS-01: 19 files, 15 required present, all modes correct    EXIT=0

Their vacuity guards (`MIN_FILES=17`, `MIN_FILES=5`) hide this on a thin fake repo — the fake has to be stocked
past the floor before it shows, which is why nobody hit it. That is the [[T-0086]] class in two more files, and
the fix belongs with that task rather than here; recorded so it is not lost. Ownership sits with T-0036 and
with the T-0035/T-0037/T-0043/T-0058/T-0062 chain.

**3. An adversarial fixture for `ops/test` cannot live inside the worktree.** SwiftPM walks UP the directory
tree looking for `Package.swift`, so a synthetic repo built under `.artifacts/` made `swift test` find and run
the **real** package's 16 tests, silently. Any future fixture that needs a fake repo for `ops/test` must be
built outside the worktree — and note this interacts with the `/tmp` rule in CLAUDE.md, since `/tmp` is not one
directory here. Worth a line in CLAUDE.md once somebody needs it.

Also recorded from the same run, and NOT a defect: `services/etl` does not exist on `main`, so [[T-0076]]'s
symptom is unreproducible there — the ETL tier is skipped entirely. A reviewer verifying T-0076 must
materialise the tier (a `pyproject.toml` and one test) or they will see a green `ops/test` and wrongly conclude
the defect is absent.

- Item 1 is the actual work here and is small: usage line, exit 2, matching the other entry points.
- Items 2 and 3 are recorded for the tasks that own them; do not fix them under this id without saying so.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-three verification of T-0077. All three were executed
  by an agent that did not write the fix.
- 2026-09-08T04:05:00Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:05:00Z
- 2026-09-08 agent/claude-opus-5, round five. Item 1 of this brief was already fixed on this branch at
  086272f/0be7589 for the OPERAND of `new`/`claim`/`lock`/`review`; measured first, before touching anything:

      $ for c in claim lock new-task; do bash ops/$c; echo "EXIT=$?"; done
      usage: queue.py claim <id> [options]
      refused '': the operand comes first and may not be blank.
      EXIT=2
      usage: queue.py lock <id> [options]
      refused '': the operand comes first and may not be blank.
      EXIT=2
      usage: queue.py new "<title>" [options]
      refused '': the operand comes first and may not be blank.
      EXIT=2

  So the named symptom is closed. The brief's actual instruction - check EVERY subcommand in the dispatch,
  not only the three named - is not, and neither is [[T-0084]] in the same file. Both are below.

### ROUTE 1 - every subcommand refuses a wrong command line, not only the three named

RED, executed at 69be364 (fixture: a repo-shaped tree under `.artifacts/fix`, so `ROOT = parents[2]` lands
there and the real `queue/` is never touched):

    === RED 1a: check/sweep/next accept any junk silently ===
    --- queue.py check --owner agent/mallory T-9999 --nonsense ---
    QUEUE CHECK FAIL
     - only 1 task(s) visible, floor is 40 - ...
    EXIT=1
    --- queue.py sweep --owner agent/mallory T-9999 --nonsense ---
    SWEEP done (0 moved, 0 kept)
    EXIT=0
    --- queue.py next --owner agent/mallory T-9999 --nonsense ---
    (no unblocked ready task)
    EXIT=0

    === RED 1b: a misspelled flag is silently ignored ===
    $ queue.py new "flag typo red" --touchez ops/lib/queue.py --exclusiv Package.swift
    queue/backlog/T-0001-flag-typo-red.md
    EXIT=0
    11:exclusive: []
    12:touches: []

    === RED 1c: a flag eats the NEXT FLAG as its value ===
    $ queue.py new "flag eats flag" --touches --state done
    queue/backlog/T-0001-flag-eats-flag.md
    EXIT=0
    4:state: backlog
    12:touches: [--state]

    === RED 1d: stray positional silently dropped ===
    $ queue.py new "second title here" "AND ANOTHER TITLE"
    queue/backlog/T-0002-second-title-here.md
    EXIT=0

THE FIX (f5b0e70, `ops/lib/queue.py`). Guarding the operand and then handing the rest to a parser that
validates nothing just moves the silence one word to the right. `_opts` now takes the subcommand and
returns `(options, why)`; `OPTS` is the per-command allowlist and `COMMANDS = tuple(OPTS)` so the two
cannot drift; `_usage` is built from `OPTS` so a usage line cannot describe a command that no longer
exists. Unknown flag, missing value, a value that is really the next flag, and a stray word are each
refused with the usage line and exit 2. All of it is decided in `main()` before any `cmd_*` runs, so a
refusal cannot half-write a task file.

GREEN, identical commands:

    === R1a: check/sweep/next given arguments ===
    --- queue.py check --owner agent/mallory T-9999 --nonsense ---
    usage: queue.py check
    refused: --owner is not an option of `check` (it takes none).
    EXIT=2
    --- queue.py sweep --owner agent/mallory T-9999 --nonsense ---
    usage: queue.py sweep
    refused: --owner is not an option of `sweep` (it takes none).
    EXIT=2
    --- queue.py next --owner agent/mallory T-9999 --nonsense ---
    usage: queue.py next
    refused: --owner is not an option of `next` (it takes none).
    EXIT=2

    === R1b: queue.py new "flag typo red" --touchez ... --exclusiv ... ===
    usage: queue.py new "<title>" [--depends V] [--exclusive V] [--pins V] [--state V] [--touches V]
    refused: --touchez is not an option of `new` (--depends, --exclusive, --pins, --state, --touches).
    EXIT=2

    === R1c: queue.py new "flag eats flag" --touches --state done ===
    usage: queue.py new "<title>" [--depends V] [--exclusive V] [--pins V] [--state V] [--touches V]
    refused: --touches was given '--state', which is another option, not a value.
    EXIT=2

    === R1d: queue.py new "second title here" "AND ANOTHER TITLE" ===
    usage: queue.py new "<title>" [--depends V] [--exclusive V] [--pins V] [--state V] [--touches V]
    refused: 'AND ANOTHER TITLE' is not an option. `new` takes one operand ("<title>") then options, and a
    stray word was ignored.
    EXIT=2

    === nothing was written by any refusal ===
        (blank = none)

SELF-ATTACK on that fix, executed - one name over, one mechanism over, one type over, one entry point over.

  (a) one NAME over: an option that is valid for a DIFFERENT subcommand. Refused, four for four:
      `lock T-0001 --hours 5` -> "--hours is not an option of `lock` (--owner)."
      `review T-0001 --owner agent/x`, `new "n" --session abc`, `claim T-0001 --reviewer agent/bob` alike.

  (b) one TYPE over: an EN DASH where `--` was meant, and a non-ASCII option name. Both refused:
      `new "endash" ––touches a`   -> "'––touches' is not an option. `new` takes one operand ..."
      `new "unicode name" --touchés a` -> "--touchés is not an option of `new` (...)."

  (c) one ENTRY POINT over: through the bash wrappers rather than queue.py, with MSYS_NO_PATHCONV=1 and
      values MSYS rewrites (`/bin/true`, `ref:path`). All refused, exit 2, and `git status --porcelain --
      queue/` was empty afterwards - the real queue never moved.

  (d) one MECHANISM over: the `--name=value` spelling. **THIS ONE WORKED**, and then one SCALE down from
      it worked harder. `--name=` supplies an EMPTY value, and the `=` branch skipped the dash guard:

          $ queue.py claim T-0500 --owner=
          claimed T-0500 -> queue/claimed/T-0500-demo.md  (now: git add queue/ && git commit && git push ...)
          EXIT=0
          5:owner: agent/unknown

      `--owner ""` did the same, and `--touches=` / `--touches ""` recorded `touches: []`. The flag was
      supplied, its value was discarded, the task was claimed for the wrong owner, nothing was printed -
      the exact silence this route exists to remove.

      CLASS CLOSED, not the instance (81225ae): no option here has a meaningful empty value - `_list("")`
      is `[]` and every scalar is a name, a path or a number - so an empty value is refused for all of
      them. Re-run of the surviving command, verbatim:

          --- claim T-0500 --owner= ---
          usage: queue.py claim <id> [--hours V] [--owner V] [--session V] [--worktree V]
          refused: --owner was given an empty value; drop the flag or give it one.
          EXIT=2
          --- claim T-0501 --owner "" ---
          ... refused: --owner was given an empty value; drop the flag or give it one.  EXIT=2
          --- new "empty touches eq" --touches= ---
          ... refused: --touches was given an empty value; drop the flag or give it one.  EXIT=2
          --- review T-0502 --reviewer= ---   ... EXIT=2
          --- claim T-0503 --hours= ---       ... EXIT=2

      Edge tokens re-checked after the close: `--`, `-x`, `---`, `--=` as the first word after the
      operand are all refused with the usage line and exit 2.

### ROUTE 2 - [[T-0084]]: repeated list flags must ACCUMULATE

RED, executed at 69be364:

    $ queue.py new "route two red" --touches a --touches b --touches c
    queue/backlog/T-0001-route-two-red.md
    EXIT=0
    --- what was recorded ---
    12:touches: [c]

THE FIX (f5b0e70). `LIST_OPTS = {touches, exclusive, pins, depends}` accumulate across repeats; `_list`
flattens repeats and commas in any mix, so the undocumented `--touches a,b,c` workaround keeps working.
The docstring now says so, because "nowhere an agent reads" is half of why T-0084 happened.

GREEN, identical command:

    $ queue.py new "route two red" --touches a --touches b --touches c
    queue/backlog/T-0001-route-two-red.md
    EXIT=0
    --- what was recorded ---
    12:touches: [a, b, c]

And the harm T-0084 filed - the pre-commit hook refusing an agent's own files - measured through the
hook's OWN parse of the line queue.py now writes:

    $ queue.py new "hook parse demo" --touches ops/lib/queue.py --touches ops/claim --touches ops/lock
    12:touches: [ops/lib/queue.py, ops/claim, ops/lock]
    --- the pre-commit hook's own parse of that line ---
        allowed: ops/lib/queue.py
        allowed: ops/claim
        allowed: ops/lock

SELF-ATTACK, executed:

  (a) one NAME over: the other three list options. `--exclusive` x2, `--pins` x2, `--depends` x2 in one
      command -> `exclusive: [Package.swift, project.pbxproj]`, `pins_affected: [P-SRC-02, P-OPS-01]`,
      `depends_on: [T-0059, T-0084]`. All three accumulate; the fix is not touches-only.
  (b) one MECHANISM over: comma and repeat and `=` MIXED -
      `--touches a,b --touches c --touches=d,e` -> `touches: [a, b, c, d, e]`.
  (c) one SCALE over: eight repeats -> `touches: [t1, t2, t3, t4, t5, t6, t7, t8]`.
  (d) one TYPE over: an empty repeat `--touches=` - see route 1 (d); refused after 81225ae.
  Route 2 held against all four.

### ROUTE 3 - [[T-0084]]: a repeated SCALAR flag is an error, not silent last-wins

RED, executed at 69be364:

    $ queue.py claim T-0001 --owner agent/alice --owner agent/mallory
    claimed T-0001 -> queue/claimed/T-0001-route-two-red.md  (now: git add queue/ ...)
    EXIT=0
    5:owner: agent/mallory

GREEN, identical command:

    usage: queue.py claim <id> [--hours V] [--owner V] [--session V] [--worktree V]
    refused: --owner was given twice ('agent/alice' then 'agent/mallory'); it holds one value and which
    one was meant is not knowable here.
    EXIT=2
    ready/: T-0001-route-two-red.md   claimed/:            <- the task did not move

SELF-ATTACK, executed:

  (a) one NAME over: every other scalar in the dispatch. `--hours 2 --hours 99`, `--session a --session b`,
      `--worktree ../wt/a --worktree ../wt/b`, `review --reviewer agent/bob --reviewer agent/alice` - all
      four refused with the usage line and exit 2, and `queue/review/` stayed empty.
  (b) THE ONE THAT MATTERS, `--state`, because it is interpolated into the path `cmd_new` writes:
      `new "state twice" --state backlog --state done` and the `=` spelling of it both ->
      "refused: --state was given twice ('backlog' then 'done')", EXIT=2, nothing written.
  (c) one MECHANISM over: MIXED spellings of the same scalar, `--owner agent/x --owner=agent/y` - refused.
  (d) one TYPE over: the SAME value twice, `--owner agent/x --owner agent/x` - refused. Deliberate: a
      repeat is refused on the name, not on whether the two values happen to differ, so the guard cannot
      be walked past by repeating a value.
  Route 3 held against all four.

### Gates, and what this change did NOT break

    $ bash ops/queue-check          QUEUE OK (84 tasks)                                            EXIT=0
    $ bash ops/check-pins           PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux    EXIT=0
    $ bash ops/check-pins --source-only
                                    PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
                                                                                                   EXIT=0
    $ PYTHON=$(command -v python) bash ops/test
                                    TESTS linux=50/50 ios=skipped failed=0 skipped=0   OK          EXIT=0

HARD RULE 6. The two checkers that drive `queue.py` through a fake repo were run BEFORE and AFTER, and
are byte-identical either side:

    before: BRIEF CHECK OK        EXIT=0        after: BRIEF CHECK OK        EXIT=0
    before: LOCK LIFECYCLE FAIL   EXIT=1        after: LOCK LIFECYCLE FAIL   EXIT=1

`check-lock-lifecycle` was ALREADY red before this change, on the same two lines ("review did not release
the lock", "review refused a task that holds no locks"), and nothing runs it - that is [[T-0090]], filed
from this task in an earlier round. It is not a regression from this commit, and this commit does not
repair it.

`ops/lib/queue.py` is 920 lines, up from 843 (`git diff --numstat 69be364 HEAD -- ops/lib/queue.py` ->
`110  33`): **+110 inserted, -33 removed, net +77 lines**, against the 300-line
cap it is exempt from under [[T-0059]] (BLOCKED - six unmerged branches hold this file). Not split, per
the task instruction.

### Filed, not fixed

`ops/review` cannot run at all under `MSYS_NO_PATHCONV=1`, which is the setting every agent on this box is
told to use. The wrapper is unchanged by this task (last touched by b1e95aa, T-0032) and the failure is in
the shell, before python sees argv:

    $ MSYS_NO_PATHCONV=1 bash ops/review
    python.exe: can't open file 'C:\\c\\Users\\phineasf\\...\\ops\\lib\\queue.py': [Errno 2] No such file
    EXIT=2
    $ bash ops/review
    usage: queue.py review <id> [--reviewer V]
    refused '': the operand comes first and may not be blank.
    EXIT=2

`readlink -f "$0"` yields a POSIX path that Windows python resolves against the current drive. `ops/review`
is the ONE wrapper using that idiom; the other six use `git rev-parse --show-toplevel`, which is [[T-0077]]'s
defect in the other direction. Outside this task's `touches:`; recorded here so it is not lost.

Also recorded: this task's dispatch prompt said CLAUDE.md carries "a section on this checkout being on NTFS
with eight rules". It does not - `grep -in ntfs CLAUDE.md` on this worktree returns nothing. The eight rules
exist only in the prompt. Whoever expected them to be in the file should put them there.

### The limit of this fix, stated so nobody reads it as wider than it is

`_opts` validates the SHAPE of a command line - the option name, that it takes exactly one value, that the
value is not the next option, not empty, and not a repeat of a scalar. It does NOT validate the CONTENT of
a value, and one line proves it:

    $ queue.py new "traversal" --exclusive ../../../pwned --touches ../../../etc/passwd
    queue/backlog/T-0001-traversal.md
    EXIT=0
    11:exclusive: [../../../pwned]
    12:touches: [../../../etc/passwd]

That is [[T-0089]] - already filed from this task in an earlier round, with the fix specified as one
`lock_path(res)` used by all four sites, sequenced after [[T-0032]] merges - plus the same shape in
`touches:`, which `.githooks/pre-commit` reads as an allowlist. Route 1 of this task is "a wrong command
line is refused instead of obeyed in silence"; "a well-formed value that names somewhere it should not"
is a different route and this commit does not close it.


- 2026-09-08 agent/claude-opus-5 — **the adversarial verification returned holds=false with two overclaimed
  routes, both defeated on the fix's OWN WORDING. That is the round-three pattern a third time, and both are
  closed here.**

  **(1) The empty-value guard shipped a weaker criterion than its own comment states.** The comment justifies
  the refusal with *"`_list("")` is []"* — correct — and the code was `if not val.strip()`. But `_list(",")`
  is ALSO `[]`, and a comma survives `.strip()`:

        RED   ops/new-task "..." --touches ,        -> exit 0, recorded  touches: []
              ops/new-task "..." --exclusive ,,,    -> exit 0, recorded  exclusive: []
              ops/new-task "..." --depends " , "    -> exit 0, recorded  depends: []

  A supplied flag whose value was thrown away with nothing printed — verbatim the silence this commit claims
  to remove. Now the guard tests the PARSED value for a list option:

        GREEN refused: --touches was given ',', which parses to nothing; drop the flag or give it a value.

  **(2) The DASHES guard lived inside the `else:` branch, so the `--name=value` spelling never reached it.**
  One step past the fixer's own self-attack, which discovered `=` bypasses this parser and then closed only
  the EMPTY instance sitting in that same branch:

        RED   --touches=--state   -> exit 0, recorded  touches: [--state]
              --touches --state   -> refused, exit 2          <- the identical option, two spellings, two answers

  Both checks are now hoisted above the `if eq:` split, so the two spellings take one path:

        GREEN --touches=--state   -> refused: --touches was given '--state', which is another option, not a value.
              --touches --state   -> refused: identical message

  **CONTROL — the thing the fix exists for still works**, which matters because it is trivial to close a
  bypass by breaking the feature:

        --touches ops/a --touches ops/b   -> touches: [ops/a, ops/b]
        --touches=ops/x                   -> touches: [ops/x]
        ops/queue-check                   -> QUEUE OK (84 tasks)

  **On route 2's status, stated as the verifier stated it rather than collapsed:** the literal word
  "accumulate" held — no repeat overwrote an earlier value — but the HARM [[T-0084]] names was not closed,
  because `--touches a --touches ,` recorded `[a]` with the second repeat contributing nothing. That is fixed
  by (1), not by the accumulation logic.

  **A third finding, outside all three routes, filed separately:** `dump()` writes multi-line scalars raw,
  because its round-trip check `_scalar(s) == s` is true for a string containing newlines — so a value with an
  embedded newline injects arbitrary front-matter lines into the task file it writes.
