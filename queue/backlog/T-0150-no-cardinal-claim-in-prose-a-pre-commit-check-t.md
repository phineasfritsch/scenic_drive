---
id: T-0150
title: no cardinal claim in prose - a pre-commit check that a count in a pin statement, an acceptance line or an ops comment was printed by a command, and a sweep of the merged ones
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.githooks/pre-commit, ops/lib/, CLAUDE.md, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0143]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Found by the hourly panel's PROCESS lens (2026-09-18 ~10:13) and grounded by its fable pass. The one defect
every review round in this repository finds is a number in prose that no command printed: the round-1
review of PR #88 found eleven things, nine of them that shape; the round-8 review of PR #82 found the round-7
Log carrying a paragraph three times; T-0139 was signed off with its PR body saying `544 lines` where the
file has 552; PINS.yaml:91 says "six cases" where the docstring it points at says seven; PR #71's
`b687caf` acceptance quoted 55 where the runs print 56 and 63. The rounds converge in substance (the code
findings shrink each round) and cycle on this. It survives sign-off, so it is not a review-throughput
problem; it has to be refused at WRITE time.

**The rule**, one line in CLAUDE.md's Verification section: *no cardinal claim in prose - paste the command
and its output, or say nothing about the number.*

**The check**, pre-commit #4, narrow and mechanical: over the staged versions of `pins/PINS.yaml`
`statement:` lines, every `acceptance:` line in a queue task file, and comments in `ops/` and `pins/`, a
number that names a count of files/tests/cases/mutations/lines (`\b[0-9]+ (files?|tests?|cases?|
mutations?|lines?|suites?)\b`) must sit inside a backtick-quoted command output on the same line, or the
line must carry `measured:` with the command. Demonstrated red on `git show b687caf:queue/claimed/T-0116-*.md`
lines 283-284 and on `pins/PINS.yaml:91`, then green on the tree with those corrected. Refusal names the file
and line. Whitelist: dated Log lines (T-0143's append-only check owns those; never rewrite them - annotate).

**The sweep**, one commit: correct the already-merged instances (T-0139's PR body number stays where it is -
a PR body is not in the tree - but its task file's quote of it gets a dated annotation; PINS.yaml:91's
"six" -> what the docstring says, with the command that prints it).

Sequenced after T-0143 because both edit `.githooks/pre-commit` check numbering and both refuse on queue
files; land T-0143 first and reuse its staged-file iteration. Pair the check with the author prompt: every
fixer/author prompt already says "every acceptance line is a command that really prints what it quotes";
the hook is what makes that true when the prompt is ignored.

## Log
- 2026-09-18T17:55:00Z filed by agent/claude-fable-5-1 from the 10:13 panel (PROCESS lens, grounded). Not started.
