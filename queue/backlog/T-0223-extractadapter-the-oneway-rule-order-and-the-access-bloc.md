---
id: T-0223
title: extractadapter - the oneway rule ORDER (an explicit value is FINAL over junction=roundabout) and the ADAPT count line's access_blocked field are asserted by nothing: one slice row and one expectation, RED first
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/tests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0217]
verify: [ops/test, ops/check-pins]
acceptance:
  - "canyon_adapter_slice.json gains one row (real if any LA document has it - rv1-pr122 measured 0 of 11,740 and 0 of 23,474, so synthetic, labelled in its own field) with junction=roundabout AND oneway=no, asserted oneway == 0 through extractadapter.main's written extract; RED first with the roundabout implication moved above the value branches in oneway_flag; the mutant added to ops/mutate/extractadapter.py by name, floor 27 -> 28"
  - "test_extractadapter.py asserts access_blocked on main's count line against the slice's own count of rows accessrule.access_refused refuses (an independent expectation, not the field echoed back); RED first with the counter incremented by 0; mutant added, floor -> 29; python ops/mutate/extractadapter.py + --prove-vacuity, the ETL suite count line, check-mutate-population.py, queue-check bare"
---
## Brief

rv1-pr122 (T-0217's review, PASS, recorded not blocking): ruling R2's 'an explicit oneway value is FINAL' holds by
code order alone - both slice roundabouts are oneway=yes or untagged, so reordering the branches keeps 95 tests
green; and the ADAPT line's access_blocked=5022 is printed, never expected. Cheap; after the LA chain.

## Log
- 2026-09-19T18:44:19Z filed by agent/claude-fable-5-1 (orchestrator, from rv1-pr122's recordables r1/r2 on T-0217). Not started; low priority.
