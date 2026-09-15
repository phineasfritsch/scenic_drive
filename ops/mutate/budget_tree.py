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

from budget_mutations import MUTATIONS, ROOT, SUBJECTS

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
