"""The four consumers read the SHARED inputs directory, and an absent payload is a refusal by name.

T-0177 put `resolve_inputs_dir` in `etl.fetch` and stopped there (its ruling R3: the four consumers were
outside its `touches:`), so `etl.dem`, `etl.landcover`, `etl.oracle` and `etl.extract` each still computed
`ROOT / "inputs"` - which from `.worktrees/<id>/services/etl` is a directory the payloads have never been in.
The California extract and the LA 3DEP tiles live ONLY in the main checkout's directory, so a pipeline run
from a worktree sampled nothing and said so with `[None] * len(points)`, which is indistinguishable from
ocean. That is the T-0168 trap this file exists to spring first.

Two properties, kept apart on purpose:

* a tile or raster file MISSING from the resolved directory is a REFUSAL that names the path - a fetch that
  did not happen, never a value;
* a point OUTSIDE every served region's tile set is still ABSENT (T-0142's semantics), silently and without
  reaching GDAL - that is geography, and it has no path to name.

Collapsing the two is the defect: one is fixed by fetching, the other cannot be.

The resolution happens at IMPORT time, the way `fetch.DEST` does, so a test that wants a different directory
either patches the module attribute (which is what every sampling test already does) or sets
`SCENIC_ETL_INPUTS` and reloads - `reload_with_inputs` below. Every expected path is typed out from
`tmp_path` segment by segment rather than read back from the module under test.
"""
from __future__ import annotations

import importlib
import types

import pytest

from etl import dem, extract, fetch, landcover, oracle

ENV = "SCENIC_ETL_INPUTS"


def fake_runner(stdout, returncode=0, stderr=""):
    def run(argv, stdin):
        run.calls.append((argv, stdin))
        return types.SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)
    run.calls = []
    return run


def fake_worktree(tmp_path):
    """`<root>/.worktrees/T-9999/services/etl` plus the `<root>/services/etl/inputs` the payloads are in.

    The shared directory is asked of the resolver with an EMPTY env, so this helper states the mapping the
    consumers are supposed to obey without depending on the box's own `SCENIC_ETL_INPUTS`.
    """
    wt = tmp_path / ".worktrees" / "T-9999" / "services" / "etl"
    wt.mkdir(parents=True)
    shared = fetch.resolve_inputs_dir(wt, env={})
    shared.mkdir(parents=True)
    assert shared == (tmp_path / "services" / "etl" / "inputs").resolve(), shared
    return wt, shared


@pytest.fixture
def reload_with_inputs(monkeypatch):
    """Re-import a consumer with `SCENIC_ETL_INPUTS` set, and put it back afterwards.

    `importlib.reload` re-executes the module in its own namespace and returns the SAME object, so no other
    test module is left holding a stale import - and the teardown reload restores the real directory.
    """
    touched = []

    def go(module, inputs):
        monkeypatch.setenv(ENV, str(inputs))
        touched.append(module)
        return importlib.reload(module)

    yield go
    monkeypatch.undo()
    for module in touched:
        importlib.reload(module)


class TestEveryConsumerResolvesRatherThanComputing:
    """Red from this worktree while the modules say `ROOT / "inputs"`: that path contains `.worktrees`."""

    @pytest.mark.parametrize("module", [dem, landcover, extract])
    def test_the_inputs_directory_is_never_inside_a_worktree(self, module):
        assert ".worktrees" not in module.INPUTS.parts, (module.__name__, module.INPUTS)

    def test_the_oracle_kmz_is_never_inside_a_worktree(self):
        assert ".worktrees" not in oracle.KMZ.parts, oracle.KMZ

    @pytest.mark.parametrize("module", [dem, landcover, extract])
    def test_the_inputs_directory_is_the_resolvers_answer(self, module):
        """Anchored on the resolver, not on a second copy of its rule: a module that reimplements the
        `.worktrees` walk passes the test above and drifts the first time the rule changes."""
        assert module.INPUTS == fetch.resolve_inputs_dir(module.ROOT), module.INPUTS

    def test_the_oracle_kmz_lives_in_the_resolved_directory(self):
        assert oracle.KMZ == fetch.resolve_inputs_dir(oracle.ROOT) / "vermont-curvature.kmz", oracle.KMZ

    def test_the_oracles_manifest_stays_in_this_checkout(self):
        """Only the PAYLOADS are shared (T-0177's R2). manifest.yaml is tracked, and a task that edits its
        own manifest must read THAT edit rather than the main checkout's copy - so `pinned_digest` still
        defaults to this checkout's file even from a worktree."""
        assert oracle.pinned_digest("vermont-curvature.kmz") == oracle.pinned_digest(
            "vermont-curvature.kmz", oracle.ROOT / "inputs" / "manifest.yaml")


