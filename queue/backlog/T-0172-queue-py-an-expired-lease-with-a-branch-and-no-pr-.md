---
id: T-0172
title: queue.py - an expired lease with a branch and no open PR returns to ready/ keeping its branch; queue-next shows the unblocked backlog beside ready/
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py, ops/queue-next, ops/queue-sweep, ops/lib/check-queue-roundtrip, queue/README.md]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

From the 2026-09-18 15:13 panel (STRATEGY F1/F2 and the grounding pass). Two dispatcher blind spots, both
demonstrated by the queue on main today:

1. **Abandoned work reads as held work.** The sweep (`queue.py` ~552-590) keeps every expired lease whose
   task names a `branch:`, on purpose (a sweep that nulls `owner:` on a branch with an open PR creates the
   add/add divergence eleven branches were repaired for). But T-0030 - lease expired 2026-09-08T01:19Z, WIP
   pushed at a2f1e2b, NO pull request - was invisible for eleven days: not in ready/, so `next`/`claim` never
   offered it, and not swept, so nobody re-leased it. Rule: an expired lease whose declared branch has NO open
   PR is abandonment. Return it to ready/ KEEPING `branch:` and `worktree:` (so the next claim adopts the WIP
   instead of re-authoring), with a Log line. The sweeper deliberately does no network I/O (queue.py's own
   comment); rule how it learns "no open PR" - an explicit `--prs <file>` from `gh pr list --json headRefName`,
   or a `--with-gh` opt-in, never a silent fetch - and what it does when it cannot tell (keep, and say so).
   RED: a fixture task in claimed/ with an expired lease, a branch, and no PR stays in claimed/ on today's
   sweep; green when it lands in ready/ with its branch intact. The existing keep-with-PR case stays green.
2. **`queue-next` offers only ready/.** `cmd_next` (queue.py ~599-602) reads ready/, which today held four
   harness tasks and zero M2 tasks while T-0169 (depends_on []) sat in backlog/: the dispatcher structurally
   prefers guardrail work over route work. Print, beside ready/, the UNBLOCKED BACKLOG: backlog tasks whose
   every `depends_on` id is in done/, oldest first, marked "backlog - promote to ready/ before claiming".
   RED: with T-0169-shaped fixture in backlog/ and depends_on [], today's `next` prints nothing for it.

House style: `ops/lib/check-queue-roundtrip` has the fixture pattern; keep every file under 300 lines (split
queue.py at a seam if it crosses - it is the serial chokepoint, so the split is its own ruling). The author
rule (CLAUDE.md, Verification) applies; PR base is `main`.

## Log
- 2026-09-18T21:54:27Z filed by agent/claude-fable-5-1 from the 15:13 panel's grounded synthesis. Not started.
