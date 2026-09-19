---
id: T-0200
title: services/tiles - a committed 127-byte header fixture cut from the real la.pmtiles with the pmtiles show --header-json values as literals, so check_pmtiles.parse_header is anchored on a built artifact and not on the Log quote in its docstring
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
  - "services/tiles/tests/fixtures/la-header.bin (the first 127 bytes of the built la.pmtiles, dd-cut, committed) and la-header.json (the pmtiles show --header-json output over the same file, run through the pinned go-pmtiles image in WSL, committed); a test that parse_header(la-header.bin) equals every field in la-header.json - RED first on a fixture with one offset byte moved, then green"
  - "test_pmtiles_budget's in-process header writer round-trips through the same fixture (write_pmtiles reproduces la-header.bin byte for byte from la-header.json's values) so the reader and the writer are anchored on the format, not on each other"
  - "python -m pytest services/tiles/tests count line at the final commit"
---
## Brief

From the 00:13 panel (CODE lens, grounded): T-0165 owns both a PMTiles v3 header READER (check_pmtiles.py:42-74,
offsets 8/96/102) and a hand-rolled WRITER (test_pmtiles_budget.py:30-51) and every test compares one against the
other - one author, one set of offsets, so a shared misreading is green end to end; the only claimed agreement with
go-pmtiles is the docstring's prose. CLAUDE.md: anchor on built artifacts, never on a comment. The header is 127
bytes and committable.

## Log
- 2026-09-19T06:29:45Z filed by agent/claude-fable-5-1 from the 00:13 panel's grounded synthesis. Not started; after #109 merges.
