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
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, ops/mutate/]
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
- 2026-09-19T07:53:05Z touches: WIDENED to `ops/mutate/` by agent/claude-opus-5 (the owner), because R1 below adds three
  mutations to `ops/mutate/scenic_tags.py` and raises its floor (a numeric change ships its population - CLAUDE.md,
  Verification). The pre-commit hook reads `touches:` from the header, so the widening is in the header and its reason
  is this line. The fixtures R3 commits are under `services/etl/tests/fixtures/`, already inside `services/etl/tests/`.
  Nothing else outside `touches:` is staged.
- 2026-09-19T07:53:05Z R1 THE ORACLE HARDENING (rv1-pr111's three recordables), ruled by agent/claude-opus-5 before code.
  WHAT IS WRONG TODAY, restated from the shipped module rather than from the review: `scenecheck.scored_value` is
  `int(raw)` with no contract at all, so (a) a tertiary tagged `scenic_score=42` is counted as `scored` and ranks #1 in
  the read the owner makes, (b) a motorway at `-3` clears clause 2 because `-3 > 0` is false, and (c) `scenic_score=abc`
  or `7.5` is a ValueError traceback out of `counts()` - the oracle crashes instead of naming the way. And `counts()`
  and `top()` disagree about ONE way: `counts()` tests `scenic_refused` FIRST and `continue`s, so a way carrying BOTH
  `scenic_refused=1` and a score is counted as `refused` and never as `scored`, while `top()` never looks at
  `scenic_refused` at all and ranks it. Two halves of one oracle with two answers about one road.
  THE RULING, three parts:
  (1) THE CONTRACT IS RESTATED IN THE CHECKER, DELIBERATELY. The writer keeps 0..10 (`tagwriter.quantise` clamps);
      the checker reads the BYTES THAT SHIP and may not assume the writer wrote them - a hand-edited PBF, a second
      producer, or a future writer is exactly what an independent oracle is for. `scenic_score` must be an INTEGER
      LITERAL in `SCORE_MIN..SCORE_MAX`, and those two bounds are IMPORTED from `tagwriter` by identity (the R8
      principle: the rules are imported, never restated - a second copy of a bound is how the writer and the checker
      agree with each other while both are wrong about a road). What is restated is that the value must SATISFY the
      contract; the numbers themselves are not copied.
  (2) THE REFUSAL SHAPE: a third CHECK4 clause, `malformed=N`, printed on the same line between `gated_scored` and
      `scored`, and `refuses()` exits 4 (`ops/sane`'s corpus-bounds code) when any of the three is non-zero. The
      CHECK4 line becomes `CHECK4 null_score=N gated_scored=N malformed=N scored=N refused=N not_a_road=N`. A
      malformed way is NAMED on stderr, one line per way (`way <id> scenic_score=<raw>: <why>`), capped at the first
      20 with a `... and N more` tail, because an oracle that prints 12,000 lines is an oracle nobody reads. A
      non-integer tag value is therefore a refusal that names the way, never a traceback.
      WHAT COUNTS AS MALFORMED, the three shapes: a `scenic_score` that is not an integer literal (`7.5`, `abc`, ``);
      an integer outside 0..10; and a way carrying BOTH `scenic_refused` and a `scenic_score`, which ruling R2 of
      T-0168 forbids ("`scenic_refused=1` and NO `scenic_score` tag - never a silent 0"). The third is the ONE ANSWER
      the acceptance asks for: a contradictory way is neither `refused` nor `scored`, it is `malformed`, in both
      halves.
  (3) ONE ANSWER BY CONSTRUCTION, not by two matching edits. `counts()` and `top()` stop classifying ways
      independently: a single `classify(way_id, tags) -> (kind, detail)` returns exactly one of
      `not_a_road / refused / malformed / null_score / scored`, `counts()` tallies its answer and `top()` ranks only
      the ways it calls `scored`. Two halves that each decide what a way is can drift; two halves that ask the same
      function cannot. A malformed way is excluded from the ranking - it cannot rank on a number the writer could not
      have written.
  THE POPULATION (a numeric module ships one): `ops/mutate/scenic_tags.py` gains three mutations, one per part -
  accept a score outside the range; let `top()` rank a way `classify` refused; let the non-integer value raise instead
  of being named - and `MIN_MUTATIONS` 25 -> 28. Each is demonstrated RED first on a hand-built read-back file, then
  green. `scenecheck.py` is 151 lines today; if the hardening crosses 300 it splits along a boundary of meaning (the
  classification and the CLI), not at a line number.
- 2026-09-19T07:53:05Z R2 THE GRID WINDOW and its way-count bound, ruled by agent/claude-opus-5 on MEASUREMENT, not on
  an estimate. The window is T-0168's own `--bbox -118.55,33.98,-118.35,34.15` (its 06:05:31Z entry: "They are a LATER
  RUN of the same five commands"), clipped from the MAIN checkout's `services/etl/work/la/la-filtered.osm.pbf`
  read-only. Clipped and counted first, before any scoring, `osmium extract` 11.018s + `osmium fileinfo -e`:
  **35,126 ways / 205,193 nodes / 26 relations, 2,859,589 B**, bounding box (-118.5883364,33.9597942,-118.3176785,
  34.1597259). That is 2.8x the canyon window's 12,402 and past this task's own ~25,000 bound, so THE RUN SPLITS, as
  the bound says: T-0168 measured `waydoc` at 1m56.591s and `assemble` at 3m33.557s for 11,740 rows (18.2 ms/row in
  the assembler), and every container step in this session must finish inside ONE foreground call.
  TWO SUB-WINDOWS, cut at longitude -118.45, both measured:
    grid-a  -118.55,33.98,-118.45,34.15   11,451 ways /  75,752 nodes  (Santa Monica, Brentwood, Pacific Palisades)
    grid-b  -118.45,33.98,-118.35,34.15   23,887 ways / 135,023 nodes  (Westwood, Century City, Culver City, Mar Vista)
  grid-b is above the canyon window and below the bound only if the urban per-row cost is at or under the mountain's;
  it runs SECOND and each of its stages is its own foreground call, and if `waydoc` on grid-a shows a per-row cost
  that puts grid-b's `assemble` over ~500s, grid-b splits again at -118.40. Measured, then decided - not assumed.
  THE SEAM: `osmium extract` completes every way that crosses the boundary (T-0168 measured the same effect on the
  canyon window's bbox), so a way crossing -118.45 is in BOTH clips with its full geometry and is scored twice. The
  merged grid ranking is over the UNION KEYED BY way_id; a way present in both must carry the SAME score, and that
  equality is checked and quoted rather than assumed - if the two clips disagree about one road, that is a finding
  about the score's dependence on its window, and it goes in the Log.
- 2026-09-19T07:53:05Z R3 THE COMPARISON - the exact predicate and the fixture shape, ruled by agent/claude-opus-5.
  THE PREDICATE, stated so it can be false: let `C10` be the canyon window's TENTH row by the ranking
  `scenecheck.top` prints - way 1237332026, Fernwood Pacific Drive, `scenic_score_unit` **0.7284** (T-0168's
  06:05:31Z entry, re-read here from the shipped read-back rather than copied from prose). The grid window's top ten
  RANK BELOW the canyon window's top ten iff **every one of the grid's ten `scenic_score_unit` values is strictly
  less than C10's**. The unit value and not the 0..10 integer, because the integer is a 4-bit quantisation in which
  the canyon's tenth and a grid way could tie at 7 while differing by 0.04 - a tie is not "below", and the acceptance
  word is BELOW.
  THE FIXTURES: the top **25** rows of each window - `way_id, name, highway, lat, lon, scenic_score,
  scenic_score_unit` exactly as `scenecheck.top` produces them - as
  `services/etl/tests/fixtures/canyon_top25.json` and `services/etl/tests/fixtures/grid_top25.json`, each carrying a
  `meta` naming the window bbox, the read-back file it was produced from, its way counts and the run that made it.
  Twenty-five and not ten so the fixture shows the shoulder of each distribution - a reviewer can see HOW FAR below,
  and a later window can be compared without a new run. The 7 MB scored tables are NOT committed (the work dir is
  gitignored and per-checkout).
  THE TEST: `tests/test_window_ranking.py::test_the_grid_windows_top_ten_ranks_below_the_canyon_windows` over the two
  fixtures, RED FIRST with the two fixture paths swapped (the canyon read as the grid), then green - or NOT green:
  IF THE PREDICATE IS FALSE ON THE REAL DATA THE TASK FAILS ITS OWN ACCEPTANCE. The test stays red, the Log names
  which grid ways outrank Topanga and why (the terms, from the scored table), and the PR says so on its first line.
  That is the finding this window was queued to produce - the one queued thing that can DISCONFIRM the index - and
  hiding it would make every other number here worthless.
- 2026-09-19T07:53:05Z R4 WHICH OF T-0168's STILL OPEN THIS RUN INHERITS, named and NOT fixed, by
  agent/claude-opus-5:
  INHERITED F1 SERVICE WAYS RANK WITH ROADS - and this is the window where it bites, not a footnote: 312,645 of the
  LA clip's 561,000 ways are `highway=service`, and they are concentrated exactly here (Westwood's alleys, Century
  City's parking aisles, Santa Monica's driveways), not in the canyons. Nothing in the score knows a driveway from a
  road. Unfixed here - a class prior or T-0164's POI term is the fix, and both are another task - but every service
  way that reaches the grid's top ten is NAMED in the read, because the owner's judgement needs to know which rows
  are roads.
  INHERITED F3 `points_of_interest_absent` ON EVERY WAY (T-0164 has not landed): 0.14 of E is a constant across both
  windows, so the comparison is between two rankings missing the SAME term - which is what makes it a fair
  comparison, and also what makes it provisional. Named in the PR.
  INHERITED F2 the gates: whatever fraction of the grid is gated is reported as a number, not smoothed.
  INHERITED F5 `extract.Osmium.rel()` cannot see the shared inputs directory from a worktree. This run does not call
  `etl.extract` at all - it clips with `osmium extract` directly out of the MAIN checkout's `la-filtered.osm.pbf`,
  mounted read-only at /src - so the defect is not hit; it is still there, still unfixed, and still named.
  NOT INHERITED, because this run cannot reach it: T-0168's F4 (the licence count) was a one-time re-record.
