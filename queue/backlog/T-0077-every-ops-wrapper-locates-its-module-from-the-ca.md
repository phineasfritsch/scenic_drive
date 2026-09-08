---
id: T-0077
title: every ops wrapper locates its module from the caller's git toplevel, so another repo's module runs instead
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/new-task]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/check-pins` is

    exec "$py" "$(git rev-parse --show-toplevel)/ops/lib/pins.py" "$@"

so it locates its module from **the caller's** git toplevel, not from its own directory. Run this repo's
`ops/check-pins` from inside any other git repository and it executes **that** repository's
`ops/lib/pins.py`. Executed by the T-0072 verifier against a synthetic repo containing a four-line module
that prints a green summary:

    PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux
    EXIT=0

with nothing in this repo modified. Every guard added by T-0066 and T-0072 - the population floors, the
REQUIRED lists, the strict argv parser, the run floor - is bypassed at once, by choosing a working directory.

Pre-existing: `git show dac14c3:ops/check-pins` has the same line. T-0055 fixed this class in the wrappers'
`cd`, and `ops/lib/pins.py` itself now derives `ROOT` from `__file__` (which is why all four *entry points*
keep their guards). The one path not fixed is how the wrapper finds the module in the first place.

**The same line has a second knob**, and the two want one decision: `PY="${PYTHON:-$(command -v python3 ||
command -v python)}"`. `PYTHON=true` is now refused, but a four-line script that answers the probe token and
then does nothing still passes, and `PYTHON=` is honoured by every other wrapper unprotected. See [[T-0076]],
where the same expression picks an interpreter without pytest on a real developer machine - that is this knob
going wrong by accident rather than on purpose.

- Resolve the module from `${BASH_SOURCE[0]}`, the way T-0055 taught the wrappers to resolve the repo root.
  It is one line per wrapper and it closes the whole class.
- Then decide the `PYTHON` question once, in writing: pin the interpreter, probe candidates for the modules
  each script needs, or state in the file that this is a deliberate local convenience. Do not leave it decided
  by omission in six files.
- **Every wrapper has the same shape**: `ops/check-pins`, `ops/queue-check`, `ops/claim`, `ops/new-task`,
  `ops/lock`, `ops/queue-next`, `ops/queue-sweep`, `ops/test`, `ops/sane`. Grep before assuming this list is
  complete, and fix them together - a class fixed in one file is a class still open.
- Red demonstration: build a throwaway repo with a fake `ops/lib/pins.py` that prints a green line, run this
  repo's `ops/check-pins` from inside it, and show `ok=99 ... exit 0`. Then show it refusing after the fix.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-two adversarial verification of [[T-0072]]. The
  synthetic-repo bypass was executed by the verifier, not reasoned about.
