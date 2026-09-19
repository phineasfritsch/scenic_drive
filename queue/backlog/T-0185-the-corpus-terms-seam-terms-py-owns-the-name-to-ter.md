---
id: T-0185
title: the corpus terms seam - terms.py owns the name -> (term_id, family) inverse, CorpusWriter.add_term consumes assemble.py's scored table, terms_osm and terms_raster stop shipping empty
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/terms.py, services/etl/etl/corpuswriter.py, services/etl/etl/corpus.py, services/etl/etl/assemble.py, services/etl/tests/]
pins_affected: [P-DATA-01]
reviewer: null
depends_on: [T-0146, T-0173, T-0188]
verify: [ops/test, ops/check-pins]
acceptance:
  - "terms.py exports the inverse map name -> (term_id, family) for every score.score unit term, with 105 `byway` documented as the exception (a status-bonus string on the scorer side, a 0..1 row on the device side - rule how it is stored); a test that the inverse round-trips TERM_NAMES and that every RANKED/MAPPED term of way_record has an id, RED by name on a missing one"
  - "`python -m etl.corpus --input <extract> --scores <assemble.py's output>` writes one row per (segment, term) into terms_osm or terms_raster by family; the two tables stay physically separate (no FK, no view, no combined column - ODbL posture); a test that a scored table with N ways and K terms yields N*K rows split by family, RED by name before the writer consumes scores; P-DATA-01 idempotence (two builds byte-identical) re-asserted with terms present"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From the 2026-09-19 20:13 panel (CODE lens, grounded). The scoring path has ONE mapping (way_record.RANKED/MAPPED/
DEFERRED_TERMS; normalise imports it; assemble reaches score.score only through score_kwargs). The corpus
vocabulary is a SECOND, unconnected one: terms.py keys eleven ids, corpuswriter.add_term takes (family,
term_id), and no name -> (term_id, family) inverse exists anywhere; term 105 `byway` is not a score.score kwarg
at all. Nothing on main writes a terms row (corpus.py: "terms_osm and terms_raster are emitted EMPTY"; add_term
is called only from a test), and T-0146's assemble.py writes a scored JSON that nothing consumes. Whoever writes
the first term row hand-types that eleven-entry map; done twice (once for the PBF, once for the corpus) it is the
two-answers-for-one-road failure score.py and terms.py were written to prevent. NOT a prerequisite of T-0168
(its brief writes name-keyed tags onto the PBF for GraphHopper and never touches term ids); sequence after #102.

## Log
- 2026-09-19T02:58:56Z filed by agent/claude-fable-5-1 from the 20:13 panel's grounded synthesis. Not started.
- 2026-09-19T03:29:43Z depends_on += T-0188 by agent/claude-fable-5-1 (21:13 panel): the corpus the device reads must carry every gate ScenicKit refuses on (P-PROD-01) before its first terms row is written.
