---
id: T-0117
title: The review sheet captures no verdict and seeds from no disagreement
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
depends_on: [T-0108]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**The two halves of [[T-0108]]'s brief that were not built.** T-0108 shipped the sheet — Street View links at
the length-midpoint, the band selection, both refusals — and its review (PR #69) found these two items
missing and undisclosed. They are written down here so the deferral is a task rather than a silence. The
sheet itself says so on the page (`review_sheet.NOT_RECORDED_NOTICE`), and that notice must be deleted by
whoever closes item 1.

1. **Record the verdict.** Today every row carries three radios and nothing reads them: no `<form>`, no
   `<script>`, no `localStorage`, no download. Click thirty and close the tab and thirty verdicts are gone —
   which is verbatim the failure `review_sheet.py`'s own opening paragraph names. The brief wants them
   "written to a file that the score tuning reads": the Bradley-Terry input the plan already wants, gathered
   30 at a time instead of one drive at a time. So: define the file (id, verdict, sheet identity, timestamp),
   write a reader for it in Python with round-trip tests, and give the page a way to produce it.

   **The trap that stopped T-0108 from doing this in the fix pass, and it is a real one.** A static page can
   only persist through JavaScript, and this suite cannot execute the sheet's JavaScript: the ETL image
   (`services/etl/Dockerfile`) ships python3/osmium/gdal and no node, so a node-driven test would skip there
   and be vacuous exactly where the pipeline runs. Asserting `"localStorage" in html` pins a string, not a
   behaviour — the shape of defect this repository exists to reject. Whoever takes this must decide the
   execution story FIRST: add node to the image and pin it by digest, or make the recording step a Python
   one the suite can run end to end. Untested browser JavaScript is not an acceptable answer.

2. **Seed from the disagreements.** `select()` reads `score` and never `terms`. The brief asks for the rows
   where one term is extreme and the others are not — the segments where the composite is doing something
   interesting and is most likely wrong. This wants T-0029: what "extreme" means depends on how the terms are
   normalised, and picking thresholds before that exists is inventing product.

## Log
- 2026-09-08 filed by the T-0108 fix pass, from finding 3 of the PR #69 review. Not started.
