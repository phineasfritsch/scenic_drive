#!/usr/bin/env python3
"""Mutation harness for the queue state machine that ops/lib/check-lock-lifecycle guards.

SUBJECT   ops/lib/queue.py - cmd_claim, cmd_review, _would_duplicate_on_merge.
CHECK     ops/lib/check-lock-lifecycle. A catch requires a NAMED case to fail, i.e. a line matching
          FAIL_LINE below, which is what its `bad()` prints. A non-zero exit with no such line is a TRAP.

WHY THIS FILE EXISTS. reviewer-pr79 built a throwaway mutation harness against this same subject and found
that of three mutations, one - deleting the merge rehearsal outright (`_would_duplicate_on_merge` ->
`return []`) - produced output BYTE-IDENTICAL to baseline, and that baseline, the caught mutants and the
missed one all exited 1, so the exit code carried no signal at all. Both are fixed on this branch; this
harness is what stops either from silently reopening.

THE PASS CONDITION IS `caught == len(MUTATIONS)`, FULL STOP. Every other harness in this repository shipped

    return 0 if caught + len(trapped) == len(MUTATIONS) and not wrongly_caught else 1

which counts `trapped` - the harness's own name for "non-zero exit with NO named test failing" - toward
passing. Demonstrated consequence: break a harness's own FAIL_LINE regex with the subject pristine and every
mutation scores trapped and the run exits 0, so the harness cannot tell "the subject is covered" from "I am
broken". The corrected contract, from ops/mutate/guidance.py on task/T-0129, is followed here:

  * trapped, compile-only and skipped each FAIL the run. A trap is a real detection but not by an assertion.
  * --prove-vacuity requires `caught == 0` AND `missed == len(MUTATIONS)`. Requiring only caught == 0 is also
    satisfied by a harness broken in the compile-only direction.
  * the EQUIVALENT arm requires its mutants to go MISSED specifically, not merely "not caught".
  * SKIP is its own bucket, never folded into MISSED. A stale anchor is the opposite of a missed mutation.

Anchored on identifiers and on statements in the subject, never on a comment.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SUBJECT = ROOT / "ops" / "lib" / "queue.py"
CHECK = ROOT / "ops" / "lib" / "check-lock-lifecycle"

# The vacuity stub: a check that names no case and objects to nothing. Every mutation must then go MISSED.
EMPTY_CHECK = ("#!/usr/bin/env bash\n"
               "# vacuity stub - asserts nothing\n"
               "echo 'LOCK LIFECYCLE OK'\n"
               "exit 0\n")

MUTATIONS = [
    # --- the lock, which is what the check is named for --------------------------------------------------
    ("claim does not write the lock file", SUBJECT,
     '        for res in fm.get("exclusive") or []:\n'
     '            (LOCKS / f"{res}.lock").write_text(f"{tid} {owner} {iso(t)}\\n", encoding="utf-8", newline="\\n")',
     '        for res in []:\n'
     '            (LOCKS / f"{res}.lock").write_text(f"{tid} {owner} {iso(t)}\\n", encoding="utf-8", newline="\\n")'),

    ("review moves the task but never releases the lock", SUBJECT,
     "        for _, lock in mine:\n            lock.unlink()",
     "        for _, lock in mine:\n            pass"),

    ("a lock held by another task is released along with our own", SUBJECT,
     "            if holder.split()[:1] == [tid]:\n"
     "                mine.append((res, lock))\n"
     "            else:\n"
     '                foreign.append(f"{res} (held by {holder})")',
     "            if True:\n"
     "                mine.append((res, lock))\n"
     "            else:\n"
     '                foreign.append(f"{res} (held by {holder})")'),

    # --- who may grade the work --------------------------------------------------------------------------
    ("reviewer == owner is accepted", SUBJECT,
     "        if reviewer == owner:\n"
     '            print(f"reviewer {reviewer_raw} is also the owner of {tid} - a worker may not grade its own work")',
     "        if reviewer == owner and False:\n"
     '            print(f"reviewer {reviewer_raw} is also the owner of {tid} - a worker may not grade its own work")'),

    ("review accepts a task that is not in claimed/", SUBJECT,
     '        if state != "claimed":\n            print(f"{tid} is in {state}/, not claimed/")',
     '        if state not in ("claimed", "done"):\n            print(f"{tid} is in {state}/, not claimed/")'),

    # --- the merge rehearsal. THE FIRST OF THESE IS reviewer-pr79's M2, which was MISSED before this branch.
    ("the merge rehearsal is deleted outright (return [])", SUBJECT,
     "    ref = _main_ref()\n    if ref is None:\n        return None",
     "    ref = _main_ref()\n    return []"),

    # The trap the subject's own docstring names: "Asking 'does the path exist' answers yes and misses the
    # defect". The branch DID write a file at main's path, so a working-tree test says "no duplicate" while
    # git keeps both copies on merge.
    ("the rehearsal asks whether the path exists instead of whether this branch can delete it", SUBJECT,
     '        reachable, _ = _git("merge-base", "--is-ancestor", commit, "HEAD")\n'
     "        if not reachable:\n"
     "            bad.append(path)",
     "        if not (ROOT / path).exists():\n"
     "            bad.append(path)"),

    ("'git cannot answer' is read as 'no duplicate' instead of being refused", SUBJECT,
     "        dup = _would_duplicate_on_merge(tid)\n        if dup is None:",
     "        dup = _would_duplicate_on_merge(tid) or []\n        if dup is None:"),

    # Exists to prove case 3's RESIDUAL assertion is load-bearing rather than decorative. That case no longer
    # demands a bare `QUEUE OK` - it demands that every problem cmd_check reports be gone except the
    # MIN_TASKS floor - and this is the mutation that leaves a new one: the task ends up in claimed/ AND
    # review/ at once. Nothing else in this set is caught by that assertion, so without it the change to
    # case 3 would be untested.
    ("review writes the task to review/ without removing the claimed/ copy", SUBJECT,
     '        dest = Q / "review" / p.name\n'
     '        dest.write_text(dump(fm, body), encoding="utf-8", newline="\\n")\n'
     "        p.unlink()",
     '        dest = Q / "review" / p.name\n'
     '        dest.write_text(dump(fm, body), encoding="utf-8", newline="\\n")'),
]

# Cannot change behaviour. Anything but MISSED here means a case has an opinion about how the subject is
# WRITTEN rather than about what it does.
EQUIVALENT = [
    ("rename the comprehension variable in the rehearsal's loop", SUBJECT,
     "    for path in (l.strip() for l in out.splitlines()):",
     "    for path in (line.strip() for line in out.splitlines()):"),

    ("split a tuple assignment into two statements", SUBJECT,
     "        mine, foreign = [], []",
     "        mine = []\n        foreign = []"),
]

FAIL_LINE = re.compile(r"^FAIL: ", re.M)


def compiles(path: pathlib.Path) -> bool:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        return True
    except SyntaxError:
        return False


def run_check():
    env = dict(os.environ)
    env.setdefault("PYTHON", sys.executable)
    p = subprocess.run(["bash", str(CHECK)], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    return p.returncode, (p.stdout + p.stderr)


def run_all(pristine, mutations):
    """A verdict per mutation. SKIP is its own bucket: a mutation that did not land says the harness is
    stale, which is the opposite of what MISSED says."""
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    for name, path, old, new in mutations:
        text = pristine[path].decode("utf-8")
        if old not in text:
            sys.stdout.write("SKIP        %-70s anchor not found - harness is stale\n" % name)
            out["skipped"].append(name)
            continue
        code = -1
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if path.read_bytes() == pristine[path]:
                sys.stdout.write("SKIP        %-70s mutation did not land\n" % name)
                out["skipped"].append(name)
                continue
            if not compiles(path):
                verdict = "compile_only"
            else:
                code, txt = run_check()
                verdict = "caught" if FAIL_LINE.search(txt) else ("trapped" if code != 0 else "missed")
        finally:
            path.write_bytes(pristine[path])
        out[verdict].append(name)
        label = {"caught": "caught", "trapped": "trapped", "compile_only": "compile-only",
                 "missed": "MISSED", "skipped": "SKIP"}
        note = {"caught": "a named case printed FAIL:  exit=%d" % code,
                "trapped": "non-zero exit, but NO named case failed - does not count",
                "compile_only": "a fact about Python, not about this check - does not count",
                "missed": "exit=0  no case objected"}
        sys.stdout.write("%-12s%-70s %s\n" % (label[verdict], name, note[verdict]))
    return out


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = {SUBJECT: SUBJECT.read_bytes()}
    pristine_check = CHECK.read_bytes()
    sys.stdout.write("pristine %-24s md5 %s\n" % (SUBJECT.name, hashlib.md5(pristine[SUBJECT]).hexdigest()))
    sys.stdout.write("pristine %-24s md5 %s\n" % (CHECK.name, hashlib.md5(pristine_check).hexdigest()))

    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: the check is replaced by a stub that asserts nothing, so\n"
                             "every mutation must report MISSED - not merely 'not caught'.\n")
            CHECK.write_text(EMPTY_CHECK, encoding="utf-8", newline="\n")

        code, txt = run_check()
        sys.stdout.write("BASELINE%-74s exit=%d\n" % ("", code))
        if code != 0 or FAIL_LINE.search(txt):
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            sys.stdout.write(txt)
            return 2

        r = run_all(pristine, MUTATIONS)

        if not prove:
            sys.stdout.write("\nEQUIVALENT MUTANTS - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            eq = run_all(pristine, EQUIVALENT)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        CHECK.write_bytes(pristine_check)

    if SUBJECT.read_bytes() != pristine[SUBJECT] or CHECK.read_bytes() != pristine_check:
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2
    sys.stdout.write("\nrestored: %s %s\n" % (hashlib.md5(SUBJECT.read_bytes()).hexdigest()[:8],
                                              hashlib.md5(CHECK.read_bytes()).hexdigest()[:8]))

    sys.stdout.write("caught by a named case: %d of %d   (trapped %d, compile-only %d, MISSED %d, skipped %d)\n"
                     % (len(r["caught"]), len(MUTATIONS), len(r["trapped"]), len(r["compile_only"]),
                        len(r["missed"]), len(r["skipped"])))
    for bucket, why in (("trapped", "detected, but by a crash and not an assertion - DOES NOT COUNT"),
                        ("compile_only", "a compile failure is not a check catching anything - DOES NOT COUNT"),
                        ("missed", "no case objected"),
                        ("skipped", "anchor missing - the harness is stale")):
        for n in r[bucket]:
            sys.stdout.write("  %s: %s (%s)\n" % (bucket.upper(), n, why))

    if prove:
        ok = len(r["caught"]) == 0 and len(r["missed"]) == len(MUTATIONS)
        sys.stdout.write("VACUITY PROOF %s: with a stub check, caught=%d (need 0) and MISSED=%d of %d\n"
                         "  (requiring MISSED to be complete, not just caught==0, is what stops a harness\n"
                         "   broken in the compile-only direction from proving its own non-vacuity)\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(r["missed"]), len(MUTATIONS)))
        return 0 if ok else 1

    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
