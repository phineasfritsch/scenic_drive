#!/usr/bin/env python3
"""P-PROC-06's assertion: a numeric module ships a mutation population, and no population quietly retires.

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-mutate-population.py
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-mutate-population.py --prove-red

CLAUDE.md, Verification: "A new numeric module (under services/etl/etl/ or Sources/) ships its mutation
population under ops/mutate/ with a literal floor." Until this file nothing read that rule. sinuosity.py
merged through four review rounds without one, assemble.py shipped without one, and T-0170's
Sources/Handoff/StraightLineDistance.swift shipped without one and became T-0199.

THREE QUESTIONS, THREE CONSEQUENCES (T-0186, ruling R4).
  1. Does a module this PR ADDS have a population? `git diff --diff-filter=A` against the merge base with
     origin/main. No population and no allowlist entry -> REFUSE by name, exit 1. This is the gate.
  2. Has a population NARROWED? COVERED_FLOOR is the literal list of the modules some driver declares today.
     A driver that drops a path from SUBJECT_MODULES -> exit 1, even with an empty diff. P-PROC-05's lesson
     one level up: a COUNT of populations reads clean while the one that mattered is gone.
  3. Which EXISTING modules have neither? Printed as DEBT and never red (ruling R4 iii). Making the backlog
     blocking would either stop every unrelated PR or buy a dishonest allowlist entry for score.py.

HOW COVERAGE IS DECLARED (ruling R3). Every population driver carries `SUBJECT_MODULES`, a literal tuple of
repo-relative paths, read here as TEXT - never imported, because importing a driver executes its population.
Before this task the subjects were stated ten different ways and geometry.py stated its three in a DOCSTRING,
which CLAUDE.md forbids a guard from anchoring on. DRIVERS below is a WHITELIST: any other ops/mutate/*.py
with a `__main__` block is a refusal until it is classified, and geometry_probe.py is exempt by name with its
reason rather than declaring geometry.py's subjects - a probe that declared them would keep the coverage
looking intact after geometry.py was deleted, which is the defect this gate exists to catch.

WHAT IT CANNOT DO. It cannot tell a numeric module from a non-numeric one; that reading is in T-0186's Log
and in the reason beside every allowlist entry. It refuses the mechanical shadows of a bad widening: a reason
that is empty, an entry for a module a population covers, an entry for a file that does not exist.

EXITS. 0 every added module is covered or allowlisted and the floor holds. 1 a coverage refusal. 2
fail-closed - a driver or subject missing, an unclassified driver, a malformed allowlist, this pin gone from
PINS.yaml, or a root that matched no module. Never "ok" on something it could not read.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import pathlib
import re
import subprocess
import sys
import tempfile

# The mutation table lives beside this file, not on the caller's sys.path (T-0055's rule for every ops/lib
# entry point): `python ops/lib/check-mutate-population.py` from the repo root must find it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

PIN_ID = "P-PROC-06"
PINS_FILE = "pins/PINS.yaml"
MUTATE_DIR = "ops/mutate"
ALLOWLIST_FILE = "ops/lib/mutate-population-allowlist.json"

# (root, suffix, recursive). Sources/ is BOTH root targets - ScenicKit and Handoff (ruling R2).
MODULE_ROOTS = (("services/etl/etl", ".py", False), ("Sources", ".swift", True))

DRIVERS = ("budget.py", "gates.py", "geometry.py", "guidance.py", "handoff.py", "hazards.py", "retrace.py",
           "routescore.py", "scenic_tags.py", "segmentscore.py")
PROBES = {"geometry_probe.py": "a probe over geometry.py's population; it declares no subject of its own"}

# The literal floor: every module a driver declares today. Losing one is a refusal (ruling R4 ii).
COVERED_FLOOR = (
    "services/etl/etl/proximity.py", "services/etl/etl/scenecheck.py", "services/etl/etl/sinuosity.py",
    "services/etl/etl/snap.py", "services/etl/etl/tagwriter.py",
    "Sources/Handoff/AppleMapsDirections.swift", "Sources/Handoff/HandoffError.swift",
    "Sources/ScenicKit/Budget/BudgetError.swift", "Sources/ScenicKit/Budget/BudgetOutcome.swift",
    "Sources/ScenicKit/Budget/LambdaSearch.swift", "Sources/ScenicKit/Gates/ConsideredTags.swift",
    "Sources/ScenicKit/Gates/GateDecision.swift", "Sources/ScenicKit/Gates/GateReason.swift",
    "Sources/ScenicKit/Gates/Gates.swift", "Sources/ScenicKit/Guidance/GuidanceMapping.swift",
    "Sources/ScenicKit/Guidance/GuidanceSign.swift", "Sources/ScenicKit/Hazards/HazardFlag.swift",
    "Sources/ScenicKit/Hazards/HazardStrip.swift", "Sources/ScenicKit/Loop/RetraceDetector.swift",
    "Sources/ScenicKit/Scoring/RouteScore.swift", "Sources/ScenicKit/Scoring/SegmentScore.swift",
    "Sources/ScenicKit/Scoring/SegmentTerms.swift",
)

DECL_RE = re.compile(r"^SUBJECT_MODULES\s*=\s*\(([^)]*)\)", re.M)
STRING_RE = re.compile(r"[\"']([^\"']+)[\"']")
MAIN_RE = re.compile(r"^if __name__ == [\"']__main__[\"']:", re.M)
PIN_RE = re.compile(r"^-\s+id:\s*%s\s*$" % re.escape(PIN_ID), re.M)

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Refusal(Exception):
    """Something could not be read, or is self-contradictory. Exit 2, never a verdict."""


def _read(root: pathlib.Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8")
    except OSError as exc:
        raise Refusal(f"cannot read {rel}: {exc}") from exc


def modules(root: pathlib.Path) -> list[str]:
    """Every module under the two roots, repo-relative, sorted. An empty root is a refusal."""
    found: list[str] = []
    for rel, suffix, recursive in MODULE_ROOTS:
        base = root / rel
        paths = sorted(base.rglob("*" + suffix) if recursive else base.glob("*" + suffix))
        if not paths:
            raise Refusal(f"{rel} matched no *{suffix} file; an empty root must never read as 'all covered'")
        found.extend(p.relative_to(root).as_posix() for p in paths)
    return sorted(found)


def declared(root: pathlib.Path, known: set[str]) -> dict[str, list[str]]:
    """{driver filename: the modules it declares}. Whitelist-checked; every claim must name a real module."""
    present = sorted(p.name for p in (root / MUTATE_DIR).glob("*.py"))
    if not present:
        raise Refusal(f"{MUTATE_DIR} holds no *.py; the populations this gate reads are gone")
    unclassified = [n for n in present
                    if n not in DRIVERS and n not in PROBES and MAIN_RE.search(_read(root, f"{MUTATE_DIR}/{n}"))]
    if unclassified:
        raise Refusal(f"{MUTATE_DIR}: runnable driver(s) in neither DRIVERS nor PROBES: "
                      f"{', '.join(unclassified)}. Classify a new driver; never ignore one.")
    out: dict[str, list[str]] = {}
    for name in DRIVERS:
        if name not in present:
            raise Refusal(f"{MUTATE_DIR}/{name} is named in DRIVERS and is not there; a population was "
                          f"deleted, or the whitelist is stale")
        match = DECL_RE.search(_read(root, f"{MUTATE_DIR}/{name}"))
        if match is None:
            raise Refusal(f"{MUTATE_DIR}/{name} declares no SUBJECT_MODULES; a population whose subject only "
                          f"a docstring states cannot be read by a gate (T-0186 R3)")
        paths = STRING_RE.findall(match.group(1))
        if not paths:
            raise Refusal(f"{MUTATE_DIR}/{name}: SUBJECT_MODULES is empty")
        unknown = [p for p in paths if p not in known]
        if unknown:
            raise Refusal(f"{MUTATE_DIR}/{name}: SUBJECT_MODULES names {', '.join(unknown)}, which is not a "
                          f"module under {' or '.join(r for r, _, _ in MODULE_ROOTS)}")
        out[name] = paths
    return out


def allowlist(root: pathlib.Path, known: set[str], covered: set[str]) -> dict[str, str]:
    raw = _read(root, ALLOWLIST_FILE)
    try:
        doc = json.loads(raw)
    except ValueError as exc:
        raise Refusal(f"{ALLOWLIST_FILE} is not JSON: {exc}") from exc
    entries = doc.get("modules")
    if not isinstance(entries, dict) or not entries:
        raise Refusal(f"{ALLOWLIST_FILE} has no non-empty `modules` object")
    for path, reason in sorted(entries.items()):
        if not isinstance(reason, str) or not reason.strip():
            raise Refusal(f"{ALLOWLIST_FILE}: `{path}` has no reason. A name with no reason is a silent "
                          f"widening of the allowlist (T-0186 R5)")
        if path in covered:
            raise Refusal(f"{ALLOWLIST_FILE}: `{path}` is allowlisted as computing no number AND is mutated "
                          f"by a population. The two claims contradict; drop one")
        if path not in known:
            raise Refusal(f"{ALLOWLIST_FILE}: `{path}` is not a module in the tree. A stale entry would "
                          f"cover a future file of that name before anyone read it")
    return entries


def added_modules(root: pathlib.Path, known: set[str]) -> list[str]:
    """Modules this branch ADDS against the merge base with main. Refuses rather than guessing."""
    def git(*args: str) -> str:
        proc = subprocess.run(("git", "-C", str(root)) + args, capture_output=True, text=True)
        if proc.returncode != 0:
            raise Refusal(f"git {' '.join(args)}: {proc.stderr.strip() or proc.returncode}")
        return proc.stdout.strip()

    base = ""
    for ref in ("origin/main", "main"):
        with contextlib.suppress(Refusal):
            base = git("merge-base", ref, "HEAD")
            break
    if not base:
        raise Refusal("no merge base with origin/main or main; the added-module set cannot be computed")
    names = git("diff", "--diff-filter=A", "--name-only", base, "HEAD").splitlines()
    return sorted(n.strip() for n in names if n.strip() in known)


def check(root: pathlib.Path, added: list[str] | None = None) -> int:
    if not PIN_RE.search(_read(root, PINS_FILE)):
        raise Refusal(f"{PINS_FILE} has no `- id: {PIN_ID}`: the only thing that runs this check is gone")
    known = set(modules(root))
    decls = declared(root, known)
    covered = {p for paths in decls.values() for p in paths}
    allowed = allowlist(root, known, covered)
    new = added_modules(root, known) if added is None else sorted(n for n in added if n in known)

    print(f"{PIN_ID}: {len(known)} modules, {len(covered)} covered by {len(decls)} populations, "
          f"{len(allowed)} allowlisted, {len(new)} added by this branch")

    lost = [m for m in COVERED_FLOOR if m not in covered]
    if lost:
        print(f"{PIN_ID}: POPULATION FLOOR - module(s) that had a population and no longer do:")
        for m in lost:
            print(f"  {m}")
        print("  A population is not retired by narrowing SUBJECT_MODULES. Restore it, or take the module "
              "out of COVERED_FLOOR in the same commit that removes the mutations, with the reason.")
        return 1

    debt = [m for m in sorted(known) if m not in covered and m not in allowed]
    if debt:
        print(f"  DEBT (informational, never red): {len(debt)} existing module(s) with no population and no "
              f"allowlist entry")
        for m in debt:
            print(f"    {m}")

    naked = [m for m in new if m not in covered and m not in allowed]
    if naked:
        print(f"{PIN_ID}: module(s) added by this branch with no mutation population:")
        for m in naked:
            print(f"  {m}")
        print("  CLAUDE.md, Verification: a new numeric module ships its mutation population under "
              "ops/mutate/ with a literal floor.")
        print(f"  Either add a driver to {MUTATE_DIR} that names it in SUBJECT_MODULES, or - if it computes "
              f"no number reaching score, route or tags - add it to {ALLOWLIST_FILE} with the reason.")
        return 1

    print(f"{PIN_ID}: every added module is covered or allowlisted; the floor of {len(COVERED_FLOOR)} "
          f"holds")
    return 0


# --------------------------------------------------------------------------------- --prove-red

def prove_red(root: pathlib.Path) -> int:
    """Each case is a way this gate stops being a gate. A check never seen red is untested (CLAUDE.md).

    The table is imported HERE rather than at module scope so a missing sibling is this gate's own refusal -
    exit 2 with a sentence - instead of an ImportError traceback out of an ops entry point (T-0087).
    """
    try:
        from mutate_population_red import CASES as RED_CASES
        from mutate_population_red import apply_mutation, build_sandbox, pin_deleted_case
    except ImportError as exc:
        raise Refusal(f"--prove-red: ops/lib/mutate_population_red.py is not importable: {exc}") from exc
    CASES = RED_CASES + (pin_deleted_case(PIN_ID, PINS_FILE),)
    known = modules(root)
    bad = 0
    print(f"{PIN_ID} --prove-red: {len(CASES)} cases against a copy of the tree at {root}")
    print(f"  {'case':<44} {'expect':>6} {'got':>4}  verdict")
    for name, edits, added, expected in CASES:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            build_sandbox(root, tmp, known, (PINS_FILE, ALLOWLIST_FILE), MUTATE_DIR)
            try:
                for kind, target, arg in edits:
                    apply_mutation(tmp, kind, target, arg, ALLOWLIST_FILE)
            except ValueError as exc:
                raise Refusal(f"--prove-red: {exc}") from exc
            sink = io.StringIO()
            with contextlib.redirect_stdout(sink):
                got = main(["--root", str(tmp), "--added", *added])
        ok = got == expected
        bad += 0 if ok else 1
        print(f"  {name:<44} {expected:>6} {got:>4}  {'ok' if ok else 'NOT DISCRIMINATING'}")
    if bad:
        print(f"{PIN_ID} --prove-red: {bad} case(s) did not behave as stated. The check is not a check.")
        return 1
    print(f"{PIN_ID} --prove-red: all {len(CASES)} cases behaved as stated")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ops/lib/check-mutate-population.py", add_help=True)
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="repository root (default: this file's)")
    parser.add_argument("--added", nargs="*", default=None,
                        help="the added-module set, in place of the git diff (used by --prove-red)")
    parser.add_argument("--prove-red", action="store_true", help="run the mutation table and print it")
    args = parser.parse_args(argv)
    root = pathlib.Path(args.root)
    try:
        return prove_red(root) if args.prove_red else check(root, args.added)
    except Refusal as exc:
        print(f"{PIN_ID}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
