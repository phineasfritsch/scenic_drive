---
id: T-0079
title: the MIN_ ratchet constants have no commit-msg protection, unlike the test floors
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:59:05Z
lease_expires_at: 2026-09-08T08:59:05Z
worktree: wt/T-0079
branch: task/T-0079
exclusive: []
touches: [.githooks/commit-msg]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`.githooks/commit-msg` refuses a commit that LOWERS any `pins/floor_*.txt` without a `floor-lower: <reason>`
line. Nothing protects the other ratchets, which are ordinary module constants:

    ops/lib/pins.py            MIN_PINS, MIN_RAN, MIN_RAN_SOURCE_ONLY, REQUIRED, REQUIRED_RAN
    ops/lib/check-exec-bits    MIN_FILES, REQUIRED
    ops/lib/check-line-cap     MIN_FILES, MIN_CAPPED, EXEMPT

`MIN_RAN = 9` -> `MIN_RAN = 6` is a one-line edit, no justification required, nothing red - and after
[[T-0072]] re-ratcheted the floors to today's counts, that one line restores exactly the headroom T-0072 was
filed to remove. **A ratchet whose notch can be moved silently is a suggestion again, one commit later.**

Noted by the T-0072 fix agent, which could not fix it: `.githooks/commit-msg` was outside that task's
`touches:`.

The asymmetry is the whole point. Raising a floor is free. Lowering one is sometimes correct - a pin is
genuinely retired, a suite is genuinely split - and the hook does not forbid it, it forbids doing it without
saying why. The constants deserve the same treatment and currently get none.

- Extend `.githooks/commit-msg` to the constants. They are integers on a line matching a known name in a known
  file, so the same `old > new` comparison works; parse them out of the staged blob the way the floors are
  parsed out of theirs.
- Removing an entry from `REQUIRED`, `REQUIRED_RAN` or `EXEMPT` is a lowering too, and is the more likely
  evasion: it needs no number to change. Count the entries.
- Anchor on the identifier, never on a comment - the names are the anchor and they are stable.
- Consider whether this wants to be a check rather than a hook. A hook is bypassable with `--no-verify` and is
  not run in CI; `ops/check-pins` runs on every push. The honest answer may be both, and the reason belongs in
  the file.
- Demonstrate red for each: lower one constant per file with no justification and show the refusal, then with
  a justification and show it accepted, then remove one `REQUIRED` entry and show that counted as a lowering.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the T-0072 fix agent's report, which identified it while
  re-ratcheting the floors it had just been asked to tighten.
- 2026-09-08T02:59:05Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:59:05Z
