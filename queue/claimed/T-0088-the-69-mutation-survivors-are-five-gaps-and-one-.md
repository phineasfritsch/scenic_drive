---
id: T-0088
title: the 69 mutation survivors are five gaps, and one of them is the fixture's own record shape
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T05:48:57Z
lease_expires_at: 2026-09-08T11:48:57Z
worktree: wt/T-0088
branch: task/T-0088
exclusive: []
touches: [services/etl/tests/, services/etl/etl/, ops/lib/etl_mutation.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

[[T-0081]] added `ops/etl-mutation` and measured **117 killed, 69 survived of 186**. A survivor count is a
map, not a verdict, and that task's log says so. This is the reading of the map: **the 69 are not 69
independent gaps. They are five, and one of them is a real hole in the oracle's own output.**

Every claim below was executed against `task/T-0081`.

**1. `etl/oracle.py:main()` is not called by any test — ~12 survivors, one cause.**

    grep -rn 'oracle.main\|from etl.oracle import' services/etl/tests/   ->  nothing

Every constant in `main()` mutates green: exit `2 -> 3`, exit `0 -> 1`, `cap=args.limit or 400 -> 401`, and
the `20260907 -> 20260908` at line 135. Those are not twelve findings, they are one untested function, and its
exit codes are the contract `ops/etl-curvature-fixture` depends on.

**2. The emitted fixture record's SHAPE is never asserted — 4 survivors, and this is the serious one.**
`oracle_select.py:162` builds each kept record:

    kept.append({"way_id": …, "name": …, "surface": …, "oracle_curvature": …, "coords": …})

Dropping **any** key — including `oracle_curvature`, the value the entire oracle exists to carry, and `coords`,
the geometry the comparison is made against — leaves the suite green. The keys appear in the repository only
inside the committed `tests/fixtures/curvature_oracle.json`; no assertion ever reads them. So the fixture could
be regenerated without its curvature values and nothing would object, which is the same shape as the
provenance defect T-0069 was filed for, one level further in.

**3. Parser guards for malformed input are untested — 4 `continue` survivors.**
`oracle.py:82`, `:86`, `:119`, `:125` are `if not m: continue` and `if not rows: continue` on a Placemark with
no DESCRIPTION or no way rows. Turning any into `pass` is green: no test feeds a malformed block.

**4. `eligible()`'s multi-operand exclusion is untested — 4 survivors at `oracle_select.py:153`.**
Dropping any of the three operands, or flipping `or` to `and`, is green. This is E4's neighbourhood, and E4
is the evasion that beat T-0074 first.

**5. `NODE_TAGS` and the `highway` value set are unasserted** — the X11/X12 class T-0081's rules reproduced
verbatim. Already described there; listed for completeness.

- Five tests, roughly. Not sixty-nine.
- **Assert the record shape first** (gap 2). It is the cheapest and it guards the thing the oracle is for.
- After each test lands, re-run `ops/etl-mutation` and **lower `MAX_SURVIVORS`** to the new number. That is
  the ratchet working; the constant is guarded by `.githooks/commit-msg`, so raising it needs a stated reason.
- Do NOT chase survivors one at a time. Gap 1 is twelve of them and one test.
- Some survivors are genuinely equivalent mutations and will never die. When the number stops falling, say
  which remain and why, rather than leaving a floor nobody can explain.

## Log
- 2026-09-08 filed by agent/claude-opus-5. The 69 came from `ops/etl-mutation` on `task/T-0081`; the grouping
  was done by reading the modules and confirming each cause, not by counting lines.
- 2026-09-08T05:48:57Z claimed by agent/claude-opus-5; lease until 2026-09-08T11:48:57Z

### Measurement before this session's work

`ops/etl-mutation` on `task/T-0088` at 6d64df1 (gap 2 landed, ratchet not yet moved):

    MUTATION 121 killed, 65 survived, of 186 run in 576s

So the 69 in the brief was already 65: gap 2's two tests killed the four `oracle_select.py:162` record-key
survivors. `MAX_SURVIVORS` was still 69 and is lowered per gap below.

One local note, because it cost a run: `ops/etl-mutation` resolves `${PYTHON:-$(command -v python3 || command
v python)}`, and on this Windows box `python3` is the WindowsApps 3.14 shim with no pytest, so the harness
reported `baseline: FAIL / the suite does not pass unmutated` for a suite that passes. Every run below is
`PYTHON=.../Python310/python bash ops/etl-mutation`. The guard did exactly its job - it refused rather than
reporting numbers - but the message names the suite, not the interpreter.

### Gap 1 - `etl/oracle.py:main()` is called by no test

`grep -rn 'oracle.main\|from etl.oracle import' services/etl/tests/` returned nothing, so nineteen mutants in
one 33-line function had nothing to object to them. New: `services/etl/tests/test_oracle_cli.py` (15 cases)
and `services/etl/tests/oracle_kmz.py`, a builder that can emit a MALFORMED Placemark - which is what gap 3
needs and what `test_oracle_build.py`'s builders deliberately cannot do.

The exit codes are asserted as the contract `ops/etl-curvature-fixture` actually reads: that script judges
`--list-ways` and `--build` by exit code alone, and the dangerous direction is a build that selected NOTHING
returning 0, because the script then walks past `BUILD FAILED` and `mv`s an empty fixture over the committed
one. The cap is asserted through the `selection` line `build()` writes into the fixture, so 400 and 20260907
are checked where a reader can see them rather than by introspecting a signature; the seed additionally has
to CHANGE the sample (twelve eligible ways, cap four, `20260907` against the mutant's own `20260908`), and
two builds of the same inputs have to be byte-identical, which is what `--check`'s `diff` needs.

Three more survivors of the same family as gap 2 fell out of the CLI's build path and are closed with it:
`source`, `osm_source` and `rebuild_with` could each be dropped from the object `build()` writes with the
suite green - the per-way record defect one level up, at the fixture's own provenance block.

RED, before green. Every mutation below is applied by `ops/lib/etl_mutation_rules.mutants_for` itself, not
retyped by hand, then restored (`.artifacts/redsweep.py`):

    UNMUTATED           15 passed in 0.19s
    CAUGHT   oracle.py:135 constant 400 -> 401                 test_both_wrappers_default_to_the_cap_and_seed
    CAUGHT   oracle.py:135 constant 20260907 -> 20260908       test_the_cli_caps_at_400_when_no_limit_is_given
    CAUGHT   oracle.py:156 not      drop `not`                 test_a_missing_kmz_is_refused_with_2
    CAUGHT   oracle.py:158 constant 2 -> 3                     test_a_missing_kmz_is_refused_with_2
    CAUGHT   oracle.py:163 constant 0 -> 1                     test_a_missing_kmz_is_refused_with_2
    CAUGHT   oracle.py:166 boolop   Or -> And                  test_build_without_an_export_is_refused_with_2
    CAUGHT   oracle.py:166 not      drop `not`            [0]  test_build_without_an_export_is_refused_with_2
    CAUGHT   oracle.py:166 not      drop `not`            [1]  test_build_with_an_export_that_is_not_a_file
    CAUGHT   oracle.py:166 operand  drop operand 0 of Or       test_build_without_an_export_is_refused_with_2
    CAUGHT   oracle.py:166 operand  drop operand 1 of Or       test_build_with_an_export_that_is_not_a_file
    CAUGHT   oracle.py:169 constant 2 -> 3                     test_build_without_an_export_is_refused_with_2
    CAUGHT   oracle.py:170 boolop   Or -> And                  test_the_cli_caps_at_400_when_no_limit_is_given
    CAUGHT   oracle.py:170 constant 400 -> 401                 test_the_cli_caps_at_400_when_no_limit_is_given
    CAUGHT   oracle.py:170 operand  drop operand 0 of Or       test_limit_replaces_the_cap_and_truncates
    CAUGHT   oracle.py:170 operand  drop operand 1 of Or       test_the_cli_caps_at_400_when_no_limit_is_given
    CAUGHT   oracle.py:174 constant 0 -> 1                     test_a_build_that_wrote_ways_exits_0
    CAUGHT   oracle.py:174 constant 2 -> 3                     test_a_build_that_wrote_ways_exits_0
    CAUGHT   oracle.py:176 constant 1 -> 2                     test_a_build_that_wrote_ways_exits_0
    CAUGHT   oracle.py:179 constant 0 -> 1                     test_the_survey_exits_0_and_counts_both_kinds
    CAUGHT   oracle_select.py:172 constant 400 -> 401          test_both_wrappers_default_to_the_cap_and_seed
    CAUGHT   oracle_select.py:172 constant 20260907 -> ...908  test_both_wrappers_default_to_the_cap_and_seed
    CAUGHT   oracle_select.py:198 constant True -> False  [0]  test_it_creates_the_directory_it_writes_into
    CAUGHT   oracle_select.py:198 constant True -> False  [1]  test_a_build_that_wrote_ways_exits_0
    CAUGHT   oracle_select.py:199 dictkey drop key 'source'    test_it_names_both_inputs_and_the_command
    CAUGHT   oracle_select.py:199 dictkey drop 'osm_source'    test_it_names_both_inputs_and_the_command
    CAUGHT   oracle_select.py:199 dictkey drop 'rebuild_with'  test_it_names_both_inputs_and_the_command
    CAUGHT   oracle_select.py:216 constant 1 -> 2              test_it_is_written_the_way_the_committed_fixture

    0 of the listed mutants were NOT caught

GREEN, unmutated: `200 passed` for the whole ETL suite (185 before this file).

Full run after gap 1 landed (770174d):

    MUTATION 149 killed, 37 survived, of 186 run in 488s

28 survivors gone, one more than the 27 demonstrated - `selection` and `funnel` at `oracle_select.py:199`
died too, because the new cases read those keys to check the cap and the funnel. Ratchet: `MAX_SURVIVORS`
69 -> 37.

### Gap 3 - the parser guards were never reached

`oracle.py:82`, `:86`, `:119` and `:125` are `if not m: continue` / `if not rows: continue` / `if not cm:
continue`. Three of the four are an `AttributeError` on `None.group(1)` the moment they stop guarding, so
they are not equivalent mutations - they had simply never been executed, because every KMZ the suite wrote
was well-formed. `tests/oracle_kmz.py` (added with gap 1) builds a Placemark from parts, so a test can leave
out the `<description>`, the way rows or the `<coordinates>`. New: `services/etl/tests/test_oracle_parser.py`
(6 cases), plus one case in `test_oracle_select.py` for `load_export`'s sibling pair - the same defect in the
other module, where the two opening guards are what let one reader take both `-f geojsonseq` and `-f geojson`.

`:86` is the only one of the four whose failure is silent: a Placemark whose description is not a
constituent-ways table gets yielded as a collection with an empty way list, `single_way_collections` then
drops it on `len(rows) != 1`, and nothing downstream changes - what changes is the count in
`oracle: N collections, M of them single-way`, which is the number a human compares across a re-pin.

    UNMUTATED           21 passed in 0.10s
    CAUGHT   oracle.py:82  continue `continue` -> `pass`   test_a_placemark_with_no_description_is_skipped...
    CAUGHT   oracle.py:86  continue `continue` -> `pass`   ...and_not_dereferenced (collections)
    CAUGHT   oracle.py:119 continue `continue` -> `pass`   test_a_placemark_with_no_description_is_skipped
    CAUGHT   oracle.py:125 continue `continue` -> `pass`   (kml_geometry)
    SURVIVED oracle_select.py:86 continue `continue` -> `pass`    21 passed
    CAUGHT   oracle_select.py:90 continue `continue` -> `pass`    test_load_export_reads_a_plain_geojson...
    SURVIVED oracle_select.py:91 operand  drop operand 1 of Or    21 passed
    CAUGHT   oracle_select.py:92 operand  drop operand 1 of Or    test_load_export_reads_a_plain_geojson...
    CAUGHT   oracle_select.py:93 operand  drop operand 1 of Or    test_load_export_reads_a_plain_geojson...

TWO SURVIVED, and both are equivalent mutations rather than missing cases. They are left as survivors and
explained rather than chased, which is the whole point of measuring:

- `oracle_select.py:86`, `if not line.startswith("{"): continue`. Turning it into `pass` sends the line into
  the `try` below, and every line that does not start with `{` and occurs in a real export - blank, `[`,
  `]}`, a truncated tail - raises `JSONDecodeError` and is skipped by the guard at `:90` instead. The two
  guards produce different behaviour only for a line that is VALID JSON and is not an object (`null`, `[]`,
  a bare number), which no exporter writes. `:86` is a clearer statement of intent than `:90`, not a
  different decision.
- `oracle_select.py:91`, `str(feature.get("id") or "")`. This one was written as a case first and the case
  disproved its own premise: the reasoning was that dropping `or ""` makes an id-less feature `str(None)` and
  that `"None".startswith("n")` then collects it as a tagged node. `str(None)` is `"None"` with a capital N.
  It begins with neither `"w"` nor `"n"`, so both branches skip it exactly as `""` does. Every id that
  reaches a branch is a string beginning `w` or `n`, whose `str()` is itself; every falsy one stringifies to
  something that reaches neither. The finding is written into the test's docstring so the next reader does
  not re-derive it.

GREEN, unmutated: `210 passed`.

Full run after gap 3 landed (004dc2b):

    MUTATION 163 killed, 23 survived, of 186 run in 451s

14 gone against the 7 demonstrated. The extra seven are the malformed features in the `load_export` case
doing work the case was not aimed at: `oracle_select.py:94` and `:98`, the `startswith(...) and
geom.get("type") == ...` pair that decides whether a feature is read as a way or as a node, and - because a
null geometry means the way has no `ours` - two of the four at `:153` and the `continue` at `:154`, which are
gap 4's. Ratchet: `MAX_SURVIVORS` 37 -> 23.

### Gap 4 - `eligible()`'s comparability guard had three dead operands

    if not ours or not theirs or len(ours) < 3:
        continue

Every export the suite wrote contained every published way, with the KML's own geometry, three vertices long,
so all three operands were dead code under test - the same reason E4 beat T-0074 six lines further down. Three
cases in `test_oracle_select.py`, one per operand, each driven against a well-formed neighbour in the same
KMZ so `have_geometry == 1` says the probe was excluded HERE rather than never eligible:

- `not ours` - a published way `osmium getid` did not return. This is the ORDINARY case, not a corrupt one:
  21 of 3318 ids are absent from the pinned extract because the KMZ predates it, and
  `ops/etl-curvature-fixture` deliberately carries on. Without the operand it is `len(None)`, and the rebuild
  dies on input it was designed to tolerate.
- `not theirs` - a Placemark with a way table and no `<LineString>`, so the geometry Curvature computed over
  was never published. Condition 2 IS the comparison against that geometry; admitting the way anyway admits
  it on two conditions out of three while the fixture goes on claiming three.
- `len(ours) < 3` - a radius needs three points, and `assign_radii` gives a single-segment way `MAX_RADIUS`,
  which is above every band in `LEVELS`. Its curvature is 0 by construction, not by measurement, so agreeing
  with the oracle there is agreeing that 0 == 0 and counting it as evidence about the five steps.

<!-- -->

    UNMUTATED           18 passed in 0.08s
    CAUGHT   oracle_select.py:153 boolop  Or -> And           test_a_published_way_the_export_never_returned
    CAUGHT   oracle_select.py:153 operand drop operand 0      test_a_published_way_the_export_never_returned
    CAUGHT   oracle_select.py:153 operand drop operand 1      test_a_way_the_kml_carries_no_geometry_for
    CAUGHT   oracle_select.py:153 operand drop operand 2      test_a_way_of_fewer_than_three_vertices
    CAUGHT   oracle_select.py:154 continue `continue` -> `pass`  test_a_published_way_the_export_never_returned

    0 of the listed mutants were NOT caught

Three of those five had already died as a side effect of gap 3's malformed features; the cases are kept
separate anyway, because a side effect is not a statement about the operand and the next person to touch
`load_export` would take the coverage away without knowing it.

GREEN, unmutated: `213 passed`.

Full run after gap 4 landed (f887858):

    MUTATION 165 killed, 21 survived, of 186 run in 486s

Only 2 more, because three of gap 4's five had already died in gap 3. Ratchet: 23 -> 21 is folded into the
sweep-up below rather than committed on its own.

### The sweep-up, before calling anything a floor

Reading the 21 one by one, seven of them are not equivalent mutations at all - they are real holes that a
line or two of test closes, and writing "explained floor" over a hole one can close in three lines is the
thing this repository exists to catch. So, one more pass, and the three assigned gaps are untouched by it:

- `oracle.py:47`, `path = manifest or (ROOT / "inputs" / "manifest.yaml")`. The `manifest` PARAMETER could be
  dropped entirely with the suite green, because every caller in the suite passes exactly the default path,
  so no case could tell an honoured argument from an ignored one. Everything `oracle_select.build` refuses
  rests on this function answering about the manifest it was ASKED about.
- `oracle.py:58`, `return want or None`. A `sha256:` line with nothing after it names no digest, which the
  docstring promises reads as None; without the `or None` it reads as the empty string.
- `oracle_select.py:94`, `ident.startswith("w") and ...`. Drop the id test and ANY LineString feature is read
  as a way, `int(ident[1:])` on an id-less one being `int("")`. Covered by adding an id-less LineString to
  the export-reader case, which is the same shape as the id-less node already there.
- `oracle_select.py:118` and `:119`, `for dy in (-1, 0, 1)` / `for dx in (-1, 0, 1)`. The trailing `1` could
  become a `2` on both axes with the suite green: the one cell-boundary case in the file put the node BELOW
  the way, so only the -1 neighbour was ever exercised. A node just north, or just east, is still inside the
  30 m radius, and missing it is condition 3 failing OPEN - a squash-exposed way compared and counted.
- `oracle_select.py:167` twice, `round(lat, 7)` / `round(lon, 7)`. 11 mm, against a `GEOMETRY_TOL_M` of 1 m
  and a 684 KB file that `--check` compares line by line. Nothing asserted the precision.

<!-- -->

    UNMUTATED           28 passed in 0.13s
    CAUGHT   oracle.py:47  operand  drop operand 0 of Or    test_the_manifest_argument_is_the_file_that_is_read
    CAUGHT   oracle.py:58  operand  drop operand 1 of Or    test_a_sha256_line_with_nothing_after_it_names_no...
    CAUGHT   oracle_select.py:94  operand drop operand 0    test_a_plain_geojson_collection_reads_the_same_as...
    CAUGHT   oracle_select.py:118 constant 1 -> 2   [0]     test_the_proximity_grid_finds_a_node_across_a_cell...
    CAUGHT   oracle_select.py:118 constant 1 -> 2   [1]     test_the_proximity_grid_also_searches_the_cell_above
    CAUGHT   oracle_select.py:119 constant 1 -> 2   [0]     test_the_proximity_grid_also_searches_the_cell_above
    CAUGHT   oracle_select.py:119 constant 1 -> 2   [1]     test_the_proximity_grid_also_searches_the_cell_above
    CAUGHT   oracle_select.py:167 constant 7 -> 8   [0]     test_the_records_coordinates_are_rounded_to_seven...
    CAUGHT   oracle_select.py:167 constant 7 -> 8   [1]     test_the_records_coordinates_are_rounded_to_seven...

    0 of the listed mutants were NOT caught

`test_oracle_parser.py` widened from "the four guards in etl.oracle" to every reader in the two modules -
the KML Placemark parser, the osmium-export parser and the manifest parser - since all three have the same
defect: each consumes a file this repository does not write, and each had only ever been fed input this
repository did write. `load_export`'s case moved there from `test_oracle_select.py` for the same reason, and
that also keeps both files under the 300-line cap (297 and 215).

GREEN, unmutated: `217 passed`.

### The demonstration tool was lying, and how that surfaced

The sweep-up run above reported `oracle_select.py:119 constant 1 -> 2` CAUGHT twice. The full
`ops/etl-mutation` run afterwards reported one survivor at `:119`. Two measurements of the same mutant
disagreeing is not a discrepancy to reconcile, it is one of them being wrong, so it was chased:

CPython validates a `.pyc` against its source's **mtime in whole seconds** and its **size**. Two mutants of
one module differ by a single character, and `ast.unparse` gives them the SAME size. So two mutant runs
inside the same wall-clock second reuse the FIRST one's bytecode, and the second mutant is judged on code
that was never on disk for it. `-p no:cacheprovider` is pytest's cache, not this one.

`ops/etl-mutation` has never hit it: at ~2.3 s per mutant, consecutive writes are more than a second apart
and so always land in different seconds. That is not a guarantee, it is an accident of how slow the suite is.
`.artifacts/redsweep.py` runs one file in 0.15 s, hit it immediately, and reported CAUGHT for a mutant that
survives - which is precisely the failure mode this repository exists to contradict, arriving through the
tool built to demonstrate it. Reproduced by running the same two-mutant plan twice and getting two different
answers; stable across repeated runs after the fix.

Fixed in BOTH: `purge_bytecode()` deletes the module's `.pyc` after every write and after every restore, and
`PYTHONDONTWRITEBYTECODE=1` in the child environment stops a new one being written. The harness change is in
`ops/lib/etl_mutation.py`, which the final run below re-measures.

The real survivor it had hidden: `for dx in (-1, 0, 1)` -> `(-2, 0, 1)`, a tagged node one cell WEST of the
way. The mirror case only covered north and east, and the pre-existing boundary case only south. The test is
now all four neighbours in one loop, each asserting that the pair really does straddle a cell edge and really
is inside the 30 m radius, so a case that stopped straddling would fail rather than pass vacuously.

ALL FOUR red demonstrations re-run against the WHOLE suite with the fixed tool - the transcripts above were
produced by the tool before the fix and are superseded by these:

    gap 1     27 listed, 27 CAUGHT, 0 not caught
    gap 3      9 listed,  7 CAUGHT, 2 SURVIVED (oracle_select.py:86 and :91, equivalent, explained above)
    gap 4      5 listed,  5 CAUGHT, 0 not caught
    sweep-up   9 listed,  9 CAUGHT, 0 not caught
    UNMUTATED 217 passed

Final run, with the fixed harness (6c44d8f):

    MUTATION 172 killed, 14 survived, of 186 run in 537s

Ratchet: `MAX_SURVIVORS` 23 -> 14. The whole sequence, all measured rather than projected:

    186 mutants   117/69   T-0081, the first measurement
                  121/65   gap 2, the emitted record's shape (landed before this session)
                  149/37   gap 1, main() and the cap/seed defaults
                  163/23   gap 3, the parser guards
                  165/21   gap 4, eligible()'s comparability guard
                  172/14   the survivors that were holes rather than equivalences

### The residual 14, one at a time

Six are a real hole. Eight cannot be killed by any test this suite can contain.

**Gap 5, the brief's own fifth item - 6 survivors, a real hole, deliberately not closed here.**

    oracle_select.py:37   dictkey   drop key 'traffic_calming'          (NODE_TAGS)
    oracle_select.py:38   setmember drop 'stop' / 'give_way' / 'crossing' / 'mini_roundabout'
                                    / 'traffic_calming'                 (NODE_TAGS["highway"])

`test_load_export_collects_only_nodes_carrying_a_squash_tag` feeds a `highway=traffic_signals` node and a
`barrier=gate` node, so those two entries die; the other six values have no case at all. This is the X11/X12
class T-0081 named and the brief lists as gap 5, "already described there; listed for completeness" - it was
not in this session's scope, and closing it here would take the work off whoever holds it. It is one
parametrised case over `NODE_TAGS` itself, driven through `load_export`, and it would take the number to 8.
Written down precisely so nobody has to re-derive it.

**Genuinely equivalent - these can never die.**

- `oracle_select.py:68` twice, `fh.read(1 << 20)` -> `2 << 20` and `1 << 21`. The block size of a streaming
  sha256 cannot change the digest; the same bytes are read in different-sized chunks. A test that could tell
  them apart would be asserting about read syscalls rather than about the digest. (T-0074's E6 - collapsing
  that loop to a SINGLE read - is a different mutation, is not equivalent, and dies against
  `test_two_large_kmzs_sharing_a_first_block_still_get_different_digests`.)
- `oracle.py:54` and `:56`, `line.split(":", 1)` -> `split(":", 2)`. The only two lines that reach these are
  `- name: <filename>` and `sha256: <hex>`, and neither value can contain a colon, so `[1]` is the same
  string under both. Observable only for a manifest the format cannot produce.
- `oracle_select.py:86`, `if not line.startswith("{"): continue` -> `pass`. Every line that does not start
  with `{` and can occur in a real export - blank, `[`, `]}`, a truncated tail - raises `JSONDecodeError` and
  is skipped by the guard at `:90` instead. The two differ only for a line that is VALID JSON and is not an
  object (`null`, `[]`, a bare number), which no exporter writes. `:86` is a clearer statement of the same
  decision, not a different one.
- `oracle_select.py:91`, `str(feature.get("id") or "")` -> `str(feature.get("id"))`. `str(None)` is `"None"`
  with a capital N, so it begins with neither `"w"` nor `"n"` and both branches skip it exactly as `""` does.
  Every id that reaches a branch is a string beginning `w` or `n`, whose `str()` is itself. This one was
  written as a test case first, on the opposite reasoning, and the case disproved its own premise; the
  finding is in the docstring of `test_a_plain_geojson_collection_reads_the_same_as_a_sequence`.
- `oracle_select.py:98`, dropping `geom.get("type") == "Point"` from the node branch. `osmium export` emits a
  node only as a Point, so no file the toolchain can produce distinguishes the two. Killing it would mean
  fabricating an `n`-prefixed feature carrying a LineString and asserting about it - a test about a file that
  cannot exist. Its sibling at `:94` is NOT in this category and is killed: an id-less LineString is a real
  shape, produced by any export run without `--add-unique-id=type_id`.

**Unkillable without the fetched input - 1.**

- `oracle_select.py:187`, `if want and digest != want:` with `digest != want` dropped, which refuses every
  KMZ whose basename is the pinned one regardless of its bytes. To kill it a test would have to present a
  file named `vermont-curvature.kmz` whose sha256 IS the manifest's pin - `build()` asks
  `oracle.pinned_digest(kmz.name)` with no manifest argument, so the pin always comes from the repository's
  own `inputs/manifest.yaml`, and the only file that satisfies it is the real 2.5 MB oracle: gitignored,
  fetched by `ops/etl-fetch-inputs`, absent from a fresh checkout. The guard IS exercised end to end - with
  this operand dropped, `ops/etl-curvature-fixture` refuses the pinned oracle and exits 2 - just not by a
  suite that must run without the input.

### Verification

- `services/etl`: 217 passed (185 at the start of this session).
- `ops/check-pins --source-only`: `PINS ok=3 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only`.
- `ops/test`: the Swift suites pass (16 tests, 3 suites); it then exits 1 on
  `FAIL: services/api exists but vitest produced no report`, which is this worktree having no
  `services/api/node_modules`. Pre-existing and unrelated: this branch changes 0 files under `services/api`.
