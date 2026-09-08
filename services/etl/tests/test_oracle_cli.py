r"""`etl.oracle`'s command line, whose exit codes are the contract `ops/etl-curvature-fixture` reads.

Nothing called `main()`. `grep -rn 'oracle.main\|from etl.oracle import' services/etl/tests/` returned
nothing, and `ops/etl-mutation` measured what that costs: every constant in the function mutated green.
`return 2` at the missing-KMZ refusal, `return 0` after `--list-ways`, `return 0 if n else 2` after a build,
`return 0` at the tail, and `cap=args.limit or 400`. Twelve survivors, one cause - an untested function.

They are not decoration. `ops/etl-curvature-fixture` runs `etl.oracle` three times and judges two of those
runs BY THEIR EXIT CODE ALONE:

    "$PY" -m etl.oracle --list-ways > ids.txt 2>/dev/null || { (cd "$ETL" && ...) > ids.txt; }
    if ! (cd "$ETL" && "$PY" -m etl.oracle --build "../../$out" --export ...); then
      echo "BUILD FAILED: etl.oracle --build exited non-zero"; exit 2; fi

So `--list-ways` returning anything but 0 sends the rebuild down a fallback path it did not need, and a
successful `--build` returning anything but 0 aborts the only guard on fixture reproducibility this
repository has. The other direction is worse: a build that selected NOTHING must be non-zero, or the script
walks past `BUILD FAILED` and `mv`s an empty fixture over the committed one - which is the shape of the
failure agent/reviewer-34 reproduced, a run that is internally consistent and wrong.

Every case here passes `--kmz` explicitly. `inputs/vermont-curvature.kmz` is 2.5 MB, gitignored and fetched
by `ops/etl-fetch-inputs`, so a test that fell back to the default would pass or fail on whether somebody had
run the fetch.
"""
from __future__ import annotations

import json
from pathlib import Path

from etl import oracle
from etl import oracle_select as sel
from tests import oracle_kmz as ok

PAIR = (333, 444)   # two ways in one Placemark: a collection condition 1 refuses
REPO = Path(__file__).resolve().parents[3]
COMMITTED = Path(__file__).resolve().parent / "fixtures" / "curvature_oracle.json"


def _twelve(tmp_path: Path):
    """Twelve single-way collections, well separated, with an export that returns all of them.

    Twelve so a cap below it truncates, and so two different seeds picking the same subset - which would make
    `test_the_seed_decides_which_ways_are_sampled` vacuous - is one chance in 495.
    """
    ways = [(1000 + i, [(44.0 + i * 0.01 + d, -72.8) for d in (0.0, 0.001, 0.002)]) for i in range(1, 13)]
    kmz = ok.write_kmz(tmp_path / "many.kmz", *[ok.collection(w, c) for w, c in ways])
    export = ok.write_export(tmp_path / "many.geojsonseq", ways=[ok.road(w, c) for w, c in ways])
    return kmz, export


def _one(tmp_path: Path, way_id: int = 111, **props):
    kmz = ok.write_kmz(tmp_path / "one.kmz", ok.collection(way_id))
    export = ok.write_export(tmp_path / "one.geojsonseq", ways=[ok.road(way_id, **props)])
    return kmz, export


def _fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sample_line(path: Path) -> str:
    """The `selection` entry recording the cap and the seed the fixture was actually built with.

    Found by prefix rather than by index, so a reordered list still reads the right line and a DELETED line
    raises instead of silently comparing something else.
    """
    return next(s for s in _fixture(path)["selection"] if s.startswith("deterministic sample"))


def _ids(path: Path) -> list[int]:
    return [w["way_id"] for w in _fixture(path)["ways"]]


def _indent(path: Path) -> int:
    """The leading-space count of the fixture's first member line - `json.dumps(..., indent=N)`."""
    second = path.read_text(encoding="utf-8").splitlines()[1]
    return len(second) - len(second.lstrip(" "))


