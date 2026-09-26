---
id: T-0243
title: ops/lib Swift readers fail closed - limbs (a)-(f) of check-map-attribution and check-drive-copy stop cutting // inside a line; only whole-comment lines are dropped and every identifier-naming line is compared whole
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-map-attribution, ops/lib/check-map-attribution-lib, ops/lib/check-map-attribution-sites, ops/lib/check-map-attribution-mutations, ops/lib/check-drive-copy]
pins_affected: [P-ATTR-01]
reviewer: null
depends_on: [T-0236]
verify: [ops/check-pins]
acceptance:
  - "every Swift reader under ops/lib uses the fail-closed rule T-0236 round 4 ruled for limb (g): no mid-line // cutting and no string-state tracking; a line whose trimmed text starts with // is dropped, every other line naming a guarded identifier is compared whole against its approved list (re-measured and quoted)"
  - "rv3-t0236's three lexer escapes (a quote inside a /* */ block comment, a raw string, a string inside an interpolation - driver at .artifacts/rv3-t0236/drive.py in the main checkout) are --prove-red rows for EACH limb that reads Swift, and rv1-t0236's M3d (a HandoffDrive case inside a string interpolation in DriveCopy, which exits 0 on main) is a --prove-red row of check-drive-copy - each shown red before, green after"
  - "check-drive-copy --prove-red finishes in under 5 minutes on this box (rv2-t0236 measured over 10), or the Log rules why not"
  - "a Swift file under apps/ios that contains a CR byte (0x0D) is REFUSED by every Swift-reading limb, fail closed - rv4-t0236's B1-r4: a bare CR ends a // comment for Swift's lexer but not an awk record, so '// x<CR>let dataCredit = MapStyle.demoAttribution' was dropped as a comment line and compiled as code (driver .artifacts/rv4-t0236/attack.py in the main checkout, S3a/S3b exit 0 on PR #130's head 41654c5); S3a and S3b become --prove-red rows"
---
## Brief

PR #130 went four review rounds on one class: an awk reader that tracks string state and cuts // can be steered by
ordinary Swift spellings into dropping a line from the population it whitelists. Round 4 closed the class for limb
(g) by not parsing at all. The other limbs and check-drive-copy still parse. Overlaps T-0238's interpolation clause -
whichever lands second rules the merge.

## Log
- 2026-09-26T02:16:05Z filed by agent/claude-opus-5 (orchestrator) from rv3-t0236's B1-r3 and the round-4 ruling.
- 2026-09-26T03:07:54Z added by agent/claude-opus-5 (orchestrator): the bare-CR clause from rv4-t0236's B1-r4; PR #130 merges with this gap recorded under CLAUDE.md's review-rounds rule (P-ATTR, not P-SAFE; four rounds spent on the reader).
