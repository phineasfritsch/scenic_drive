"""What ops/mutate/budget.py does to the working tree, and how it proves it is measuring the right bytes.

Split out of budget.py at the 300-line cap. Two defences, for two different ways a mutation harness can end
up reporting verdicts about a file nobody meant to measure.

THE SENTINEL - a run that is KILLED, not failed, dies between writing a mutation and the `finally` that puts
the file back, and leaves a mutated subject on disk. That happened on this box while this harness was being
fixed: a backgrounded run was killed mid-mutation, the following run recorded
`pristine LambdaSearch.swift md5 1f7512ba` - a file with `maxEvaluations: Int = 2` in it - and the working
tree kept the mutation afterwards. try/finally cannot defend against SIGKILL, so the defence is a file
written before the first mutation and removed after the last restore. Finding one at startup means the
previous run did not finish.

THE HEAD COMPARISON - the sentinel is armed by this harness and by nothing else, so it says nothing about a
subject left dirty for any other reason: a hand-run red demonstration killed halfway, an editor, a merge. The
third review demonstrated exactly that, planting a live mutation by hand and running the harness with no
sentinel present: it printed `pristine LambdaSearch.swift md5 d08228d8` - the mutant, snapshotted as the
baseline - then `BASELINE exit=0`, then `caught by a named test: 34 of 34`, and exited 0 over a corrupted
subject. The task Log had been crediting a check that did not exist ("the subject md5 is checked against HEAD
before and after every mutating run" describes a human reading a printed number). This is that check: the
bytes on disk are compared with `git show HEAD:<path>`, and a difference REFUSES.

What it does NOT cover, said plainly: TEST_FILES are deliberately excluded. A fix pass edits tests by design,
so refusing on them would refuse the ordinary case - and a test file left emptied by a killed --prove-vacuity
run makes every mutation report MISSED, which fails loudly (`caught 0 of N`) instead of reading as a clean
sheet. The subjects are the files whose CONTENT every verdict is a statement about, and they are the ones a
fixer has no reason to have modified while asking what the suite catches. `--allow-dirty-subject` is the
escape hatch for the fixer who does, and it says so in the output.
"""
from __future__ import annotations

import pathlib
import subprocess

from budget_mutations import MUTATIONS
from budget_paths import ROOT, SUBJECTS

# EVERY suite that can see the subjects, and the fact that it is every one of them is part of the claim.
# The number used to be spelled out here ("ALL FOUR"), and the sixth round added a fifth suite - so the
# sentence is written without a count now, for the same reason
# Tests/ScenicKitTests/LambdaSearchBudgetUseTests.swift stopped repeating it: a number in prose beside a list
# is a second copy that can only go stale, and this comment is about a list going stale. The list below is
# the one place it lives. reviewer-pr71's blocking finding:
# commit bc5e7f6 split ten tests into LambdaSearchBudgetUseTests.swift and --prove-vacuity kept emptying
# only the first file, so it reported "VACUITY PROOF FAILED: 8 mutations were reported caught" while the
# task log recorded OK. The harness's own message - "with no tests present" - was false; it was measuring
# the sibling test file. A demonstration that decayed at the last commit, and exactly the shape of defect
# this repository exists to catch.
#
# The refusal suite was the third such split, and that its entry is LOAD-BEARING was demonstrated rather
# than assumed: with it removed from this list, --prove-vacuity leaves it standing, it catches "the shortest
# route seen is reported as the longest" - the one mutation only it catches - and the run reports
# `VACUITY PROOF FAILED: caught=1 (need 0)`, exit 1. With the full list: MISSED 1 of 1, exit 0. A suite
# missing from here fails the proof loudly; it does not weaken it quietly.
#
# LambdaSearchSteeringTests.swift is the fourth, added with F-SG1 and listed here in the same commit, and
# demonstrated the same way rather than by analogy: dropped from this list, --prove-vacuity leaves it
# standing, it catches "let the ceiling slip by one percent, on the guard that STEERS the bracket" - the one
# mutation only it catches - and the run reports `VACUITY PROOF FAILED: caught=1 (need 0)`, exit 1. Listed,
# the same mutation goes MISSED 1 of 1, exit 0. Both runs are in the task Log.
#
# BOTH demonstrations above were RE-RUN in the fifth fix pass rather than carried forward. Three of these
# four suites gained tests that round, and "the one mutation only it catches" is a property of the whole set
# of suites, so a proof measured before the files it is about change is a claim and not a measurement. Both
# still reproduce against this tree: dropped -> `VACUITY PROOF FAILED: with no tests present, caught=1
# (need 0) and MISSED=0 of 1`, exit 1; shipped -> `VACUITY PROOF OK: ... caught=0 (need 0) and
# MISSED=1 of 1`, exit 0. The re-run is in the task Log.
#
# BudgetOutcomeTests.swift is the fifth, added in the seventh round with the sixth review's two BudgetOutcome
# findings, and demonstrated the same way rather than by analogy: dropped from this list, --prove-vacuity
# leaves it standing, it catches "the outcome clamps the duration it was handed down to the ceiling" - one
# of the two mutations only this suite catches (the other rounds `extraTime` to a whole second), because no
# other suite constructs an outcome the search could never produce, or one bought at a fraction of a second
# - and the run reports `VACUITY PROOF FAILED: caught=1 (need 0)`, exit 1. Listed, the same mutation goes
# MISSED 1 of 1, exit 0. Both runs are in the task Log.
#
# That this is EVERY such suite is checkable rather than asserted:
# `grep -rln 'LambdaSearch\|BudgetOutcome\|BudgetError' --include=*.swift Sources Tests` returns the three
# subjects and exactly these five files.
TEST_FILES = [ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchBudgetUseTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchRefusalTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchSteeringTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "BudgetOutcomeTests.swift"]

