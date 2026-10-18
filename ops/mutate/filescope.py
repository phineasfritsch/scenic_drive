"""Mutation population for ops/lib/check-file-scope.py (T-0406): every way the 2026-10-17 reviews shadowed a name a
frozen safety block uses, and the generated placements of the same class.

    python ops/mutate/filescope.py [--only R1,G7,L3,...]

The subjects are COPIES: DesignSystem, FeaturePlanSheet, FeatureScenicHome and FeatureSurpriseMe are copied from
the tracked tree (which must equal HEAD) to .build/mutate-filescope/Sources, and each mutation is applied to that
copy, the guard run on it as its shipping command line (`check-file-scope.py --sources <copy>`), and the copy
restored byte for byte. No tracked byte and no .py file moves, so no __pycache__ can go stale. Before any mutation
the guard must be green on the pristine copy (a guard red without a mutant proves nothing).

KILLED means exit 1 AND the refusal names the mutated file (`FILE-SCOPE refuse  <module>/<file>`) AND, for the
lexer rows, the reason. R1-R5 are the review mutants verbatim (T-0398 rv1/rv2, T-0397 rv2 twice, T-0396 rv1); R6/R7
are T-0406 rv1's MUT-A/MUT-B (an #if branch's braces skew the depth, a decoy branch undoes it).
G rows are generated: each file-scope shadow x {above the imports, between them, at the end} x each frozen-block
file; each member shadow inserted into the first type of each frozen-block file; each file-scope shadow as a new
file in each module. L rows are the fail-closed lexer rows. D rows are generated directive rows: 6 conditions x
{#if, #else, #elseif} x skew 1-3 x {file-scope, member} decoy, skew in a closure and an interpolation, directives at
depth 0-3, and the directive lexer refusals. The floor is the literal MIN_MUTATIONS.

Exit 0 every mutation killed and at least MIN_MUTATIONS ran; 1 a survivor or too few; 2 cannot tell; 64 a bad
--only. Classified in ops/lib/mutate_population_table.py PROBES: its subject lives in ops/lib, outside MODULE_ROOTS.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import mutate_only  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUARD = "ops/lib/check-file-scope.py"
SOURCES = "apps/ios/Packages/ScenicApp/Sources"
MODULES = ("DesignSystem", "FeaturePlanSheet", "FeatureScenicHome", "FeatureSurpriseMe")
WORK = ROOT / ".build" / "mutate-filescope" / "Sources"
MIN_MUTATIONS = 615

FROZEN_FILES = ("FeatureScenicHome/SafetyDisclaimer.swift", "FeatureScenicHome/ScenicHomeScreen.swift",
                "FeatureScenicHome/PostDriveCard.swift", "FeatureSurpriseMe/SurpriseCard.swift",
                "FeaturePlanSheet/PlanPreviewCard.swift", "FeaturePlanSheet/PlanPreviewActions.swift",
                "DesignSystem/AttributionFooter.swift")
FILE_SHADOWS = (
    "private enum DesignTokens { static let fgMuted = Color.clear }",
    "private let `DesignTokens` = ShadowTokens.self",
    "fileprivate enum /* x */ DesignTokens { static let fgMuted = Color.clear }",
    "fileprivate enum\n    DesignTokens\n{ static let fgMuted = Color.clear }",
    "fileprivate typealias Text = EmptyText",
    "extension Text { func fixedSize(horizontal: Bool, vertical: Bool) -> some View { EmptyView() } }",
    "extension Capsule { func fill(_ c: Color) -> some View { EmptyView() } }",
    "extension View { func foregroundStyle(_ c: Color) -> some View { opacity(0) } }",
)
MEMBER_SHADOWS = (
    "    private var DesignTokens: ShadowTokens.Type { ShadowTokens.self }",
    "    private var `DesignTokens`: ShadowTokens.Type { ShadowTokens.self }",
    "    private enum /* x */ DesignTokens { static let fgMuted = Color.clear }",
)
OPENER = re.compile(r"^(?:@\w+ )*(?:(?:public|internal|fileprivate|private|final) )*(?:struct|enum|class|extension) .*\{$")

# (id, file, placement, text, reason-substring or "")
MUTATIONS = [
    ("R1", "FeatureSurpriseMe/SurpriseCard.swift", "append",
     "private enum DesignTokens { static let fgMuted = Color.clear }", ""),
    ("R2", "FeatureSurpriseMe/SurpriseCard.swift", "append",
     "private enum ShadowTokens { static let fgMuted = Color.clear }\nprivate let `DesignTokens` = ShadowTokens.self", ""),
    ("R3", "FeatureScenicHome/DriveShadow.swift", "new",
     "fileprivate enum DesignTokens { static let fgMuted = Color.clear }\nimport SwiftUI", ""),
    ("R4", "FeatureScenicHome/DriveShadow.swift", "new",
     "fileprivate enum PostDriveQuestion {}\nimport SwiftUI", ""),
    ("R3b", "FeatureScenicHome/DriveCard.swift", "prepend",
     "fileprivate enum DesignTokens {\n    static let fg = Color.clear\n}", ""),
    ("R3c", "FeatureScenicHome/DriveEndConfirm.swift", "prepend",
     "fileprivate enum DesignTokens {\n    static let fg = Color.clear\n}", ""),
    ("R4b", "FeatureScenicHome/DriveScreen.swift", "prepend",
     "fileprivate enum PostDriveQuestion {\n    static func asks(after display: Any, alreadyAsked: Bool) -> Bool { true }\n}",
     ""),
    ("R5", "FeaturePlanSheet/PlanPreviewCard.swift", "append",
     "extension Text { func fixedSize(horizontal: Bool, vertical: Bool) -> some View { EmptyView() } }", ""),
]
for _rel in FROZEN_FILES:
    for _place in ("prepend", "after-import", "append"):
        MUTATIONS += [("", _rel, _place, s, "") for s in FILE_SHADOWS]
    MUTATIONS += [("", _rel, "member", s, "") for s in MEMBER_SHADOWS]
for _module in MODULES:
    MUTATIONS += [("", f"{_module}/Shadow{k}.swift", "new", "import SwiftUI\n" + s, "")
                  for k, s in enumerate(FILE_SHADOWS, 1)]
MUTATIONS = [(m[0] or f"G{i}",) + m[1:] for i, m in enumerate(MUTATIONS, 1)]
_CARD = "FeatureSurpriseMe/SurpriseCard.swift"
_LEXER = [
    (_CARD, "append", "/* never closed\nprivate enum DesignTokens {}", "an unterminated /* comment"),
    (_CARD, "append", 'let s = "open\nprivate enum DesignTokens {}', "a newline inside a single-line string"),
    (_CARD, "append", 'let s = """\nnever closed', "an unterminated string"),
    (_CARD, "append", "let r = #/a{/#", "an unknown raw-string delimiter"),
    (_CARD, "append", "let r = /{{/", "bare /regex/"),
    (_CARD, "body", "        _ = /{{/", "bare /regex/"),
    (_CARD, "append", "}", "below depth 0"),
    (_CARD, "append", "struct X {", "a brace depth of 1"),
    (_CARD, "append", "// hide\rprivate enum DesignTokens {}", "a lone CR"),
    (_CARD, "append", "let `DesignTokens = 1", "an unterminated backtick"),
    (_CARD, "append", "\udcff", "not UTF-8"),
    (_CARD, "append", "let `{{` = 1", "not at an approved site"),
    (_CARD, "append", 'let s = "\\("}}")" + #"}}"#', "not at an approved site"),
    (_CARD, "append", 'let s = #"\\#("{{")"#', "not at an approved site"),
    ("FeatureScenicHome/HomeTypeSize.swift", "delete", "", "approved but not in the tree"),
]
MUTATIONS += [(f"L{i}",) + m for i, m in enumerate(_LEXER, 1)]

