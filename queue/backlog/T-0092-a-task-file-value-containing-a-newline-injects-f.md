---
id: T-0092
title: a task-file value containing a newline injects front matter, and dump does not quote it
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
