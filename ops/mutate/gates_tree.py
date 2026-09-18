#!/usr/bin/env python3
"""What the tree contains, and whether it is what HEAD says it is. The runner is ops/mutate/gates.py.

Split out of gates.py in round 8 of PR #82, when adding the harness's own files to the HEAD check pushed that
file past the 300-line cap CLAUDE.md sets. The concern here is exactly one question asked twice: *which files
bear on a measurement, and are they the committed ones?* Discovery answers the first, `not_at_head` the
second. Everything about mutating, building and judging stayed in the runner.

Neither function takes the repository root from a module-level constant of its own: the caller passes the
`root` it is already using, so this file cannot drift out of agreement with gates.py about which tree is
being measured. `HARNESS` is the one list built from this file's own location, because those paths are the
harness, not the subject.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve()
MUTATE = HERE.parent

# The harness's OWN files, HEAD-checked beside the subjects since round 8 of PR #82. The floors in gates.py
# are a POPULATION check: they catch a mutation deleted from the corpus and they catch nothing at all about a
# mutation whose body is WEAKENED on disk - `new` edited until it is equivalent to `old`, say - which would
# then be reported caught or missed on terms nobody reviewed. All four files, because a check that covered
# only the runner would be the same hole one file along; the corpus is split across two of them.
HARNESS = (MUTATE / "gates.py", MUTATE / "gates_corpus.py", MUTATE / "gates_corpus_sets.py", HERE)

# Every suite that could catch a mutation - DISCOVERED, not one hardcoded path.
#
# T-0132: a suite split at the 300-line cap silently broke the hardcoded-single-path form in five separate
# harnesses. The half that moved out kept catching mutations while `--prove-vacuity` went on printing "EVERY
# test file is replaced". The reviewer of PR #82 reproduced that decay here, and the second round of fixes
# split this very suite into three files - so the decay would have landed for real. A file counts if it
# mentions any of the three symbols under test; that is a property of the tree, so a split half is picked up
# the moment it exists.
SUBJECT_SYMBOLS = re.compile(r"\bGates\b|\bGateDecision\b|\bGateReason\b|\bConsideredTags\b")


def discover_test_files(root: pathlib.Path):
    out = []
    for p in sorted((root / "Tests").rglob("*.swift")):
        if SUBJECT_SYMBOLS.search(p.read_text(encoding="utf-8", errors="replace")):
            out.append(p)
    return out


def head_bytes(root: pathlib.Path, path: pathlib.Path):
    rel = path.relative_to(root).as_posix()
    p = subprocess.run(["git", "show", "HEAD:" + rel], cwd=root, capture_output=True)
    return p.stdout if p.returncode == 0 else None


def not_at_head(root: pathlib.Path, paths):
    """Paths whose bytes on disk differ from `git show HEAD:`, with why. Without this the harness snapshots
    whatever is on disk as "pristine" and measures THAT: the second review of PR #82 put one `expressway`
    branch into Gates.swift, ran this harness unmodified, and got "caught by a named test: 28 of 28" / exit 0
    over a tree that hard-excludes every expressway-tagged motorway. Printing the md5 was not enough."""
    bad = []
    for p in paths:
        h = head_bytes(root, p)
        if h is None:
            bad.append((p, "not tracked at HEAD"))
        elif h != p.read_bytes():
            bad.append((p, "differs from HEAD"))
    return bad
