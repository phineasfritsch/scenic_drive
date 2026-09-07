---
id: T-0037
title: P-SRC-02 will silently exempt apps/ios/Packages/ScenicApp Swift files once T-0010 lands
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T15:44:53Z
lease_expires_at: 2026-09-07T18:44:53Z
worktree: ../wt/T-0037
branch: task/T-0037
exclusive: []
touches: [ops/lib/check-line-cap]
pins_affected: []
reviewer: agent/reviewer-21
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/check-line-cap` (P-SRC-02) enforces CLAUDE.md's 300-line cap over

    git ls-files 'Sources/**/*.swift' 'Tests/**/*.swift'

which is the ROOT package and nothing else. `apps/ios/Packages/ScenicApp` - DesignSystem, MapAdapter,
NavAdapter and every feature target, i.e. most of the Swift that will ever be written for this product - is
outside those globs. The moment T-0010 lands that package, its files are exempt from the cap and the check
still prints a cheerful one-liner. CLAUDE.md puts no package outside the cap. Found by agent/reviewer-13 while
reviewing T-0019, before the exempt tree existed - which is the only reason it is being fixed rather than
discovered later by a 900-line view controller.

Fix: examine every tracked `.swift` file at any depth, and add a coverage guard so that narrowing the set
again is loud rather than silent.

Stacked on `task/T-0035`, not on `main`: both tasks edit this one file, T-0035 is reviewed and only waiting on
CI, and two branches editing one file from a common ancestor that lacks the first fix is how one of them gets
silently lost. The PR targets `task/T-0035` and should be retargeted to `main` when that merges.

## Log
- 2026-09-07 claimed by agent/claude-opus-5; reviewer agent/reviewer-21; branch off task/T-0035.

- **RED, before any change.** Built a genuine 301-line Swift file in the tree the pin does not reach and
  staged it, along with a stub `Package.swift` so the package exists the way T-0010 will create it:

      apps/ios/Packages/ScenicApp/Package.swift
      apps/ios/Packages/ScenicApp/Sources/DesignSystem/Tokens.swift   (301 lines, no trailing newline)

      $ bash ops/lib/check-line-cap
      P-SRC-02: 9 Swift files tracked, none over 300 lines
      exit=0

  The file is not merely allowed, it is not even counted - the total stays at 9. A check that reports a number
  which silently excludes most of the codebase is worse than no number.

- **The fix.** `git ls-files '*.swift'` (git's pathspec matches at any depth) replaces the two rooted globs.
  Verified the pathspec really does reach the nested package before relying on it:

      $ git ls-files '*.swift'
      Package.swift
      Sources/ScenicKit/... (5)
      Tests/ScenicKitTests/... (4)
      apps/ios/Packages/ScenicApp/Package.swift
      apps/ios/Packages/ScenicApp/Sources/DesignSystem/Tokens.swift

  Note the root `Package.swift` is now inside the cap too, which is correct - it is Swift, and CLAUDE.md's
  file discipline names no exemption. That is why the clean-tree count moves from 9 to 10.

- **GREEN on the same probe:**

      $ bash ops/lib/check-line-cap
      P-SRC-02: file(s) over the 300-line cap:
        apps/ios/Packages/ScenicApp/Sources/DesignSystem/Tokens.swift (301 lines)
      exit=1

- **Coverage guard, demonstrated red on its own.** Fixing the glob today does not stop someone re-narrowing it
  tomorrow, and the failure would again be silence. So: every tracked `*Package.swift` names a Swift package,
  and a `Package.swift` is itself a `.swift` file, therefore a package whose directory contributes NOTHING to
  the examined set proves the set has been narrowed. Simulated exactly that regression by putting the old
  globs back with the guard in place:

      $ bash ops/lib/check-line-cap
      P-SRC-02: Swift package(s) contribute no file to the checked set - the 300-line cap does not reach them:
        apps/ios/Packages/ScenicApp
      exit=1

  It names the package that fell out, which is the fact the reader needs.

- **Vacuous-pass floor re-checked**, since the file set changed: a throwaway `git init` repo containing only a
  copy of the script, zero tracked Swift files:

      P-SRC-02: only 0 tracked .swift file(s) (expected >= 5).
        An empty or truncated set must never read as 'no file exceeds 300 lines'.
      exit=1

  Scratch repo deleted.

- **Probe removed** (`git rm --cached` + `rm -rf apps/ios/Packages`), tree clean apart from the one-file fix:

      $ bash ops/lib/check-line-cap   -> P-SRC-02: 10 Swift files tracked, none over 300 lines   exit=0
      $ bash ops/check-pins           -> PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux   exit=0
      $ bash ops/queue-check          -> QUEUE OK (34 tasks)   exit=0
      $ bash ops/test                 -> TESTS linux=50/50 ios=skipped failed=0 skipped=0 / OK   exit=0
      $ git status --short            -> M ops/lib/check-line-cap
      $ git ls-files -s ops/lib/check-line-cap -> 100755 (exec bit intact)

  The `linux=50/50` floor is this branch's, not main's 76: task/T-0035 predates the ETL pytest tier.

- **Not verified: CI.** GitHub Actions stopped executing at about 15:11 UTC - every run since, on every branch
  including `main`, completes in 4-6 seconds with zero steps and no downloadable log, which is an Actions
  minutes or spending-limit problem on a private free-plan repo, not this diff. All of the above is local.
  agent/reviewer-21 should re-derive it locally rather than waiting on a check that cannot run.

- Handing to agent/reviewer-21; state -> review.
