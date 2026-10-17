"""The embedded styles in MapAdapter are the generated styles, and each appearance returns its own.

`services/tiles/make_styles.py` emits `styles/scenic-light.json` and `styles/scenic-dark.json`;
`apps/ios/Packages/ScenicApp/Sources/MapAdapter/ScenicLightStyle.swift` and `ScenicDarkStyle.swift` carry
those documents as raw string literals, because MapAdapter's target declares no `resources:` and declaring
them means editing a serial-only manifest (that file says so in its own words; T-0197 ruling R4 keeps the
shape until M4's download sheet). A copy drifts: regenerating the JSON without regenerating the Swift ships
a basemap this repository no longer describes, and nothing in either language notices.

TWO assertions, because byte-equality alone is blind to the arms trading places (rv1-pr112 RV-3): both
literals stay byte-equal to their file while `MapAppearance.styleJSON` hands `.light` the DARK document,
and every count, every identifier and every byte of both styles is unchanged. So the ARM is read too, off
the switch inside `styleJSON` with `//` stripped - never off a comment (CLAUDE.md).

Each assertion is also exercised RED here, in process, against a mutated copy of the source: one flipped
hex digit in the literal, and the two arms swapped.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "apps/ios/Packages/ScenicApp/Sources/MapAdapter"
# The EMBEDDED styles: no glyphs, no sprite, no symbol layer (T-0196 rv1 B1). The published labelled styles
# sit one level up and never reach the device until ScenicStyleDocument rewrites `basemap://`.
STYLES = ROOT / "services/tiles/styles/embedded"
OPEN_DELIMITER = '#"""\n'
CLOSE_DELIMITER = '\n"""#'
# Re-measured 2026-10-17 off styles/embedded/ (T-0196 rv1 B1: labels off-device, `kind` filters).
# A floor with a name: an extractor that returned "" or the
# closing brace would satisfy every equality below against a file that was also emptied.
SIZES = {"light": 4538, "dark": 4566}
# What the device style may contain: these top-level keys, these layer types, and as its only URL the
# placeholder the shipping `ScenicStyleDocument.materialize` rewrites. A whitelist, so a `glyphs`, a `sprite`,
# a symbol layer or any other URL MapLibre would request and nothing serves is refused whatever it is spelled.
DEVICE_KEYS = {"version", "name", "metadata", "sources", "layers"}
DEVICE_LAYER_TYPES = {"background", "fill", "line"}
URL = re.compile(r"[a-z][a-z0-9+.-]*://[^\"]*")
PLACEHOLDER_LINE = re.compile(r'public static let archivePlaceholder = "([^"]+)"$')
APPEARANCES = [("light", "ScenicLightStyle"), ("dark", "ScenicDarkStyle")]


def swift_source(type_name: str) -> str:
    return (ADAPTER / f"{type_name}.swift").read_text(encoding="utf-8")


def embedded_style(source: str) -> str:
    """The raw literal between its delimiters, exactly as the compiler sees it.

    The literal is a raw multi-line one - OPEN_DELIMITER ... CLOSE_DELIMITER above - with the closing
    delimiter at column zero, so nothing is escaped and no indentation is stripped: the bytes between the
    two delimiter lines are the document. A source without
    both delimiters raises rather than returning something comparable - an extractor that quietly yields ""
    turns this whole file green over a style it never read.
    """
    start = source.find(OPEN_DELIMITER)
    if start < 0:
        raise ValueError("no raw-literal opening delimiter in the source")
    start += len(OPEN_DELIMITER)
    end = source.find(CLOSE_DELIMITER, start)
    if end < 0:
        raise ValueError("no raw-literal closing delimiter in the source")
    return source[start:end + 1]


def style_arms(source: str) -> dict[str, str]:
    """`case .<x>:` -> the first line carrying code after it, inside `public var styleJSON: String`.

    Scoped to that property because `MapAppearance` switches over the same two cases three times; read with
    `//` stripped and a trailing CR removed, so a doc comment naming a style cannot be mistaken for an arm.
    """
    arms: dict[str, str] = {}
    pending: str | None = None
    started = False
    for raw in source.splitlines():
        code = re.sub(r"//.*$", "", raw.rstrip("\r")).strip()
        if not started:
            started = "public var styleJSON: String" in code
            continue
        if pending is not None:
            if not code:
                continue
            arms[pending] = code
            pending = None
        match = re.match(r"case \.(\w+):$", code)
        if match:
            pending = match.group(1)
        elif code == "}" and arms:
            break
    return arms


@pytest.mark.parametrize("appearance,type_name", APPEARANCES)
def test_the_embedded_literal_is_byte_equal_to_the_generated_style(appearance: str, type_name: str) -> None:
    embedded = embedded_style(swift_source(type_name)).encode("utf-8")
    generated = (STYLES / f"scenic-{appearance}.json").read_bytes()
    assert embedded == generated, f"{type_name}.swift has drifted from scenic-{appearance}.json"


