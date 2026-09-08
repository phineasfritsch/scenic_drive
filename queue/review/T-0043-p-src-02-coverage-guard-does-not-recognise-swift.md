---
id: T-0043
title: P-SRC-02 coverage guard does not recognise Swift versioned manifests (Package@swift-6.0.swift)
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T22:28:15Z
lease_expires_at: 2026-09-08T00:28:15Z
worktree: null
branch: task/T-0043
exclusive: []
touches: [ops/lib/check-line-cap]
pins_affected: []
reviewer: agent/reviewer-43
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/check-line-cap`'s coverage guard (added by T-0037) finds Swift packages with `git ls-files
'*Package.swift'`. SwiftPM also supports version-specific manifests named `Package@swift-<version>.swift`,
which that pathspec does not match. Confirmed empirically by agent/reviewer-21 while reviewing T-0037 and
filed there as MINOR.

No file dodges the 300-line cap because of this - the cap runs over `git ls-files '*.swift'`, which catches
every Swift file regardless - and it cannot be exploited today because SwiftPM requires a base `Package.swift`
to exist for a package to build at all. What it means is narrower: a package that had ONLY a versioned
manifest would not be seen by the guard, so the guard would not notice if that package fell out of the checked
set. It is a hole in the guard, not in the cap.

- Widen the pathspec to catch `Package@swift-*.swift` as well, or state in the check why the base-manifest
  requirement makes that unnecessary - one or the other, not silence.
- Demonstrate red: a throwaway repo whose package carries only `Package@swift-6.0.swift`, with the FILES glob
  narrowed so the package genuinely falls out; show the guard missing it before the change and catching it
  after.

Also noted by reviewer-21, informational: there is no vendoring exemption in the cap, and CLAUDE.md does not
offer one either, so today's behaviour is faithful to the rule. Whoever first vendors third-party Swift will
need to decide that deliberately rather than discover it.

## Log
- 2026-09-07T22:28:15Z claimed by agent/unknown; lease until 2026-09-08T00:28:15Z

- 2026-09-08T05:55Z claimed and fixed by agent/claude-opus-5, stacked on task/T-0037 (done), which added the
  coverage guard and owns this file.

  **Widened, not excused.** The brief offered "widen the pathspec, or state why the base-manifest requirement
  makes it unnecessary - one or the other, not silence." Widened. The excuse was available and is weaker than
  it looks: SwiftPM does require a base `Package.swift` today, so the versioned-only package cannot build -
  but this guard is not about what builds. It exists to notice when a package falls OUT of the checked set,
  and a guard that only enumerates packages it expects to be well-formed will not notice the malformed one
  going missing. That is the case it is for.

  `git ls-files '*Package.swift' '*Package@swift-*.swift'`, reduced to directories and de-duplicated, because
  a package shipping both spellings is one package and would otherwise have been reported twice. The loop now
  consumes directories rather than manifest paths, which is what it always wanted.

  **The demonstration had to be narrow, because the hole is.** A `Package@swift-6.0.swift` is itself a .swift
  file, so while FILES globs every tracked .swift the package always contributes and there is nothing to
  report. The hole only shows once FILES is narrowed - which IS the regression this guard exists to catch, and
  exactly how the Apple package was silently exempt before T-0037. So the demo narrows FILES to the
  pre-T-0037 shape and compares the two manifest spellings:

      control: package has a base Package.swift
        old check:  CAUGHT: pkg
        new check:  CAUGHT: pkg
      the bug: package has ONLY Package@swift-6.0.swift
        old check:  MISSED (exit 0): P-SRC-02: 10 Swift files tracked, none over 300 lines
        new check:  CAUGHT: pkg
      both spellings present: pkg reported 1 time(s) (must be 1)
      the real repo, unnarrowed: P-SRC-02: 10 Swift files tracked, none over 300 lines

  The control line is the one that makes the middle line mean anything: the old check catches the ordinary
  case, so its silence on the versioned-only case is about the spelling and not about the demo being broken.

  **Verification:** `ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`;
  `ops/check-pins --source-only` -> `PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only`
  (the push gate still runs this pin and is unchanged in cost); `ops/test` -> `TESTS linux=50/50 ios=skipped
  failed=0 skipped=0` / `OK`; `ops/queue-check` -> `QUEUE OK (34 tasks)`. GitHub Actions is DISABLED repo-wide
  (T-0053), so there is no CI signal at all.

  **The informational note in the brief stands and I did not act on it.** There is still no vendoring
  exemption in the cap and CLAUDE.md offers none, so today's behaviour remains faithful to the rule. Whoever
  first vendors third-party Swift decides that deliberately.

  **What to attack.** The dedupe runs `dirname` per line in a subshell loop, which is fine for a handful of
  manifests and silly for a thousand - it is not hot, but say so if you disagree. More usefully: this fixes
  the guard for Swift while `ops/lib/check-line-cap` still globs Swift ONLY, so the 300-line cap does not
  reach Python or TypeScript at all - where every M2 task is now working, and where `services/etl/etl/
  byways.py` sits at 296 lines and `ops/lib/queue.py` at 498. That is filed as T-0058 and T-0059 and it is a
  much bigger hole than the one this task closes; a reviewer might reasonably ask why I did the small one
  first. The answer is that they touch the same file and would have collided, and this one was already in
  ready/ with a written brief.
