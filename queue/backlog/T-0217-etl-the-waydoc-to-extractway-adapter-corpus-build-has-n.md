---
id: T-0217
title: etl - the waydoc -> ExtractWay adapter: corpus.build has no committed path from a real extract (three shapes, no converter), so nothing in CI has ever fed it real ways
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, ops/mutate/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: [T-0206]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURED in T-0206's Log: corpus.build -> extractway.load_extract reads {region, ways:[{id, cls, highway, access_ok, oneway, nodes, name?, surface?}]}; the real window doc is waydoc.py's {way_id, tags, coords}; window-scored.json is a third shape; grep access_ok hits only consumers. SHIP one module that derives cls from tagfilter.WAY_CLASSES, surface from surface.surface_state, oneway from the tags, and access_ok = 0 iff tags.get('access') in assemble.CLOSED_ACCESS or tags.get(assemble.MOTOR_VEHICLE_KEY) == assemble.MOTOR_VEHICLE_REFUSED - the two access rules of assemble.gate_reason (assemble.py:146-150) factored into ONE importable predicate that gate_reason itself calls, evaluated independently of the surface and track rules (no second copy). NOT access_ok == (gate_reason(tags) != GATE_NO_ACCESS): gate_reason returns the FIRST firing rule, so a private unpaved road answers GATE_UNPAVED_SURFACE and would read access_ok=1; the committed slice carries exactly such a way (access=private + surface=dirt) asserted access_ok=0 AND surface=unpaved, with a test bound to the shipping entry point over a committed slice of REAL ways (from the canyon window; licence line ODbL) covering access=private, motor_vehicle=no, oneway=-1, oneway=yes, a roundabout, a way with no name, a class outside the table (T-0206's throwaway skipped 2 of 23,474 - name them)"
  - "its ops/mutate population with a literal floor (it is a new numeric-adjacent module under services/etl/etl/ - or an allowlist entry with a reason if ruled non-numeric), python ops/lib/check-mutate-population.py bare; the ETL suite count line; the canyon window built end to end from the committed adapter with ways/segments/bytes equal to T-0206's 11,740 / 24,205 / 6,135,808 or the difference explained row by row"
---
## Brief

T-0206's R1: 'the waydoc->ExtractWay adapter is NOT this task's shipping work' - its measurement adapter lives in the
gitignored work/ dir of a worktree that will be removed. A class/access/oneway decision over real tags is a safety-
adjacent table (access_ok feeds the corpus the hazard strip reads), so it ships with a population, not as a script.
The throwaway is preserved at services/etl/work/t0206/ in the main checkout for reference only.

## Log
- 2026-09-19T13:12:06Z filed by agent/claude-fable-5-1 (orchestrator, from T-0206's measurement on PR #120). Not started.
- 2026-09-19T16:40:26Z acceptance line 1 corrected by agent/claude-fable-5-1 (06:13 panel, CODE lens, fable-grounded on assemble.py:141-150 / schema.py): the panel's first predicate (access_ok == gate_reason != GATE_NO_ACCESS) would grant access to a private unpaved road because gate_reason returns the first firing rule; the corrected line factors the two access rules into one importable predicate and pins the private+dirt row.
