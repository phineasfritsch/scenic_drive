---
id: T-0033
title: ops/etl-fetch-inputs --record-digest must verify and refuse to silently re-pin a changed file
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T21:04:44Z
lease_expires_at: 2026-09-07T23:04:44Z
worktree: null
branch: task/T-0033
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(Filed with an empty brief and written properly at claim time by agent/claude-opus-5, who filed it. A task
nobody wrote a brief for is a task whose acceptance nobody can argue with.)

`--record-digest NAME` exists so that pinning a digest is a deliberate human act - `etl/fetch.py:8` says so:
"A fetcher that silently accepts whatever the network hands it the first time, and pins THAT, is not
verifying anything." It currently keeps that promise for a NEW entry and breaks it for an existing one.

Run `--record-digest` against an entry that already carries a valid pinned sha256 and upstream has since
changed the file, and it downloads the new bytes, prints the new digest, and says nothing at all about the
old one. A human pastes it into the manifest and the pin is gone. That is exactly the failure T-0025 pinned
the Curvature KMZ to prevent - its log says "an oracle that silently follows upstream is not an oracle. If
they regenerate it the fetch fails and a human re-pins it having looked at what changed" - and nothing
currently makes anybody look at what changed.

Worse, `download()` writes straight to `inputs/<name>`, so the known-good, digest-verified file is
OVERWRITTEN by unverified new bytes before anything compares them. A refusal after that point is a refusal
that has already destroyed the thing it was protecting.

- On a mismatch: refuse, with a distinct exit code, printing BOTH digests and both byte sizes. Leave the
  previously verified file on disk untouched.
- On a match: say so and succeed - re-running the command must be safe and must not look like a change.
- No `--force` flag. To re-pin deliberately, a human sets the manifest's `sha256` to `TODO` and runs the
  command again: two auditable edits in git, which is a stronger record than a flag nobody sees in a diff.
- Demonstrate red: an entry pinned to digest A, upstream serving bytes with digest B. Before the change the
  command exits 0 and prints B; after it, it refuses, names both, and the file on disk is still the one that
  matches A.

## Log
- 2026-09-07T21:04:44Z claimed by agent/unknown; lease until 2026-09-07T23:04:44Z
