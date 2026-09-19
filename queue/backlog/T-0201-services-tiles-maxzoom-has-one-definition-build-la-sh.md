---
id: T-0201
title: services/tiles - MAXZOOM has one definition: build-la.sh reads check_pmtiles.MIN_MAXZOOM the way it reads BUDGET_BYTES, with a test forbidding the literal
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/tiles/]
pins_affected: []
reviewer: null
depends_on: [T-0165]
verify: [ops/test, ops/check-pins]
acceptance:
  - "build-la.sh's MAXZOOM default derives from check_pmtiles.MIN_MAXZOOM (python -c, the BUDGET_BYTES precedent at build-la.sh:52); --maxzoom stays as the deliberate override and the checker's --min-maxzoom must be passed alongside it or the recipe refuses by name; a test mirroring test_the_build_recipe_reads_the_budget_out_of_this_module forbids a bare MAXZOOM=<digits> literal - RED first, then green"
  - "python -m pytest services/tiles/tests count line; bash -n services/tiles/build-la.sh"
---
## Brief

From the 00:13 panel (CODE lens, grounded): T-0165 applied the one-definition rule to the 120 MB budget
(build-la.sh:52 reads it out of the checker; a test forbids the copy) but not to the zoom it ruled in the same
round - build-la.sh:23 MAXZOOM=14 duplicates check_pmtiles.py:36 MIN_MAXZOOM = 14 with no test forbidding it;
raise the checker's floor to 15 and the recipe builds z14, then its own step 6 refuses the file it just built.
If #109 is still open when this is read, the round-2 reviewer records it and the fix rides the branch instead.

## Log
- 2026-09-19T06:29:45Z filed by agent/claude-fable-5-1 from the 00:13 panel's grounded synthesis. Not started; after #109 merges unless its reviewer folds it in.
