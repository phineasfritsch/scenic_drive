---
id: T-0019
title: P-OPS-01 passes vacuously when ops/ is empty (reviewer-5 finding)
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T10:04:12Z
lease_expires_at: 2026-09-07T13:04:12Z
worktree: ../wt/T-0019
branch: task/T-0019
exclusive: []
touches: [pins/PINS.yaml, ops/lib/check-exec-bits]
pins_affected: [P-OPS-01]
reviewer: agent/reviewer-10
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

agent/reviewer-5 found this while re-reviewing T-0015. P-OPS-01's assertion is

    test -z "$(git ls-files -s ops .githooks | awk ...)"

If `git ls-files -s ops .githooks` returns NOTHING - because someone deleted `.githooks/pre-commit`, or renamed
the directories - the awk output is empty, `test -z ""` is true, and the pin reports OK. It passes on an empty
artefact, which CLAUDE.md forbids in as many words.

FIX: require a minimum file count as well, e.g. prefix the assertion with
    test "$(git ls-files ops .githooks | wc -l)" -ge 17 &&
or better, assert the presence of the specific load-bearing files (ops/test, ops/sane, ops/check-pins,
.githooks/pre-commit, .githooks/commit-msg) so a rename cannot silently empty the set.

RED: `git rm --cached -r .githooks` (or move ops/ aside) and show ops/check-pins still reports P-OPS-01 OK today,
then fails after the fix. Restore afterwards.

This is the same class as any other vacuous guard: sweep the other pins for it in the same task.

## Log
- 2026-09-07T10:04:12Z claimed by agent/claude-opus-5; lease until 2026-09-07T13:04:12Z
- 2026-09-07T12:10:00Z The one-liner assertion was `test -z "$(git ls-files -s ops .githooks | awk ...)"`. Over an EMPTY file list awk prints nothing, `test -z ""` is true, and the pin reported OK - so a deleted .githooks/ or a renamed ops/ would have read as "all modes correct" forever. That is the "never weaken an assertion to something that passes on an empty artefact" rule, violated by the pin meant to enforce discipline.
- 2026-09-07T12:10:00Z Moved the logic into ops/lib/check-exec-bits so the pin is one readable line and the checks can carry their own error messages. Three checks now: (1) at least 17 tracked files under ops/ and .githooks/; (2) all 14 load-bearing scripts actually tracked by name, so a rename cannot empty the set; (3) modes - scripts 100755, data (*.json/*.txt/*.md and ops/api-url) 100644.
- 2026-09-07T12:10:00Z GREEN: "P-OPS-01: 22 files, 14 required present, all modes correct"; ops/check-pins -> PINS ok=9 pending=3 failed=0.
- 2026-09-07T12:10:00Z RED 1: chmod -x ops/sane -> "ops/sane (script, should be 100755, is 100644)", exit 1.
- 2026-09-07T12:10:00Z RED 2: chmod +x ops/lib/ro_cases.json -> "(data, should be 100644, is 100755)", exit 1. A blanket chmod +x still cannot satisfy the pin.
- 2026-09-07T12:10:00Z RED 3: git rm --cached ops/merge -> "load-bearing script(s) not tracked: ops/merge", exit 1. A rename or deletion is caught by name, not just by count.
- 2026-09-07T12:10:00Z RED 4 (the vacuous case this task exists for): ran the script in a fresh throwaway git repo containing only itself -> "only 1 files tracked ... An empty or truncated set must never read as 'all modes correct'", exit 1. Under the OLD assertion that same situation returned OK.
- 2026-09-07T12:10:00Z moved to review/, reviewer agent/reviewer-10
