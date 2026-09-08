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