class TestTheExitCodesTheRebuildScriptReads:
    def test_a_missing_kmz_is_refused_with_2_and_names_the_fix(self, tmp_path, capsys):
        """Exit 2 and a message naming the file and `ops/etl-fetch-inputs`. The inputs are gitignored and
        fetched, so "the oracle is not on this machine" is the ordinary first-run state, and the one thing
        the operator needs is which command puts it there."""
        missing = tmp_path / "nowhere" / "vermont-curvature.kmz"
        assert oracle.main(["--kmz", str(missing)]) == 2
        err = capsys.readouterr().err
        assert str(missing) in err
        assert "ops/etl-fetch-inputs" in err

    def test_list_ways_exits_0_so_the_rebuild_does_not_take_its_fallback_path(self, tmp_path, capsys):
        """Step 1 of `ops/etl-curvature-fixture`. The ids are the input to `osmium getid`, one `w<id>` per
        line, and only single-way collections may appear: condition 1 is enforced here as well as in
        `eligible()`, because a two-way collection's id fetched here would be exported, compared, and
        counted."""
        kmz = ok.write_kmz(tmp_path / "k.kmz",
                           ok.collection(222), ok.collection(111), ok.placemark("Pair", ways=PAIR))
        assert oracle.main(["--kmz", str(kmz), "--list-ways"]) == 0
        assert capsys.readouterr().out.split() == ["w111", "w222"]

    def test_build_without_an_export_is_refused_with_2_and_writes_nothing(self, tmp_path, capsys):
        """`--build` alone cannot select anything: condition 2 compares the KML's geometry against the
        export's, and condition 3 needs the export's tagged nodes. Building without one would produce a
        fixture selected on one condition out of three and say nothing about it."""
        kmz = ok.write_kmz(tmp_path / "k.kmz", ok.collection(111))
        out = tmp_path / "fixture.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out)]) == 2
        assert not out.exists(), "a refused build still wrote a fixture"
        assert "--export" in capsys.readouterr().err

    def test_build_with_an_export_that_is_not_a_file_is_refused_with_2(self, tmp_path):
        """`--export` naming a path that does not exist is the same refusal as omitting it - `osmium export`
        having failed leaves exactly this state, and the run must stop rather than build from nothing."""
        kmz = ok.write_kmz(tmp_path / "k.kmz", ok.collection(111))
        out = tmp_path / "fixture.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out),
                            "--export", str(tmp_path / "never-written.geojsonseq")]) == 2
        assert not out.exists()

    def test_a_build_that_wrote_ways_exits_0_and_prints_the_funnel(self, tmp_path, capsys):
        """The success path. The funnel goes to stdout because a human reads it: `single_way` and
        `no_squash` differing by a lot is how a selection bug looks before it becomes a wrong percentage."""
        kmz, export = _one(tmp_path)
        out = tmp_path / "fixture.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out), "--export", str(export)]) == 0
        printed = capsys.readouterr().out
        assert "wrote 1 way(s)" in printed
        for stage in ("single_way", "have_geometry", "geometry_identical", "no_squash"):
            assert stage in printed, f"the funnel did not report {stage}"
        assert _ids(out) == [111]

    def test_a_build_that_selected_nothing_exits_2_rather_than_0(self, tmp_path):
        """The dangerous direction, and the reason `0 if n else 2` is not `0`.

        `ops/etl-curvature-fixture` builds to a staging file and `mv`s it over the committed fixture once the
        build has exited zero. An empty build reporting success replaces the oracle with nothing, and every
        downstream number stays internally consistent while measuring an empty set. The fixture is still
        WRITTEN here - the funnel in it is the diagnosis - but the exit code stops the move.
        """
        kmz, export = _one(tmp_path, junction="roundabout")
        out = tmp_path / "fixture.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out), "--export", str(export)]) == 2
        assert _fixture(out)["ways"] == []
        assert _fixture(out)["funnel"]["single_way"] == 1, "the funnel must say where the way died"
        assert _fixture(out)["funnel"]["no_squash"] == 0

    def test_the_survey_exits_0_and_counts_both_kinds_of_collection(self, tmp_path, capsys):
        """No flags at all: the orientation command. It is the only place the two counts appear side by
        side, and their ratio is what tells a human whether a re-fetched KMZ is the same shape as the old
        one before anything is rebuilt from it."""
        kmz = ok.write_kmz(tmp_path / "k.kmz", ok.collection(111), ok.placemark("Pair", ways=PAIR))
        assert oracle.main(["--kmz", str(kmz)]) == 0
        assert "2 collections, 1 of them single-way" in capsys.readouterr().out