# T-0406 rv1 B1: braces in an #if branch skew the depth; a decoy body's branch undoes it. R6/R7 are MUT-A/MUT-B
# verbatim ("skew": the part before @@ goes after the first body opener, the rest before that body's `    }`).
_LOOP, _IF = "FeatureScenicHome/LoopLinks.swift", "#if compiler(>=99)"
_FILE_DECOY = "    }\n}\nprivate enum DesignTokens { static let bg = 0 }\nprivate enum Hide {\n    static func h() {"
_MEMBER_DECOY = "    }\n    static let DesignTokens = 0\n    static func h() {"
MUTATIONS += [
    ("R6", _LOOP, "skew", f"        {_IF}\n        {{{{\n        #endif\n@@\n{_FILE_DECOY}\n        {_IF}\n        }}}}\n"
                          "        #endif", ""),
    ("R7", _LOOP, "skew", f"        {_IF}\n        {{\n        #endif\n@@\n{_MEMBER_DECOY}\n        {_IF}\n        }}\n"
                          "        #endif", ""),
]
CONDS = ("compiler(>=99)", "swift(>=99)", "canImport(Nope)", "os(Linux)", "DEBUG", "!DEBUG")
FORMS = {"if": lambda c, body: [f"#if {c}", *body, "#endif"],
         "else": lambda c, body: [f"#if {c}", "#else", *body, "#endif"],
         "elseif": lambda c, body: [f"#if {c}", f"#elseif {c}", *body, "#endif"]}


