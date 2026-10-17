"""Every colour in the committed styles is a DesignTokens value, and nothing claims the attribution corner.

The token set is per appearance: a dark-mode value in the light style is as wrong as a colour from nowhere,
because the two tables are the two halves of one design and a value from the wrong half is exactly the bug
a human eye does not catch in a diff of hex triples.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_pmtiles import read_metadata  # noqa: E402
from make_styles import SOURCE_LAYERS, TOKENS, dumps, fields_named, style  # noqa: E402
from make_styles import main as make_styles_main  # noqa: E402
from test_pmtiles_budget import LA_BBOX, good_metadata, write_pmtiles  # noqa: E402

STYLES_DIR = Path(__file__).resolve().parents[1] / "styles"
APPEARANCES = ("light", "dark")
ARCHIVE_ENV = "SCENIC_LA_PMTILES"
# The vector layers the BUILT archive carries, read off `pmtiles show --metadata` on the LA extract and
# typed HERE rather than imported from make_styles. That is the whole point of rv1-pr109 B2: asserting
# `source-layer in make_styles.SOURCE_LAYERS` proves only that the module agrees with itself, so adding
# "waters" to the tuple and pointing the water fill at it left every test green while
# `make_styles.py --check --archive` refused. The anchor has to live outside the module under test.
ARCHIVE_VECTOR_LAYERS = ("boundaries", "buildings", "earth", "landcover", "landuse", "places", "pois",
                         "roads", "water")
# Anything that looks like a colour literal anywhere in the file, not only where we expect one: a colour
# hidden inside an expression is still a colour on screen.
COLOUR_LITERAL = re.compile(r"^(#[0-9A-Fa-f]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\))$")


def tokens_for(appearance: str) -> set[str]:
    return {value[appearance] for value in TOKENS.values()}


def colours_in(node, out: list[str] | None = None) -> list[str]:
    """Every colour literal in the document: -color properties plus any literal hiding in an expression."""
    out = [] if out is None else out
    if isinstance(node, dict):
        for key, value in node.items():
            if key.endswith("-color") and isinstance(value, str):
                out.append(value)
            else:
                colours_in(value, out)
    elif isinstance(node, list):
        for value in node:
            colours_in(value, out)
    elif isinstance(node, str) and COLOUR_LITERAL.match(node):
        out.append(node)
    return out


def load(appearance: str) -> dict:
    return json.loads((STYLES_DIR / f"scenic-{appearance}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("appearance", APPEARANCES)
def test_every_colour_is_a_token_of_that_appearance(appearance: str) -> None:
    allowed = tokens_for(appearance)
    found = colours_in(load(appearance))
    assert found, "a style with no colours in it would pass this test vacuously"
    off = sorted({c for c in found if c not in allowed})
    assert off == [], f"{appearance}: colours that are not {appearance} tokens: {off}"


@pytest.mark.parametrize("appearance", APPEARANCES)
def test_one_off_token_colour_is_caught(appearance: str) -> None:
    """The red run, in-process: MapLibre's own default blue is not one of our tokens."""
    document = load(appearance)
    document["layers"][0]["paint"]["background-color"] = "#4264fb"
    off = sorted({c for c in colours_in(document) if c not in tokens_for(appearance)})
    assert off == ["#4264fb"]


def test_the_two_appearances_do_not_share_a_palette() -> None:
    """A style that passed both token sets would mean the appearances are not actually different."""
    assert tokens_for("light") != tokens_for("dark")
    light, dark = colours_in(load("light")), colours_in(load("dark"))
    assert set(light) - tokens_for("dark"), "the light style is entirely made of dark tokens"


@pytest.mark.parametrize("appearance", APPEARANCES)
def test_nothing_claims_the_lower_right_corner(appearance: str) -> None:
    """AttributionFooter owns that corner; the style contributes nothing to it.

    A style cannot reserve screen space. What it can do is declare no source attribution (so the
    renderer's own control draws nothing). The footer is SwiftUI drawn ABOVE the map on its own 85% ground,
    so a label underneath cannot cover it (T-0196 R6); the symbol layers are exactly the two label layers,
    so a new one - POI icons, shields - is a deliberate edit of this list.
    """
    document = load(appearance)
    for name, source in document["sources"].items():
        assert "attribution" not in source, f"{name} declares attribution; the footer already credits it"
    symbols = [layer["id"] for layer in document["layers"] if layer["type"] == "symbol"]
    assert symbols == ["roads-label", "places-label"]
    assert document["metadata"]["scenic:attribution_owner"] == "DesignSystem.AttributionFooter"


def archive_layer_subjects(tmp_path: Path) -> list[tuple[str, set[str]]]:
    """The layer names an ARCHIVE declares, per subject.

    The fixture is the primary subject and always runs, so this test never depends on a 63 MB file being on
    the box. The real build is a second subject named by $SCENIC_LA_PMTILES; when that variable is set the
    file MUST be there - this asserts rather than skipping, because a green that is really an absence is the
    defect this whole task keeps finding.
    """
    meta = good_metadata(vector_layers=[{"id": name} for name in ARCHIVE_VECTOR_LAYERS])
    fixture = write_pmtiles(tmp_path / "layers.pmtiles", LA_BBOX, meta)
    subjects = [("fixture", {layer["id"] for layer in read_metadata(fixture)["vector_layers"]})]
    named = os.environ.get(ARCHIVE_ENV)
    if named:
        real = Path(named)
        assert real.is_file(), f"{ARCHIVE_ENV}={named} names no file"
        subjects.append((real.name, {layer["id"] for layer in read_metadata(real)["vector_layers"]}))
    return subjects


