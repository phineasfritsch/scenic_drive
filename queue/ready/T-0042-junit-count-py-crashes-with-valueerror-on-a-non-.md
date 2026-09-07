---
id: T-0042
title: junit_count.py crashes with ValueError on a non-numeric failures= or errors= attribute
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/junit_count.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/junit_count.py` reads `failures=` and `errors=` off summary-only `<testsuite>` elements with a bare
`int(...)`. A non-numeric attribute - `failures="abc"`, or an empty string from a half-written report - raises
an uncaught `ValueError` traceback out of both `count()` (`junit_count.py:24`, pre-existing) and
`list_failures()` (`junit_count.py:56`, introduced with the summary-only branch) instead of the documented
clean exit 2.

Found by agent/reviewer-18 while re-reviewing T-0023 and filed there as MAJOR, non-blocking, because the
failure is symmetric (both paths break the same way, so the count and the naming cannot disagree) and loud
(a traceback, not a silent zero) - and `ops/test`'s parse guard still catches it via `read`'s empty stream.
So there is no false green today. It is still the wrong failure: the module's docstring promises exit 2 for an
unreadable report, and a traceback is what a reader mistakes for a broken runner rather than a broken report.

- Treat a non-numeric or missing count attribute the way a parse error is treated: `junit_count: cannot read
  <path>: ...` on stderr, exit 2, on BOTH paths.
- Demonstrate red first with a hand-built `<testsuite tests="1" failures="abc">`: show the traceback, then
  show the clean exit 2.
- `ops/lib/check-failure-naming` (P-OPS-02) already generates malformed-report fixtures; add this shape to it
  so the property is guarded rather than just fixed.

## Log