def _ind(lines: list[str], pad: str = "        ") -> str:
    return "\n".join(pad + ln for ln in lines)


def _why(cond: str, flagged: str) -> str:
    return "one bare build flag" if "(" in cond else flagged


_D = []
for _c in CONDS:
    for _form, _wrap in FORMS.items():
        for _k in (1, 2, 3):
            for _decoy in (_FILE_DECOY, _MEMBER_DECOY):
                _D.append((_LOOP, "skew", _ind(_wrap(_c, ["{" * _k])) + "\n@@\n" + _decoy + "\n"
                           + _ind(_wrap(_c, ["}" * _k])), _why(_c, "not brace-neutral")))
    _D.append((_LOOP, "body", "        let f = {\n" + _ind(FORMS["if"](_c, ["{"]), " " * 12) + "\n        }",
               _why(_c, "not brace-neutral")))
    _D.append((_LOOP, "body", '        _ = """\n        \\(\n' + _ind(FORMS["if"](_c, ["{"])) + '\n        0)\n        """',
               "not on a line of its own"))
    _D.append((_CARD, "append", "\n".join(FORMS["if"](_c, ["private enum DesignTokens { static let bg = 0 }"])),
               _why(_c, "not at an approved site")))
    _D.append((_LOOP, "member", _ind(FORMS["if"](_c, ["static let DesignTokens = 0"]), "    "),
               _why(_c, "not at an approved site")))
    _D.append((_LOOP, "body", _ind(FORMS["if"](_c, ["let x = 1"])), _why(_c, "not at an approved site")))
    _D.append((_LOOP, "body", "        _ = {\n" + _ind(FORMS["if"](_c, ["let x = 1"]), " " * 12) + "\n        }",
               _why(_c, "not at an approved site")))
_D += [
    (_CARD, "append", "#if DEBUG", "without its #endif"),
    (_CARD, "append", "#endif", "without its #if"),
    (_LOOP, "body", "        #if DEBUG\n    }\n    static func x() {\n        #endif", "closes a scope opened before"),
    (_CARD, "append", "#if DEBUG\n#else DEBUG\n#endif", "text after"),
    (_LOOP, "body", "        let x = 1; #if DEBUG\n        #endif", "not on a line of its own"),
]
MUTATIONS += [(f"D{i}",) + m for i, m in enumerate(_D, 1)]

# T-0406 rv2 B1: a bare regex literal opening with '/=' skews the depth. R8/R9 are MUT-C/MUT-D verbatim. X rows are
# generated: each first character after the opening '/' x {statement, interpolation, closure, trailing comment}
# x skew 1-3 x {file-scope, member} decoy; Y rows are the slash-line rule's other refusals.
_BARE = "bare /regex/"
MUTATIONS += [
    ("R8", _LOOP, "skew", "        _ = /=\\{\\{/\n@@\n" + _FILE_DECOY + "\n        _ = /=\\}\\}/", _BARE),
    ("R9", _LOOP, "skew", '        _ = "\\(/=\\{/ )"\n@@\n' + _MEMBER_DECOY + '\n        _ = "\\(/=\\}/ )"', _BARE),
]
FIRSTS = ("=", "= ", ")", "]", "}", "a", ".", '"', "")
PLACES = (lambda r: f"_ = {r}", lambda r: f'_ = "\\({r} )"', lambda r: f"_ = {{ {r} }}", lambda r: f"_ = {r} // x")
_X = []
for _f in FIRSTS:
    for _p in PLACES:
        for _k in (1, 2, 3):
            for _decoy in (_FILE_DECOY, _MEMBER_DECOY):
                _X.append((_LOOP, "skew", "        " + _p(f"/{_f}" + "\\{" * _k + "/") + "\n@@\n" + _decoy + "\n        "
                           + _p(f"/{_f}" + "\\}" * _k + "/"), _BARE))
MUTATIONS += [(f"X{i}",) + m for i, m in enumerate(_X, 1)]
_Y = [
    (_LOOP, "body", "        var x = 6; x /= 2 // halve", _BARE),
    (_LOOP, "body", "        _ = 12 / 3 / 2", _BARE),
    (_LOOP, "body", '        _ = /\\{"/"\n        _ = 1', _BARE),
    (_LOOP, "body", "        _ = /\\{/*x*/", _BARE),
    (_CARD, "append", "let r = ##/a{/##", "an unknown raw-string delimiter"),
]
MUTATIONS += [(f"Y{i}",) + m for i, m in enumerate(_Y, 1)]