@pytest.mark.parametrize("appearance", APPEARANCES)
def test_every_source_layer_exists_in_the_archive(appearance: str, tmp_path: Path) -> None:
    """Every source-layer a committed style names is declared by the archive that has to draw it."""
    for subject, have in archive_layer_subjects(tmp_path):
        named = [layer["source-layer"] for layer in load(appearance)["layers"] if "source-layer" in layer]
        assert named, "a style naming no source-layer would pass this vacuously"
        missing = sorted({name for name in named if name not in have})
        assert missing == [], f"{subject}: {appearance} names source-layer(s) the archive has not got: {missing}"


def test_the_generators_source_layer_table_is_the_archives(tmp_path: Path) -> None:
    """`SOURCE_LAYERS` is a transcription of the archive's vector_layers, so it is checked against them."""
    for subject, have in archive_layer_subjects(tmp_path):
        assert sorted(set(SOURCE_LAYERS) - have) == [], f"{subject}: not in the archive"


def test_the_build_recipe_checks_the_styles_against_the_archive() -> None:
    """`make_styles.py --check --archive` is the only executable anchor between the typed table and a real
    archive, and until rv1-pr109 B2 nothing ran it - not this recipe, not ops/publish-tiles, not the suite.
    Anchored on the invocation, which is executed, never on a comment, which gets stripped."""
    recipe = (Path(__file__).resolve().parents[1] / "build-la.sh").read_text(encoding="utf-8")
    assert "make_styles.py" in recipe, "the recipe never runs the style generator"
    assert "--check --archive" in recipe, "the recipe never checks the styles against the archive it built"


@pytest.mark.parametrize("appearance", APPEARANCES)
def test_the_committed_file_is_what_the_generator_emits(appearance: str) -> None:
    """Otherwise the styles are hand-edited and the generator is decoration."""
    on_disk = (STYLES_DIR / f"scenic-{appearance}.json").read_text(encoding="utf-8")
    assert on_disk == dumps(style(appearance, "la.pmtiles")) + "\n"


@pytest.mark.parametrize("appearance", APPEARANCES)
def test_the_route_line_is_six_over_a_two_point_casing(appearance: str) -> None:
    """DesignTokens describes the route as a 6 pt line over a 2 pt casing; the style is where that lives."""
    layers = {layer["id"]: layer for layer in load(appearance)["layers"]}
    assert layers["route-line"]["paint"]["line-width"] == 6
    assert layers["route-casing"]["paint"]["line-width"] == 10
    assert layers["route-line"]["paint"]["line-color"] == TOKENS["route"][appearance]
    assert layers["route-scenic"]["paint"]["line-color"] == TOKENS["scenic"][appearance]
    # Bottom to top: casing, line, then the scenic episodes on top of the line they highlight.
    order = [layer["id"] for layer in load(appearance)["layers"]]
    assert order.index("route-casing") < order.index("route-line") < order.index("route-scenic")


@pytest.mark.parametrize("appearance", APPEARANCES)
def test_glyphs_and_sprite_are_served_beside_the_archive(appearance: str) -> None:
    """One base, the archive's own prefix; never a third-party CDN (basemap_assets.py checks the files)."""
    document = load(appearance)
    assert document["glyphs"] == "basemap://glyphs/{fontstack}/{range}.pbf"
    assert document["sprite"] == f"basemap://sprites/v4/{appearance}"


# The fields the LA archive declares per source-layer (T-0196 M2, `name:xx` omitted), typed HERE for the same
# reason as ARCHIVE_VECTOR_LAYERS. There is no `pmap:kind`: that was the v3 spelling.
ARCHIVE_FIELDS = {
    "earth": {"kind", "min_zoom", "name"}, "landcover": {"kind"}, "landuse": {"kind", "sort_rank"},
    "water": {"kind", "kind_detail", "min_zoom", "name"}, "buildings": {"kind", "height"},
    "roads": {"kind", "kind_detail", "min_zoom", "name", "ref"}, "places": {"kind", "min_zoom", "name"},
    "boundaries": {"kind"}, "pois": {"kind", "name"},
}


def fields_fixture(tmp_path: Path, fields: dict[str, set[str]]) -> Path:
    layers = [{"id": name, "fields": {f: "String" for f in sorted(fields.get(name, set()))}}
              for name in ARCHIVE_VECTOR_LAYERS]
    return write_pmtiles(tmp_path / "fields.pmtiles", LA_BBOX, good_metadata(vector_layers=layers))


def test_every_field_a_layer_reads_is_in_the_archive(tmp_path: Path) -> None:
    """Through `make_styles --check`, the entry point build-la.sh runs."""
    assert make_styles_main(["--check", "--archive", str(fields_fixture(tmp_path, ARCHIVE_FIELDS))]) == 0


def test_a_filter_on_the_v3_field_name_is_refused(tmp_path: Path) -> None:
    """RED: an archive whose roads carry `pmap:kind` and no `kind` - the field today's filters read is absent."""
    v3 = {**ARCHIVE_FIELDS, "roads": {"pmap:kind", "name"}}
    assert make_styles_main(["--check", "--archive", str(fields_fixture(tmp_path, v3))]) == 1


@pytest.mark.parametrize("appearance", APPEARANCES)
def test_the_committed_layers_read_only_archive_fields(appearance: str) -> None:
    named = {layer["id"]: fields_named(layer) for layer in load(appearance)["layers"]
             if layer.get("source") == "protomaps"}
    assert any(named.values()), "no layer reads a field; this would pass vacuously"
    for layer_id, fields in named.items():
        source_layer = next(x["source-layer"] for x in load(appearance)["layers"] if x["id"] == layer_id)
        assert fields <= ARCHIVE_FIELDS[source_layer], f"{layer_id} reads {sorted(fields)}"
