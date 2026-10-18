---
id: T-0410
title: sane_version.py imports() - no v- row imports from a services/api/src subdirectory, so resolving against src/ survives
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, queue/]
pins_affected: []
reviewer: null
depends_on: [T-0402]
verify: [ops/check-pins, ops/queue-check]
acceptance:
  - "bash ops/lib/check-sane-prod --only <the new v- row(s)> -> SANE-PROD pass, exit 3 with the whole version line"
  - "RED: mutant posixpath.join(posixpath.dirname(path), spec) -> posixpath.join(SRC, spec) in imports() -> the new row fails"
---
## Brief

Found 2026-10-18 by agent/rv2-t0402 reviewing PR #296 (T-0402) round 2. In ops/lib/sane_version.py imports(), the
mutant `posixpath.join(posixpath.dirname(path), spec)` -> `posixpath.join(SRC, spec)` survives all 36 v- rows of
check-sane-prod (`SANE-PROD ok 36/36`): every fixture import sits in a file directly under services/api/src
(src/index.ts, src/spell.ts), where the importing file's directory equals SRC. Measured: today's tree has no
subdirectory under services/api/src (`git ls-files services/api/src` has no path four levels deep), so the mutant is
equivalent today. Once a src/sub/x.ts imports `../../../etl/...`, resolving against SRC lands one level too high,
the changed target is missed and the version row says ok while a deploy is pending (fail open).

Fix: add to BASE in ops/lib/sane_version_cases.py a file in a src subdirectory (and a two-deep one) whose import
names its own target outside services/api, plus a v- row per depth changing only that target -> exit 3
`(1 bundle, 0 unclassified, 0 not bundled)`. Show the mutant above red, then restored green. Run only the v- rows.

## Log
- 2026-10-18T01:36:34Z filed by agent/rv2-t0402 from the PR #296 round-2 review (T-0402 Log, same timestamp).
