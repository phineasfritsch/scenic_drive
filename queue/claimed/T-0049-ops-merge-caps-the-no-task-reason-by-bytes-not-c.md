---
id: T-0049
title: ops/merge caps the no-task reason by bytes, not characters, and can split a UTF-8 sequence
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T21:35:40Z
lease_expires_at: 2026-09-07T23:35:40Z
worktree: ../wt/T-0049
branch: task/T-0049
exclusive: []
touches: [ops/merge, ops/lib/check-merge-reason-cap, pins/PINS.yaml]
pins_affected: [P-OPS-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/merge:52,60-61` caps the sanitised `--no-task-reason` at "200 characters" using `${#no_task_reason}` and
`${no_task_reason:0:200}`, which count BYTES in this shell even under `LC_CTYPE=C.UTF-8`. agent/reviewer-26
reproduced it while reviewing T-0044: 198 ASCII characters plus two emoji is 200 characters and 206 bytes, so
the truncation lands mid-sequence and splits a 4-byte UTF-8 character - `xxd` shows `41 f0 9f 2e 2e`, with
`f0 9f` orphaned - putting invalid UTF-8 into the audit line.

This does NOT reopen the injection T-0044 closed: every UTF-8 lead and continuation byte is >= 0x80, so no CR,
LF or ESC can ever fall out of a split. It is a data-integrity and documentation-mismatch defect, and the
audit trail is the one thing on that code path that has to be trustworthy.

- Count characters, or truncate on a character boundary, or say "bytes" in the message and the comment. Any of
  the three is defensible; pick one and argue it in the log.
- Demonstrate red with reviewer-26's exact construction (198 ASCII + 2 emoji) and check the bytes with `xxd`
  rather than eyeballing the terminal, which will happily render a mangled sequence as a replacement glyph.
- Confirm the injection defences T-0044 added still hold afterwards: newline, CR, ESC, U+2028, U+0085, and the
  `>>>`/`<<<` delimiters.

## Log
- 2026-09-07T21:35:40Z claimed by agent/claude-opus-5 (session 01SS4jAGs2oyr4Z4Wd8yK82t); lease until 2026-09-07T23:35:40Z.
  Branching from task/T-0044, not main: ops/merge's --no-task-reason handling exists only there (T-0021/T-0022/T-0044
  all have open PRs against ops/merge; `git log --oneline task/T-0021 task/T-0022 task/T-0044 -- ops/merge` puts
  9a18891 on task/T-0044 newest). touches: extended past the seeded [ops/merge] because the fix is being anchored
  on a new pin assertion (P-OPS-02) rather than on a comment - see the decision entry below.
