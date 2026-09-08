#!/usr/bin/env python3
"""Run check-self-referential-tests against the REAL commits where each defect actually shipped.

`check-self-referential-cases.py` reproduces the shapes in a scaffold, which proves the matcher works.
This proves something stronger: pointed at the files as they were when a reviewer had to find the defect by
hand, the check fires - and pointed at the same files after the fix, it does not.

## Why the commits are pinned by SHA

The first version anchored on `origin/task/T-0116~1`. That is a MOVING TARGET: the branch advanced, `~1`
became the fix commit, and the demonstration silently stopped demonstrating anything. A reviewer caught it -
the transcript in the task Log was true when written and false a few hours later.

So every commit below is a full SHA, and the run refuses if one cannot be read. A demonstration that
decays into a green is worse than no demonstration, because it is evidence somebody will cite.

## Why a SKIP is a FAILURE

The first version did `continue` on an unreadable ref without setting `ok = False`, so pointed at a branch
that did not exist it printed `AGAINST HISTORY OK` and exited 0 having checked nothing. Green on nothing -
precisely the class this whole check exists to close, in the check's own demonstration.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECK = ROOT / "ops" / "lib" / "check-self-referential-tests.py"

# (label, test path, source dir, commit BEFORE the fix, commit AFTER it, what the before-run must name)
HISTORY = [
    ("T-0118 LearnedCorridorSpeeds",
     "Tests/ScenicKitTests/LearnedCorridorSpeedsTests.swift",
     "Sources/ScenicKit/Traffic",
     "245d5418ebf1", "d8d15e2", "LearnedCorridorSpeeds.maxRatio"),
    ("T-0116 LambdaSearch",
     "Tests/ScenicKitTests/LambdaSearchTests.swift",
     "Sources/ScenicKit/Budget",
     "10c2c5a", "b1be8cc", "out.duration vs out.ceiling"),
]

PAD_TESTS = "\n".join("        #expect(value%d == %d)" % (i, i) for i in range(1, 13))
PAD = {
    "PadOne.swift": 'import Testing\n@Suite("pad one") struct PadOneSuite {\n'
                    '    @Test("pad") func pad() {\n' + PAD_TESTS + "\n    }\n}\n",
    "PadTwo.swift": 'import Testing\n@Suite("pad two") struct PadTwoSuite {\n'
                    '    @Test("pad") func pad() {\n' + PAD_TESTS + "\n    }\n}\n",
}
# The check refuses to run over a truncated Sources/ tree. This scaffold carries one module's sources, which
# for Traffic is two types - below that floor. Pad the scaffold; lowering the floor to fit it would be the
# check bending to accommodate its own demonstration.
PAD_SOURCES = {
    "PadTypeA.swift": "public struct PadTypeA { public static let a = 1 }\n",
    "PadTypeB.swift": "public struct PadTypeB { public static let b = 2 }\n",
}


def git(*args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout


def run_at(commit: str, test_path: str, source_dir: str) -> tuple[int, str]:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="selfref-hist-"))
    try:
        (tmp / "ops" / "lib").mkdir(parents=True)
        (tmp / "Sources" / "Probe").mkdir(parents=True)
        (tmp / "Tests" / "ProbeTests").mkdir(parents=True)
        shutil.copy(CHECK, tmp / "ops" / "lib" / CHECK.name)
        for name, body in PAD.items():
            (tmp / "Tests" / "ProbeTests" / name).write_text(body, encoding="utf-8", newline="\n")
        for name, body in PAD_SOURCES.items():
            (tmp / "Sources" / "Probe" / name).write_text(body, encoding="utf-8", newline="\n")

        code, listing = git("ls-tree", "--name-only", commit, source_dir + "/")
        if code != 0 or not listing.strip():
            return 3, "cannot list %s at %s" % (source_dir, commit)
        for path in listing.split("\n"):
            if not path.endswith(".swift"):
                continue
            code, body = git("show", "%s:%s" % (commit, path))
            if code != 0:
                return 3, "cannot read %s at %s" % (path, commit)
            (tmp / "Sources" / "Probe" / pathlib.Path(path).name).write_text(
                body, encoding="utf-8", newline="\n")

        code, body = git("show", "%s:%s" % (commit, test_path))
        if code != 0:
            return 3, "cannot read %s at %s" % (test_path, commit)
        (tmp / "Tests" / "ProbeTests" / "Case.swift").write_text(body, encoding="utf-8", newline="\n")

        p = subprocess.run([sys.executable, str(tmp / "ops" / "lib" / CHECK.name)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ok = True
    for label, test_path, source_dir, before, after, must_name in HISTORY:
        code_b, out_b = run_at(before, test_path, source_dir)
        code_a, out_a = run_at(after, test_path, source_dir)

        sys.stdout.write("\n=== %s\n" % label)

        # A SKIP is a FAILURE. The first version continued past an unreadable ref without setting ok, so a
        # deleted or renamed branch turned the whole demonstration into a green.
        if code_b == 3 or code_a == 3:
            ok = False
            sys.stdout.write("  FAIL: cannot read the pinned commits - %s\n"
                             % (out_b if code_b == 3 else out_a).strip())
            continue

        sys.stdout.write("  before %s: exit %d\n" % (before, code_b))
        for line in out_b.strip().splitlines()[:5]:
            sys.stdout.write("      %s\n" % line)
        sys.stdout.write("  after  %s: exit %d   %s\n"
                         % (after, code_a, out_a.strip().splitlines()[0] if out_a.strip() else ""))

        if code_b != 1:
            ok = False
            sys.stdout.write("  FAIL: the check did not fire on the file a reviewer read by hand\n")
        elif must_name not in out_b:
            ok = False
            sys.stdout.write("  FAIL: it fired, but never named %r - so it found something else\n"
                             % must_name)
        if code_a != 0:
            ok = False
            sys.stdout.write("  FAIL: the check still fires after the fix\n")

    if not HISTORY:
        sys.stdout.write("FAIL: no history entries - a demonstration over nothing is not a demonstration\n")
        return 2

    sys.stdout.write("\nSELF-REF HISTORY %s (%d commit pairs)\n" % ("OK" if ok else "FAIL", len(HISTORY)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
