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
- 2026-10-18T13:07:28Z measured so far (agent/claude-opus-5); NOT review-ready, the session hit its tool budget:
  - A1: python ops/lib/frozen_comments.py over the 10 frozen files: FROZEN-COMMENT ok  10 file(s), no block comment
    outside the 0 approved (exit 0). python ops/lib/check-drive-display.py on the branch: exit 0, 3 structs (243 kept
    lines) are their approved whole blocks.
  - A3 RED on main: frozencomments.py --only R1 with main readers (7cf55fb1): MUTATE SURVIVED  R1 PlanPreviewCard.swift
    r1 (reader silent). A4 on main: R1 applied to the real tree, bash ops/lib/check-safety-disclaimer exit 1 and its
    ONLY refusal is the sha256 row (PlanPreviewCard.swift content changed, sha256 9f3acc3d..., approved 925ffe2d...),
    which is rv2-t0405's finding reproduced. GREEN on the branch: MUTATE killed  R1 PlanPreviewCard.swift r1.
  - A5: swiftc 6.3.3 Foundation-only twin (.build/t0407-twin/Twin.swift, same shape: /* at the end of the typeSize
    line, */ before titleRow, the frozen body between, a twin body above): compiled, printed title | eta | why | hazards
    (no map, no conditions line).
  - R6 file-scope answer: R1 copy, check-file-scope exit 1 (line 25 1|    var body: some View{ is not the approved
    typeSize line). A byte-equal twin with /* and */ on lines of their own: FILE-SCOPE ok  62 file(s), exit 0 - so
    check-file-scope does NOT refuse a byte-equal twin; on main the frozen readers refuse that shape only because the
    approved first line then occurs twice. Outside the four modules (ScenicDriveApp.swift) nothing but frozen_block
    reads it, and the new rule refuses any block comment there.
  - G and C rows: the first two runs stopped at cannot tell (G rows passed their arguments to generated() out of
    order); fixed in the commit below, NOT yet run. Still open before review: the G/C rows RED on main and GREEN here,
    the whole gate list on a merged head, fetch + merge origin/main, push, PR. Local runs are slow on this box
    (python start 12 s, one preview reader 34-48 s), so the full 165-row population is expected to run in CI.
- 2026-10-18T14:58:26Z merged origin/main da475b6c (T-0398 #293, T-0409 #301; merge 4b37101b, no conflict) and
  ruled what it changed before more code (agent/claude-opus-5, author):
  - R7 (supersedes R4) main's T-0398 added ops/lib/check-estimate-badge.py, a FIFTH frozen-block reader (10 badge
    blocks read from their declaration line, ABOVE/BELOW fenced) whose docstring listed `/* */` comments under WHAT
    IT CANNOT SEE. R2 binds the rule inside every reader, so this one is bound too: check() first runs
    frozen_comments.refusals on every file a badge block is read from (CannotRun is a refusal). Its SITES whitelist
    already refuses a twin that repeats an ETA word, but a twin that hides a badge block and draws its ETA without
    the badge needs no new word. Frozen files 10 -> 13 (+ SurpriseCard, LoopPreviewCard, TripItineraryCard).
  - R8 the population gains the reader: its eight `{` blocks x 8 generated rows, two controls on each of its five
    files; MIN_MUTATIONS 165 -> 239 (1 R1 + 26 blocks x 8 + 30 controls). Its two one-line blocks (the round-trip
    call and the Copy literal) generate no twin (no ` {`); both sit in SurpriseCard.swift, covered by its `{` rows.
  - R9 a generator defect, found by the first branch run: where a block's ABOVE line is a lone `}` closing the
    previous member, the eol/own/nested openers hid that `}` while the twin held only the block, so the mutant had
    unbalanced braces (swiftc would reject it) and the reader refused it as `the lexer cannot read it` - refused,
    but not by the block-comment reason, so 9 sample rows printed SURVIVED (G19 G28 G64 G65 G83 G119 G147 G156 G183).
    The twin now repeats every line the comment hides before the respaced block. Measured over all 208 G rows with
    frozen_comments.refusals directly: 208/208 named with the block-comment reason, none `cannot read`.
- 2026-10-18T14:58:26Z acceptance re-quoted on the merged head (791b2e9a + the R9 fix, committed with this entry):
  1. A1 python ops/lib/frozen_comments.py <the 13 frozen files>: `FROZEN-COMMENT ok  13 file(s), no block comment
     outside the 0 approved`, exit 0.
  2. A2 the full 239-row population was NOT run locally (one row costs 20-45 s on this box); it runs in CI through
     P-SAFE-03's assertion. Local sample, `--only` R1 + one G row per block (row 1+8i+(i%8), all eight
     place/twin shapes across the 26 blocks), after R9: `MUTATE ok  27/27 killed or passed (floor 239, population
     239)`, `MUTATE silent  0 row(s)`, exit 0. Controls C209-C238 (30 rows, unchanged by R9) on 791b2e9a: 30 passed.
  3. A3 RED on main: the same 27 rows with origin/main's four readers (-frozen, -preview, check-drive-display.py,
     check-estimate-badge.py) restored in a copy: `MUTATE FAIL  survivors [all 27]`, `MUTATE silent  10 row(s) no
     reader refused at all: R1 G1 G10 G19 G28 G55 G64 G65 G74 G83`, exit 1. The other 17 are refused on main by
     other limbs (a changed fence or the f4/drive/SITES whole-line lists), never by a block-comment reason.
     GREEN on the branch: 27/27 killed (A2).
  4. A4 R1 applied to the tracked PlanPreviewCard.swift, `bash ops/lib/check-safety-disclaimer`: exit 1, `P-SAFE-03:
     a frozen preview render block changed: PlanPreviewCard's body: PlanPreviewCard.swift line 33: a /* */ block
     comment in a frozen file (lines 33-62, opening `@Environment(\.dynamicTypeSize) private var typeSize /*`), none
     approved`; restored with git checkout, `git status --porcelain -- apps/ios` empty.
  5. A5 unchanged since 13:07:28Z (swiftc twin compiled and drew title | eta | why | hazards).
  6. A6 P-SAFE-03's assertion ends `ops/mutate/frozencomments.py`; check-pins-yaml `PINS-YAML ok pins=53
     fields=426`; the file-scope answer is R6 above.
  7. A7 the gate list, bare, on 791b2e9a (each limb's last line): check-safety-disclaimer exit 0 (`Not checked
     here: rendering (T-0180), taps, ...`); check-map-attribution exit 0 (`... every app .swift, pbxproj and root
     Sources (-linked).`); check-file-scope `FILE-SCOPE ok  62 file(s) in 4 module(s), 1042 approved line(s)`;
     mutate/filescope.py `MUTATE ok  618/618 killed (floor 615, population 618)`; check-drive-display `3 structs
     (243 kept lines) are their approved whole blocks`; check-estimate-badge `45 approved whole lines ...; 10 badge
     blocks equal their approved bodies and fences; 85 declarations (292 lines)`, --prove-red `PROVE-RED OK: 18/18`;
     check-mutate-population `P-PROC-06: ... the floor of 173 holds`; check-mutate-only `NAME-PAIRS OK: 245251 pair
     tokens over 50 id populations`; check-mutate-anchors `17 drivers run from the repo root, 17 reached their
     population line`; check-pins-yaml ok; check-exec-bits `P-OPS-01: 265 files, 23 required present, all modes
     correct`; queue-check `QUEUE OK (403 tasks)`. All exit 0. The R9 commit touches only ops/mutate/frozencomments.py
     (generator + docstring), frozen_comments.py's docstring and this file; the gates reading them are re-run on it.
- 2026-10-18T16:05:29Z pre-review mutant pass, survivor M1 closed by class (agent/claude-opus-5, owner):
  - R10 M1 put the `/*` inside a // tail on PlanPreviewCard's typeSize line (`... typeSize // see titleRow /*`), a
    stray `*/ private var titleRow` below and R1's twin above. Neither swiftc nor the lexer reads a // tail's `/*` as a
    comment, so no reader saw a block comment and every reader was silent; swiftc rejects the shape (`unexpected end
    of block comment`). The pass offered an EQUIVALENT ruling with that compile witness. Ruled instead: the Brief
    asks for `/*` OR `*/` outside a string to be refused, and the rule must not lean on the compiler. So
    frozen_comments.refusals now also refuses every `*/` the SHIPPING lexer reads as code (`strays`): each `*/` outside
    a recorded block comment (and not the `*/` of `*/*`, whose `/*` opens a comment the rule already refuses) becomes
    `/**/` in a probe, the lexer runs again, and one it then opens a comment at was code. A `*/` in a string, a
    multi-line string or a // line stays inert; one in an interpolation is code. The refusal line keeps the
    block-comment reason, so every reader that already calls the rule refuses it by name with no reader edit.
  - R11 the population gains the class: R2 (M1 verbatim) and T rows (each of the 26 blocks x twin before/after, the
    opener a ` // see below /*` tail on the code line above ABOVE, or a `// /*` line of its own, the `*/` on its own
    line after the block). A tail hides nothing, so a T row's twin is the block alone (repeating the G rows' hidden
    lines unbalanced the braces on the first measure: 28 of 52 refused as `the lexer cannot read it`, not by the
    reason). Row ids are appended after C238 (R2, T240-T291), so every earlier id quoted above is unchanged.
    MIN_MUTATIONS 239 -> 292.
  - RED on HEAD's rule (d0fe4103's frozen_comments.py in a copy), every row through refusals in-process: `R: 1/2`,
    `G: 208/208`, `C: 30/30`, `T: 0/52 as required`. Through the shipping readers at 15:53:27Z,
    `--only R2,T240,T253,T262,T271,T277`: `MUTATE SURVIVED` x6, `MUTATE silent  3 row(s) no reader refused at all:
    R2 T240 T253`, `MUTATE FAIL  survivors [...]; ran 6, floor 292`, exit 1.
  - GREEN with the rule, in-process: `population 292 floor 292 files 15`, `pristine refusals 0`, `R: 2/2`, `G:
    208/208` (0 by the stray line), `C: 30/30`, `T: 52/52 as required, 52 by the stray-closer line`, `bad none`.
    Through the shipping readers, `--only R2,T240,T244,T253,T262,T271,T277,C209,C238`: R2 and the seven T rows
    `MUTATE killed`, both controls `MUTATE passed`, `MUTATE silent  0 row(s)`, `MUTATE ok  9/9 killed or passed (floor
    292, population 292)`, exit 0. The full 292-row population runs in CI through P-SAFE-03's assertion.
