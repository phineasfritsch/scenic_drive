"""Mutation coverage for the curvature oracle's two modules.

WHY THIS EXISTS. T-0025, T-0069 and T-0074 each closed the routes they were shown and were beaten by the next
variant of the same idea. T-0074 closed seven and an adversary executed ten more that pass - the same size
dodge one power of two up, the refusal keyed on a directory instead of a size, the partial read at a bigger
block. The list does not terminate, so a test per route is the wrong shape. A mutation run answers the whole
class at once, and keeps answering it for mutations nobody has thought of.

WHY NOT mutmut OR cosmic-ray, which the brief names. Both are real tools and either would work. Neither is
pinned in `services/etl/inputs/manifest.yaml`, the ETL's whole discipline is that every input is pinned and
digest-verified, and the numbers this repo trusts are the ones produced inside the pinned `scenic-etl` image.
Adding an unpinned dependency to produce a trust signal is the wrong trade, and a framework nobody here can
audit is a poor fit for a repository whose founding premise is that checks lie. This harness is ~200 lines of
stdlib `ast`, it enumerates its mutations explicitly, and it runs anywhere the suite runs.

WHAT A SURVIVOR MEANS. A mutant that the suite does not kill is a change to the module that no test objects
to. It is not automatically a defect - some mutations are genuinely equivalent - but every one of the ten
evasions that beat T-0074 is in this file's rule set, so a survivor is where the next adversary will go.

    ops/etl-mutation                  both modules
    ops/etl-mutation --module etl/oracle_select.py
    ops/etl-mutation --list           enumerate mutants without running anything

The rules live in ops/lib/etl_mutation_rules.py, split out because they change for a different reason: that
file grows when somebody finds a new shape of evasion, this one when the way a run is judged changes. It is
audited there against the ten evasions that beat T-0074, and says which one it deliberately does not model.
"""
import argparse
import ast
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from etl_mutation_rules import mutants_for   # noqa: E402  (sys.path set immediately above)

ROOT = pathlib.Path(__file__).resolve().parents[2]
ETL = ROOT / "services" / "etl"
DEFAULT_MODULES = ["etl/oracle.py", "etl/oracle_select.py"]

# A survivor budget, not a target. It exists so this can gate without pretending the number is zero today:
# raise the bar by LOWERING it, never by loosening a rule. `.githooks/commit-msg` guards MAX_* bindings.
MAX_SURVIVORS = 37    # measured 2026-09-08: 149 killed, 37 survived, of 186. Lower it as tests land;
                      # never raise it. `.githooks/commit-msg` guards MAX_* bindings (T-0079).
                      #   117/69  T-0081, the first measurement
                      #   121/65  T-0088 gap 2, the emitted record's shape
                      #   149/37  T-0088 gap 1, main() and the cap/seed defaults


# ----------------------------------------------------------------------------- the run
def dirty(rels):
    """Modules git does not consider clean. None when git cannot answer, which is refused, not assumed.

    A killed run leaves a module mutated on disk. The baseline check usually catches that - a mutated module
    normally fails the suite - but an EQUIVALENT mutation leaves the suite green, so the baseline passes and
    every result after it is computed against a module nobody meant to change. Asking git puts the evidence
    outside the loop.
    """
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", *[f"services/etl/{x}" for x in rels]],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return [l[3:].strip() for l in r.stdout.splitlines() if l.strip()]


