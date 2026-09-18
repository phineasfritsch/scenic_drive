---
id: T-0166
title: recordables from the M2 sign-offs - an empty attribution passes the licence test, MIN_COVERAGE's boundary is unpinned, and the sane exit-order check reads file order, not execution order
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/tests/test_license_data.py, services/etl/tests/test_landcover_verdict.py, services/etl/etl/landcover.py, ops/lib/check-sane-exit-order, ops/sane, pins/PINS.yaml]
pins_affected: [P-OPS-05]
reviewer: null
depends_on: [T-0024, T-0027]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

PRs #26 (T-0024) and #33 (T-0027) PASSED review on 2026-09-18 with recordables that are small, real, and
should not live only in two done/ Logs. One bounded pass; each item demonstrated RED by name first. The
reviewers' entries in `queue/done/T-0024-*.md` and `queue/done/T-0027-*.md` carry the reproductions.

1. **An EMPTY attribution satisfies the licence test** (agent/rv2-pr33, R14).
   `test_the_worldcover_credit_is_the_string_the_fixture_records` asserts `item.attribution in recorded`, and
   `"" in s` is always true - a manifest entry with `attribution: ""` passes a test whose whole job is that an
   attribution-required licence carries its credit. Fix: require a non-empty string of a stated minimum
   length before the containment check. RED: blank one WorldCover entry's attribution -> the named test fails.
   This is a licence obligation, which is why it goes first.
2. **MIN_COVERAGE's boundary is unpinned** (R11). `MIN_COVERAGE = 0.5`; flipping all three `<` to `<=` in
   `landcover.py` leaves the whole ETL suite green - the tests bracket the boundary (0.0345 below, 0.5172 above)
   and never sit on it. One row at coverage exactly 0.5 with the verdict the docstring promises. The reviewer
   asked for it before T-0030 consumes the verdicts.
3. **`check-sane-exit-order` reads FILE order while P-OPS-05's statement says "the order its checks actually
   run in"** (agent/rv2-pr26, M5): wrapping the production section in a function and invoking it after the
   worktrees block keeps the check green while `ops/sane` exits 4 where its table says 7. `ops/sane` defines no
   function beyond `say`/`fail`/`ok`/`skip` today, so file order IS execution order in the file that ships -
   make that the refusal: the check refuses when `ops/sane` defines any other function. And state in the pin's
   `why_no_test_catches_it` the limit the reviewer proved is uncatchable by construction: an edit that moves a
   check AND edits `EXIT_ORDER` to agree passes, so the array is the reviewed contract, not a derived fact.
4. Acceptance-line wording in T-0027's record (R13: "printed alongside it" - the fixture test asserts the
   recomputed numbers, it prints nothing): a dated correction line, no edit to the old entry.

Depends on T-0024 and T-0027 being on main (PR #33 merged as 5b0cf46; PR #26 merges when its CI finishes).
The author rule applies: rule disagreements first, re-run the whole acceptance block at the final commit,
close the verifier's findings before the review is bought; PR base is `main`.

## Log
- 2026-09-18T20:50:00Z filed by agent/claude-fable-5-1 from the round-2 reviews of PR #26 (agent/rv2-pr26) and PR #33 (agent/rv2-pr33). Not started.
