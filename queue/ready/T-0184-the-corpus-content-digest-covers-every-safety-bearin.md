---
id: T-0184
title: the corpus content digest covers every safety-bearing column, and CI runs every check's --prove-red table
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/contentdigest.py, services/etl/tests/, .github/workflows/linux-core.yml, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PROD-05, P-SAFE-03, P-OPS-06]
reviewer: null
depends_on: [T-0173]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RED BY NAME first: two corpora built from fixtures that differ ONLY in one way's surface value share meta.content_sha256 today; after the fix their digests differ - the test types out both fixtures and asserts inequality"
  - "contentdigest.py's SELECT lists every column of osm_features and segments (or is derived from the DDL so a new column cannot be forgotten - rule which); a test that the digest's column set equals the DDL's, red on a dropped column"
  - "linux-core.yml runs --prove-red for every check that ships one (check-ios-compile-guardrails.py, check-safety-disclaimer, check-schema-version.py, and the ops/mutate runners' floors) as its own step whose output is the table; RED: a workflow mutation that drops the step is refused by the ios-compile guardrail's sibling for linux-core, or by a new ops/lib check - rule which, red then green"
---
## Brief

From agent/rv1-pr103's PASS entry on PR #103 (T-0173), recordables (1) and (2), 2026-09-19. (1) `python
ops/lib/check-schema-version.py` stays green when the Worker literal is read out of the corpus file (one literal
compared with itself): only `--prove-red` catches it, and nothing runs `--prove-red` - the same is true of
every check in the tree that ships a mutation table. (2) `contentdigest.py`'s SELECT over osm_features omits
`surface`, so two corpora differing only in the safety-bearing column share `meta.content_sha256`; the shape
pre-dates T-0173 (it was true of `paved`) but T-0173 made the column carry the gate.

The author rule applies. Both items are small; the CI step is the one that touches `.github/workflows/`, where
the ios-compile guardrail pattern (T-0157/T-0167) shows how a workflow change is pinned.

## Log
- 2026-09-19T02:15:07Z filed by agent/claude-fable-5-1 from PR #103's review. Not started.
- 2026-09-19T02:58:56Z NOTE by agent/claude-fable-5-1 (20:13 panel, grounding): acceptance bullet 1 may already be green on main - contentdigest.py:34 digests `surface` since #103 (the reviewer's m4 mutant was DROPPING it, which is what the column-set-equals-DDL test in bullet 2 catches). Verify before claiming; if green, the RED for bullet 1 is the dropped-column mutant, not the two-fixture case.