def run_suite(py):
    r = subprocess.run([py, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", "-o", "addopts="],
                       cwd=ETL, capture_output=True, text=True, timeout=900)
    return r.returncode == 0     # True = suite PASSED = the mutant SURVIVED


LOCK = None


def take_lock():
    """One run at a time. Returns False when another holds it.

    Earned, not anticipated: a run whose stdout pipe closed kept going invisibly while a second run started,
    and the two rewrote the same two modules in place at the same time. The clean-tree guard then refused the
    second - correctly, but for the wrong reason, and the tree was left holding a comment-stripped module
    (`ast.unparse` does not preserve comments, so an interrupted run leaves more damage than one flipped
    operator).
    """
    global LOCK
    LOCK = ROOT / ".artifacts" / "etl-mutation.lock"
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        holder = LOCK.read_text(encoding="utf-8").strip() or "?"
        print(f"MUTATION FAIL: another run holds {LOCK.relative_to(ROOT).as_posix()} (pid {holder}).")
        print("  Two runs rewrite the same modules in place and corrupt each other. If that pid is gone,")
        print("  delete the file and check `git status` on services/etl/etl/ before starting.")
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


def main(argv):
    ap = argparse.ArgumentParser(prog="ops/etl-mutation")
    ap.add_argument("--module", action="append", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N mutants (for a quick sample)")
    a = ap.parse_args(argv)
    py = sys.executable
    modules = a.module or DEFAULT_MODULES

    total = 0
    plan = []
    for rel in modules:
        p = ETL / rel
        if not p.is_file():
            print(f"MUTATION FAIL: {rel} does not exist under {ETL}")
            return 2
        src, muts = mutants_for(p)
        plan.append((rel, p, src, muts))
        total += len(muts)

    if total == 0:
        # The vacuity guard. A run that generated no mutants must never read as a clean run - that is the
        # failure this whole repository exists to contradict, and it would arrive here as "0 survivors".
        print("MUTATION FAIL: no mutants generated - the rules matched nothing, so nothing was tested")
        return 2

    if a.list:
        for rel, _p, _s, muts in plan:
            for line, rule, desc, _m in muts:
                print(f"{rel}:{line}  {rule:9s} {desc}")
        print(f"MUTANTS {total}")
        return 0

    # Clean first, THEN baseline. A killed previous run can leave an equivalent mutation on disk, which the
    # baseline would happily pass - so the cheap question that git can answer comes before the expensive one
    # the suite answers about itself.
    if not take_lock():
        return 2
    try:
        return _run(py, modules, plan, a)
    finally:
        drop_lock()


def _run(py, modules, plan, a):
    d = dirty(modules)
    if d is None:
        print("MUTATION FAIL: git cannot say whether the modules are clean, so a leftover mutation from a")
        print("  killed run could not be ruled out. Refusing rather than reporting numbers about a tree of")
        print("  unknown provenance.")
        return 2
    if d:
        print("MUTATION FAIL: these modules are not clean, and this harness rewrites them in place:")
        for x in d:
            print(f"    {x}")
        print("  Commit or restore them first. A killed run leaves a mutant on disk, and an equivalent one")
        print("  passes the baseline below without anyone noticing.")
        return 2

    # The suite must pass BEFORE any mutation, or every mutant reads as killed and the run means nothing.
    print("baseline: ", end="", flush=True)
    if not run_suite(py):
        print("FAIL")
        print("MUTATION FAIL: the suite does not pass unmutated, so no mutant result can be trusted")
        return 2
    print("suite passes")

    survivors, killed, n = [], 0, 0
    t0 = time.time()
    for rel, path, src, muts in plan:
        original = src
        for line, rule, desc, mutate in muts:
            if a.limit and n >= a.limit:
                break
            n += 1
            tree = ast.parse(original)
            if not mutate(tree):
                continue
            try:
                mutated = ast.unparse(ast.fix_missing_locations(tree))
            except Exception as e:
                print(f"  {rel}:{line} {rule}: could not unparse ({type(e).__name__}); skipped")
                continue
            path.write_text(mutated, encoding="utf-8", newline="\n")
            try:
                lived = run_suite(py)
            finally:
                path.write_text(original, encoding="utf-8", newline="\n")
            if lived:
                survivors.append((rel, line, rule, desc))
                print(f"  SURVIVED  {rel}:{line}  {rule:9s} {desc}")
            else:
                killed += 1
        if a.limit and n >= a.limit:
            break

    secs = int(time.time() - t0)
    print()
    print(f"MUTATION {killed} killed, {len(survivors)} survived, of {n} run in {secs}s")
    if survivors:
        print("  A survivor is a change to the module that no test objects to. Some are genuinely equivalent;")
        print("  every evasion that beat T-0074 is one of the rules above, so this is where the next one goes.")
    if len(survivors) > MAX_SURVIVORS:
        print(f"  ABOVE THE BUDGET of {MAX_SURVIVORS} - raise the bar by lowering it, never by loosening a rule.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
