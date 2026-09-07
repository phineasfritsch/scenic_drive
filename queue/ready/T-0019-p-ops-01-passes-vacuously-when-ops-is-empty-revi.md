---
id: T-0019
title: P-OPS-01 passes vacuously when ops/ is empty (reviewer-5 finding)
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml]
pins_affected: [P-OPS-01]
reviewer: null
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
