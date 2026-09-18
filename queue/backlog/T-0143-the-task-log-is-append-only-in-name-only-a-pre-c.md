---
id: T-0143
title: the task Log is append-only in name only: a pre-commit check that a branch's own queue file never changes or duplicates a dated line
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/pre-commit, ops/lib/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Found by the hourly panel's PROCESS lens and grounded by its fable pass. In the last 24 hours two task files
had dated Log lines rewritten by a `str.replace` renumbering (T-0126 at `38d252f`, T-0133 at `72e4802` - both
failed review on it) and one had its round-7b entry appended THREE times under one timestamp (T-0133 before
`d89e721`). `queue/README.md` says "`## Log` is append-only" and nothing enforces it.

Do: pre-commit check #4 - for the branch's own task file (the one whose id matches `^task/(T-[0-9]+)`),
compare against the merge-base copy: every `- 20..` dated line present in the base must be byte-identical
in the staged file, and no dated line may appear twice. Fail closed if the base copy cannot be read. A
fixture in ops/lib/ with at least: an append (must COMMIT), an edit to an old line (must REFUSE, naming the
line), a duplicated entry (must REFUSE), a new task file with no base (must COMMIT). Demonstrated red
against `git show 38d252f:` of T-0126's file.

## Log
- 2026-09-18T03:05:00Z filed by agent/claude-fable-5-1 from the hourly panel's grounded synthesis (.artifacts/panel/last.md). ops/new-task allocated T-9902 again ([[T-0138]]); renamed by hand.
