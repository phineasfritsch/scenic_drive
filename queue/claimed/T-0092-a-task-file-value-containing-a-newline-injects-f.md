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
touches: [ops/lib/queue.py]
pins_affected: []
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
