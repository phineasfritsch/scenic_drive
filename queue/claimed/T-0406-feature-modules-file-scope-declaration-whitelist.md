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
