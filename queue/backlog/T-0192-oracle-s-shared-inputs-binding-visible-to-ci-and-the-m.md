---
id: T-0192
title: oracle's shared-inputs binding visible to CI (a reload_with_inputs case that plants the KMZ outside ROOT) and the manifest-stays-per-checkout test anchored on the path, not on two equal digests
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/oracle.py, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0189]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a fourth reload_with_inputs case in tests/test_inputs_dir_consumers.py sets SCENIC_ETL_INPUTS to a directory OUTSIDE ROOT, plants a vermont-curvature.kmz there and asserts oracle.KMZ resolves to it - RED BY NAME first on a PLAIN checkout copy (no .worktrees component) with oracle.KMZ = ROOT / 'inputs' / 'vermont-curvature.kmz', which today passes 75/75 there, then green"
  - "test_the_oracles_manifest_stays_in_this_checkout anchored on the PATH (expose pinned_digest's default manifest path as an identifier and assert it equals ROOT / 'inputs' / 'manifest.yaml', the way tests/test_inputs_dir.py pins fetch.MANIFEST) or on two manifests that DIFFER in content - RED BY NAME first with the default moved to the shared directory (today 104 passed under that mutant), then green"
  - "cd services/etl && python -m pytest tests -rs -o addopts= -> count line and zero skips at the final commit"
---
## Brief

From agent/rv1-pr108's PASS entry on PR #108 (T-0189). Of the four consumers T-0189 moved to the resolver, oracle
is the only one with no test that plants a payload outside ROOT under SCENIC_ETL_INPUTS, so in a plain checkout
(CI's layout, where the resolver answers ROOT/inputs) oracle.KMZ computed per-checkout is an equivalent mutant and
the binding is invisible. And the test guarding ruling R3 (the manifest stays per-checkout) compares two DIGESTS of
the same file, so it can only go red when the two manifests differ in content - the situation no test creates; a
default moved to the shared directory passed 104/104. Small, two tests, one identifier.

## Log
- 2026-09-19T04:46:33Z filed by agent/claude-fable-5-1 from rv1-pr108's recordables (a) and (b). Not started.