class TestTheSampleIsCappedAndSeededByTheDocumentedNumbers:
    """400 and 20260907 are declared THREE times: `main`'s `args.limit or 400`, and the `cap`/`seed`
    defaults of both `oracle.build` and `oracle_select.build`. `oracle.build` re-declares them so that
    `python -m etl.oracle --build` keeps working while the selection lives in one module.

    Three copies of a number are three answers to the question it settles - the defect the `ORACLE_TOLERANCE`
    comment records, where a second copy of the 2% threshold let a sweep to 0.5 print `100.000%` green. They
    are not merged here, because merging them is a change to the modules and this task is measuring them; the
    cases below instead pin all three to the same value, so a drift in any one of them is red.

    The values are observable rather than introspected: `build()` writes them into the fixture's `selection`
    list, which is the fixture's own record of how its sample was drawn.
    """

    def test_the_cli_caps_at_400_when_no_limit_is_given(self, tmp_path):
        kmz, export = _twelve(tmp_path)
        out = tmp_path / "fixture.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out), "--export", str(export)]) == 0
        assert _sample_line(out) == "deterministic sample of 400 from 12 eligible, seed 20260907"
        assert len(_ids(out)) == 12, "a cap above the eligible count must not drop anything"

    def test_limit_replaces_the_cap_and_actually_truncates(self, tmp_path):
        """`--limit` exists so a human can take a quick sample; if it did not reach the cap, the run would
        take the full one and the fixture would claim a number it did not use."""
        kmz, export = _twelve(tmp_path)
        out = tmp_path / "fixture.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out),
                            "--export", str(export), "--limit", "4"]) == 0
        assert _sample_line(out) == "deterministic sample of 4 from 12 eligible, seed 20260907"
        assert len(_ids(out)) == 4

    def test_both_wrappers_default_to_the_cap_and_seed_the_cli_uses(self, tmp_path):
        """The other two copies, called with no cap and no seed so the defaults are what is under test."""
        kmz, export = _twelve(tmp_path)
        through_oracle, through_select = tmp_path / "a.json", tmp_path / "b.json"
        oracle.build(through_oracle, export, kmz)
        sel.build(through_select, export, kmz)
        want = "deterministic sample of 400 from 12 eligible, seed 20260907"
        assert _sample_line(through_oracle) == want
        assert _sample_line(through_select) == want

    def test_the_seed_decides_which_ways_are_sampled(self, tmp_path):
        """The recorded string alone would pass for a seed nothing reads. This is the seed doing its job:
        the same twelve ways, the same cap of four, two seeds, two different subsets. `20260908` is the
        exact mutation `ops/etl-mutation` makes to it."""
        kmz, export = _twelve(tmp_path)
        default_seed, other_seed = tmp_path / "default.json", tmp_path / "other.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(default_seed),
                            "--export", str(export), "--limit", "4"]) == 0
        sel.build(other_seed, export, kmz, cap=4, seed=20260908)
        assert len(_ids(default_seed)) == len(_ids(other_seed)) == 4
        assert _ids(default_seed) != _ids(other_seed), "the sample does not depend on the seed at all"

    def test_two_builds_of_the_same_inputs_are_byte_identical(self, tmp_path):
        """What the seed is FOR. `ops/etl-curvature-fixture --check` rebuilds into a temp file and `diff`s
        it against the committed fixture; that comparison means nothing unless a rebuild of unchanged inputs
        reproduces the file exactly, byte for byte, including the order of the sampled ways."""
        kmz, export = _twelve(tmp_path)
        first, second = tmp_path / "first.json", tmp_path / "second.json"
        for out in (first, second):
            assert oracle.main(["--kmz", str(kmz), "--build", str(out),
                                "--export", str(export), "--limit", "4"]) == 0
        assert first.read_bytes() == second.read_bytes()


class TestTheFixtureTheCliWritesSaysWhereItCameFrom:
    """The provenance block, the staging directory and the formatting - all of which mutated green.

    `ops/etl-mutation` dropped `source`, `osm_source` and `rebuild_with` from the object `build()` writes and
    nothing objected. That is the defect this task opened with, one level up from the per-way record: the
    three strings appear in this repository only inside the committed fixture, and no assertion read them.
    They are what a reader has instead of the session that produced the file - which URL the published values
    came from, which OSM extract they were computed over, and which command regenerates both. A fixture that
    has lost them is 684 KB of numbers with no way back to their origin, and no way to check them.
    """

    def test_it_names_both_inputs_and_the_command_that_rebuilds_it(self, tmp_path):
        """Compared against the committed fixture rather than against literals typed here: a rebuild that
        changes any of the three makes `ops/etl-curvature-fixture --check` report a difference, which is the
        one signal saying the committed file is no longer what the pipeline produces."""
        kmz, export = _one(tmp_path)
        out = tmp_path / "fixture.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out), "--export", str(export)]) == 0
        wrote = _fixture(out)
        committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
        for key in ("source", "osm_source", "rebuild_with"):
            assert wrote[key] == committed[key], f"a rebuild no longer records the same {key}"
        assert (REPO / wrote["rebuild_with"]).is_file(), (
            "the fixture names a rebuild command that is not in the tree, which is the same as naming none")

    def test_it_creates_the_directory_it_writes_into(self, tmp_path):
        """`ops/etl-curvature-fixture` never builds onto the committed fixture. It builds into
        `services/etl/work/curvature-oracle/`, which is gitignored and absent on a fresh checkout, and moves
        the result into place only after every check has passed - the ordering that stopped a refused
        226-way build from leaving its output behind. `mkdir(parents=True)` is what makes that staging
        directory exist; without it the first rebuild on a clean tree dies before selecting anything."""
        kmz, export = _one(tmp_path)
        out = tmp_path / "work" / "curvature-oracle" / "rebuilt.json"
        assert not out.parent.exists(), "this case tests nothing unless the directory is missing"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out), "--export", str(export)]) == 0
        assert _ids(out) == [111]

    def test_it_is_written_the_way_the_committed_fixture_is_written(self, tmp_path):
        """`--check` compares a rebuild against the committed file with `diff`. Re-indent the writer and
        every one of that file's ~30 000 lines differs while nothing about the oracle has changed; a diff
        that is always total is a diff nobody reads, and the check it feeds stops being able to say
        anything. Same for the line endings, on a repository that is edited from Windows."""
        kmz, export = _one(tmp_path)
        out = tmp_path / "fixture.json"
        assert oracle.main(["--kmz", str(kmz), "--build", str(out), "--export", str(export)]) == 0
        assert _indent(out) == _indent(COMMITTED) == 1
        assert b"\r\n" not in out.read_bytes(), "CRLF would make every line of the diff differ"
        assert out.read_text(encoding="utf-8").endswith("\n")
