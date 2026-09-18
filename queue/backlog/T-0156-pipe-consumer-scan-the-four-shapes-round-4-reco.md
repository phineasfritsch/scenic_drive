---
id: T-0156
title: pipe-consumer scan - the four shapes round 4 recorded and did not block on, and early-exit consumers other than grep
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-pipe-consumers, pins/PINS.yaml]
pins_affected: [P-OPS-03]
reviewer: null
depends_on: [T-0140]
verify: [ops/check-pins]
acceptance: []
---
## Brief

PR #87 (T-0140) was signed off at round 4 by agent/rv4-pr87 with five RECORDABLE shapes, none blocking because
none exists under `ops/`, `.githooks/` or `pins/PINS.yaml` today and the scan's header already states it is a
text heuristic with listed blind spots. Its Log entry in `queue/done/T-0140-*.md` carries each with its
measurement. They are bounded and cheap; do them in one pass, each demonstrated red by a probe file the way
`.artifacts/r4-demo.sh` did, and stop there - this scan has had four review rounds and is off the product's
critical path.

1. **A bare backslash continuation inside a pipeline.** `producer |` / `  timeout 5 \` / `  grep -q PAT`
   exits 141 and is not reported: the join continues a line ending in `|`, `| \` or `| # comment`, but once
   joined, a following line ending in a bare `\` is not continued again. Fix: inside a pending join, a line
   ending in `\` keeps the join open.
2. **The scan's own grep status is unread.** The per-file `grep -E -e "$PATTERN" -e "$ENVPATTERN" "$scan" |
   grep -vE ...` feeds a `while read` through a process substitution; a grep that FAILED (exit 2) would yield
   zero hits and the check would print OK - the shape this file forbids, one level up, the same way the awk
   status was before round 3. Fix: run grep to a temp file, read its status, treat 0 and 1 as answers and
   anything else as REFUSING. Demonstrate red with a PATTERN made invalid in a copy.
3. **The self-exemption is by path.** `ops/lib/check-pipe-consumers` skips itself unconditionally. Narrow it:
   scan this file too, with the lines that QUOTE the shape marked by an identifier the scan recognises (not by
   a comment), or assert the exempted file's own greps read to EOF.
4. **A binary file under the scanned paths** is reported as a hit through grep's `Binary file ... matches`
   line - it fails closed, by accident of GNU grep 3.0. Make it deliberate: `grep -a`, or refuse by name.
5. **Early-exit consumers other than grep** - `| head -N`, `| sed Nq`, `| read` - are the same mechanism and
   are stated in the scan's header as not seen. Decide once: either scan them where the pipeline's STATUS is
   read (an `if`, `&&`, `||`, or a pin assertion), which excludes the dozen value captures inside `$( )`
   that exist today (`ops/sane:29,31,42`, `.githooks/pre-commit:110,113`, `ops/deploy:25`,
   `ops/agent-preflight:14,86`), or leave them out and say why in the pin's statement.

Depends on T-0140 (PR #87) landing. One reviewer, one round: the acceptance block is re-run in the final
commit (the rule that cut PR #88 to two rounds), and T-0155's replay, if it has landed, runs first.

## Log
- 2026-09-18T18:50:00Z filed by agent/claude-fable-5-1 from agent/rv4-pr87's round-4 PASS of PR #87 (recordables S1-S5). Not started.
