#!/usr/bin/env python3
"""T-0407 (P-SAFE-03, P-SAFE-07, P-SAFE-09, P-ATTR-01): a file that holds a frozen block holds no /* */ comment.
    python ops/lib/frozen_comments.py FILE...   # each FILE a Swift file a frozen-block reader reads
THE CLASS (rv2-t0405 on PR #298): every frozen-block reader compares whole trimmed lines and drops only lines that
START with //, so a `/*` at the end of the line above a frozen block and a `*/` at the start of the line after it
comment the block out while every approved line is still there to read; a twin declaration spelled one space
differently then draws instead, and the only refusal left was the file's sha256 row (re-approved routinely).
The rule closes the class the way frozen_directives closes `#if`: ANY block comment in such a file is refused unless
it is an APPROVED entry `basename|whole opening line|whole closing line` (the set is empty: none existed on
2026-10-18). It is called INSIDE the readers - check-safety-disclaimer-frozen's frozen_block,
check-drive-display.py's frozen() and check-estimate-badge.py's check() - on the file each block is read from, so the
frozen-file set is whatever the readers read, never a second list.
THE LEXER is check-file-scope.py's (T-0406), loaded from that file: its `_block_comment` is wrapped so every block
comment the shipping lexer opens is recorded, and `checked_lines` runs unchanged - strings, raw strings,
interpolation, nesting and // are read exactly as that guard reads them. FAIL CLOSED: the wrap is proved on a canary
before each file (a renamed hook is exit 2, never a silent zero); a file the lexer cannot read is a refusal.
A STRAY `*/` (T-0407 pre-review M1): a `/*` in a // tail is a comment to neither swiftc nor the lexer, so a `*/` below
it closes nothing, and every reader read on. swiftc rejects that file ("unexpected end of block comment"), but the
rule does not lean on the compiler: a `*/` the shipping lexer reads as CODE is refused too. Each `*/` outside a block
comment (and not the `*/` of `*/*`, whose `/*` opens a comment refused above) becomes `/**/` in a probe and the lexer
runs again; one it then opens a comment at was code. A `*/` in a string or a // line stays inert in the probe.
NOT REFUSED: `/*` or `*/` inside a // line or a string literal (a comment to neither swiftc nor the lexer). Exit 0
none; 1 a refusal (one line per comment or stray closer); 2 the check could not run.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import warnings

sys.dont_write_bytecode = True
LEXER = pathlib.Path(__file__).resolve().parent / "check-file-scope.py"
APPROVED: tuple[str, ...] = ()
CANARY = b"struct A {\n    /* x */ let a = 1\n}\n"


class CannotRun(Exception):
    pass


def _load():
    spec = importlib.util.spec_from_file_location("check_file_scope_lexer", LEXER)
    if spec is None or spec.loader is None:
        raise CannotRun(f"cannot load the lexer {LEXER}")
    mod = importlib.util.module_from_spec(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)  # its docstring's `\{`; bytecode is never cached here
        spec.loader.exec_module(mod)
    for name in ("_block_comment", "checked_lines", "LexError"):
        if not hasattr(mod, name):
            raise CannotRun(f"the lexer {LEXER.name} has no {name}: this rule reads comments through it")
    return mod


def _lex(raw: bytes, mod) -> list[tuple[int, int, int, int]]:
    """(start, end, first line, last line) of every block comment the shipping lexer opens; LexError propagates."""
    found: list[tuple[int, int, int, int]] = []
    inner = mod._block_comment

    def record(text: str, i: int, line: int) -> tuple[int, int]:
        end, last = inner(text, i, line)
        found.append((i, end, line, last))
        return end, last

    mod._block_comment = record
    try:
        mod.checked_lines(raw)
    finally:
        mod._block_comment = inner
    return found


def spans(raw: bytes, mod=None) -> list[tuple[int, int]]:
    """(first, last) 0-based line of every block comment the shipping lexer opens; LexError propagates."""
    return [(first, last) for _, _, first, last in _lex(raw, mod or _load())]


def strays(raw: bytes, mod=None) -> list[int]:
    """0-based line of every `*/` the shipping lexer reads as code (see A STRAY above); LexError propagates."""
    mod = mod or _load()
    cuts = [(i, end) for i, end, _, _ in _lex(raw, mod)]
    text = raw.decode("utf-8").replace("\r\n", "\n")  # the lexer's own text: _lex above refused anything else
    inside = lambda k: any(i <= k < end for i, end in cuts)  # noqa: E731
    at, p = [], text.find("*/")
    while p >= 0:
        if not inside(p) and not inside(p + 1):
            at.append(p)
        p = text.find("*/", p + 1)
    probe, marks, prev = "", {}, 0
    for p in at:
        probe += text[prev:p]
        marks[len(probe)], probe, prev = p, probe + "/**/", p + 2
    opened = {i for i, _, _, _ in _lex((probe + text[prev:]).encode("utf-8"), mod)} if at else set()
    return [text.count("\n", 0, p) for q, p in marks.items() if q in opened]


def refusals(path: pathlib.Path, label: str = "") -> list[str]:
    """One line per unapproved block comment in PATH, or the lexer's refusal; [] when it holds none."""
    mod = _load()
    if spans(CANARY, mod) != [(1, 1)]:
        raise CannotRun("the lexer did not record the canary's one block comment: the wrap no longer reads it")
    head = f"{label}: " if label else ""
    try:
        raw = path.read_bytes()
    except OSError as e:
        return [f"{head}{path.name}: cannot read it ({e.strerror}) - a frozen file it cannot read is never a pass"]
    try:
        found, stray = spans(raw, mod), strays(raw, mod)
    except mod.LexError as e:
        return [f"{head}{path.name}: the lexer cannot read it - {e}; a frozen file it cannot read is never a pass"]
    lines = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").split("\n")
    out = []
    for first, last in found:
        if f"{path.name}|{lines[first]}|{lines[last]}" in APPROVED:
            continue
        out.append(f"{head}{path.name} line {first + 1}: a /* */ block comment in a frozen file (lines {first + 1}-"
                   f"{last + 1}, opening `{lines[first].strip()}`), none approved - it can hide a frozen block while "
                   "every approved line is still read (rv2-t0405, ops/lib/frozen_comments.py)")
    for ln in stray:
        out.append(f"{head}{path.name} line {ln + 1}: a /* */ block comment in a frozen file ends at a stray `*/` the "
                   f"lexer reads as code (`{lines[ln].strip()}`), its `/*` in a // tail or a string - swiftc rejects it "
                   "and the readers read on (T-0407 M1, ops/lib/frozen_comments.py)")
    return out


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(newline="\n")
    if len(argv) < 2:
        print("FROZEN-COMMENT cannot run  usage: frozen_comments.py FILE...")
        return 2
    bad = []
    try:
        for name in argv[1:]:
            bad += refusals(pathlib.Path(name))
    except CannotRun as e:
        print(f"FROZEN-COMMENT cannot run  {e}")
        return 2
    for line in bad:
        print(f"FROZEN-COMMENT refuse  {line}")
    if bad:
        return 1
    print(f"FROZEN-COMMENT ok  {len(argv) - 1} file(s), no block comment outside the {len(APPROVED)} approved, no "
          "stray */")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
