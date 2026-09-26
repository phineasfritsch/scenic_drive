"""The mutant runner for ops/mutate/menu.py: what a build is, what a catch is, and the six mutually exclusive
buckets one mutation lands in. straightline_run.py's machinery with this population's scratch path and filter;
ops/lib/check-mutate-population.py reads the whole `menu*.py` family as one driver's code, and this file has
no `__main__` block.

A catch is a NAMED test recording an issue, and the name must be one the entry names. A non-zero exit with no
named failure is `trapped`; a mutation that does not compile is `compile-only`; an anchor that is gone is
`skipped`; a catch by some other test is `wrong killer`. None of them counts.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

from menu_mutations import ROOT

# Under .build/, which .gitignore excludes, and its own scratch path because this box is shared.
SCRATCH = ".build/mutate-menu"
# The two suites every `killers` entry names, by their type names.
FILTER = "RouteMenuTests|MenuCLITests"
# `Test "<display name>" recorded an issue`. ASCII only: the failure glyph mis-decodes on this console.
FAIL_LINE = re.compile(r'Test\s+(?:"([^"]*)"|([A-Za-z_]\w*\(\)))\s+recorded an issue')


def failing_test_names(txt: str) -> list:
    seen = []
    for m in FAIL_LINE.finditer(txt):
        groups = [g for g in (m.groups() or ()) if g]
        name = groups[0] if groups else " ".join(m.group(0).split())[:60]
        if name not in seen:
            seen.append(name)
    return seen


def empty_suite(path: pathlib.Path) -> str:
    """An empty suite named after the file it replaces, so the filter still matches and the build still
    compiles - a compile failure would make the vacuity proof pass for the wrong reason."""
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (path.stem, path.stem))


def head_bytes(path: pathlib.Path) -> bytes:
    rel = path.resolve().relative_to(ROOT).as_posix()
    out = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + rel], capture_output=True)
    if out.returncode != 0:
        raise SystemExit("not in HEAD: %s - a mutation report is a claim about a commit" % rel)
    return out.stdout.replace(b"\r\n", b"\n")


def not_at_head(paths) -> list:
    return [p.resolve().relative_to(ROOT).as_posix() for p in paths
            if p.read_bytes().replace(b"\r\n", b"\n") != head_bytes(p)]


def build() -> int:
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test() -> tuple:
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH, "--filter", FILTER],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(pristine, population, require_killers: bool):
    """One verdict per mutation, in six mutually exclusive buckets."""
    out = {"caught": [], "wrong_killer": [], "trapped": [], "compile_only": [], "missed": [],
           "skipped": []}
    for entry in population:
        name, path, old, new = entry[0], entry[1], entry[2], entry[3]
        killers = entry[4] if require_killers else []
        text = pristine[path].decode("utf-8")
        if text.count(old) != 1:
            sys.stdout.write("SKIP        %-62s anchor found %d times in %s\n" % (name, text.count(old),
                                                                                path.name))
            out["skipped"].append(name)
            continue
        names, code = [], 0
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if build() != 0 and build() != 0:
                verdict = "compile_only"
            else:
                code, txt = test()
                names = failing_test_names(txt)
                if not names:
                    verdict = "trapped" if code != 0 else "missed"
                else:
                    red = [k for k in killers if k in names]
                    verdict = "caught" if len(red) == len(killers) else "wrong_killer"
        finally:
            path.write_bytes(pristine[path])
        out[verdict].append(name)
        label = {"caught": "caught", "wrong_killer": "WRONG KILLER", "trapped": "trapped",
                 "compile_only": "compile-only", "missed": "MISSED"}
        note = {"caught": "by: " + " | ".join(names) if names else "no test objected",
                "wrong_killer": "named %s; red were %s" % (killers, names[:3]),
                "trapped": "non-zero exit, but NO named test failed - DOES NOT COUNT",
                "compile_only": "a fact about Swift, not about these tests - DOES NOT COUNT",
                "missed": "exit=%d  no test objected" % code}
        sys.stdout.write("%-14s%-62s %s\n" % (label[verdict], name, note[verdict]))
        sys.stdout.flush()
    return out
