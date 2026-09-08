---
id: T-0092
title: a task-file value containing a newline injects front matter, and dump does not quote it
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T08:12:49Z
lease_expires_at: 2026-09-08T11:12:49Z
worktree: null
branch: task/T-0092
exclusive: []
touches: [ops/lib/queue.py, ops/lib/check-queue-roundtrip, pins/PINS.yaml]
pins_affected: [P-PROC-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`dump()` decides whether a scalar needs quoting with a round-trip test — roughly `_scalar(s) == s` — and that
test is **true for a string containing newlines**. So a value with an embedded newline is written raw, and
every line after the first becomes another front-matter key.

Executed against `task/T-0087`:

    fm["reviewer"] = "agent/x\nowner: agent/x"   ->  dump()  ->  the file now contains

        5:  owner: null
        ...
        14: reviewer: agent/x
        15: owner: agent/x

    and parse() reads back:
        owner    = 'agent/x'          <- line 5's `null` overwritten by line 15
        reviewer = 'agent/x'

**One field's value sets another field.** The parser is last-wins, so an injected line beats the real one
written above it. That is an integrity hole in the format every check in this repository reads:

- `owner` and `reviewer` are what P-PROC-01 compares. A `reviewer` carrying `\nowner: agent/someone-else`
  makes "the reviewer is not the owner" true while the task's actual owner is displaced — the rule
  [[T-0068]] and [[T-0073]] were both filed to make un-evadable, defeated from a direction neither considered.
- `state` can be injected, and `cmd_check` compares `state` against the DIRECTORY. Injecting a matching
  `state` is how a hand-moved file stops being reported.
- `exclusive` can be injected, which is how a task acquires or sheds a lock it never declared.

**No exploit is needed to hit this by accident.** Task titles and reviewer names are agent-supplied strings,
and this session alone has pasted multi-line command output into task fields more than once.

- `dump()` must quote or block-scalar any value containing a newline. The round-trip test is the bug: it asks
  "does this survive `_scalar`" when the question is "can this be one line".
- Decide whether a newline in a scalar is ever legitimate. It probably is not, in which case `dump()` should
  REFUSE rather than quote — a task field holding a paragraph is a smell, and the `## Log` section is where
  prose belongs.
- `parse()` should reject a duplicate key outright rather than taking the last. Last-wins is what turns an
  injected line into a winning line, and a real task file has no reason to repeat a key. That half is worth
  doing even if `dump()` is fixed, because it closes the hole for files written by anything other than
  `dump()` — a hand edit, a merge resolution, or a future tool.
- Red demonstration is above and reproduces in three lines against `ops/lib/queue.py`.

## Log
- 2026-09-08 filed by agent/claude-opus-5. Found by the adversarial verifier of T-0087 while attacking a
  different route, and confirmed here independently.
- 2026-09-08T08:12:49Z claimed by agent/claude-opus-5; lease until 2026-09-08T11:12:49Z

- 2026-09-08 — **closed twice over: refuse a line break at write time, refuse a duplicate key at read time.**

  Quoting is not one of the two, and it is worth saying why it was rejected:
  `reviewer: "agent/x\nowner: agent/y"` still occupies two physical lines and the second is still parsed as
  a key. The value has no representation in this format, so **writing it is the bug** — `dump()` raises.

  The parse-side rule is the one that holds when this module is not the writer. The amplifier is not the
  newline, it is **last-wins**: a second `owner:` line beats the real one above it however it got there —
  hand edit, merge, injection. Measured before enforcing: **0** of the task files in this tree carry a
  duplicate key, so nothing legitimate is refused.

  **RED** (`.artifacts/demo-injection.py`, run against this worktree's module):

        CASE 1 - reviewer carries a newline that declares an owner
           5: owner: agent/claude-opus-5
           6: reviewer: agent/claude-opus-5
           7: owner: agent/nobody          <-- injected
          parse() reads back: owner='agent/nobody'  reviewer='agent/claude-opus-5'
          reviewer == owner ? False   -> queue-check's rule PASSES

  That is the dangerous payload, and it is not the one the brief used. A payload naming the *same* agent in
  both fields makes `owner == reviewer` and trips the rule anyway. Naming a **third** agent displaces the
  real owner entirely: the worker reviews its own work, and P-PROC-01 reports that the reviewer is not the
  owner — satisfied by a value written into a different field. [[T-0068]] hardened the presence of those
  operands and [[T-0073]] hardened the comparison; this walks past both without touching either.

        CASE 2 - the same shape through a LIST element (exclusive:)
          dump() WROTE it; parse() reads owner='agent/x]'
        CASE 3 - a hand-written file with two owner: lines, no dump() involved
          parse() accepted it: owner='agent/x' (the SECOND line won)
        CONTROL - an ordinary task round-trips: True

  **GREEN:**

        CASE 1  dump() REFUSED: front-matter field 'reviewer' contains a line break, which cannot be
                written: every line after the first would parse as another key and overwrite it (last-wins).
        CASE 2  dump() REFUSED: front-matter field 'exclusive' contains a line break, ...
        CASE 3  parse() REFUSED: front matter defines 'owner' twice; the parser is last-wins, so the later
                line silently replaces the earlier one.
        CONTROL round-trip identical: True

        $ ops/queue-check          QUEUE OK (95 tasks)                     exit 0
        $ ops/check-pins --source-only   PINS ok=3 skipped=8 pending=1 expired=0 failed=0   exit 0

  **A defect this task found in something else while proving itself.** Running `queue-check` on this branch
  (which is `task/T-0087` + `main`) reported `duplicate id T-0088` — a real collision between
  `task/T-0081`'s T-0088 and `task/T-0087`'s. It passes on `main` alone and on `task/T-0087` alone; only the
  merge shows it, and no rehearsal had ever merged `task/T-0087` because it has no open PR. Renumbered to
  `T-0102`; the race is [[T-0101]] and the enumeration blindness is [[T-0099]].

  **And one of my own, worth recording because CLAUDE.md warns about it by name:** I wrote
  `ops/queue-check 2>&1 | tail -3 && echo "exit=$?"` and read `exit=0` for a run that exits 1 — `$?` after a
  pipeline is the LAST command's status. The failure above was nearly missed for that reason.

- 2026-09-08 — **reviewer-pr60 FAILED this (F1-F6). Fixed: the writer now asks the reader, and the property
  is committed as a checker that can be seen red from the tree.**

  Every finding was reproduced against the committed module (`976410a`) before anything was changed
  (`.artifacts/fix-t0092/repro.py`, gitignored, exit 1):

        === F2: dump() writes values parse() cannot read back (str.splitlines set) ===
          \n           dump REFUSED
          \r           dump REFUSED
          \x0b VT      dump WROTE it -> parse read ['agent/nobody']  round-trips=False
          \x0c \x1c \x1d \x1e \x85 \u2028 \u2029      ... all seven the same
          LEAKED: 8/10
        === F3 ===  parse ACCEPTED: owner=['agent/nobody'] touches=['a', 'ops/lib/queue.py']
        === F4 ===  dump wrote ['worktree: [a, b]'] -> parse read ['a', 'b']  round-trips=False
        === F5 ===  dump wrote a raw key; parse read reviewer='agent/nobody: agent/worker'
        REPRO: 4 finding-families still reproduce                                     exit=1

  **F2 / F4 / F5 — a writer must ASK the reader, never model it.** `_no_newline` is deleted. Its guard was
  `"\n" in v or "\r" in v` while `parse()` splits with `str.splitlines()`, which ends a line on TEN
  characters; the guard's expected value came from the author's model of the format instead of from the
  parser that reads it — this repository's signature defect, committed by the very change that diagnosed it.
  `_entry(k, v)` now renders each candidate encoding, hands it to `parse()`, and keeps it only if `parse()`
  returns exactly `{k: v}`; `dump()` then re-parses the finished file and refuses to return anything that
  does not come back as what went in. One mechanism closes all ten line-break characters instead of two
  (F2), the `[a, b]` scalar that was read back as a LIST (F4, now quoted and recovered), a KEY with no
  writable form (F5, which the character list never inspected), and a comma inside a list element, which
  nobody had reported.

  **F3 — the second way a key gets redefined.** A `  - value` line appended to the CURRENT key and threw
  away whatever it held (`fm[key] = []`), so no key repeated and the duplicate-key rule could never fire.
  `parse()` now permits a block item only under a key declared with an empty value; a scalar or a flow list
  underneath is refused. Measured before enforcing, as the duplicate rule was: all 95 task files in this
  tree still parse, and `dump()` writes them **byte-identically** to the shipped version
  (`.artifacts/fix-t0092/nochurn.py`: `examined=95 differ=0`), so nothing is reformatted.

  **F1 — the change now has something that goes red.** New `ops/lib/check-queue-roundtrip`, wired as
  **P-PROC-02** (`anchor: source`, so `ops/check-pins --source-only` runs it too). Three populations, each
  with a floor on what was ACTUALLY EXAMINED, never on what was merely present:

        QUEUE ROUNDTRIP OK: 29 write payloads, 9 read payloads, 95 task files      exit=0

  **RED, then GREEN — the check against the code it protects:**

        $ cp 976410a^:ops/lib/queue.py ops/lib/queue.py     # the whole T-0092 change deleted
        $ bash ops/lib/check-queue-roundtrip
          P-PROC-02: WRITE reviewer carries '\n' + a key: dump() wrote
            'agent/worker\nowner: agent/nobody' and parse() read 'agent/worker'
          ... 22 more                                                              exit=1
        $ ops/check-pins --source-only                                             exit=1
          P-PROC-02: A task file round-trips through ops/lib/queue.py ...

        $ cp 976410a:ops/lib/queue.py ops/lib/queue.py      # what PR #60 actually shipped
        $ bash ops/lib/check-queue-roundtrip
          P-PROC-02: WRITE worktree carries '\x0b' + a list item: dump() wrote
            '../wt\x0b  - agent/nobody' and parse() read ['agent/nobody']           exit=1
        $ ops/check-pins --source-only                                             exit=1

        $ git checkout -- ops/lib/queue.py                  # this task's fix restored
        $ bash ops/lib/check-queue-roundtrip                                       exit=0
        $ ops/check-pins --source-only
          PINS ok=4 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only  exit=0

  That is the F1 answer stated as a number: before this commit `ops/check-pins --source-only` reported
  `ok=3` with or without the change; it now reports `ok=4`, and reverting `ops/lib/queue.py` alone turns it
  red.

  **RED on an EMPTY population — the floors are floors on what was examined.** A count of task files
  *found*, or of payloads *defined*, would pass over a population nothing iterated. Each counter is
  incremented only after its case reaches a verdict, and each was demonstrated at zero:

        $ SCENIC_RT_QUEUE=<empty dir> bash ops/lib/check-queue-roundtrip
          P-PROC-02: only 0 task files examined (expected >= 40)                   exit=1
        $ bash <copy with BREAKS = [] and the payload tail unused>
          P-PROC-02: only 1 write payloads examined (expected >= 24)               exit=1
        $ bash <copy with READ_REFUSE = [] and READ_ACCEPT = []>
          P-PROC-02: only 0 read payloads examined (expected >= 6)                 exit=1
        (all three restored -> QUEUE ROUNDTRIP OK: 29 / 9 / 95                     exit=0)

  The check also asserts the other side of the rule — an ordinary task file, a block list under an empty
  key, a flow list, an empty flow list, `owner: "null"` staying quoted (T-0073 route 2). A rule that only
  ever refuses is an outage, not a check.

  **F6 — `ops/test` was declared in `verify:` and never run.** Run now, on this tree and on `main`:

        $ ops/test        FAIL: services/api exists but vitest produced no report  exit=1   (this branch)
        $ ops/test        FAIL: services/api exists but vitest produced no report  exit=1   (main)

  There is no `services/api/node_modules` anywhere on this box, so it is red for a reason older than this
  branch and identical on `main`. Recorded, not claimed as passing. The Swift side runs and passes inside
  it (16 tests, 3 suites).

  **Still red on this branch, none of it caused here:** `ops/test` (above); `ops/lib/check-lock-lifecycle`
  exits 1 with AND without this change ([[T-0090]]) — measured both ways, `976410a: exit=1`,
  `this fix: exit=1`.

  **Reviewer findings not fixed, deliberately:** the reviewer's two out-of-scope notes stand as filed —
  P-SAFE-05 shelling `swift test` with no `--scratch-path` (a stale `.build` makes `ops/check-pins` red for
  everyone, and CLAUDE.md forbids the invocation) is a real defect of P-SAFE-05, not of this task; it wants
  its own queue entry. Full `ops/check-pins` on this tree: `ok=10 skipped=0 pending=3 expired=0 failed=0`,
  exit 0.

  `touches:` widened from `[ops/lib/queue.py]` to add `ops/lib/check-queue-roundtrip` and `pins/PINS.yaml`,
  because the fix for F1 is exactly "commit a checker and make a pin run it" and neither path could be
  staged otherwise. `pins_affected:` is no longer `[]`.
