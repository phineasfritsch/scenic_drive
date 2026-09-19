"""`make_styles.TOKENS` is a TRANSCRIPTION of DesignTokens.swift, and a transcription anchored to nothing
is a copy that drifts.

Every other test in this directory reads the styles against `TOKENS`, so changing a hex digit in `TOKENS`
and regenerating moves the whole suite with it: the styles stay "correct" against a table that no longer
says what DesignSystem says, and the map ships a colour the app does not have. This file is the anchor -
it parses the Swift DECLARATIONS and asserts the transcription equals them, per appearance.

Anchored on the declarations, never on the doc-comment table at the top of DesignTokens.swift: CLAUDE.md
forbids anchoring a test on a comment, and that table is exactly the comment a rename would leave behind.
`test_the_table_is_read_from_the_declarations_not_the_doc_comment` is the guard on that.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from make_styles import TOKENS  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
DESIGN_TOKENS = ROOT / "apps/ios/Packages/ScenicApp/Sources/DesignSystem/DesignTokens.swift"

# A whole-line comment, doc or otherwise. Stripped before anything is parsed.
COMMENT_LINE = re.compile(r"^[ \t]*//.*$", re.M)
# `public static let bg = dynamic(light: 0xFFF7ED, dark: 0x0F172A)` - the ten hex-pair tokens.
DYNAMIC = re.compile(
    r"static\s+let\s+(\w+)\s*=\s*dynamic\(\s*light:\s*0x([0-9A-Fa-f]{6})\s*,\s*dark:\s*0x([0-9A-Fa-f]{6})\s*\)"
)
# `border` is the one token whose dark value is not a hex triple. Its appearance mapping is read off the
# ternary's own condition rather than assumed from the order the two branches happen to be written in.
BORDER = re.compile(
    r"static\s+let\s+border\s*=.*?userInterfaceStyle\s*==\s*\.dark\s*\n?\s*\?\s*"
    r"UIColor\(\s*white:\s*([0-9.]+)\s*,\s*alpha:\s*([0-9.]+)\s*\)\s*\n?\s*"
    r":\s*DesignTokens\.srgb\(0x([0-9A-Fa-f]{6})\)",
    re.S,
)


def swift_source() -> str:
    assert DESIGN_TOKENS.is_file(), f"{DESIGN_TOKENS} is where the tokens live; it moved"
    return DESIGN_TOKENS.read_text(encoding="utf-8")


def declared_tokens(source: str) -> dict[str, dict[str, str]]:
    """The token table as DesignTokens.swift DECLARES it: {name: {"light": literal, "dark": literal}}."""
    code = COMMENT_LINE.sub("", source)
    table = {name: {"light": f"#{light.upper()}", "dark": f"#{dark.upper()}"}
             for name, light, dark in DYNAMIC.findall(code)}
    match = BORDER.search(code)
    assert match, "border is no longer declared as a dark-first ternary; re-read the declaration"
    white, alpha, light_hex = match.groups()
    channel = round(float(white) * 255)
    table["border"] = {"light": f"#{light_hex.upper()}",
                       "dark": f"rgba({channel},{channel},{channel},{alpha})"}
    return table


def test_the_transcription_equals_the_declarations() -> None:
    """The mutant this file exists for: one hex digit changed in TOKENS, styles regenerated, suite green."""
    assert declared_tokens(swift_source()) == TOKENS


@pytest.mark.parametrize("appearance", ("light", "dark"))
def test_no_token_is_invented_or_missing(appearance: str) -> None:
    declared = declared_tokens(swift_source())
    assert sorted(declared) == sorted(TOKENS), "the two tables name different tokens"
    for name in declared:
        assert TOKENS[name][appearance] == declared[name][appearance], name


def test_the_table_is_read_from_the_declarations_not_the_doc_comment() -> None:
    """CLAUDE.md: never anchor a test on a comment. DesignTokens.swift carries the same table as a doc
    comment, so this proves the parse survives with every comment line deleted - and that the comment
    really was there to be mis-read."""
    source = swift_source()
    assert "#FFF7ED" in source, "the doc-comment table is gone; this guard has nothing to prove"
    assert "#FFF7ED" not in COMMENT_LINE.sub("", source), "hex triples are in code, not only in comments"
    assert declared_tokens(COMMENT_LINE.sub("", source)) == declared_tokens(source)


def test_border_dark_keeps_its_alpha() -> None:
    """Flattening the translucent hairline to an opaque hex would look right on bg and wrong everywhere."""
    assert declared_tokens(swift_source())["border"]["dark"] == "rgba(255,255,255,0.08)"
    assert TOKENS["border"]["dark"] == "rgba(255,255,255,0.08)"


def test_eleven_tokens_are_found_at_all() -> None:
    """A parser that silently matched nothing would make every assertion above vacuously true."""
    assert len(declared_tokens(swift_source())) == 11
