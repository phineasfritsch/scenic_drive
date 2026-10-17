#!/usr/bin/env python3
"""Mutation harness for Sources/ScenicAPIClient/APIBaseURL.swift - the one base-URL rule (T-0394).

    python ops/mutate/apibaseurl.py
    python ops/mutate/apibaseurl.py --only 1,2
    python ops/mutate/apibaseurl.py --prove-floor

The population is ops/mutate/apibaseurl_mutations.py. The protocol is straightline.py's, in one file because
this subject is one file: the mutated file and both harness files must equal HEAD before the first build (a
report is a claim about a commit); the TEST file is deliberately not guarded, so the red-then-green Log runs
the same entries against the suite before and after a test lands. A catch is a NAMED test recording an issue,
and every name in the entry's `killers` must be among them; anything else is its own failing bucket.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
shutil.rmtree(pathlib.Path(__file__).resolve().parent / "__pycache__", ignore_errors=True)

import mutate_only

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("Sources/ScenicAPIClient/APIBaseURL.swift",)

from apibaseurl_mutations import (EQUIVALENT, MIN_EQUIVALENT, MIN_MUTATIONS, MIN_TEST_FILES, MUTATED_FILES,
                                  MUTATIONS, ROOT, SUBJECT, TEST_DIR)

TESTS = sorted(TEST_DIR.glob("APIBaseURL*.swift"))
HARNESS = (pathlib.Path(__file__).resolve(),
           pathlib.Path(__file__).resolve().parent / "apibaseurl_mutations.py")
SCRATCH = ".build/mutate-apibaseurl"
FILTER = "APIBaseURLTests"
FAIL_LINE = re.compile(r'Test\s+(?:"([^"]*)"|([A-Za-z_]\w*\(\)))\s+recorded an issue')


def population_floor():
    """The reason to refuse, or None."""
    if len(MUTATIONS) < MIN_MUTATIONS:
        return "MUTATIONS holds %d entries, below the floor of %d" % (len(MUTATIONS), MIN_MUTATIONS)
    if len(EQUIVALENT) < MIN_EQUIVALENT:
        return "EQUIVALENT holds %d entries, below the floor of %d" % (len(EQUIVALENT), MIN_EQUIVALENT)
    if len(TESTS) < MIN_TEST_FILES:
        return "TESTS globbed %d files, below the floor of %d" % (len(TESTS), MIN_TEST_FILES)
    nameless = [n for n, _p, _o, _w, k in MUTATIONS if not k]
    if nameless:
        return "these entries name no killer: %s" % ", ".join(nameless)
    if SUBJECT not in {p for _n, p, _o, _w, _k in MUTATIONS}:
        return "no MUTATIONS entry edits %s, the path SUBJECT_MODULES declares" % SUBJECT.name
    return None


def prove_floor() -> int:
    """`--prove-floor`: each arm must refuse and the unpatched control must not. Builds nothing."""
    base = {"MUTATIONS": list(MUTATIONS), "EQUIVALENT": list(EQUIVALENT), "TESTS": list(TESTS),
            "MIN_MUTATIONS": MIN_MUTATIONS}
    arms = [("MUTATIONS emptied", {"MUTATIONS": []}),
            ("MUTATIONS one short", {"MUTATIONS": base["MUTATIONS"][:-1]}),
            ("floor raised by one", {"MIN_MUTATIONS": MIN_MUTATIONS + 1}),
            ("EQUIVALENT emptied", {"EQUIVALENT": []}),
            ("TESTS emptied", {"TESTS": []}),
            ("one entry's killers emptied", {"MUTATIONS": [m[:4] + ([],) for m in base["MUTATIONS"][:1]]
                                             + base["MUTATIONS"][1:]})]
    g, refused = globals(), 0
    try:
        for label, patch in arms:
            g.update(base)
            g.update(patch)
            why = population_floor()
            sys.stdout.write("FLOOR ARM   %-32s %s\n" % (label, why or "NO REFUSAL - THIS ARM FAILED"))
            refused += why is not None
        g.update(base)
        control = population_floor()
    finally:
        g.update(base)
    ok = refused == len(arms) and control is None
    sys.stdout.write("FLOOR PROOF %s: %d of %d arms refused, control %s\n"
                     % ("OK" if ok else "FAILED", refused, len(arms), control or "clean"))
    return 0 if ok else 1


def head_bytes(path: pathlib.Path) -> bytes:
    rel = path.resolve().relative_to(ROOT).as_posix()
    out = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + rel], capture_output=True)
    if out.returncode != 0:
        raise SystemExit("not in HEAD: %s - a mutation report is a claim about a commit" % rel)
    return out.stdout.replace(b"\r\n", b"\n")


def not_at_head(paths) -> list:
    return [p.name for p in paths if p.read_bytes().replace(b"\r\n", b"\n") != head_bytes(p)]


def swift(*args: str):
    p = subprocess.run(["swift", *args, "--scratch-path", SCRATCH], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def build() -> int:
    return swift("build", "--build-tests")[0]


def test():
    return swift("test", "--filter", FILTER)


def failing_names(txt: str) -> list:
    seen = []
    for m in FAIL_LINE.finditer(txt):
        name = m.group(1) or m.group(2)
        if name not in seen:
            seen.append(name)
    return seen


def run_all(pristine, population, require_killers: bool) -> dict:
    out = {k: [] for k in ("caught", "wrong_killer", "trapped", "compile_only", "missed", "skipped")}
    for entry in population:
        name, path, old, new = entry[:4]
        killers = entry[4] if require_killers else []
        text = pristine[path].decode("utf-8")
        if text.count(old) != 1:
            sys.stdout.write("SKIP          %-52s anchor occurs %d times\n" % (name, text.count(old)))
            out["skipped"].append(name)
            continue
        names, code = [], 0
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if build() != 0 and build() != 0:
                verdict = "compile_only"
            else:
                code, txt = test()
                names = failing_names(txt)
                if not names:
                    verdict = "trapped" if code != 0 else "missed"
                else:
                    verdict = "caught" if all(k in names for k in killers) else "wrong_killer"
        finally:
            path.write_bytes(pristine[path])
        out[verdict].append(name)
        sys.stdout.write("%-14s%-52s %s\n" % (verdict.upper() if verdict != "caught" else "caught", name,
                                               "red: " + " | ".join(names) if names else "exit=%d" % code))
    return out


def main(argv) -> int:
    picked = mutate_only.select_only(argv, [str(i) for i in range(1, len(MUTATIONS) + 1)])
    if "--prove-floor" in argv:
        return prove_floor()
    refusal = population_floor()
    if refusal is not None:
        sys.stdout.write("REFUSING TO RUN: %s\n" % refusal)
        return 2
    only = picked is not None
    chosen = [m for i, m in enumerate(MUTATIONS, 1) if not only or str(i) in picked]
    sys.stdout.write("population  mutations=%d (floor %d)  equivalent=%d (floor %d)  subject=%s  tests=%s\n"
                     % (len(MUTATIONS), MIN_MUTATIONS, len(EQUIVALENT), MIN_EQUIVALENT, SUBJECT.name,
                        ", ".join(t.name for t in TESTS)))
    if only:
        sys.stdout.write("PARTIAL RUN over %d of %d mutations (--only); never MUTATE OK\n"
                         % (len(chosen), len(MUTATIONS)))
    dirty = not_at_head(list(MUTATED_FILES) + list(HARNESS))
    if dirty:
        sys.stdout.write("REFUSING: not what HEAD says it is: %s\n" % ", ".join(dirty))
        return 2
    pristine = {f: f.read_bytes() for f in MUTATED_FILES}
    eq = None
    try:
        if build() != 0 and build() != 0:
            sys.stdout.write("baseline does not build\n")
            return 2
        code, _txt = test()
        sys.stdout.write("BASELINE    --filter %s exit=%d\n" % (FILTER, code))
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2
        r = run_all(pristine, chosen, True)
        if not only:
            for name, _p, _o, _n, witness in EQUIVALENT:
                sys.stdout.write("  witness     %s: %s\n" % (name, witness))
            eq = run_all(pristine, EQUIVALENT, False)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
    if not_at_head(MUTATED_FILES):
        sys.stdout.write("RESTORE FAILED\n")
        return 2
    sys.stdout.write("caught by the test that names it: %d of %d   (wrong killer %d, trapped %d, compile-only %d, "
                     "MISSED %d, skipped %d)\n" % (len(r["caught"]), len(chosen), len(r["wrong_killer"]),
                                                    len(r["trapped"]), len(r["compile_only"]), len(r["missed"]),
                                                    len(r["skipped"])))
    if only:
        ok = len(r["caught"]) == len(chosen)
        sys.stdout.write("PARTIAL %s: %d of %d selected mutations caught by the test that names it\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(chosen)))
        return 0 if ok else 1
    eq_ok = len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d MISSED as required\n" % (len(eq["missed"]),
                                                                                  len(EQUIVALENT)))
    ok = len(r["caught"]) == len(MUTATIONS) and eq_ok
    sys.stdout.write("MUTATE %s  caught=%d/%d equivalent_missed=%d/%d\n"
                     % ("OK" if ok else "FAILED", len(r["caught"]), len(MUTATIONS), len(eq["missed"]),
                        len(EQUIVALENT)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
