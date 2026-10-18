---
id: T-0407
title: Frozen-block readers fail open to a /* */ comment that hides the frozen body while a twin body draws instead - refuse block comments in every frozen file
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-18T08:40:33Z
lease_expires_at: 2026-10-19T08:40:33Z
worktree: .worktrees/T-0407
branch: task/T-0407
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
- 2026-10-18T08:40:33Z claimed by agent/claude-opus-5; lease until 2026-10-19T08:40:33Z
- 2026-10-18T11:27:56Z rulings before code (agent/claude-opus-5, author):
  - R1 THE LEXER. One lexer, check-file-scope.py's (T-0406): a new ops/lib/frozen_comments.py loads that file with
    importlib and wraps its `_block_comment` so every block comment the shipping lexer opens is recorded as a line
    span; `checked_lines` then runs unchanged. Strings, raw strings, interpolation, nesting and `//` are therefore
    read exactly as check-file-scope reads them - no second lexer to skew. check-file-scope.py is at the 300-line
    cap, so it is not edited. Fail closed: the wrap is proved on a canary (`/* x */` must record exactly one span)
    on every call, so a renamed hook is "cannot run", never a silent zero; a LexError is a refusal by reason.
  - R2 THE FROZEN FILES are bound structurally, not by a hand list: the refusal is called INSIDE the readers -
    bash `frozen_block` (check-safety-disclaimer-frozen; used by -frozen, -preview and check-map-attribution's f4)
    and check-drive-display.py's `frozen()` - on the file each block is read from. Every file any frozen-block
    reader reads is covered, and so is the next one added. Measured today (10 files): HomeSheet.swift,
    ScenicHomeScreen.swift, ScenicDrive/ScenicDriveApp.swift (-frozen); PlanPreviewCard.swift,
    PlanPreviewActions.swift (-preview); PlanPreviewMap.swift, PlanSheetScreen.swift (f4); DriveCard.swift,
    DriveEndConfirm.swift, DriveScreen.swift (check-drive-display).
  - R3 THE RULE: any block comment the lexer opens in a frozen file (a `/*` outside a string literal and outside a
    `//` comment; nested ones counted as Swift counts them) is refused unless it is an approved
    `basename|whole opening line|whole closing line` entry. Measured: `grep -rn '/\*' apps/ios --include=*.swift`
    hits only Package.swift line 10, inside a `//` comment and not a frozen file, so the approved set is EMPTY and
    nothing is weakened. A stray `*/` in code is not refused separately: swiftc rejects it ("unexpected end of block
    comment"), so it cannot hide code; `/*` inside a `//` line is a line comment to both swiftc and the lexer.
  - R4 `ops/lib/check-estimate-badge.py` (in the orchestrator's gate list) exists on neither main nor origin/main
    (`git ls-tree -r --name-only origin/main | grep estimate`: none). The estimate-badge frozen blocks are -preview's
    `estimateTag` (frozen_block) and check-drive-display's BLOCKS, both covered by R2. The gate is quoted as run.
  - R5 THE POPULATION (ops/mutate/frozencomments.py) runs the SHIPPING reader functions on a copy of the app tree:
    `require_frozen_blocks`, `require_preview_blocks`, `require_preview_wiring` (sourced as the entry points source
    them, `fail` recording instead of exiting) and check-drive-display.py's `frozen()`. Not the whole entry points:
    `bash ops/lib/check-safety-disclaimer` plus check-map-attribution did not finish inside 120 s on this box, and
    the earlier limbs `exit` on a twin's duplicate lines before the frozen readers run. R1 (rv2-t0405's mutant
    verbatim) is also run once through the whole shipping entry point below. KILLED = the reader names the mutated
    file with the block-comment reason. Rows: R1 verbatim; per frozen block x {`/*` at the end of the line above the
    approved ABOVE line (rv2's shape), `/*` on its own line there, `/*` on the block's first line, nested
    `/* /* */` opener} x {twin before, twin after}; per frozen file two CONTROLS (`"/*"` in a string, `// /*` line)
    that must NOT be refused by this rule. Literal floor MIN_MUTATIONS.
  - R6 the check-file-scope question is answered by measurement below (R1 copy, and a byte-equal own-line twin).

### Acceptance (committed before code)
1. `python ops/lib/frozen_comments.py <the 10 frozen files>` exits 0: `FROZEN-COMMENT ok  10 file(s)`.
2. `python ops/mutate/frozencomments.py` exits 0: `MUTATE ok  N/N killed` with N >= MIN_MUTATIONS, controls passed.
3. RED on main: the same driver with main's three readers restored reports R1 and the twin rows SILENT (no reader
   refusal at all); GREEN on this branch.
4. R1 through the whole shipping `bash ops/lib/check-safety-disclaimer --app-tree <copy>` is refused by the preview
   frozen reason naming the block comment.
5. A native swiftc Foundation-only twin with the commented-out body plus the twin body compiles and runs the twin.
6. P-SAFE-03's assertion runs ops/mutate/frozencomments.py; check-pins-yaml ok; the file-scope answer recorded.
7. The whole gate list, bare, plus check-mutate-anchors, quoted on the merged head.
