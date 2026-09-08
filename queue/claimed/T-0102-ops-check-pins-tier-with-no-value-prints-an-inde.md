---
id: T-0102
title: ops/check-pins --tier with no value prints an IndexError traceback, the same shape T-0087 fixed in queue.py
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T08:53:47Z
lease_expires_at: 2026-09-08T10:53:47Z
worktree: null
branch: task/T-0102
exclusive: []
touches: [ops/lib/pins.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0087 was "three ops/* entry points print a traceback where every other one prints a usage line", and its
brief asked whether the same shape existed elsewhere. It does, one file over. `ops/lib/pins.py` reads the
value of `--tier` by index:

    ops/lib/pins.py:103:        tier = argv[argv.index("--tier") + 1]

so the flag written without a value indexes off the end of the list. Red, executed on task/T-0087 at
0be7589, from the worktree root:

    $ bash ops/check-pins --tier
        sys.exit(main(sys.argv[1:]))
                 ~~~~^^^^^^^^^^^^^^
      File "C:\Users\phineasf\Documents\GitHub\wt\T-0087\ops\lib\pins.py", line 103, in main
        tier = argv[argv.index("--tier") + 1]
               ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
    IndexError: list index out of range
    EXIT=1

Two things are wrong here, not one. The traceback is the visible half; the exit code is the other. Every
other ops/* entry point answers a bad invocation with exit 2, and this exits 1 - the code check-pins uses
for "a pin FAILED". An agent or a CI step that reads only the status cannot tell "you typed the flag wrong"
apart from "a load-bearing property of this repo is broken".

Wanted: a usage line and exit 2, matching queue.py's main() after T-0087. While in there, check what a
`--tier` value that is not a tier does - `ops/check-pins --tier bogus` must not be able to report a green
run over zero pins, which is the T-0066 vacuity class in a second place.

Not fixed under T-0087: `ops/lib/pins.py` is outside that task's `touches:` and is held by T-0066, which is
claimed. Filed rather than fixed so the finding is not lost and T-0066's owner is not conflicted with.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from T-0087, whose brief asked for the class to be swept rather
  than only the three named entry points. The red run above is verbatim.

- 2026-09-08 — **filed as `T-0088` and renumbered to `T-0102`: that id was allocated twice.** `main` carries a
  different `T-0088` ("the 69 mutation survivors are five gaps, and one of them is the fixture's own record
  shape"), filed from `task/T-0081` while this branch was in flight.

  **Neither tree was wrong on its own, which is the point.** `ops/queue-check` passes on `main` and passes on
  this branch; the duplicate exists only in the MERGE of the two, and it was found by merging them in a
  throwaway. That is the same merge-time-only class as the stale `claimed/` copy [[T-0063]] was filed for and
  the reason [[T-0065]]'s rehearsal exists — and it was invisible to that rehearsal too, because this branch
  has no open PR and the rehearsal enumerated pull requests ([[T-0099]]).

  Second instance of the same race in one day; `T-0099` was the first. Root cause and fix are [[T-0101]]:
  `next_id()` READS the refs and the commit that publishes the id happens minutes later, so two allocators
  that both read before either pushed get the same number. Allocation needs the compare-and-swap that
  claiming already has.
- 2026-09-08T08:53:47Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:53:47Z
