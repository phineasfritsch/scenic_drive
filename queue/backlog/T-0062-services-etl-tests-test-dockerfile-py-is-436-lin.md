---
id: T-0062
title: services/etl/tests/test_dockerfile.py is 436 lines on task/T-0046
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0046, T-0058]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`services/etl/tests/test_dockerfile.py` is **436 lines** on `task/T-0046`, against the 300-line cap. It was
125 lines on `task/T-0038` and grew across T-0046's four review rounds of pip-parser work.

Nothing reported it, because `ops/lib/check-line-cap` globbed Swift only. T-0058 extends the cap to Python and
TypeScript - and the merge rehearsal that found this file is the reason T-0058 carries an exemption for it:
without one, the first merge of the Dockerfile chain after T-0058 turns `main` red on a file that was over the
cap long before either task existed.

So this is not a regression and not T-0058's fault; it is a debt the new check made visible, which is what the
check is for. The exemption is the deliberate, auditable way to carry it for exactly as long as it takes to
land this task, and `check-line-cap` refuses an exemption whose file has dropped back under the cap, so it
cannot quietly become permanent.

- Split it along whatever seams the file already has. T-0046's log describes distinct concerns - the pip
  destination-flag whitelist, the PEP 508 marker segmentation, the shlex tokenizer, and the Dockerfile
  parsing itself - which is a good sign the file is several tests wearing one filename.
- Do NOT delete tests to get under the number. The file is long because T-0046 was attacked four times and
  each round added real cases; every one of them is load-bearing and a reviewer should refuse any diff that
  drops coverage to satisfy a line count.
- When it is under 300, DELETE the exemption entry from `ops/lib/check-line-cap`. Leaving it is itself a
  failure the check reports: "exemption(s) no longer needed - the file is under the cap, so delete the entry".
- Verify with the merge rehearsal, not just on the branch: merge `task/T-0046` and `task/T-0058` into a
  scratch branch and run `bash ops/lib/check-line-cap`. That combination is the only place the problem exists.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from a full merge rehearsal - 30 branches merged in dependency order
  into a throwaway, gates run after each. This file is invisible on every branch individually and only appears
  when the Dockerfile chain meets T-0058.
