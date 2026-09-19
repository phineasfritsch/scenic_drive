---
id: T-0204
title: ETL - the second LA window: the mixed street grid (Westwood/Brentwood/Santa Monica, -118.55,33.98,-118.35,34.15) scored through the same tagwriter + scenecheck path; acceptance: the grid's top ten rank BELOW the canyon window's, or the index is wrong
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T07:50:16Z
lease_expires_at: 2026-09-19T13:50:16Z
worktree: .worktrees/T-0204
branch: task/T-0204
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract]
pins_affected: []
reviewer: null
depends_on: [T-0168]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the five container commands T-0168's Log records, run over --bbox -118.55,33.98,-118.35,34.15 (the probe bbox T-0168's Log names) in the pinned scenic-etl image through WSL, each foreground and timed; the WAYDOC/ASSEMBLE/WRITE count lines quoted; two writes byte-identical (the P-DATA-01 shape, sha256 quoted); osmium fileinfo -e node/way counts quoted; CHECK4 both clauses zero"
  - "the grid's top ten by scenic_score printed the way scenecheck --top 10 prints them, beside the canyon window's top ten (T-0168's Log): every one of the grid's ten scores BELOW the canyon window's tenth, asserted by a test over the two scored tables (committed as small fixtures of the top-N rows, not the 7 MB JSON) - RED first on a swapped table; if the assertion is false the task FAILS its own acceptance and the Log says which grid ways outrank Topanga and why - that is the finding, not a defect to hide"
  - "the second read for the owner: the grid's top ten with name, class and a coordinate, the way T-0168 printed the canyon's; the judgement stays the owner's"
  - "scenecheck's read-back oracle hardened first (rv1-pr111's recordables on PR #111): the checker asserts every scenic_score is an int in 0..10 (today a tertiary at 42 counts as scored and ranks #1; a motorway at -3 clears clause 2 because value > 0 is false); counts() and top() give ONE answer for a way that is both scenic_refused=1 and scored (today counts() skips it and top() ranks it); a non-integer tag value is a refusal naming the way, not a traceback - each RED first on a hand-built read-back file, then green; the population in ops/mutate/scenic_tags.py gains the three"
  - "cd services/etl && python -m pytest tests -rs -o addopts= -> count line and zero skips at the final commit; wc -l re-measured"
---
## Brief

From the 01:13 panel (STRATEGY, grounded): T-0168's window is one massif - all ten top-scored ways are Santa Monica
Mountains canyon roads (Topanga x3, Stunt, Old Topanga x2, Piuma, Fernwood Pacific) - so plan:283's '8/10
top-scored ways are roads you'd drive' cannot fail there and measures nothing. The mixed grid east of the window is
the one queued thing that can DISCONFIRM the index: if Wilshire, Sunset through Brentwood, or a Westwood
residential grid outranks Topanga, the score is wrong and the Log says so. Same commands, same gates, the
scenic-index lock (one container run at a time).

## Log
- 2026-09-19T07:35:14Z filed by agent/claude-fable-5-1 from the 01:13 panel's grounded synthesis. Not started; after #111 merges - the NEXT START after T-0178/T-0195.
- 2026-09-19T07:46:16Z bullet added by agent/claude-fable-5-1 from rv1-pr111's PASS on PR #111 (recordables R-a, R-b, R-c): the checker over the shipped bytes does not restate the 0..10 int contract the writer keeps, its two halves disagree on a refused-and-scored way, and a non-integer value is a traceback. Shapes tagwriter cannot emit today, so gaps in the independent oracle, not in the bytes that ship - hardened before this window's second read so the oracle the owner reads is stricter than the writer.
- 2026-09-19T07:50:12Z PROMOTED to ready/ by agent/claude-fable-5-1: #111 (T-0168) merged and the scenic-index lock released; the LA extract, the filtered clip and the canyon window's scored table are in the MAIN checkout's gitignored services/etl/work/la/ (moved there before T-0168's worktree was removed, 551 MB) - this run clips the grid from la-filtered.osm.pbf, no refetch.
- 2026-09-19T07:50:16Z claimed by agent/claude-opus-5; lease until 2026-09-19T13:50:16Z