class TestAPayloadOnlyInTheSharedDirectoryIsRead:
    def test_dem_samples_a_tile_that_is_not_under_its_own_root(self, tmp_path, reload_with_inputs):
        """The T-0168 case: the code runs from a worktree, the tile is in the main checkout only.

        The tile file is not a raster and nothing opens it - `runner` is injected, exactly as every other
        sampling test in this suite does it, so this needs no GDAL and no library that writes a GeoTIFF.
        What is under test is WHICH directory `tile_path` looked in.
        """
        _, shared = fake_worktree(tmp_path)
        (shared / "3dep-n38w123.tif").write_bytes(b"not really a tiff")
        m = reload_with_inputs(dem, shared)
        assert m.sample_tile("n38w123", [(37.5, -122.5)], runner=fake_runner("123\n")) == [123.0]

    def test_landcover_samples_a_raster_that_is_not_under_its_own_root(self, tmp_path, reload_with_inputs):
        _, shared = fake_worktree(tmp_path)
        (shared / "worldcover-n36w123.tif").write_bytes(b"not really a tiff")
        m = reload_with_inputs(landcover, shared)
        assert m.sample_codes([(37.5, -122.5)], runner=fake_runner("10\n")) == [10]

    def test_extract_defaults_its_source_to_the_shared_directory(self, tmp_path, reload_with_inputs, capsys):
        """extract already refuses by name; what moves is WHERE it looks. Its refusal naming the shared
        path is the observable, because a real run needs a 1.2 GB pbf and osmium."""
        _, shared = fake_worktree(tmp_path)
        m = reload_with_inputs(extract, shared)
        assert m.main(["--region", "sfbay"]) == 2
        assert str(shared / m.SOURCE_PBF) in capsys.readouterr().err


class TestAMissingPayloadIsARefusalThatNamesThePath:
    def test_dem_refuses_a_tile_that_is_not_on_disk(self, monkeypatch, tmp_path):
        """Red today: `[None] * len(points)`, which reads downstream as `no elevation here` and zeroes the
        terrain terms of the scenic score on real mountain roads."""
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        with pytest.raises(FileNotFoundError) as e:
            dem.sample_tile("n38w123", [(37.5, -122.5)], runner=fake_runner("100\n"))
        assert str(tmp_path / "3dep-n38w123.tif") in str(e.value), str(e.value)

    def test_dems_whole_sample_refuses_too(self, monkeypatch, tmp_path):
        """The refusal has to reach the entry point the pipeline calls, not only the per-tile helper."""
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        with pytest.raises(FileNotFoundError) as e:
            dem.sample([(37.5, -122.5)], runner=fake_runner("100\n"))
        assert "3dep-n38w123.tif" in str(e.value), str(e.value)

    def test_landcover_refuses_a_raster_that_is_not_on_disk(self, monkeypatch, tmp_path):
        """Red today: `continue`, leaving None in place - the same fraction an ocean tile would produce."""
        monkeypatch.setattr(landcover, "INPUTS", tmp_path)
        with pytest.raises(FileNotFoundError) as e:
            landcover.sample_codes([(37.5, -122.5)], runner=fake_runner("10\n"))
        assert str(tmp_path / "worldcover-n36w123.tif") in str(e.value), str(e.value)


class TestAbsenceThatIsGeographyStaysAbsence:
    """T-0142's semantics, asserted separately so the refusal above cannot be widened over them."""

    def test_a_point_no_region_serves_is_none_and_never_reaches_gdal(self, monkeypatch, tmp_path):
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        runner = fake_runner("")
        assert dem.sample([(0.0, 0.0), (10.0, 10.0)], runner=runner) == [None, None]
        assert runner.calls == [], "gdal was called for a point no tile covers"

    def test_a_nan_point_is_none_rather_than_a_refusal(self, monkeypatch, tmp_path):
        """NaN has no tile name, so there is no path to name and nothing to fetch."""
        monkeypatch.setattr(dem, "INPUTS", tmp_path)
        monkeypatch.setattr(landcover, "INPUTS", tmp_path)
        runner = fake_runner("")
        assert dem.sample([(float("nan"), -122.0)], runner=runner) == [None]
        assert landcover.sample_codes([(float("nan"), -122.0)], runner=runner) == [None]
        assert runner.calls == []
