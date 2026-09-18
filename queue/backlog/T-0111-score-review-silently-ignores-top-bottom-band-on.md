---
id: T-0111
title: score-review silently ignores --top/--bottom/--band on an unscored sheet
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/review_sheet.py, services/etl/tests/test_review_sheet.py, ops/score-review]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/score-review <unscored>.json --top 30 -> at most 30 rows, or a non-zero refusal naming --sort-by"
  - "RED: the same command today prints '13054 segments in, 13054 rows out' and exits 0"
---
## Brief

**`ops/score-review .artifacts/la-ucla.json --top 30` printed `13054 segments in, 13054 rows out` and exited
0.** The flag was not rejected, not warned about, and not applied. It was discarded.

`services/etl/etl/review_sheet.py:47-51`:

    if not scored:
        # No composite score exists yet (T-0029). Reviewing the TERMS is still worth doing ...
        take(segments, "unscored")

`select()` reaches that branch whenever no input segment carries a numeric `score`, which is **every real
input today** - there is no composite score yet, by design, and `ops/score-review`'s own header says so:
*"`score` may be absent - there is no composite score yet (T-0029) - in which case every segment is listed
and the terms are what gets reviewed."* So the documented behaviour and the implemented behaviour agree.
Both are wrong, and the header is why nobody noticed.

**This defeats the single thing the tool exists for.** Its first line: *"so 'does this segment look like its
score' costs ten minutes instead of a Saturday."* A sheet with 13,054 rows is a Saturday. The tool is
currently unable to produce a short sheet for any input it will actually be given before T-0029 lands, which
is the entire window in which a human gate is most useful.

It is also this repository's recurring defect class wearing a different hat: **a selection flag whose effect
is conditional on data the caller does not have, failing open and silent.** `--top 30` on unscored input is
indistinguishable, from the exit code and from the summary line, from `--top 30` working.

Do:

1. In the unscored path, `--top`/`--bottom`/`--band` must not be silently dropped. Two acceptable shapes,
   pick one and say why in the log:
   - **Refuse**: exit non-zero with `score-review: --top needs something to rank by; this input has no
     'score'. Pass --sort-by <term> to rank on a term.` Failing loud is always allowed.
   - **`--sort-by <term>`**: rank on a named key inside `terms`, so `--top 30 --sort-by curv_per_km` works on
     exactly the input the ETL produces today. This is the more useful of the two; refusing is the floor.
2. Whichever you pick, the summary line must never report `N segments in, N rows out` while a limit was
   requested and not honoured. Make the count line state the selection that was actually applied.
3. Fix the header comment in `ops/score-review` and the docstring in `review_sheet.py` at the same time. The
   comment currently documents the bug as the design; leaving it would let the next person re-derive it.

**RED FIRST.** The demonstration is already written above and reproduces in one command against a real file:
`ops/score-review <unscored>.json --top 30` printing a row count far above 30 and exiting 0. Record that
exact line in the log, then make it fail.

**Do not "fix" this by requiring a score.** Reviewing terms on unscored segments is the correct behaviour and
the reason the branch exists - T-0029 is blocked, and the human gate must not be blocked behind it. Only the
silent discarding of the limit flags is the defect.

## Log
