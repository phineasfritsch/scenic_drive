---
id: T-0219
title: P-DATA-03 corpus half - meta.region is stamped by etl.corpus and read back by nothing: the reader against the active region, in the same shape as the tiles half (check-pmtiles-provenance.py), red first
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, services/etl/etl/, services/etl/tests/, pins/PINS.yaml]
pins_affected: [P-DATA-03]
reviewer: null
depends_on: [T-0197]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/lib/check-corpus-provenance.py (100644, python; the shape of ops/lib/check-pmtiles-provenance.py): in-process fixtures built by the SHIPPING corpus.build - meta.region == the active region passes; region 'bay' refused by name; region key ABSENT refused naming 'meta.region is None'; built_at older than 30 days refused (P-DATA-03's second clause) - each RED first with the mutant in the shipping checker, then green; SCENIC_LA_CORPUS=<path> adds the real artefact when set (this box: the T-0206 union corpus under services/etl/work/t0206/) and says so when not"
  - "P-DATA-03's pin text loses the 'UNASSERTED and UNOWNED' sentence and names both halves' checks; bash ops/check-pins --source-only bare; check-exec-bits, check-line-cap, queue-check bare"
---
## Brief

rv1/rv2-pr119 (T-0197) both recorded it: etl.corpus stamps meta.region (services/etl/etl/corpus.py, writer.set_meta)
and nothing reads it back against the active region; T-0205 merged as #116 writing meta.surface_coverage instead.
The tiles half of P-DATA-03 is asserted by check-pmtiles-provenance.py since #119; this is the other half.

## Log
- 2026-09-19T16:59:37Z filed by agent/claude-fable-5-1 (orchestrator, from rv1/rv2-pr119's recordables on T-0197). Not started; a harness chore, after #119.
