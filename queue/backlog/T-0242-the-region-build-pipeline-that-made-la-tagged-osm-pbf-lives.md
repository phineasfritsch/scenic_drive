---
id: T-0242
title: the region build pipeline that made la-tagged.osm.pbf lives in the tree - pass1/pass2/pass3 and the window/tile drivers committed under services/etl with one entry point, a test through it, and a rebuild that reproduces sha256 648fc3db...3d39
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/etl/region/, services/etl/tests/test_region_build.py, services/etl/tests/fixtures/, ops/etl-region]
pins_affected: []
reviewer: null
depends_on: [T-0208, T-0209]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the scripts T-0208's round-2 Log names (pass1.sh, pass1c.sh, pass2_reference.py, pass2.sh, pass3_merge.py, run_stage.sh, windows.sh, windows_top.py, handover_*.py - preserved in the MAIN checkout at services/etl/work/t0208/, gitignored) are committed under services/etl/etl/region/ behind ONE entry point (ops/etl-region, 100755), each script's role ruled in the Log; scratch helpers that built nothing shipped are named and left out"
  - "a test runs the entry point end to end over a two-tile fixture and asserts one score per shared way (the seam property T-0208 bound through assemble.main) - RED by name when the entry point skips the region reference"
  - "a full LA rebuild through ops/etl-region in the ETL image via WSL reproduces la-tagged.osm.pbf byte for byte (sha256 648fc3dbb80c8e84...3d39, 45,914,107 B) - each stage's count lines quoted into the Log as the stage lands; a differing digest is ruled, never waved through"
---
## Brief

From agent/rv1-t0208's recordable R1 on PR #129 (2026-09-25): the artifact every LA route stands on cannot be rebuilt
from the tree. T-0208 merged as PR #129 with the gap recorded (harness rule: after the rounds, the remaining finding
is filed as its own task).

## Log
- 2026-09-26T00:55:31Z filed by agent/claude-opus-5 (orchestrator) after PR #129 merged. The work dir was moved from .worktrees/T-0208/services/etl/work/ to the main checkout's services/etl/work/t0208/ (89 entries, 372 MB) before the worktree was removed.