SENTINEL = ROOT / ".artifacts" / "budget-mutation-in-flight"

SENTINEL_MESSAGE = (
    "REFUSING: %s exists, so the previous run was killed while a mutation was on disk.\n"
    "  The subject files may still be mutated. A run starting now would snapshot a MUTATED file\n"
    "  as `pristine`, measure every verdict against it, and restore the mutant afterwards.\n"
    "  Check them - `git diff -- Sources/ScenicKit/Budget/` - restore, then delete the sentinel.\n")


def head_bytes(path: pathlib.Path):
    """The file as COMMITTED at HEAD, or None if git cannot answer for it (no git, no commit, new file)."""
    rel = path.relative_to(ROOT).as_posix()
    try:
        p = subprocess.run(["git", "show", "HEAD:" + rel], cwd=ROOT, capture_output=True)
    except OSError:
        return None
    return p.stdout if p.returncode == 0 else None


def differs_from_head(snapshot) -> list:
    """The subjects in `snapshot` whose bytes are not HEAD's. Takes bytes rather than reading the files, so
    the caller measures exactly what it snapshotted - and so the proof below can exercise this with the bytes
    a mutated file WOULD have, without writing one.

    A path git cannot answer for is not reported: this check exists to catch a corrupted subject, not to
    refuse to run outside a git checkout."""
    out = []
    for f, b in snapshot.items():
        head = head_bytes(f)
        if head is not None and head != b:
            out.append(f)
    return out


def unanswerable(snapshot) -> list:
    """The subjects git could NOT answer for, so `differs_from_head` said nothing either way about them.

    "Not dirty" and "not compared" are different facts, and the run printed the first when it meant the
    second (N-SG2): with git unreachable `differs_from_head` returns [] over a genuinely mutated subject and
    budget.py asserted "subjects match git show HEAD: yes (3 files)". Reporting the difference is this
    function's whole job; refusing is deliberately not, per the docstring above."""
    return [f for f in snapshot if head_bytes(f) is None]


