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

## Acceptance
1. `python ops/lib/check-file-scope.py` exits 0 and prints `FILE-SCOPE ok` with the measured file and line counts.
2. `python ops/mutate/filescope.py` exits 0: `MUTATE ok  N/N killed (floor N ...)`, N the literal MIN_MUTATIONS.
3. `python ops/mutate/filescope.py --only 1-4` (the four review mutants verbatim) exits 0, each killed by name.
4. The guard is in P-SAFE-03's assertion; `python ops/lib/check-pins-yaml.py` passes.
5. Bare gates green: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-pins-yaml.py,
   check-exec-bits, queue-check.
