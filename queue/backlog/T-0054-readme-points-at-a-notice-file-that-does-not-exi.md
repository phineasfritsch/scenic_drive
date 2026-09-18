---
id: T-0054
title: README points at a NOTICE file that does not exist
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [NOTICE, README.md, LICENSE-DATA]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`README.md:15` ends "See `LICENSE-DATA` and `NOTICE`." There is no NOTICE file. `git ls-files` finds none at
the repo root or anywhere else in the tree (the only hits are inside `services/api/node_modules/`), and it has
never existed - not in any commit reachable from main. So the README promises a second attribution document
that a reader cannot open.

Found while fixing T-0027's LICENSE-DATA gap (agent/reviewer-32's finding 7). It is NOT the same gap: the ESA
WorldCover CC-BY-4.0 attribution T-0027 owed is now in LICENSE-DATA, and
`test_every_attribution_licence_it_uses_is_actually_attributed` (services/etl/tests/test_manifest.py) checks
every attribution-requiring licence in `services/etl/inputs/manifest.yaml` against that file. Nothing checks
the README's claim, because NOTICE is not a data licence question - it is where third-party SOFTWARE notices
would go (MapLibre, Ferrostar, GRDB, Protomaps, the Swift and npm dependency trees), and none of that is
written down anywhere yet.

Decide one of two things and do it, rather than leaving the dangling reference:
  - write NOTICE, listing the third-party software licences the app and services ship, and add a check that
    every dependency manifest's licences appear in it (the shape of `manifest.unattributed` is the model); or
  - delete "and `NOTICE`" from README.md:15 and say in LICENSE-DATA where software notices will live.

RED: a check that the README's file references all resolve - `grep -o '\`[A-Z-]*\`' README.md` against
`test -f` - fails today on NOTICE. Demonstrate it red before writing NOTICE, so the check is known to work.

## Log
