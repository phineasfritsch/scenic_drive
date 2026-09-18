---
id: T-0109
title: checkbounds returns 0 when no extract exists, contradicting its own docstring
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/checkbounds.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`etl/checkbounds.py`'s own docstring states the contract:

    Exit 0 in bounds, 4 out of bounds (ops/sane's reserved code for corpus/graph bounds), 2 if it cannot
    tell. "Cannot tell" is never 0: an unreadable meta.json and a perfect extract must not print the same
    thing.

The code contradicts it in the one case that will be true on every fresh checkout:

    if not regions:
        print("BOUNDS skip  no extract has been built here")
        return 0

**"No extract has been built" is the definition of cannot tell**, and it returns 0. Everywhere else the file
gets this right — a missing `meta.json` returns 2, an unreadable one returns 2, a region with no recorded
counts returns 2. This single path is the exception, and it is the path a clone with no build takes.

The message is honest; the exit code is not. Anything reading only the status — `ops/sane`, CI, a future
gate — cannot distinguish *"the extract is within bounds"* from *"there is no extract"*.

Do:

1. Return 2, matching the docstring and the other three cannot-tell paths.
2. Then handle the consequence honestly rather than by weakening the check: `ops/sane` must treat "no
   extract built here" as a **skip** rather than a failure — it already has a `skip()` helper and prints one
   per check. The distinction to preserve is *sane says skip because there is nothing to check*, while
   *checkbounds says 2 because it was asked and could not answer*.
3. Red demo: a tree with no `work/` directory. Before: `BOUNDS skip`, exit 0. After: exit 2, and
   `ops/sane` printing `bounds  skip  no extract built` while still exiting 0 overall.

**Do not** fix this by deleting the skip message. The message is the useful part; only the code is wrong.

Found while adding a second region ([[T-0107]]) — a region with no counts correctly returns 2, which is
what made the neighbouring path's 0 visible.

## Log
