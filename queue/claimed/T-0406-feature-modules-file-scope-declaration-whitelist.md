---
id: T-0406
title: Close the shadowing class once - every file-scope line in the feature modules is at an approved site (whitelist by brace depth), so no declaration can shadow a name a frozen safety block uses
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T23:09:14Z
lease_expires_at: 2026-10-18T23:09:14Z
worktree: .worktrees/T-0406
branch: task/T-0406
exclusive: []
touches: [ops/lib/, ops/mutate/, pins/PINS.yaml, queue/]
pins_affected: [P-SAFE-03, P-SAFE-07, P-SAFE-09, P-ATTR-01]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Five review rounds on 2026-10-17 found the same hole from different directions. A file-scope declaration added to a
feature module shadows a name that a frozen safety block references. The frozen lines stay byte-equal while the
behaviour changes. The only check that goes red is a sha256 digest, and re-approving a digest is routine. Each round
closed one spelling; the next reviewer found another:
- T-0398 rv1 (PR #293): `private enum DesignTokens { fgMuted = .clear ... }` appended to SurpriseCard.swift hides the
  estimate tag (P-SAFE-07).
- T-0398 rv2: the same with Swift backtick identifiers (`` private let `DesignTokens` = ShadowTokens.self ``) gets
  past the name-based declaration scan. Shown to compile and shadow with native swift: `tag colour=CLEAR`.
- T-0397 rv2 (PR #295): a `fileprivate enum DesignTokens` placed ABOVE `import SwiftUI` in DriveCard.swift draws the
  drive disclaimer in clear (P-SAFE-03). A `fileprivate enum PostDriveQuestion` there makes the post-drive question
  open for a moving driver (P-SAFE-09). swiftc 6.3.3 confirmed that a file-scope type shadows the imported one.
- T-0396 rv1 (PR #294): `extension Text { func fixedSize(...) -> some View { EmptyView() } }` overloads a modifier the
  frozen conditions and estimate Texts call.

Close the CLASS once, structurally, instead of per spelling. Use one guard over FeatureScenicHome,
FeatureSurpriseMe and FeaturePlanSheet, and DesignSystem if cheap:
1. Lex each .swift file. Strip `//` comments, nested `/* */` comments, and string literals: "...", multi-line
   """...""" and raw `#"..."#` forms, including interpolation. Track brace depth.
2. Every line at depth 0 that has code on it, and every opening line of a depth-0 declaration, must be byte-equal to
   an approved entry for that file. Keep the approved list as data under ops/lib, seeded from today's tree. Every
   import, extension, struct, enum, class, typealias, func, let and var at file scope is therefore whitelisted, and
   any new one is refused, whatever its name, spelling, backticks or position (above or below the imports).
3. FAIL CLOSED: an unterminated comment or string, an unknown raw-string delimiter, or a depth that goes negative or
   does not return to 0 is a refusal. It is never a pass.
4. A new feature file is refused until its file-scope lines are approved: the module's file set is whitelisted too.
5. Add a mutant population under ops/mutate with a literal floor. Use the four mutants above verbatim, plus a
   generated set: each shadow placed above the imports, between them, at the end, as a new file, with backticks, with
   a comment between the keyword and the name, and as an extension of each frozen-block type (Text, Capsule, View).
   Each must be refused by name. Show them RED on main's guards, then GREEN.
6. Name the residual limits in the guard's header and in the pins' rows. Example: a declaration in ANOTHER module
   (DesignSystem itself) is covered only by the digest pins.

This task lands first. T-0397 and T-0398 then merge main and need no shadowing guard of their own.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the T-0396 rv1, T-0397 rv2 and T-0398 rv1/rv2 findings.
- 2026-10-17T23:09:14Z claimed by agent/claude-opus-5; lease until 2026-10-18T23:09:14Z
- 2026-10-17T23:28:15Z RULINGS before code (agent/claude-opus-5).
  R1 THE GUARD is `ops/lib/check-file-scope.py` (Python: a lexer is a state machine, and PR #130 lost two rounds to
     an awk one). Its data is `ops/lib/check-file-scope-approved.txt`, its population `ops/mutate/filescope.py`.
  R2 LEXER. Code / `//` comment / nested `/* */` / string, with a stack so `\(...)` (and `\#(...)` in a raw string
     of one or more `#`) re-enters code inside a string. String forms: "..." (a newline inside is a refusal),
     """...""" and their raw `#..#"..."#..#` / `#"""..."""#` forms. Backtick identifiers are skipped to the closing
     backtick (Swift 6.2 raw identifiers may hold `{` - unskipped, `` `{{` `` would skew the depth). FAIL CLOSED, each
     a refusal naming its reason: an unterminated block comment, string, interpolation or backtick; a `#` followed
     by anything but `#`, `"` or an identifier start (`#/regex/#` lands here); a `/` that is not `//`, `/*`, `/=` or
     followed by whitespace (the package is `.swiftLanguageMode(.v6)`, which enables bare `/regex/` literals - a
     regex holding `{` skews the depth; refused rather than lexed); a lone CR (Swift ends a `//` comment at it, so
     reading it as a non-break would hide code); bytes that are not UTF-8; a depth that goes negative or ends != 0.
  R3 WHAT IS CHECKED, A DISAGREEMENT WITH THE BRIEF RULED HERE. The Brief says depth 0. Depth 0 alone leaves the same
     class one level down: `private static let DesignTokens = ShadowTokens.self` as a MEMBER of SurpriseCard shadows
     the module type inside every frozen block of that struct (unqualified lookup finds members first), and a
     member added inside an already-approved `extension` is invisible at depth 0. So a line is checked when any of
     its code characters sits at brace depth 0 OR 1 (a `}` counts at the depth it returns to, a `{` at the depth it
     opens from). Depth >= 2 (bodies of members) is free: a local declaration shadows only its own body, and the
     frozen bodies are -frozen/-preview's whitelists. A comment-only or blank line is not checked.
  R4 THE APPROVED LIST is ORDERED and per file: `@file <module>/<path>` then one `<depth>|<line>` per checked line,
     the line byte-equal (CR stripped). Ordered and counted, so a duplicate of an approved line (a second
     `extension View {`) or a moved one (a shadow above the imports re-using approved text) is refused. A refusal
     prints the file's whole ready-to-paste block (`--print <module>/<file>` prints it too), so T-0397/T-0398 seed
     their new files by pasting.
  R5 THE FILE SET is whitelisted: every file of any extension under the four module directories, recursively, must
     have an `@file` entry and every entry must exist. Scope: FeatureScenicHome, FeatureSurpriseMe, FeaturePlanSheet
     and DesignSystem (226 lines, cheap; it is the module the frozen blocks' `DesignTokens` comes from).
  R6 RESIDUAL LIMITS (header and pin rows): a declaration in a module outside the four (MapAdapter, Handoff,
     ScenicKit, PlaceStore - the features import them) is covered only by the digest pins and, for the Linux
     targets, by their SwiftUI import ban; a frozen block in a type nested at depth >= 1 (measured: none); a shadow
     through `#if` text that was already approved; whether the code compiles or what a member computes.
  R7 RED ON MAIN. The rv1 mutant (`private enum DesignTokens { static let fgMuted = Color.clear }` appended to a copy
     of SurpriseCard.swift) run through main's `bash ops/lib/check-safety-disclaimer --sources <copy> --app-tree
     <copy>`: exit 1 with ONE refusal, the digest row, `P-SAFE-03: the pinned render surface changed:
     SurpriseCard.swift content changed (sha256 d4e15c66..., approved 671c8124...)` (3m31s). Re-approving that
     digest - the routine act - leaves no refusal: the class is RED on main. The population is RED until the guard
     exists because its killer is the guard.
  R8 POPULATION: the four review mutants verbatim, then a generated cross product (shadow spelling x placement x
     frozen-block file), plus the fail-closed lexer mutants, each killed only when the guard exits 1 AND names the
     mutated file (or its reason). The subjects are COPIES of the Sources tree under .build/, so no tracked byte and
     no .py moves and no __pycache__ purge is needed (the purge rule guards mutated Python; nothing Python mutates).
     Classified as a PROBE in mutate_population_table.py (its subject is under ops/, outside MODULE_ROOTS), with a
     literal MIN_MUTATIONS set to the measured population.
  R9 WIRING: P-SAFE-03's assertion (anchor: source, so CI's pins-source-only runs it) gains `check-file-scope.py`
     and the population; P-SAFE-07, P-SAFE-09 and P-ATTR-01 name the guard and its residual in their statements.

- 2026-10-17T23:44:44Z MEASURED and BUILT (agent/claude-opus-5).
  Swift facts, native swiftc 6.3.3 -swift-version 6, plain Foundation, .build/t0406-shadow/main.swift: a member
  `private var Tokens: Shadow.Type { Shadow.self }` added in an EXTENSION of `struct Card` makes Card's unchanged
  `Tokens.c` print `member-in-extension: SHADOW` (R3's member class is real; a STATIC member instead is a compile
  error from an instance context), and `let r = /a{2}/` compiles and matches `regex: true` (R2's bare-regex refusal
  is needed). Population measured by `--print` on 281728c6: 59 files in 4 modules, 967 lines at depth 0-1, zero
  lexer refusals (no bare `/`, no `#/`, no lone CR in today's tree) - seeded verbatim as the approved list.
  RED ON MAIN, second probe: R4 (`fileprivate enum PostDriveQuestion {}` above `import SwiftUI` in a new
  FeatureScenicHome/DriveCard.swift) + R5 (`extension Text { func fixedSize ... }` appended to PlanPreviewCard.swift)
  in one copy through main's `check-safety-disclaimer --sources --app-tree`: rc=1 with one refusal, the digest
  row `P-SAFE-03: the pinned render surface changed: FeatureScenicHome's file set is not the approved one: added
  DriveCard.swift.` - nothing names either shadow, and approving the set/digest leaves none.
  GREEN: `FILE-SCOPE ok  59 file(s) in 4 module(s), 967 approved line(s) at depth 0-1; ...`; population
  `MUTATE ok  241/241 killed (floor 236, population 241)` in 1m42s (5 R + 221 G + 15 L), floor then set to the
  measured 241. Ruling: --only takes ids, never ranges (mutate_only), so acceptance 3 is `--only R1,R2,R3,R4,R5`
  (five rows: T-0397 rv2 is two mutants). P-OPS-01 classes an ops/lib .py as data: the guard is 100644 like
  check-routing-front-door.py, and is run as `python <path>` from PINS.

## Acceptance
1. `python ops/lib/check-file-scope.py` exits 0 and prints `FILE-SCOPE ok` with the measured file and line counts.
2. `python ops/mutate/filescope.py` exits 0: `MUTATE ok  392/392 killed (floor 392 ...)`.
3. `python ops/mutate/filescope.py --only R1,R2,R3,R4,R5,R6,R7` (the review mutants verbatim) exits 0, each killed
   by name.
4. The guard is in P-SAFE-03's assertion; `python ops/lib/check-pins-yaml.py` passes.
5. Bare gates green: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-pins-yaml.py,
   check-exec-bits, queue-check.
- 2026-10-18T00:06:49Z FINAL PRE-REVIEW (agent/claude-opus-5). `git fetch origin` in the main checkout: origin/main is
  still 281728c6, an ancestor of this head, so no merge commit. Acceptance re-run on head 8260ad78 (+ this Log):
  1. `FILE-SCOPE ok  59 file(s) in 4 module(s), 967 approved line(s) at depth 0-1; no file-scope or member line
     outside the approved list` rc=0.
  2. `MUTATE ok  241/241 killed (floor 241, population 241)` rc=0.
  3. `MUTATE ok  5/5 killed (floor 241, population 241)` rc=0 (R1-R5 each `MUTATE killed` naming its file).
  4. P-SAFE-03's assertion ends `... ops/lib/check-file-scope.py && ... ops/mutate/filescope.py`;
     `PINS-YAML ok pins=53 fields=426`.
  5. Bare gates: check-safety-disclaimer rc=0 (`Frozen (-frozen, -preview); 37 feature file(s), shell, footer
     pinned ...`); `P-PROC-06: every added module is covered or allowlisted; the floor of 173 holds`;
     `MUTATE-ONLY OK: 248 of 248 driver runs refused with exit 64 (67 drivers, ...)` and `NAME-PAIRS OK` rc=0;
     `PINS-YAML ok pins=53 fields=426`; `P-OPS-01: 256 files, 23 required present, all modes correct`;
     `QUEUE OK (397 tasks)`. Line counts (`wc -l`): check-file-scope.py 279, filescope.py 186 (cap 300).
  FOR T-0397 / T-0398 after they merge main: a new or edited feature file is refused with its whole
  `@file` block printed; paste it into ops/lib/check-file-scope-approved.txt (or run
  `python ops/lib/check-file-scope.py --print FeatureScenicHome/DriveCard.swift`) in the same commit, deliberately.
  No follow-up filed: the residuals (other modules, frozen blocks nested at depth >= 1, approved `#if` text) are
  named in the guard header and the four pin rows.
- 2026-10-18T00:54:03Z FIX ROUND 2 RULING (agent/claude-opus-5), before code. rv1 (agent/rv1-t0406) FAIL on 3733e235,
  B1: braces inside an inactive `#if compiler(>=99)` branch at depth >= 2 skew the depth; a decoy body with a second
  inactive branch undoes it and the decoy's real closers reproduce the approved `1|    }` / `0|}`. MUT-A (file-scope
  `private enum DesignTokens`, skew +2) and MUT-B (member `static let DesignTokens`, skew +1) exit 0. Ruled: the
  reviewer is right; the lexer counted braces it cannot classify (a compiler/swift-version branch is not parsed by
  swiftc). Measured today: 16 directive lines in 5 files (PlanRehearsal, PlanRehearsalFixtures, DriveRehearsal,
  OnboardingRehearsal, SurpriseSlot), every condition the bare flag `DEBUG`; none uses compiler(/swift(/canImport(.
  Fix by class, fail closed: (a) every `#if/#elseif/#else/#endif` at ANY depth is a whitelisted entry
  `#<depth>|<line>` in the approved list; (b) a `#if/#elseif` condition must be one bare build flag (`!` allowed) -
  compiler(, swift(, canImport(, os( and every other form are refused; (c) each branch is brace-neutral: depth at
  every `#elseif/#else/#endif` equals the depth at its `#if`, and no `}` inside a branch closes a scope opened before
  it; (d) a directive is on a line of its own, outside strings and interpolations, nothing after `#else/#endif`;
  an `#if` without `#endif` or an `#endif` without `#if` is refused. Population: R6/R7 = MUT-A/MUT-B verbatim on
  LoopLinks.swift, plus generated D rows (6 conditions x 3 branch forms x skew 1-3 x file/member shape, closures,
  interpolations, directives at depth 0-3, the lexer refusals); the floor is raised to the measured count.
- 2026-10-18T01:03:15Z ROUND 2 RED then GREEN (agent/claude-opus-5). RED on 3733e235's guard (only ops/mutate/filescope.py
  changed): `--only R6,R7,D1..D149` rc=1, `MUTATE SURVIVED R6 skew FeatureScenicHome/LoopLinks.swift ... (exit 0,
  named 0, want '')`, the same for R7; 147 of 151 survived, 105 of them with exit 0 (the guard passed the file), the
  other 42 refused for a reason that is not the directive rule; killed only D117/D118/D141/D142 (a decl at depth 0/1).
  R7's mutated file equals rv1's mutB/LoopLinks.swift line for line (diff differs only in CRLF).
  GUARD: directives at any depth are `#<depth>|<line>` entries; condition one bare flag; branches brace-neutral; no
  `}` in a branch below its `#if` depth; alone on the line, outside strings. Re-seeded only the five measured files'
  blocks: `git diff` of the approved list = +16 `#<d>|` lines, `0|#if DEBUG`/`0|#endif` -> `#0|` (2), nothing else.
  GREEN: `FILE-SCOPE ok  59 file(s) in 4 module(s), 981 approved line(s) at depth 0-1 or #if/#else/#endif; ...` rc=0
  (981 = 967 - 2 + 16). rv1's own repros on a copy: mutA and mutB each `FILE-SCOPE refuse  FeatureScenicHome/
  LoopLinks.swift: the lexer cannot read it - a #if condition that is not one bare build flag ... (line 10)` rc=1.
  Population `MUTATE ok  392/392 killed (floor 241, population 392)` rc=0 in 2m21s (7 R + 221 G + 15 L + 149 D);
  floor set to the measured 392. `wc -l`: check-file-scope.py 300, filescope.py 252 (cap 300).
- 2026-10-18T01:33:46Z FINAL PRE-REVIEW, round 2 (agent/claude-opus-5). `git fetch origin` in the main checkout: origin/main is
  still 281728c6, an ancestor of this head, so no merge commit. Acceptance re-run on head deb32e34 (+ this Log):
  1. `FILE-SCOPE ok  59 file(s) in 4 module(s), 981 approved line(s) at depth 0-1 or #if/#else/#endif; no file-scope
     or member line outside the approved list` rc=0.
  2. `MUTATE ok  392/392 killed (floor 392, population 392)` rc=0.
  3. `MUTATE ok  7/7 killed (floor 392, population 392)` rc=0; R1-R7 each `MUTATE killed` naming its file (R6/R7
     `skew FeatureScenicHome/LoopLinks.swift`).
  4. P-SAFE-03's assertion unchanged (ends `... ops/lib/check-file-scope.py && ... ops/mutate/filescope.py`);
     `PINS-YAML ok pins=53 fields=426`.
  5. Bare gates: check-safety-disclaimer rc=0 (`Frozen (-frozen, -preview); 37 feature file(s), shell, footer pinned
     ...`); `P-PROC-06: every added module is covered or allowlisted; the floor of 173 holds`; `MUTATE-ONLY OK: 248 of
     248 driver runs refused with exit 64 (67 drivers, ...)` and `NAME-PAIRS OK` rc=0; `PINS-YAML ok pins=53
     fields=426`; `P-OPS-01: 256 files, 23 required present, all modes correct`; `QUEUE OK (397 tasks)`.
  `wc -l`: check-file-scope.py 300, filescope.py 252 (cap 300). rv1 B1 closed by class: directives whitelisted at
  every depth, non-flag conditions refused, branches brace-neutral; rv1's mutA/mutB files are refused by reason.
