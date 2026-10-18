"""P-SAFE-07's declaration whitelist (T-0398 R2, rv1's B1): every DECLARATION under apps/ios of a name the frozen
badge blocks reference is an approved whole line, and a declaration that opens a body is approved with that body.

rv1 appended a file-scoped `private enum DesignTokens { ... fgMuted = SwiftUI.Color.clear ... }` to SurpriseCard.swift:
the nine badge blocks stayed byte-equal and the tag drew invisible. The class is "the badge block is frozen, the names
it uses are not", so the names are frozen too, as a whitelist, never as spellings of a bad write:

  NAMES   every identifier in the nine approved badge bodies (string literals dropped, their \\( ) interpolations kept),
          minus Swift keywords; then, to a fixed point, every identifier in the frozen declarations below.
  DECLS   a line declares a name when the name follows a type keyword (enum struct class actor protocol typealias
          extension func associatedtype macro operator precedencegroup - every component of a dotted path), or sits
          on a line holding let / var / case where it is not reached through `.` and is followed by = : , ) or the
          line's end, or follows the binding keyword. A declaration line of a watched name is approved as a whole
          line at its file in scan order; when it opens more { than it closes and is not a type declaration (enum
          struct class actor protocol), its block to the matching close is approved line by line too - so a value,
          a getter, a func body or an extension's members (an init, a subscript) cannot change unseen.
  BARE    a line whose last token is a declaration keyword (the name on the next line) is refused outright.

Lines are kept exactly as the guard's kept(): trimmed, a CR stripped, a line dropped only when it STARTS with //.
"""
from __future__ import annotations

import re

TYPE_KW = ("enum", "struct", "class", "actor", "protocol", "typealias", "extension", "func", "associatedtype",
           "macro", "operator", "precedencegroup")
OPAQUE_KW = ("enum", "struct", "class", "actor", "protocol")
BINDING_KW = ("let", "var", "case")
KEYWORDS = set(TYPE_KW + BINDING_KW) | {
    "if", "else", "in", "some", "any", "self", "Self", "static", "private", "fileprivate", "public", "internal",
    "return", "guard", "for", "while", "switch", "default", "true", "false", "nil", "init", "subscript", "where",
    "is", "as", "try", "await", "throws", "async", "inout", "mutating", "final", "override", "lazy", "weak",
    "_", "do", "catch", "throw", "defer", "break", "continue", "repeat", "super", "open", "nonisolated"}
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
INTERP = re.compile(r"\\\(([^()]*(?:\([^()]*\)[^()]*)*)\)")
TYPE_DECL = re.compile(r"(?<![A-Za-z0-9_.])(" + "|".join(TYPE_KW) + r")\s+`?([A-Za-z_][A-Za-z0-9_.`]*)")
BINDING = re.compile(r"(?<![A-Za-z0-9_.])(" + "|".join(BINDING_KW) + r")(?![A-Za-z0-9_])")
PRIVATE = re.compile(r"(?<![A-Za-z0-9_])(private|fileprivate)(?![A-Za-z0-9_])")
BARE = re.compile(r"(?<![A-Za-z0-9_.])(" + "|".join(TYPE_KW + BINDING_KW) + r")\s*$")


def code(line: str) -> str:
    """The line with every string literal replaced by its interpolations (a name inside \\( ) is code), and every
    backtick dropped: `name` declares name (rv2's R2-B1, a `DesignTokens` let, read as no name before T-0398 R3)."""
    return STRING.sub(lambda m: " " + " ".join(INTERP.findall(m.group(0))) + " ", line).replace("`", "")


def names(lines: list[str]) -> set[str]:
    found = set()
    for line in lines:
        found.update(IDENT.findall(code(line)))
    return found - KEYWORDS


def declared(line: str) -> tuple[set[str], bool]:
    """The names this line declares, and whether a block it opens stays opaque (a type declaration)."""
    text, out, opaque = code(line), set(), False
    for kw, path in TYPE_DECL.findall(text):
        out.update(part for part in path.replace("`", "").split(".") if part)
        opaque = opaque or kw in OPAQUE_KW
    if BINDING.search(text):
        for m in IDENT.finditer(text):
            before, after = text[:m.start()].rstrip(), text[m.end():].lstrip()
            if before.endswith("."):
                continue
            if (after == "" or after[0] in ":,)" or (after[0] == "=" and not after.startswith("=="))
                    or before.endswith(BINDING_KW)):
                out.add(m.group(0))
    return out - KEYWORDS, opaque


def frozen(lines: list[str], at: int) -> list[str]:
    depth, end = lines[at].count("{") - lines[at].count("}"), at
    while depth > 0 and end + 1 < len(lines):
        end += 1
        depth += lines[end].count("{") - lines[end].count("}")
    return lines[at:end + 1]


def bare(files: list[tuple[str, list[str]]]) -> list[str]:
    return [f"{rel}: {line}" for rel, lines in files for line in lines if BARE.search(code(line))]


def declarations(files: list[tuple[str, list[str]]], seed: set[str]) -> list[tuple[str, tuple]]:
    """Fixed point: every (file, frozen lines) declaration of a watched name, in scan order. A frozen block's names
    join its OWN file's watched set when that file declares them `private` / `fileprivate` (a helper only that file
    can reach, e.g. DesignTokens' dynamic(light:dark:)); following every name app-wide freezes the whole app
    (measured 2026-10-17: 1104 declarations, 4376 lines; private names app-wide, 356 and 963)."""
    hidden = {rel: set().union(*[declared(line)[0] for line in lines if PRIVATE.search(line)])
              for rel, lines in files}
    local = {rel: set() for rel, _ in files}
    while True:
        found, grown = [], False
        for rel, lines in files:
            watched = seed | local[rel]
            for i, line in enumerate(lines):
                got, opaque = declared(line)
                if got & watched:
                    found.append((rel, tuple([line] if opaque else frozen(lines, i))))
            more = names([line for r, block in found if r == rel for line in block]) & hidden[rel]
            if not more <= local[rel]:
                local[rel] |= more
                grown = True
        if not grown:
            return found
