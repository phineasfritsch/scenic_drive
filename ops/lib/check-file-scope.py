#!/usr/bin/env python3
"""T-0406 (P-SAFE-03, P-SAFE-07, P-SAFE-09, P-ATTR-01): no declaration can be added where it would shadow a name a
frozen safety block uses. Every file-scope and member-level line of the feature modules is at an APPROVED site.

    python ops/lib/check-file-scope.py                       # the tracked tree
    python ops/lib/check-file-scope.py --sources DIR         # a copy of apps/ios/Packages/ScenicApp/Sources
    python ops/lib/check-file-scope.py --print [MODULE/FILE] # the ready-to-paste approved block(s) of the tree

THE CLASS. Five review rounds on 2026-10-17 each closed one spelling of the same hole: a declaration added outside
every frozen block (`private enum DesignTokens`, a backticked `let`, a `fileprivate enum` above `import SwiftUI`,
`extension Text { func fixedSize }`) changes what a byte-equal frozen line resolves to. The digest pins went red,
and re-approving a digest is routine. This check is a WHITELIST by position, not a scan for names: each .swift file
is lexed (`//`, nested `/* */`, "...", multi-line and raw strings with interpolation, backtick identifiers), brace
depth is tracked, and every line with a code character at depth 0 or 1 - imports, file-scope declarations of any
kind and spelling, extensions, attributes, and the MEMBER declarations of every type and extension (a member
`static let DesignTokens` shadows the module type inside that type's frozen blocks) - must equal, in order and in
number, the approved lines for that file in ops/lib/check-file-scope-approved.txt. A `}` counts at the depth it
returns to, a `{` at the depth it opens from. Depth >= 2 (member bodies) is free: a local shadows only its own body,
and the frozen bodies are check-safety-disclaimer-frozen/-preview's whitelists. The FILE SET of the four modules is
whitelisted too: a new file (any extension) is refused until its `@file` block is approved.

FAIL CLOSED, each a refusal by reason: an unterminated block comment, string, interpolation or backtick; a newline
inside a single-line string; a `#` not followed by `#`, `"` or an identifier (`#/regex/#`); a `/` that is not `//`,
`/*`, `/=` or followed by whitespace (Swift 6 mode enables bare `/regex/` literals, whose `{` would skew the depth);
a lone CR; bytes that are not UTF-8; a depth that goes negative or ends != 0; a missing or malformed approved list.

WHAT IT CANNOT SEE (residual limits, also named in the pin rows): a declaration in a module outside the four
(MapAdapter, Handoff, ScenicKit, PlaceStore) - those are covered only by the digest pins and, for the Linux targets,
their SwiftUI import ban; a frozen block inside a type nested at depth >= 1 (none today); text inside an `#if` that
was already approved; whether the tree compiles or what an approved member computes.

To approve an edit, paste the block the refusal prints over that file's block, in the same commit, deliberately.
Exit 0 every line approved; 1 a refusal; 2 the check could not run.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCES = "apps/ios/Packages/ScenicApp/Sources"
MODULES = ("DesignSystem", "FeaturePlanSheet", "FeatureScenicHome", "FeatureSurpriseMe")
APPROVED = "ops/lib/check-file-scope-approved.txt"
CHECKED_DEPTH = 1
MIN_FILES = 59
IDENT_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")


class LexError(Exception):
    pass


def _block_comment(text: str, i: int, line: int) -> tuple[int, int]:
    level, i = 1, i + 2
    while i < len(text):
        if text.startswith("/*", i):
            level, i = level + 1, i + 2
        elif text.startswith("*/", i):
            level, i = level - 1, i + 2
            if level == 0:
                return i, line
        else:
            line += text[i] == "\n"
            i += 1
    raise LexError("an unterminated /* comment")


def checked_lines(raw: bytes) -> list[tuple[int, int]]:
    """(0-based line, min code depth) for every line with a code character at depth <= CHECKED_DEPTH."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise LexError(f"bytes that are not UTF-8 ({e.reason} at byte {e.start})")
    if "\r" in text.replace("\r\n", ""):
        raise LexError("a lone CR (Swift ends a // comment at it)")
    text = text.replace("\r\n", "\n")
    n, i, line, depth = len(text), 0, 0, 0
    mins: dict[int, int] = {}
    stack: list[list] = []  # ["str", hashes, multiline] | ["interp", open parens]

    def code(d: int) -> None:
        mins[line] = min(mins.get(line, d), d)

    while i < n:
        c = text[i]
        top = stack[-1] if stack else None
        if top is not None and top[0] == "str":
            hashes, multi = top[1], top[2]
            if c == "\n":
                if not multi:
                    raise LexError(f"a newline inside a single-line string (line {line + 1})")
                line, i = line + 1, i + 1
                continue
            if c == "\\" and text.startswith("#" * hashes, i + 1):
                j = i + 1 + hashes
                if j < n and text[j] == "(":
                    stack.append(["interp", 0])
                    code(depth)
                    i = j + 1
                    continue
                if j < n and text[j] == "\n":
                    line += 1
                i = j + 1
                continue
            close = ('"""' if multi else '"') + "#" * hashes
            if text.startswith(close, i):
                stack.pop()
                code(depth)
                i += len(close)
                continue
            i += 1
            continue
        if c == "\n":
            line, i = line + 1, i + 1
        elif c in " \t":
            i += 1
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
        elif text.startswith("/*", i):
            i, line = _block_comment(text, i, line)
        elif c == "/":
            if i + 1 < n and text[i + 1] not in " \t\n=":
                raise LexError(f"a '/' that may open a bare /regex/ literal (line {line + 1})")
            code(depth)
            i += 1
        elif c == "#":
            k = i
            while k < n and text[k] == "#":
                k += 1
            if k < n and text[k] == '"':
                multi = text.startswith('"""', k)
                stack.append(["str", k - i, multi])
                code(depth)
                i = k + (3 if multi else 1)
            elif k == i + 1 and k < n and text[k] in IDENT_START:
                code(depth)
                i += 1
            else:
                raise LexError(f"an unknown raw-string delimiter or '#' form (line {line + 1})")
        elif c == '"':
            multi = text.startswith('"""', i)
            stack.append(["str", 0, multi])
            code(depth)
            i += 3 if multi else 1
        elif c == "`":
            end = text.find("`", i + 1)
            if end < 0 or "\n" in text[i + 1:end]:
                raise LexError(f"an unterminated backtick identifier (line {line + 1})")
            code(depth)
            i = end + 1
        elif c == "{":
            code(depth)
            depth, i = depth + 1, i + 1
        elif c == "}":
            depth -= 1
            if depth < 0:
                raise LexError(f"a '}}' below depth 0 (line {line + 1})")
            code(depth)
            i += 1
        else:
            if top is not None and c == "(":
                top[1] += 1
            elif top is not None and c == ")":
                if top[1] == 0:
                    stack.pop()
                else:
                    top[1] -= 1
            code(depth)
            i += 1
    if stack:
        raise LexError(f"an unterminated {'string' if stack[-1][0] == 'str' else 'interpolation'} at end of file")
    if depth != 0:
        raise LexError(f"a brace depth of {depth} at end of file")
    return sorted((ln, d) for ln, d in mins.items() if d <= CHECKED_DEPTH)


