---
id: T-0189
title: dem, landcover, oracle and extract read the shared inputs directory - the silent None from a per-worktree path is a refusal by name
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T03:45:22Z
lease_expires_at: 2026-09-19T09:45:22Z
worktree: .worktrees/T-0189
branch: task/T-0189
exclusive: []
touches: [services/etl/etl/dem.py, services/etl/etl/landcover.py, services/etl/etl/oracle.py, services/etl/etl/extract.py, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0177]
verify: [ops/test, ops/check-pins]
acceptance:
  - "dem.py, landcover.py, oracle.py and extract.py resolve their inputs directory through fetch.resolve_inputs_dir (SCENIC_ETL_INPUTS, else the main checkout's services/etl/inputs/ from a worktree path), never ROOT / 'inputs' - RED BY NAME first: a test that runs dem.sample_tile from a fake worktree path with the tile present only in the shared directory and asserts a sample, red today (None), then green"
  - "a missing tile or land-cover raster is a REFUSAL that names the path (the way extract.py already refuses), never a silent None list - RED by name on a test that today gets [None] * n back; the 'absent means absent' semantics for a point OUTSIDE every served region stay as they are (T-0142) and are asserted separately"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From agent/rv1-pr104's PASS entry on PR #104 (T-0177) - the recordable it asked to file before any sampling runs
from a worktree. T-0177's resolver reaches etl.fetch only (its ruling R3: the four consumers were outside its
touches). extract.py refuses loudly when its source is missing; dem.sample_tile returns `[None] * len(points)`
when the tile file is absent and landcover.sample_codes `continue`s past a missing raster - neither names a path.
Both still compute a per-worktree `ROOT / "inputs"`, while the California extract and the four LA 3DEP tiles
exist ONLY in the main checkout's shared directory (T-0169/T-0142). T-0168 will run from a worktree and sample
LA terrain: without this it gets zeroed terrain and a green suite.

## Log
- 2026-09-19T03:45:19Z filed by agent/claude-fable-5-1 from PR #104's review; ready/ with its acceptance block; T-0168 now depends on it. Not started.
- 2026-09-19T03:45:22Z claimed by agent/claude-opus-5; lease until 2026-09-19T09:45:22Z
