---
id: T-0037
title: P-SRC-02 will silently exempt apps/ios/Packages/ScenicApp Swift files once T-0010 lands
state: done
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

- 2026-09-07T agent/reviewer-21 independent re-derivation. Re-ran everything the owner claimed rather than
  trusting the log; did not reuse any of the owner's numbers.

  **Re-derived, all confirmed:**
  - Built the probe myself in the live worktree: `apps/ios/Packages/ScenicApp/Package.swift` +
    a genuine 301-line `Sources/DesignSystem/Tokens.swift`, `git add`ed both.
    `git show HEAD~1:ops/lib/check-line-cap > /tmp/old-clc && bash /tmp/old-clc` ->
    `P-SRC-02: 9 Swift files tracked, none over 300 lines` exit=0 - old check neither sees nor counts the file.
    Current `bash ops/lib/check-line-cap` -> `P-SRC-02: file(s) over the 300-line cap:
    apps/ios/Packages/ScenicApp/Sources/DesignSystem/Tokens.swift (301 lines)` exit=1. `git rm --cached` +
    `rm -rf`, tree back to clean, back to 10/exit 0.
  - Coverage-guard regression scenario, reproduced independently: staged the same probe pair, ran a scratch
    copy of the current script with only the FILES glob reverted to the old
    `'Sources/**/*.swift' 'Tests/**/*.swift'` (guard left as-is) ->
    `P-SRC-02: Swift package(s) contribute no file to the checked set ...
    apps/ios/Packages/ScenicApp` exit=1. Confirms the guard catches the exact regression it exists for.
  - `dir == "."` branch (root-only `Package.swift`, no other manifest anywhere): built in a throwaway
    `git init` repo (5 files total to clear MIN_FILES) - passes clean, exit 0, no false positive.
  - Path with a space (`Sources/My Package/Package.swift` + a sibling `.swift` file): throwaway repo,
    7 files, exit 0 - `dirname`/`[[ == *]]` handle the space correctly, no false anything.
  - `Foo` vs `FooBar` prefix collision (manifest at `Sources/Foo/Package.swift` with zero sibling files,
    unrelated files under `Sources/FooBar/`): exit 0, no false positive. Traced why: `prefix` always gets a
    trailing `/` when `dir != "."`, so `Sources/FooBar/D.swift` cannot match prefix `Sources/Foo/` (13th char
    differs, `B` vs `/`). The trailing slash is exactly what defeats the prefix-substring bug class the task
    asked me to look for. Also note structurally: since every `Package.swift` is itself matched by
    `git ls-files '*.swift'`, every manifest's own directory is *trivially* self-covering in the current
    (unnarrowed) FILES glob - the guard only has teeth against a *future* re-narrowing of FILES, which is
    exactly its stated purpose and exactly what the regression scenario above re-confirms.
  - MIN_FILES floor: fresh throwaway `git init` repo, zero tracked `.swift` files ->
    `P-SRC-02: only 0 tracked .swift file(s) (expected >= 5).` exit=1. Still fires after the glob widened.
  - Branch stacking: `git merge-base task/T-0035 HEAD` == `97da4ba` (tip of T-0035), confirmed an ancestor of
    T-0037's HEAD; `ops/lib/check-line-cap:59` uses `awk 'END{print NR}'`, not `wc -l` - T-0035's fix is
    present, not collided-with. `gh pr view 20` confirms `baseRefName: task/T-0035`. `git merge-base
    --is-ancestor 97da4ba origin/main` -> not an ancestor, so T-0035 is genuinely not yet merged and the
    stacking is correct, not stale.
  - Root `Package.swift` newly in scope: 27 lines (`awk 'END{print NR}' Package.swift`), harmless today.
    Confirmed clean-tree count is exactly 10 via `git ls-files '*.swift'` before running the check. No
    generated code, no snapshot/fixture files of concern (`SolarFixtures.swift` is 87-line hand-written test
    data, not codegen), no `.build/` artifacts tracked - `.gitignore` covers `.build/` and
    `apps/ios/Packages/ScenicApp/.build/` already, ahead of the package existing.
  - No vendored/third-party Swift currently tracked (`.gitmodules` absent, no `vendor/`, `Pods/`,
    `Carthage/`, `checkouts/` paths under git). Not a live defect.
  - Exec bit: `git ls-files -s ops/lib/check-line-cap` -> `100755`. Intact.

  **MINOR (non-blocking) - versioned SPM manifest naming not recognized by the coverage guard.**
  `ops/lib/check-line-cap:45`, the manifest-discovery pathspec `git ls-files '*Package.swift'`, does not match
  Swift's own version-specific manifest convention `Package@swift-<version>.swift` (e.g.
  `Package@swift-6.0.swift`) - confirmed empirically in a throwaway repo: a directory containing only
  `Sources/Versioned/Package@swift-6.0.swift` and no base `Package.swift` produces zero entries from that
  pathspec, so the coverage guard never even considers that directory a package and can't flag it if FILES is
  later re-narrowed to exclude it. Concrete failure scenario: a future package ships only a version-pinned
  manifest and someone re-narrows the FILES glob to skip that directory - the coverage guard, keyed only on
  literal `*Package.swift`, stays silent instead of naming the directory, exactly the silent-narrowing failure
  mode this pin exists to prevent. Mitigating factors, why this stays MINOR and not MAJOR: (1) SwiftPM requires
  a base `Package.swift` for a directory to resolve as a package at all - `Package@swift-*.swift` files are
  supplements, never a replacement - so this exact directory shape cannot occur in a buildable SPM package
  today; (2) it doesn't let any file dodge the 300-line cap itself - the FILES set (`git ls-files '*.swift'`)
  already sweeps up `Package@swift-*.swift` files unconditionally regardless of the guard; only the guard's
  regression trip-wire is blind in this one unreachable-today shape. No repro currently possible against this
  repo's tree (no versioned manifests exist). Filing as forward-looking, not required to block this PASS.

  **Informational, non-blocking - no vendoring exemption.** CLAUDE.md's file-discipline section states the
  300-line cap with no carve-out for vendored/third-party code, and the fix's "examine every tracked `.swift`
  at any depth" is faithful to that. If this repo ever checks in a vendored dependency's Swift source (none
  today), the cap and the coverage guard would both apply to code this team doesn't author or control. That's
  arguably correct per the letter of CLAUDE.md as written today; flagging only so a future task adding
  vendored code knows to either get a CLAUDE.md exemption or accept the cap applies.

  **Verification, all output reproduced independently in this worktree (after
  `cd services/api && npm ci --no-audit --no-fund`, per the task's known-gap note / T-0040):**

      $ bash ops/lib/check-line-cap
      P-SRC-02: 10 Swift files tracked, none over 300 lines
      exit=0

      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      exit=0

      $ bash ops/queue-check
      QUEUE OK (34 tasks)
      exit=0

      $ bash ops/test
      TESTS linux=50/50 ios=skipped failed=0 skipped=0
      OK
      exit=0

  All four match the owner's claimed numbers exactly. `linux=50/50` is this branch's floor (task/T-0035
  predates the ETL pytest tier), not main's 76 - consistent with the task brief, re-confirmed rather than
  assumed. `git status --short` clean after every probe was torn down.

  **Verdict: PASS.** No BLOCKER, CRITICAL or MAJOR found. The fix does what it claims: the root cause (narrow
  globs missing the whole Apple package tree) is closed, demonstrated red-then-green independently, and the
  coverage guard is real - it fires on the exact regression it was built for and survives every adversarial
  shape from the review brief (root-only manifest, spaced path, prefix-collision directory names) without a
  false positive or false negative, with one narrow MINOR gap (versioned manifest naming) that cannot presently
  be exploited and does not weaken the actual 300-line enforcement. Branch stacking on task/T-0035 verified
  correct and not stale. CI is genuinely not runnable right now (platform billing block, not this diff) -
  not treated as a defect per the task brief.
