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

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "apps/ios/Packages/ScenicApp/Sources/MapAdapter"
STYLES = ROOT / "services/tiles/styles"
OPEN_DELIMITER = '#"""\n'
CLOSE_DELIMITER = '\n"""#'
# Measured 2026-09-19 off the generated files. A floor with a name: an extractor that returned "" or the
# closing brace would satisfy every equality below against a file that was also emptied.
SIZES = {"light": 4563, "dark": 4591}
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
