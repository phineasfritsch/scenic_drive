---
id: T-0043
title: P-SRC-02 coverage guard does not recognise Swift versioned manifests (Package@swift-6.0.swift)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T22:28:15Z
lease_expires_at: 2026-09-08T00:28:15Z
worktree: null
branch: task/T-0043
exclusive: []
touches: [ops/lib/check-line-cap]
pins_affected: []
reviewer: null
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