def _body_site(lines: list[str]) -> int | None:
    return next((k for k, ln in enumerate(lines) if ln.startswith("    ") and ln.endswith("{")
                 and ("var body" in ln or " func " in ln)), None)


def mutate(text: str, place: str, add: str) -> str | None:
    lines = text.split("\n")
    if place == "prepend":
        return add + "\n" + text
    if place == "append":
        return text.rstrip("\n") + "\n" + add + "\n"
    if place == "skew":
        head, tail = add.split("\n@@\n")
        k = _body_site(lines)
        end = next((j for j in range(k + 1, len(lines)) if lines[j] == "    }"), None) if k is not None else None
        if end is None:
            return None
        return "\n".join(lines[:k + 1] + head.split("\n") + lines[k + 1:end] + tail.split("\n") + lines[end:])
    if place == "after-import":
        k = next((k for k, ln in enumerate(lines) if ln.startswith("import ")), None)
    elif place == "member":
        k = next((k for k, ln in enumerate(lines) if OPENER.match(ln)), None)
    else:  # body: inside the first member body that opens a `var body` or a func
        k = _body_site(lines)
    if k is None:
        return None
    return "\n".join(lines[:k + 1] + add.split("\n") + lines[k + 1:])


def run_guard() -> tuple[int, str]:
    p = subprocess.run([sys.executable, GUARD, "--sources", str(WORK)], capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(newline="\n")
    only = mutate_only.select_only(argv, [m[0] for m in MUTATIONS])
    if len(argv) > 1 and only is None:
        print("MUTATE refuse  usage: python ops/mutate/filescope.py [--only R1,G7,L3]")
        return 2
    dirty = subprocess.run(["git", "status", "--porcelain", "--", *[f"{SOURCES}/{m}" for m in MODULES]],
                           capture_output=True, text=True, cwd=ROOT)
    if dirty.returncode != 0 or dirty.stdout.strip():
        print(f"MUTATE refuse  the subject modules differ from HEAD; commit or stash first:\n{dirty.stdout}")
        return 2
    shutil.rmtree(WORK, ignore_errors=True)
    for m in MODULES:
        shutil.copytree(ROOT / SOURCES / m, WORK / m)
    rc, out = run_guard()
    if rc != 0:
        print(f"MUTATE refuse  the guard is not green on the pristine copy:\n{out}")
        return 2
    picked = [m for m in MUTATIONS if only is None or m[0] in only]
    survivors = []
    for mid, rel, place, add, reason in picked:
        path = WORK / rel
        before = path.read_bytes() if path.exists() else None
        if place == "new":
            if before is not None:
                print(f"MUTATE refuse  {mid}: the new file {rel} already exists")
                return 2
            path.write_bytes((add + "\n").encode("utf-8"))
        elif place == "delete":
            path.unlink()
        else:
            new = mutate(before.decode("utf-8"), place, add) if before is not None else None
            if new is None:
                print(f"MUTATE refuse  {mid}: no {place} site in {rel}")
                return 2
            path.write_bytes(new.encode("utf-8", errors="surrogateescape"))
        rc, out = run_guard()
        if before is None:
            path.unlink()
        else:
            path.write_bytes(before)
        if (path.read_bytes() if path.exists() else None) != before:
            print(f"MUTATE refuse  {mid}: {rel} was not restored byte for byte")
            return 2
        named = [ln for ln in out.splitlines() if ln.startswith(f"FILE-SCOPE refuse  {rel}:")]
        if rc == 1 and named and (not reason or any(reason in ln for ln in named)):
            print(f"MUTATE killed  {mid} {place} {rel}: {add.splitlines()[0][:56] if add else '(file)'!r}")
        else:
            survivors.append(mid)
            print(f"MUTATE SURVIVED {mid} {place} {rel}: {add[:56]!r} (exit {rc}, named {len(named)}, want {reason!r})")
    shutil.rmtree(WORK.parent, ignore_errors=True)
    if survivors or (only is None and len(picked) < MIN_MUTATIONS):
        print(f"MUTATE FAIL  survivors {survivors}; ran {len(picked)}, floor {MIN_MUTATIONS}")
        return 1
    print(f"MUTATE ok  {len(picked)}/{len(picked)} killed (floor {MIN_MUTATIONS}, population {len(MUTATIONS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