def prove_blind(write, head_line) -> int:
    """`--prove-blind`: demonstrate that the HEAD-comparison SENTENCE knows what it did not compare.

    The defect it is about (N-SG2) was not a wrong verdict but a wrong sentence: the run printed "subjects
    match git show HEAD: yes (3 files)" in an else-branch, and `differs_from_head` returns [] both when the
    subjects match and when git cannot answer at all. The pass condition here is therefore that the two
    states read DIFFERENTLY - identical sentences are the bug - and that the blind one names every file it
    could not compare. In memory: `subprocess.run` is replaced for the length of one call and put back, and
    the sentence is rendered a third time afterwards to show it was."""
    snapshot = {f: f.read_bytes() for f in SUBJECTS}
    with_git = head_line(snapshot)
    real_run = subprocess.run

    def unreachable(*a, **k):
        raise OSError("git is not on PATH (simulated in memory, nothing was executed)")

    try:
        subprocess.run = unreachable
        blind = head_line(snapshot)
    finally:
        subprocess.run = real_run
    restored = head_line(snapshot)

    named = all(f.name in blind for f in SUBJECTS)
    ok = (with_git == "subjects compared with git show HEAD: %d of %d match\n" % (len(SUBJECTS), len(SUBJECTS))
          and "NOT COMPARED" not in with_git
          and "NOT COMPARED" in blind and named and blind != with_git
          and restored == with_git)
    write("with git answering:   %s" % with_git)
    write("with git unreachable: %s" % blind)
    write("after restoring:      %s" % restored)
    write("BLIND PROOF %s: differs=%s, names every uncompared subject=%s, subprocess restored=%s\n"
          "  (the sentence this replaces said `yes (3 files)` in both states, over a subject nothing had\n"
          "   compared with anything)\n"
          % ("OK" if ok else "FAILED", blind != with_git, named, restored == with_git))
    return 0 if ok else 1


def prove_dirty(write) -> int:
    """`--prove-dirty`: demonstrate the HEAD comparison instead of asserting it.

    Deliberately in memory. The check is a byte comparison, so the honest proof feeds it the bytes a mutated
    subject would have; writing a real mutation to a tracked file to prove a check about mutated tracked
    files would open the very window - process killed, mutation left on disk - that this module exists to
    close. The mutation used is the first entry of the real MUTATIONS population rather than a fixture, so
    this cannot drift into proving something about text that no longer appears in the source.

    Also prints whether the subjects on disk match HEAD right now. That is information, not the pass
    condition: a fixer legitimately editing Sources/ must still be able to run this proof."""
    on_disk = {f: f.read_bytes() for f in SUBJECTS}
    unknown = [f.name for f in SUBJECTS if head_bytes(f) is None]
    if unknown:
        write("DIRTY PROOF FAILED: git cannot answer for %s, so the check cannot be demonstrated\n"
              % ", ".join(unknown))
        return 1

    committed = {f: head_bytes(f) for f in SUBJECTS}
    quiet_when_clean = differs_from_head(committed) == []

    name, path, old, new = MUTATIONS[0]
    text = committed[path].decode("utf-8")
    if old not in text:
        write("DIRTY PROOF FAILED: the anchor of %r is not in %s at HEAD\n" % (name, path.name))
        return 1
    mutated = dict(committed)
    mutated[path] = text.replace(old, new, 1).encode("utf-8")
    flags_a_mutant = differs_from_head(mutated) == [path]

    ok = quiet_when_clean and flags_a_mutant
    write("with the committed bytes:      flagged dirty = %s (must be False)\n" % (not quiet_when_clean))
    write("with %r applied:\n  flagged dirty = %s%s\n"
          % (name, flags_a_mutant, ", naming " + path.name if flags_a_mutant else " - NOT SEEN"))
    write("on disk right now: %s\n"
          % ("every subject matches HEAD" if differs_from_head(on_disk) == [] else
             "SUBJECTS DIFFER FROM HEAD - " + ", ".join(f.name for f in differs_from_head(on_disk))))
    write("DIRTY PROOF %s: committed -> accepted=%s, mutated -> refused=%s\n"
          "  (without this check a subject left mutated by a killed hand-run demo is snapshotted as\n"
          "   `pristine` and every verdict below it is measured against the mutant)\n"
          % ("OK" if ok else "FAILED", quiet_when_clean, flags_a_mutant))
    return 0 if ok else 1
