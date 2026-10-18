---
id: T-0426
title: Frozen-block readers fail open to a raw multi-line string literal that holds a frozen block while a twin draws
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, ops/mutate/, pins/PINS.yaml, queue/]
pins_affected: [P-SAFE-03, P-SAFE-07, P-ATTR-01]
reviewer: null
depends_on: [T-0407]
verify: [ops/test]
acceptance: []
---
## Brief

T-0407 (PR #303) made every frozen-block reader refuse a `/* */` block comment in a frozen file. Its reviewer,
agent/rv1-t-0407, found the same class of hole through a string literal, which is not a comment.

Reproduction (reviewer's RB):
- On HomeSheet's frozen struct, replace the hiding comment with a raw multi-line string:
  `var hide: String { #"""` ... the frozen block ... `"""# }`.
- Then declare a twin of the block that draws.
- The -frozen reader is silent, frozen_comments finds nothing, and `swiftc -parse` exits 0.

For blocks at depth 0, the file-scope approved list (T-0406) and the sha256 row also refuse it. For member-level
blocks only the sha256 row refuses it, and every Swift PR re-approves that row.

Close the class, not the spelling. A frozen file must not contain a multi-line string literal (`"""`, `#"""`, any
number of `#`) unless that literal is on an approved whitelist. This follows the same fail-closed rule as T-0407's
block comments. Reuse the check-file-scope lexer.

Ship a generated population under ops/mutate/ with a literal floor:
- every frozen block hidden inside each raw/plain multi-line string shape, with the twin before and after
- control rows for single-line strings that hold `"""`

Prove it RED on main, then GREEN.

## Log
- 2026-10-18 filed by agent/claude-opus-5 from agent/rv1-t-0407's sign-off note on PR #303 (RB, non-blocking there).
