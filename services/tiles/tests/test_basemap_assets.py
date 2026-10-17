"""The glyphs and sprites the styles request are the ones built beside the archive, and nothing else.

Every refusal here goes through `basemap_assets.main` - the entry point `ops/publish-tiles` runs as
`basemap_assets.py check` and `publish-list` - against a work tree BUILT by `main build` from a fixture
tarball whose digest a fixture pin records. The font stacks and the URL base are typed here, never imported:
a whitelist read out of the module under test would only prove the module agrees with itself.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import re
import tarfile
from pathlib import Path

import pytest

import basemap_assets
from basemap_assets import RANGES, SPRITE_SUFFIXES, main, tree_digest

ROOT = Path(__file__).resolve().parents[3]
STYLES = ROOT / "services/tiles/styles"
# Measured T-0196 M4/R4, typed here: the stacks the label layers use and the base the URLs hang off.
FONTS = {"Noto Sans Regular", "Noto Sans Medium"}
BASE = "basemap://"
WORK_ENV = "SCENIC_TILES_WORK"


def committed(appearance: str) -> dict:
    return json.loads((STYLES / f"scenic-{appearance}.json").read_text(encoding="utf-8"))


def fixture_tarball(path: Path, fonts: set[str]) -> Path:
    """An archive shaped like basemaps-assets: <top>/fonts/<font>/<range>.pbf, fonts/OFL.txt, sprites/v4/*."""
    files = {f"fonts/{font}/{r}.pbf": f"{font}{r}".encode() for font in fonts for r in RANGES}
    files["fonts/OFL.txt"] = b"SIL Open Font License"
    for sheet in ("light", "dark", "white"):
        for suffix in SPRITE_SUFFIXES:
            body = json.dumps({"arrow": {"x": 0}}) if suffix.endswith("json") else sheet + suffix
            files[f"sprites/v4/{sheet}{suffix}"] = body.encode()
    with tarfile.open(path, "w:gz") as tar:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(f"basemaps-assets-abc/{name}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return path


def write_styles(directory: Path, docs: dict[str, dict]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for appearance, doc in docs.items():
        (directory / f"scenic-{appearance}.json").write_text(json.dumps(doc), encoding="utf-8")
    return directory


@pytest.fixture
def built(tmp_path: Path):
    """(work, pin, styles): the committed styles, a tree `main build` extracted for them, a pin recording it."""
    tarball = fixture_tarball(tmp_path / "assets.tar.gz", FONTS | {"Noto Sans Italic"})
    data = tarball.read_bytes()
    pin = tmp_path / "pin.json"
    record = {"url": "file:///nowhere", "commit": "abc", "sha256": hashlib.sha256(data).hexdigest(),
              "bytes": len(data), "tree_sha256": "unrecorded"}
    pin.write_text(json.dumps(record), encoding="utf-8")
    styles = write_styles(tmp_path / "styles", {a: committed(a) for a in ("light", "dark")})
    work = tmp_path / "work"
    assert main(["build", "--work", str(work), "--archive", str(tarball), "--pin", str(pin),
                 "--styles", str(styles)]) == 1, "an unrecorded tree must refuse"
    record["tree_sha256"] = tree_digest(work)[0]
    pin.write_text(json.dumps(record), encoding="utf-8")
    return work, pin, styles


def run_check(work: Path, pin: Path, styles: Path) -> int:
    return main(["check", "--work", str(work), "--pin", str(pin), "--styles", str(styles)])


def restyle(styles: Path, edit) -> Path:
    for appearance in ("light", "dark"):
        path = styles / f"scenic-{appearance}.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        edit(doc)
        path.write_text(json.dumps(doc), encoding="utf-8")
    return styles


def layer(doc: dict, layer_id: str) -> dict:
    return next(entry for entry in doc["layers"] if entry["id"] == layer_id)


def test_the_committed_styles_pass_against_the_tree_built_for_them(built) -> None:
    assert run_check(*built) == 0


def test_a_style_naming_a_font_with_no_glyphs_is_refused(built, capsys) -> None:
    work, pin, styles = built
    restyle(styles, lambda doc: layer(doc, "roads-label")["layout"].update({"text-font": ["Noto Sans Bold"]}))
    assert run_check(work, pin, styles) == 1
    assert "Noto Sans Bold" in capsys.readouterr().err


def test_a_glyph_directory_no_style_names_is_refused(built, capsys) -> None:
    work, pin, styles = built
    (work / "glyphs/Noto Sans Italic").mkdir()
    (work / "glyphs/Noto Sans Italic/0-255.pbf").write_bytes(b"x")
    assert run_check(work, pin, styles) == 1
    assert "Noto Sans Italic" in capsys.readouterr().err


def test_a_missing_range_is_refused(built) -> None:
    work, pin, styles = built
    (work / "glyphs/Noto Sans Medium/65280-65535.pbf").unlink()
    assert run_check(work, pin, styles) == 1


def test_a_changed_glyph_byte_is_refused_by_the_tree_digest(built) -> None:
    work, pin, styles = built
    (work / "glyphs/Noto Sans Regular/0-255.pbf").write_bytes(b"not the pinned glyphs")
    assert run_check(work, pin, styles) == 1


def test_an_icon_the_sheet_lacks_is_refused(built, capsys) -> None:
    work, pin, styles = built
    restyle(styles, lambda doc: layer(doc, "places-label")["layout"].update({"icon-image": "no-such-icon"}))
    assert run_check(work, pin, styles) == 1
    assert "no-such-icon" in capsys.readouterr().err


@pytest.mark.parametrize("key,value", [
    ("glyphs", "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf"),
    ("sprite", "https://protomaps.github.io/basemaps-assets/sprites/v4/light"),
    ("glyphs", BASE + "glyphs/{fontstack}.pbf"),
])
def test_a_url_off_the_served_layout_is_refused(built, key: str, value: str) -> None:
    work, pin, styles = built
    restyle(styles, lambda doc: doc.update({key: value}))
    assert run_check(work, pin, styles) == 1


def test_a_text_font_expression_fails_closed(built) -> None:
    work, pin, styles = built
    restyle(styles, lambda doc: layer(doc, "roads-label")["layout"].update(
        {"text-font": ["case", True, ["literal", ["Noto Sans Regular"]], ["literal", ["Noto Sans Medium"]]]}))
    assert run_check(work, pin, styles) == 1


def test_build_refuses_an_archive_off_the_pin(built, tmp_path: Path) -> None:
    work, pin, styles = built
    other = fixture_tarball(tmp_path / "other.tar.gz", {"Noto Sans Regular"})
    assert main(["build", "--work", str(work), "--archive", str(other), "--pin", str(pin),
                 "--styles", str(styles)]) == 1


def test_build_extracts_exactly_the_stacks_the_styles_name(built) -> None:
    work = built[0]
    assert {p.name for p in (work / "glyphs").iterdir() if p.is_dir()} == FONTS
    assert {p.name for p in (work / "sprites/v4").iterdir()} == {
        s + x for s in ("light", "dark") for x in SPRITE_SUFFIXES}


def test_the_committed_styles_name_the_measured_stacks_and_no_icon() -> None:
    for appearance in ("light", "dark"):
        doc = committed(appearance)
        assert basemap_assets.font_stacks(doc) == FONTS
        assert basemap_assets.icon_names(doc) == set()


def test_publish_list_is_every_url_the_styles_request(capsys) -> None:
    """Full equality against an expansion of the committed URL strings written out here, not the module's."""
    expected = {"glyphs/OFL.txt"}
    for appearance in ("light", "dark"):
        doc = committed(appearance)
        glyphs = doc["glyphs"]
        assert glyphs.startswith(BASE) and doc["sprite"].startswith(BASE)
        expected |= {glyphs[len(BASE):].replace("{fontstack}", f).replace("{range}", f"{s}-{s + 255}")
                     for f in FONTS for s in range(0, 65536, 256)}
        expected |= {doc["sprite"][len(BASE):] + x for x in (".json", ".png", "@2x.json", "@2x.png")}
    assert main(["publish-list", "--work", "unused"]) == 0
    listed = capsys.readouterr().out.splitlines()
    assert len(listed) == len(set(listed)) == len(expected) == 2 * 256 + 8 + 1
    assert set(listed) == expected


def test_the_pin_records_the_measured_archive() -> None:
    pin = json.loads((ROOT / "services/tiles/basemap_assets.json").read_text(encoding="utf-8"))
    assert pin["url"] == ("https://github.com/protomaps/basemaps-assets/archive/"
                          "028c18f713baecad011301ff7a69acc39bcc2ae7.tar.gz")
    assert (pin["sha256"], pin["bytes"]) == (
        "57e40e8c512bd8042d0a3a251f19d0d1c8523ad963c666c3c6643bada4dc92d0", 6379327)
    assert (pin["tree_files"], pin["tree_bytes"]) == (521, 9962457)


def test_the_real_build_passes_when_named() -> None:
    """$SCENIC_TILES_WORK names services/tiles/work in the main checkout; set, it must pass, never skip."""
    named = os.environ.get(WORK_ENV)
    if named:
        assert main(["check", "--work", named]) == 0


def test_publish_tiles_checks_the_assets_then_uploads_the_list() -> None:
    """Anchored on executed lines of ops/publish-tiles, `#` comments dropped."""
    code = [re.sub(r"(^|\s)#.*$", "", line).strip()
            for line in (ROOT / "ops/publish-tiles").read_text(encoding="utf-8").splitlines()]
    calls = [line for line in code if "basemap_assets.py" in line]
    assert any("basemap_assets.py check" in line for line in calls), calls
    assert any("basemap_assets.py publish-list" in line for line in calls), calls
    first_put = next(i for i, line in enumerate(code) if "curl" in line)
    check_at = next(i for i, line in enumerate(code) if "basemap_assets.py check" in line)
    assert check_at < first_put, "the asset check must run before anything is uploaded"


def test_a_copied_style_is_not_mutated_by_restyle() -> None:
    doc = committed("light")
    before = copy.deepcopy(doc)
    basemap_assets.required_files([doc], BASE)
    assert doc == before