@pytest.mark.parametrize("appearance,type_name", APPEARANCES)
def test_the_extracted_literal_is_the_measured_size(appearance: str, type_name: str) -> None:
    assert len(embedded_style(swift_source(type_name)).encode("utf-8")) == SIZES[appearance]


@pytest.mark.parametrize("appearance,type_name", APPEARANCES)
def test_one_flipped_hex_digit_is_caught(appearance: str, type_name: str) -> None:
    """RED: the same comparison over a copy with a single colour digit changed."""
    source = swift_source(type_name)
    colour = re.search(r'"#[0-9a-fA-F]{6}"', embedded_style(source))
    assert colour is not None, "no hex colour in the embedded style to flip"
    original = colour.group(0)
    flipped = original[:-2] + ("0" if original[-2] != "0" else "1") + '"'
    mutated = source.replace(original, flipped, 1)
    assert embedded_style(mutated).encode("utf-8") != (STYLES / f"scenic-{appearance}.json").read_bytes()


def test_each_appearance_returns_its_own_style() -> None:
    arms = style_arms(swift_source("MapAppearance"))
    assert arms == {"light": "return ScenicLightStyle.json", "dark": "return ScenicDarkStyle.json"}


def test_swapped_arms_are_caught() -> None:
    """RED: the arms trade places, both literals still byte-equal to their files, every count unchanged."""
    swapped = (swift_source("MapAppearance")
               .replace("return ScenicLightStyle.json", "return ScenicSwappedStyle.json")
               .replace("return ScenicDarkStyle.json", "return ScenicLightStyle.json")
               .replace("return ScenicSwappedStyle.json", "return ScenicDarkStyle.json"))
    assert style_arms(swapped) == {"light": "return ScenicDarkStyle.json",
                                   "dark": "return ScenicLightStyle.json"}
    assert style_arms(swapped) != {"light": "return ScenicLightStyle.json",
                                   "dark": "return ScenicDarkStyle.json"}


def test_an_arm_read_off_a_comment_is_not_an_arm() -> None:
    """A `//`-commented arm must not satisfy the reader: CLAUDE.md forbids anchoring on a comment."""
    commented = swift_source("MapAppearance").replace("return ScenicLightStyle.json",
                                                      "// return ScenicLightStyle.json")
    assert style_arms(commented).get("light") != "return ScenicLightStyle.json"


@pytest.mark.parametrize("source", ["", 'let json = "not a raw literal"'])
def test_a_source_without_the_delimiters_raises(source: str) -> None:
    with pytest.raises(ValueError):
        embedded_style(source)


def rewritten_placeholders() -> set[str]:
    """`ScenicStyleDocument.archivePlaceholder` read off its code line, `//` lines dropped - never a comment."""
    found = set()
    for raw in swift_source("ScenicStyleDocument").splitlines():
        code = raw.rstrip("\r").strip()
        match = None if code.startswith("//") else PLACEHOLDER_LINE.fullmatch(code)
        if match:
            found.add(match.group(1))
    return found


def device_style_problems(literal: str, rewritten: set[str]) -> list[str]:
    """[] when the style asks MapLibre for nothing but the archive the shipping materialize points it at."""
    doc = json.loads(literal)
    problems = []
    if set(doc) != DEVICE_KEYS:
        problems.append(f"top-level keys off the whitelist: {sorted(set(doc) ^ DEVICE_KEYS)}")
    types = {layer.get("type") for layer in doc["layers"]}
    if not types <= DEVICE_LAYER_TYPES:
        problems.append(f"layer types off the whitelist: {sorted(types - DEVICE_LAYER_TYPES)}")
    urls = set(URL.findall(literal))
    if urls != rewritten:
        problems.append(f"URLs nothing rewrites: {sorted(urls - rewritten)}; placeholders absent: "
                        f"{sorted(rewritten - urls)}")
    return problems


@pytest.mark.parametrize("appearance,type_name", APPEARANCES)
def test_the_device_style_requests_nothing_the_app_does_not_rewrite(appearance: str, type_name: str) -> None:
    """rv1 B1: a `basemap://` glyph URL on device fails its request and MapLibre never finishes the tile."""
    rewritten = rewritten_placeholders()
    assert rewritten == {"pmtiles://la.pmtiles"}
    assert device_style_problems(embedded_style(swift_source(type_name)), rewritten) == []


@pytest.mark.parametrize("appearance", ["light", "dark"])
def test_the_published_labelled_style_as_the_device_style_is_refused(appearance: str) -> None:
    """RED: the labelled style the round before shipped in the Swift literal, refused on every limb."""
    labelled = (STYLES.parent / f"scenic-{appearance}.json").read_text(encoding="utf-8")
    assert device_style_problems(labelled, rewritten_placeholders()) == [
        "top-level keys off the whitelist: ['glyphs', 'sprite']",
        "layer types off the whitelist: ['symbol']",
        "URLs nothing rewrites: ['basemap://glyphs/{fontstack}/{range}.pbf', "
        f"'basemap://sprites/v4/{appearance}']; placeholders absent: []",
    ]
