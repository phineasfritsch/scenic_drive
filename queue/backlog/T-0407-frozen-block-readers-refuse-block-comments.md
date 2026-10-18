---
id: T-0407
title: Frozen-block readers fail open to a /* */ comment that hides the frozen body while a twin body draws instead - refuse block comments in every frozen file
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, ops/mutate/, pins/PINS.yaml, queue/]
pins_affected: [P-SAFE-03, P-SAFE-07, P-SAFE-09, P-ATTR-01]
reviewer: null
depends_on: [T-0406]
verify: [ops/check-pins]
acceptance: []
---
## Brief

Found by rv2-t0405 on PR #298 (ef599caa), 2026-10-18, and recorded as non-blocking there because main has the same
gap:
1. In PlanPreviewCard.swift, open a `/*` at the end of the unfrozen `@Environment(\.dynamicTypeSize) private var
   typeSize` line and close it at the start of the unfrozen `private var titleRow`. The frozen `var body` sits
   between them, so it is commented out.
2. Add a twin `var body: some View{` that draws the title, ETA, why line and hazards. It leaves out `map` (so P-ATTR-01
   fails open) and PlanPreviewActions (so the conditions line, P-SAFE-03, fails open too).
3. check-map-attribution's f4 and check-safety-disclaimer both stay green. The only refusal is the file's sha256
   digest row, and re-approving a digest is routine.

ops/lib/check-safety-disclaimer-preview already lists `/* */` comments under WHAT IT CANNOT SEE. The gap is shared by
every frozen_block reader: -frozen, -preview, check-drive-display, check-estimate-badge and check-map-attribution's
f4.

Close the class once, the way frozen_directives refuses `#` lines:
- Every file that holds a frozen block refuses any `/*` or `*/` outside a string literal.
- Alternatively, if T-0406's check-file-scope lexer can be reused, refuse any block comment that spans or touches an
  approved depth-0/1 line or a frozen block line.

Measure today's frozen files for block comments first. Whitelist the existing ones by whole line rather than weaken
the rule. Add the rv2 mutant verbatim plus generated variants to a mutation population with a literal floor:
- the comment opening on the line before a frozen block and on the block's first line
- nested `/* /* */ */`
- a twin body placed before and after the hidden one
- the same trick on each frozen file

Show the mutants RED on main, then GREEN. Confirm with a native swiftc Foundation-only twin that the commented-out
body plus the twin body compiles.

Also check whether check-file-scope (T-0406) already refuses the twin body, and record the answer. If its depth-1
line sequence catches a twin spelled byte-equal to the original, say so; if it does not, this task closes that too.

## Log
- 2026-10-18 filed by agent/claude-opus-5 from rv2-t0405's recordable on PR #298.
