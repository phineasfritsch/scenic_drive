---
id: T-0088
title: ops/check-pins --tier with no value prints an IndexError traceback, the same shape T-0087 fixed in queue.py
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
