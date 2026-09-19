"""The fetched payloads live in ONE directory, shared by every worktree.

T-0169 fetched and verified the California extract into `.worktrees/T-0169/services/etl/inputs/`, because
`fetch.DEST` was `<this checkout>/services/etl/inputs`. The worktree was removed with `--force` the hour
PR #99 merged and the deliverable went with it; the payloads are gitignored, so nothing in git could give
them back. These tests pin the resolver that replaces that constant: `SCENIC_ETL_INPUTS` wins, a path under
`.worktrees/<name>/` maps to the main checkout's directory, a plain checkout maps to its own, and nothing on
the way is created or symlinked (this tree is developed on Windows, where a symlink needs a privilege an
ordinary agent does not have).

Every expected path is typed out from `tmp_path` segment by segment, never read back from the resolver.
"""
from pathlib import Path

from etl import fetch

ENV = "SCENIC_ETL_INPUTS"


def worktree_etl(root: Path) -> Path:
    """`<root>/.worktrees/T-9999/services/etl` - the shape `git worktree add .worktrees/T-9999` produces."""
    d = root / ".worktrees" / "T-9999" / "services" / "etl"
    d.mkdir(parents=True)
    return d


class TestResolveInputsDir:
    def test_a_worktree_resolves_to_the_main_checkouts_inputs(self, tmp_path, monkeypatch):
        monkeypatch.delenv(ENV, raising=False)
        got = fetch.resolve_inputs_dir(worktree_etl(tmp_path))
        assert got == (tmp_path / "services" / "etl" / "inputs").resolve(), got

    def test_a_plain_checkout_resolves_to_its_own_inputs(self, tmp_path, monkeypatch):
        monkeypatch.delenv(ENV, raising=False)
        etl = tmp_path / "services" / "etl"
        etl.mkdir(parents=True)
        got = fetch.resolve_inputs_dir(etl)
        assert got == (tmp_path / "services" / "etl" / "inputs").resolve(), got

    def test_the_env_var_overrides_the_worktree_mapping(self, tmp_path, monkeypatch):
        shared = tmp_path / "elsewhere" / "osm-inputs"
        monkeypatch.setenv(ENV, str(shared))
        got = fetch.resolve_inputs_dir(worktree_etl(tmp_path))
        assert got == shared, got

    def test_a_blank_env_var_is_not_an_override(self, tmp_path, monkeypatch):
        """An exported-but-empty variable is how a shell says nothing, not 'fetch into the current directory'."""
        monkeypatch.setenv(ENV, "   ")
        got = fetch.resolve_inputs_dir(worktree_etl(tmp_path))
        assert got == (tmp_path / "services" / "etl" / "inputs").resolve(), got

    def test_it_creates_nothing_and_links_nothing(self, tmp_path, monkeypatch):
        """Not a symlink farm, and not a mkdir either: resolving a path must not put anything on disk."""
        monkeypatch.delenv(ENV, raising=False)
        got = fetch.resolve_inputs_dir(worktree_etl(tmp_path))
        assert not got.exists(), got
        assert not (tmp_path / "services").exists()


class TestTheModuleUsesTheResolver:
    def test_dest_is_never_inside_a_worktree(self):
        """Red from any `.worktrees/<id>/` checkout while DEST is `ROOT / "inputs"`; this is the T-0169 loss."""
        assert ".worktrees" not in fetch.DEST.parts, fetch.DEST

    def test_the_manifest_stays_in_this_checkout(self):
        """Only the payloads are shared. `manifest.yaml` is TRACKED (.gitignore keeps it out of the payload
        ignore), so a task that edits its own manifest must fetch against THAT edit, not the main checkout's."""
        assert fetch.MANIFEST == fetch.ROOT / "inputs" / "manifest.yaml", fetch.MANIFEST

    def test_verify_only_names_the_directory_it_verified_against(self, tmp_path, monkeypatch, capsys):
        """`--verify-only` is the acceptance every consuming task quotes, so it must say WHERE it looked."""
        monkeypatch.setattr(fetch, "DEST", tmp_path)
        m = tmp_path / "manifest.yaml"
        m.write_text("- name: file.bin\n  url: https://example.invalid/file.bin\n  verify: sha256\n"
                     f"  sha256: {'0' * 64}\n  license: CC0-1.0\n  purpose: test\n", encoding="utf-8")
        assert fetch.main(["--manifest", str(m), "--verify-only"]) == 1
        assert f"inputs directory: {tmp_path}" in capsys.readouterr().out
