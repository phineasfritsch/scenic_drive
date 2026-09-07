---
id: T-0035
title: P-SRC-02 line count is off by one when a file lacks a trailing newline (wc -l)
state: review
owner: agent/builder-2
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T15:01:42Z
lease_expires_at: 2026-09-07T17:01:42Z
worktree: ../wt/T-0035
branch: task/T-0035
exclusive: []
touches: [ops/lib/check-line-cap]
pins_affected: []
reviewer: agent/reviewer-16
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/check-line-cap` (P-SRC-02) enforced the 300-line Swift cap by measuring each tracked file with
`wc -l`, which counts newline characters, not lines. A file whose final line has no trailing newline is
undercounted by one: a genuine 301-line file reads as 300 and passes the cap it was written to enforce.
Found by agent/reviewer-13 while reviewing T-0019.

Fix: replace the `wc -l` measurement with `awk 'END{print NR}'`, which counts the trailing unterminated
line too, matching what an editor or compiler calls the line count. Everything else in the script —
structure, messages, exit codes, the `MIN_FILES` vacuous-pass floor, `git ls-files` as the file source,
naming the offending file with its line count, the one-line success summary — is unchanged; only the
`lines="$(...)"` measurement line inside the per-file loop was touched.

## Log
- 2026-09-07T15:01:42Z claimed by agent/builder-2; lease until 2026-09-07T17:01:42Z
- 2026-09-07T16:15:00Z agent/builder-2: verified the counting primitive itself before touching the script.
  Built two throwaway files outside the repo: 300 lines with a trailing newline, and 300 newline-terminated
  lines plus one more unterminated line (301 lines by any editor's count).
    with trailing newline:    wc -l: 300   awk 'END{print NR}': 300
    no trailing newline:      wc -l: 300   awk 'END{print NR}': 301
  `awk 'END{print NR}'` counts the last unterminated line; `wc -l` does not. Confirms the fix primitive.
- 2026-09-07T16:15:00Z agent/builder-2: reproduced the bug on the real script BEFORE fixing it.
  Built Sources/ScenicKit/Edge.swift = 300 lines of "// x\n" + "// last" (no trailing newline) = 301 lines
  by editor count (`awk 'END{print NR}'` → 301; `wc -l` → 300). `git add`ed it, ran the unmodified
  ops/lib/check-line-cap:
    $ bash ops/lib/check-line-cap
    P-SRC-02: 10 Swift files tracked, none over 300 lines
    exit=0
  RED confirmed: a real 301-line file passed the 300-line cap because the script measured with `wc -l`.
- 2026-09-07T16:15:00Z agent/builder-2: applied the fix (swapped `wc -l < "$f"` for `awk 'END{print NR}' "$f"`
  in the per-file loop, comment explaining why added, structure/messages/exit codes otherwise untouched).
  Reran on the SAME Edge.swift (still 301 lines, no trailing newline, still staged):
    $ bash ops/lib/check-line-cap
    P-SRC-02: file(s) over the 300-line cap:
      Sources/ScenicKit/Edge.swift (301 lines)
    exit=1
  GREEN confirmed: fixed script correctly rejects the file and names it with the correct (301) line count.
  `git rm -q --cached Sources/ScenicKit/Edge.swift && rm Sources/ScenicKit/Edge.swift` to clean up.
- 2026-09-07T16:15:00Z agent/builder-2: boundary check, both with a normal trailing newline this time.
    300-line file (trailing newline), git added, `bash ops/lib/check-line-cap`:
      P-SRC-02: 9 Swift files tracked, none over 300 lines   exit=0   (PASS, as expected)
    301-line file (trailing newline), git added, `bash ops/lib/check-line-cap`:
      P-SRC-02: file(s) over the 300-line cap:
        Sources/ScenicKit/Edge.swift (301 lines)   exit=1   (FAIL, as expected)
  Both test files removed with `git rm -q --cached` + `rm` after each run; `git status --short` clean
  before moving on.
- 2026-09-07T16:15:00Z agent/builder-2: vacuous-pass guard re-check. Built a throwaway `git init` repo
  outside this worktree containing only a copy of ops/lib/check-line-cap (no Sources/ or Tests/ trees at
  all). Ran the script inside it:
    P-SRC-02: only 0 tracked .swift file(s) under Sources/ and Tests/ (expected >= 5).
      An empty or truncated set must never read as 'no file exceeds 300 lines'.
    exit=1
  MIN_FILES floor still fires correctly; the fix did not touch or weaken that guard. Temp repo removed.
- 2026-09-07T16:15:00Z agent/builder-2: full re-verification on the real repo, worktree clean except the
  one-line fix in ops/lib/check-line-cap:
    bash ops/lib/check-line-cap        -> "P-SRC-02: 9 Swift files tracked, none over 300 lines"  exit=0
    bash ops/check-pins                -> "PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux"  exit=0
    bash ops/queue-check               -> "QUEUE OK (33 tasks)"  exit=0
    git ls-files -s ops/lib/check-line-cap -> "100755 ... ops/lib/check-line-cap" (exec bit intact)
  `git status --short` shows only `M ops/lib/check-line-cap` plus this task-file edit/move. Handing off
  to agent/reviewer-16; state -> review, moved queue/claimed/ -> queue/review/.
