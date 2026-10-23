#!/usr/bin/env python3
"""Mutation coverage for pins/PINS.yaml: inject each pin's own violation and require the assertion to go RED.

  ops/pins-mutation [--pin P-SRC-01]... [--list] [--keep] [--verbose]

WHY THIS EXISTS. T-0072's `vacuous()` refuses `assertion: "true"` and accepts `assertion: "true || false"` -
two more characters, exit 0, and a green line that reproduces byte for byte with a banned `import CoreLocation`
in Sources/ (28 of 32 cannot-fail shapes were accepted when table-tested through the module). Nor does the
route end at vacuity: drop one alternative from P-SRC-01's regex - `(CoreLocation|MapKit|...)` -> `(MapKit|...)`
- and what is left is a genuine grep that can fail, still runs, still counts toward MIN_RAN, and no longer
catches the import it was written for. No property of the assertion's TEXT separates those, so the question is
empirical: break what the pin's `statement` names, see whether it notices. `vacuous()` stays where it exists -
cheap, on every push, catches the careless shapes. This is the second and stronger gate, not a replacement.

WHY A SEPARATE ENTRY POINT rather than `ops/check-pins --mutate`: check-pins runs on every push and in every
agent preflight and must never write to the tree it checks; an injecting mode one typo away from that is the
wrong blast radius. `ops/etl-mutation` (T-0081) is the precedent - stdlib only, explicit mutations, clean-tree
guard, O_EXCL lock. No mutmut, no cosmic-ray: unpinned dependencies are refused here.

WHERE IT RUNS. Never in the caller's checkout: a throwaway `git worktree` from HEAD (queue/README.md step 8)
takes every injection and is proven clean again after each case - a dirty demo tree aborts the run rather than
produce numbers about a tree of unknown provenance. A SURVIVOR = the assertion stayed green while the property
its own statement claims was false. That pin is dead whatever its text says.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pins                                          # noqa: E402  (sys.path set immediately above)
from pins_mutation_cases import CASES, NoOp          # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

# Floors. A run that injected nothing must FAIL, not report that every pin is healthy - the same vacuity rule
# the pins themselves live under. Measured 2026-09-08 on this tree: 9 runnable pins, 29 injections, 27 of them
# must-kill and 2 filed gaps. Ratchets: raise them when cases are added, never lower one without a reason.
MIN_CASES = 29
MIN_KILLS = 27
MIN_PINS_MUTATED = 9


def sh(args, cwd, timeout=1800):
    return subprocess.run([str(a) for a in args], cwd=str(cwd), capture_output=True, text=True, timeout=timeout)


def porcelain(root):
    """The tracked+untracked delta, or None when git could not answer - which is refused, never assumed clean."""
    r = sh(["git", "status", "--porcelain"], root)
    return None if r.returncode else [x for x in r.stdout.splitlines() if x.strip()]


def runnable(p, tier):
    """The pins this runner is answerable for: an assertion that exists and executes on this tier."""
    runs_on = p.get("runs_on") or []
    runs_on = [runs_on] if isinstance(runs_on, str) else runs_on
    a = p.get("assertion")
    why = []
    if p.get("pending"):
        why.append(f"pending on {p['pending']}, so there is no assertion to make red yet")
    if not a or str(a).strip().upper() == "TODO":
        why.append("assertion is TODO/empty, which check-pins already fails")
    if tier not in runs_on:
        why.append(f"runs_on {runs_on} excludes this tier - a human or a device answers it, not a worktree")
    return not why, "; ".join(why)


def gap_ok(task_id):
    """An exemption must point at a live ticket. Missing or already done => the exemption is a lie."""
    state = pins.task_state(task_id)
    if state is None:
        return f"gap_task {task_id} does not exist in queue/"
    return f"gap_task {task_id} is done - close the gap and promote this case" if state == "done" else None


# ----------------------------------------------------------------------------- worktree
def make_worktree():
    path = ROOT.parent / f"demo-pins-mutation-{os.getpid()}"
    branch = f"tmp/demo-pins-mutation-{os.getpid()}"
    r = sh(["git", "worktree", "add", "--quiet", str(path), "-b", branch, "HEAD"], ROOT)
    if r.returncode != 0:
        print(f"MUTATION FAIL: could not create the demo worktree at {path}")
        print("  " + (r.stdout + r.stderr).strip()[:400])
        return None, None
    return path, branch


def drop_worktree(path, branch, keep):
    if keep:
        print(f"  kept {path} (branch {branch}) - remove with: git worktree remove --force {path}")
        return
    sh(["git", "worktree", "remove", "--force", str(path)], ROOT)
    sh(["git", "branch", "-D", branch], ROOT)


LOCK = None


def take_lock():
    """One run at a time: two runs would create worktrees from the same HEAD and fight over the same branch
    names only by luck of the pid. Same reason ops/etl-mutation holds one."""
    global LOCK
    LOCK = ROOT / ".artifacts" / "pins-mutation.lock"
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(f"MUTATION FAIL: another run holds {LOCK.relative_to(ROOT).as_posix()} "
              f"(pid {LOCK.read_text(encoding='utf-8').strip() or '?'}).")
        print("  If that pid is gone, delete the file and check `git worktree list` for a leftover demo tree.")
        LOCK = None
        return False
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return True


def drop_lock():
    if LOCK is not None:
        try:
            LOCK.unlink()
        except OSError:
            pass


# ----------------------------------------------------------------------------- the run
def main(argv):
    want, listing, keep, verbose = [], False, False, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--pin" and i + 1 < len(argv):
            want.append(argv[i + 1])
            i += 2
            continue
        if a == "--list":
            listing = True
        elif a == "--keep":
            keep = True
        elif a == "--verbose":
            verbose = True
        else:
            print(f"MUTATION FAIL: bad argument {a!r}; accepted: --pin <id>, --list, --keep, --verbose")
            return 2
        i += 1

    cases = [c for c in CASES if not want or c["pin"] in want]
    if listing:
        for c in cases:
            print(f"{c['pin']:10s} {c['expect']:4s} {c['name']}")
        print(f"CASES {len(cases)}")
        return 0
    if not cases:
        print(f"MUTATION FAIL: {'no case matches --pin ' + str(want) if want else '0 injections are defined'}"
              " - a run that mutates nothing is not a pass, it is a run that proved nothing")
        return 2

    if not pins.PINS.exists():
        print(f"MUTATION FAIL: {pins.PINS} missing")
        return 2
    dirt = porcelain(ROOT)
    if dirt is None:
        print("MUTATION FAIL: git cannot report the working tree state; refusing to guess")
        return 2
    if dirt:
        print("MUTATION FAIL: the working tree is not clean, and the demo worktree is created from HEAD, so")
        print("  uncommitted work would NOT be what got tested. Commit first. Dirty:")
        print("    " + "\n    ".join(dirt[:20]))
        return 2
    if not take_lock():
        return 2
    try:
        return run(cases, want, keep, verbose)
    finally:
        drop_lock()


def coverage(pinlist, cases, want):
    """Every pin this runner is answerable for must be covered or explained. A silent gap is the defect."""
    problems, notes = [], []
    tier = pins.host_tier()
    ids = {p.get("id") for p in pinlist}
    covered = {c["pin"] for c in cases if c["expect"] == "red"}
    for c in cases:
        if c["pin"] not in ids:
            problems.append(f"case {c['pin']}/{c['name']}: no such pin in PINS.yaml - a stale case is a lie")
        if c["expect"] == "gap":
            why = gap_ok(c["gap_task"])
            if why:
                problems.append(f"case {c['pin']}/{c['name']}: {why}")
    mutable = 0
    for p in pinlist:
        pid = p.get("id")
        can, why = runnable(p, tier)
        if not can:
            notes.append(f"{pid}: not modelled - {why}")
            continue
        mutable += 1
        if want and pid not in want:
            continue
        if pid not in covered:
            problems.append(f"{pid}: runs here but has NO injection - write one in pins_mutation_cases.py")
    return problems, notes, mutable


def run(cases, want, keep, verbose):
    pinlist = pins.load(pins.PINS)
    by_id = {p.get("id"): p for p in pinlist}
    problems, notes, mutable = coverage(pinlist, cases, want)
    path, branch = make_worktree()
    if path is None:
        return 2
    try:
        killed, ran, survived, errors, promote = 0, 0, [], [], []
        for pid in sorted({c["pin"] for c in cases}):
            if pid not in by_id:
                continue
            assertion = str(by_id[pid]["assertion"])
            good, out = pins.run(assertion, cwd=path)
            if not good:
                print(f"MUTATION FAIL: {pid} is already RED in a clean worktree of HEAD, so nothing this run")
                print("  could say about it would mean anything. Fix `ops/check-pins` first.")
                print(f"    {out[:400]}")
                return 2
            if verbose:
                print(f"  baseline {pid}: green")
            for c in [x for x in cases if x["pin"] == pid]:
                try:
                    revert = c["apply"](path)
                except NoOp as e:
                    errors.append(f"{pid} {c['name']}: injection did nothing - {e}")
                    continue
                try:
                    changed = porcelain(path)
                    if not changed:
                        errors.append(f"{pid} {c['name']}: injection left the tree byte-identical")
                        continue
                    ran += 1
                    still_green, _ = pins.run(assertion, cwd=path)
                finally:
                    revert()
                left = porcelain(path)
                if left:
                    print(f"MUTATION FAIL: {pid} {c['name']} did not revert cleanly; the worktree is kept at")
                    print(f"  {path} so nothing is destroyed. Leftover: {left[:5]}")
                    keep = True
                    return 2
                if c["expect"] == "gap":
                    if still_green:
                        print(f"  GAP       {pid}  {c['name']}  (survives; {c['gap_task']} owns it)")
                    else:
                        promote.append(f"{pid} {c['name']}: killed, but is exempted as a gap owned by "
                                       f"{c['gap_task']} - promote it to expect=\"red\" and delete the exemption")
                elif still_green:
                    survived.append(f"{pid} {c['name']}  (violates: {c['clause']})")
                    print(f"  SURVIVED  {pid}  {c['name']}")
                else:
                    killed += 1
                    if verbose:
                        print(f"  killed    {pid}  {c['name']}")
    finally:
        drop_worktree(path, branch, keep)

    return report(cases, ran, killed, survived, errors, promote, problems, notes, mutable, want)


def report(cases, ran, killed, survived, errors, promote, problems, notes, mutable, want):
    covered = len({c["pin"] for c in cases if c["expect"] == "red"})
    gaps = len([c for c in cases if c["expect"] == "gap"])
    print(f"PINS-MUTATION mutable={mutable} covered={covered} cases={ran} killed={killed} "
          f"survived={len(survived)} gaps={gaps} errors={len(errors)} tier={pins.host_tier()}"
          f"{' FILTERED' if want else ''}")
    for s in survived:
        print(f" - SURVIVED {s}\n   The assertion stayed green while the statement it makes was false.")
    for e in errors:
        print(f" - ERROR {e}")
    for p in promote:
        print(f" - PROMOTE {p}")
    for p in problems:
        print(f" - {p}")
    for n in notes:
        print(f"   not modelled: {n}")
    bad = bool(survived or errors or promote or problems)
    if want:
        print("   --pin was given, so the floors were NOT applied: this run is a probe, not the gate.")
    else:
        if ran == 0:
            print(" - VACUOUS: 0 injections ran. A mutation run that mutated nothing is not a healthy pin set.")
            bad = True
        for name, got, floor in (("cases", ran, MIN_CASES), ("kills", killed, MIN_KILLS),
                                 ("pins covered", covered, MIN_PINS_MUTATED)):
            if got < floor:
                print(f" - FLOOR: {name} {got} < {floor}; raise this bar, never lower it to fit a lost case")
                bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