def file_entries(path: pathlib.Path) -> list[tuple[int, str]]:
    """(1-based line, approved-list entry) for every checked line of one file; non-Swift files have none."""
    if path.suffix != ".swift":
        return []
    raw = path.read_bytes()
    lines = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").split("\n")
    return [(ln + 1, f"{d}|{lines[ln]}") for ln, d in checked_lines(raw)]


def tree_files(sources: pathlib.Path) -> list[str]:
    out = []
    for module in MODULES:
        base = sources / module
        if not base.is_dir():
            raise SystemExit(f"FILE-SCOPE cannot run  {base}: module directory missing")
        out += [p.relative_to(sources).as_posix() for p in base.rglob("*") if p.is_file() or p.is_symlink()]
    return sorted(out)


def load_approved(path: pathlib.Path) -> dict[str, list[str]]:
    if not path.is_file():
        raise SystemExit(f"FILE-SCOPE cannot run  {path}: approved list missing")
    approved: dict[str, list[str]] = {}
    current = None
    for no, line in enumerate(path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"), 1):
        if line.startswith("@file "):
            current = line[6:]
            if current in approved or current.split("/")[0] not in MODULES:
                raise SystemExit(f"FILE-SCOPE cannot run  {path}:{no}: duplicate or out-of-scope @file {current}")
            approved[current] = []
        elif line[:2] in ("0|", "1|") and current is not None:
            approved[current].append(line)
        elif line.strip() and not line.startswith("# "):
            raise SystemExit(f"FILE-SCOPE cannot run  {path}:{no}: malformed approved-list line {line[:60]!r}")
    return approved


def block(rel: str, entries: list[tuple[int, str]]) -> str:
    return "\n".join([f"@file {rel}"] + [e for _, e in entries])


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(newline="\n")
    args = argv[1:]
    sources, show = ROOT / SOURCES, None
    while args:
        if args[0] == "--sources" and len(args) > 1:
            sources, args = pathlib.Path(args[1]), args[2:]
        elif args[0] == "--print":
            show, args = (args[1] if len(args) > 1 else ""), args[2:]
        else:
            print("FILE-SCOPE cannot run  usage: check-file-scope.py [--sources DIR] [--print [MODULE/FILE]]")
            return 2
    try:
        files = tree_files(sources)
        approved = load_approved(ROOT / APPROVED) if show is None else {}
    except SystemExit as e:
        print(e.code)
        return 2
    refusals, lines_ok = [], 0
    for rel in files:
        try:
            entries = file_entries(sources / rel)
        except LexError as e:
            refusals.append(f"FILE-SCOPE refuse  {rel}: the lexer cannot read it - {e}; a file it cannot read is "
                            "never a pass")
            continue
        if show is not None:
            if show in ("", rel):
                print(block(rel, entries) + "\n")
            continue
        if rel not in approved:
            refusals.append(f"FILE-SCOPE refuse  {rel}: a file the module's approved file set does not list. Paste:\n"
                            + block(rel, entries))
            continue
        want, got = approved[rel], [e for _, e in entries]
        if want == got:
            lines_ok += len(got)
            continue
        k = next((k for k in range(min(len(want), len(got))) if want[k] != got[k]), min(len(want), len(got)))
        where = (f"line {entries[k][0]} {got[k]!r} is not the approved {want[k] if k < len(want) else 'end of file'!r}"
                 if k < len(got) else f"the approved {want[k]!r} is gone")
        refusals.append(f"FILE-SCOPE refuse  {rel}: a file-scope or member line not at an approved site: {where}. "
                        "Approve deliberately by pasting:\n" + block(rel, entries))
    if show is not None:
        print("\n".join(refusals))
        return 1 if refusals else 0
    refusals +=[f"FILE-SCOPE refuse  {rel}: approved but not in the tree" for rel in approved if rel not in files]
    if len(files) < MIN_FILES:
        refusals.append(f"FILE-SCOPE refuse  {len(files)} file(s) under {sources}, below the floor {MIN_FILES}")
    for r in refusals:
        print(r)
    if refusals:
        print(f"FILE-SCOPE FAIL  {len(refusals)} refusal(s)")
        return 1
    print(f"FILE-SCOPE ok  {len(files)} file(s) in {len(MODULES)} module(s), {lines_ok} approved line(s) at depth "
          f"0-{CHECKED_DEPTH}; no file-scope or member line outside the approved list")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
