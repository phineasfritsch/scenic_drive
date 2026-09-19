---
id: T-0227
title: etl - M2 oracles over LA: the curvature and byway oracles run over T-0208's region-normalised LA scores, not the Vermont fixture (oracle.py:36 names vermont-curvature.kmz); the fixture-scale floor re-ruled for LA from the measured population
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, services/etl/regions/la/, ops/]
pins_affected: []
reviewer: null
depends_on: [T-0208]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a Curvature-project KMZ covering the LA clip (California, or the LA county cut) fetched and digest-pinned through ops/etl-fetch-inputs and services/etl/inputs/manifest.yaml with its licence line; oracle.py stops naming vermont-curvature.kmz - the region's KMZ becomes a services/etl/regions/<region>/region.json field, Vermont's fixture kept as the CI oracle; RED first on the LA run with the field absent"
  - "ops/etl-oracle-report --with-population over T-0208's retained whole-LA scored table: the curvature agreement (plan: within 2 %) and the byway oracle (byway ways outrank matched non-byway ways; byways-caltrans.geojson / byways-fhwa.geojson clipped to the LA bbox) quoted with their counts; the pass/fail floor RULED for LA from that population in the Log - never copied from Vermont's; the M2 exit row's 'Curvature + byway oracles pass' answered MET or UNMET in one line"
  - "the ETL suite count line and zero skips; python ops/lib/check-mutate-population.py; queue-check bare; this task scores nothing (reads T-0208's table read-only) and holds no lock"
---
## Brief

From the 13:13 panel (STRATEGY, fable-grounded): every panel since 06:13 said the M2 oracles 'go real over LA under
T-0209' - false; T-0209's four clauses are import, T(lambda), runs and the VPS, and services/etl/etl/oracle.py is a
Vermont fixture by name. No task owned an LA oracle run. This one does, after T-0208's table exists.

## Log
- 2026-09-19T20:48:40Z filed by agent/claude-fable-5-1 (13:13 panel, fable-grounded on oracle.py:1-7,36, T-0209's acceptance, T-0202 Log:79). Not started; after T-0208; no lock.
