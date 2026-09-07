---
id: T-0033
title: ops/etl-fetch-inputs --record-digest must verify and refuse to silently re-pin a changed file
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T21:04:44Z
lease_expires_at: 2026-09-07T23:04:44Z
worktree: null
branch: task/T-0033
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-37
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

- 2026-09-07T23:40Z claimed, brief written, and implemented by agent/claude-opus-5. Stacked on task/T-0025,
  which owns etl/fetch.py and added --record-digest in the first place.

  **The brief was empty when I claimed it** - the template, filed by me and never written. Written at claim
  time and committed separately before any code, because a task nobody wrote a brief for is a task whose
  acceptance nobody can argue with, and I would otherwise have been marking my own homework twice.

  **What was actually wrong.** `--record-digest` kept its promise ("pinning a digest is a deliberate human
  act", etl/fetch.py:8) only for an entry that had no digest yet. Run against an ALREADY-pinned entry whose
  upstream file had changed, it downloaded the new bytes, printed the new digest, and said nothing about the
  old one. The operator pastes it in and the pin has laundered the change instead of catching it. That is
  precisely what T-0025 pinned the Curvature KMZ to prevent - "if they regenerate it the fetch fails and a
  human re-pins it having looked at what changed" - and nothing made anybody look.

  **The part that made this more than a message change.** `download()` wrote straight to `inputs/<name>`, so
  the known-good, digest-verified bytes were replaced by unverified new ones BEFORE anything compared them. A
  refusal at that point has already destroyed the thing it was refusing to give up. The download now goes to
  `<name>.recording` whenever the entry is already pinned, and only moves into place if it matches.

  Behaviour now:
    already pinned, digest DIFFERS -> exit 3, both digests and both byte sizes on stderr, pinned file on disk
      untouched, fetched bytes kept beside it as `<name>.recording` so whoever decides can actually look
    already pinned, digest MATCHES -> exit 0, "still matches its pinned sha256", no stray staging file
    not pinned (absent or TODO)    -> unchanged: prints the digest on stdout, which is the whole feature

  **No --force flag**, deliberately. To re-pin, a human sets the entry's sha256 to TODO in the manifest and
  runs the command again: two edits, both visible in a diff and both in git history. A flag is one word in a
  shell nobody reviews. The refusal message says this, and a test asserts the message says it - otherwise the
  design decision lives only in a comment.

  **12 new tests in tests/test_fetch_repin.py** (its own file: test_fetch.py is 215 lines against a 300 cap
  and covers a different concern). Three of them are the ones I would attack: that the new digest does NOT
  appear on stdout on a refusal (or the refusal is decorative for anyone using this in a pipeline), that the
  pinned file survives, and that the bootstrap path still works - the new refusal sits in front of the path
  this command was built for, and a fix that breaks the feature to protect it is not a fix.

  **RED demonstrated** by restoring the exact five-line block this replaces:

      old record-digest block: RED  (FAILED tests/test_fetch_repin.py::TestUpstreamStillMatchesThePin::...)
      bootstrap tests on old code: still green
      fetch.py restored byte-identical
      green suite: exit 0

  The second line matters: the new tests fail because of this change specifically, not because reverting it
  broke the module generally.

  **Verification** - pytest in the pinned scenic-etl image, the rest from the worktree:
    `pytest -q tests/`  -> 168 passed, 1 skipped
    `ops/test`          -> `TESTS linux=218/76 ios=skipped failed=0 skipped=0` / `OK`
    `ops/check-pins`    -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`
  fetch.py 232 lines, test_fetch_repin.py 128 - both under the cap. GitHub Actions is DISABLED repo-wide as
  of today (T-0053) because the spending limit is exhausted, so there is no CI signal on this at all and this
  is local only.

  **What to attack.** Exit 3 is new and nothing else in this repo uses it; check it does not collide with a
  caller that treats any non-zero the same way, in which case the distinct code buys nothing. The
  `.recording` file is left on disk after a refusal on purpose, and nothing ever cleans it up - decide
  whether that is a leak or the point. And `already_pinned` treats `TODO` case-insensitively but the manifest
  header only ever documents the uppercase form; a `todo` in a manifest would be a pin to a 4-character
  string, which validation rejects, but I have not tested that path.
