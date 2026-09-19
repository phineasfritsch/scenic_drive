"""P-PROC-06's red harness: the ways ops/lib/check-mutate-population.py stops being a check, and the runner.

Split off at the 300-line cap along a boundary of meaning rather than at a line number, the way
ops/mutate/budget.py is split from budget_mutations.py: that file is the CHECK - what it reads and what it
refuses - and this one is everything that proves it discriminates. Underscores in the name because it is
imported; the gate itself keeps the dashed check-* spelling every other gate under ops/lib/ uses.

TWO POPULATIONS, AND WHY BOTH.

CASES is the SANDBOX population. Each case is `(name, edits, added, expected_exit)`; the added-module set is
passed to the gate with `--added`, so these cases say nothing about how that set is computed. An edit is
`(kind, target, arg)`:

    rm     delete <target>                     a population file deleted
    add    create an empty <target>            a module added by a branch
    edit   replace arg[0] with arg[1], once    a driver narrowing SUBJECT_MODULES; the pin id deleted
    allow  set allowlist[<target>] = arg       the allowlist widened, or widened with no reason

The sandbox is a copy with only what the gate reads - the drivers, the allowlist, PINS.yaml, and an EMPTY
file per module, because the gate reads module NAMES and never module contents.

GIT_CASES is the REAL-GIT population, and it exists because every sandbox case enters through `--added`:
`return []` in `added_modules()` passed all eight of them while the gate stopped seeing anything, and the
same blindness was live in CI - a depth-1 checkout made that arm refuse on every pull request and no case
could say so (T-0186 S2). These three run the gate with NO `--added` at all, against a throwaway
`git clone --no-hardlinks` of the tree under the gitignored .build-mutate-population/ with one real commit on
top: a module added and uncovered (red), the same module added with its allowlist entry (green), and a module
MOVED in from outside the roots, which git calls an R (T-0186 S3).

`run_proof` runs both populations through the gate's OWN shipping entry point, `gate.main`, never a helper.
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import shutil
import subprocess
import tempfile

NEW_MODULE = "services/etl/etl/newterm.py"
ALLOWED_NEW = "services/etl/etl/terms.py"
DEEP_MODULE = "services/etl/etl/sub/deep.py"
GEOMETRY = "ops/mutate/geometry.py"
SINUOSITY = "services/etl/etl/sinuosity.py"
UNMUTATED = "services/etl/etl/score.py"  # a real module, in DEBT, that no population targets

# A population-shaped file OUTSIDE ops/mutate/, and the realistic way a module arrives in a root without
# being added there: written somewhere else, then moved in.
MOVED_FROM = "services/etl/mutate/byway_route_key.py"
MOVED_TO = "services/etl/etl/movedin.py"

CLONE_PARENT = ".build-mutate-population"  # .gitignore's `.build-*/`; removed again at the end of the run
IDENT = ("-c", "user.name=P-PROC-06 prove-red", "-c", "user.email=prove-red@localhost")

CASES = (
    ("control: the tree as committed", (), [], 0),
    ("a population file deleted (geometry.py)", (("rm", GEOMETRY, ""),), [], 2),
    ("a driver narrows SUBJECT_MODULES", (("edit", GEOMETRY, ('"%s", ' % SINUOSITY, "")),), [], 1),
    ("a new module added with no population", (("add", NEW_MODULE, ""),), [NEW_MODULE], 1),
    ("a new module that IS allowlisted", (), [ALLOWED_NEW], 0),
    ("a new module in a SUBPACKAGE of a root", (("add", DEEP_MODULE, ""),), [DEEP_MODULE], 1),
    # The cheap lie S1 closed: one string appended to a driver's tuple, no mutation written anywhere.
    ("a driver DECLARES a module it never mutates",
     (("edit", GEOMETRY, ('SUBJECT_MODULES = ("', 'SUBJECT_MODULES = ("%s", "' % UNMUTATED)),), [], 2),
    ("the allowlist widened to a covered module", (("allow", SINUOSITY, "looks harmless"),), [], 2),
    ("an allowlist entry with no reason", (("allow", "services/etl/etl/fetch.py", "  "),), [], 2),
)


def pin_deleted_case(pin_id: str, pins_file: str) -> tuple:
    """The last sandbox case: the only thing that runs this gate is its pin, so deleting it must refuse."""
    return (f"{pin_id} deleted from PINS.yaml",
            (("edit", pins_file, (f"- id: {pin_id}", "- id: RETIRED")),), [], 2)


def build_sandbox(root: pathlib.Path, tmp: pathlib.Path, known: list[str], copy_files: tuple[str, ...],
                  mutate_dir: str) -> None:
    for rel in copy_files:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, tmp / rel)
    (tmp / mutate_dir).mkdir(parents=True, exist_ok=True)
    for src in sorted((root / mutate_dir).glob("*.py")):
        shutil.copyfile(src, tmp / mutate_dir / src.name)
    for rel in known:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).write_text("", encoding="utf-8")


def apply_mutation(tmp: pathlib.Path, kind: str, target: str, arg, allowlist_file: str) -> None:
    """Raises ValueError on a stale or unknown mutation; the gate turns that into its own refusal."""
    if kind == "rm":
        (tmp / target).unlink()
    elif kind == "add":
        (tmp / target).parent.mkdir(parents=True, exist_ok=True)
        (tmp / target).write_text("", encoding="utf-8")
    elif kind == "edit":
        path = tmp / target
        old, new = arg
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise ValueError(f"`{old}` is not in {target}; the case is stale")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
    elif kind == "allow":
        path = tmp / allowlist_file
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["modules"][target] = arg
        path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    else:
        raise ValueError(f"unknown mutation `{kind}`")


# ------------------------------------------------------------------------------- the real-git population

def _git(cwd: pathlib.Path, *args: str) -> None:
    proc = subprocess.run(("git", "-C", str(cwd)) + args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ValueError(f"git {' '.join(args)} in {cwd}: {proc.stderr.strip() or proc.returncode}")


def _write_module(clone: pathlib.Path, rel: str) -> None:
    (clone / rel).parent.mkdir(parents=True, exist_ok=True)
    # A number, so the module is the kind this rule is about; the gate reads names, not contents.
    (clone / rel).write_text("SCALE = 1.0\n", encoding="utf-8")


def _add_uncovered(clone: pathlib.Path, allowlist_file: str) -> None:
    _write_module(clone, NEW_MODULE)
    _git(clone, "add", "--", NEW_MODULE)


def _add_allowlisted(clone: pathlib.Path, allowlist_file: str) -> None:
    _write_module(clone, NEW_MODULE)
    path = clone / allowlist_file
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["modules"][NEW_MODULE] = "prove-red: a vocabulary table, no number reaching score, route or tags"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    _git(clone, "add", "--", NEW_MODULE, allowlist_file)


def _move_in(clone: pathlib.Path, allowlist_file: str) -> None:
    _git(clone, "mv", MOVED_FROM, MOVED_TO)


GIT_CASES = (
    ("git arm: a module added, uncovered", _add_uncovered, 1),
    ("git arm: a module added WITH its allowlist entry", _add_allowlisted, 0),
    ("git arm: a module MOVED in from outside a root", _move_in, 1),
)


def git_clones(root: pathlib.Path, allowlist_file: str):
    """Yield (name, clone, expected) per real-git case. Each clone is a throwaway with one real commit on
    top of this branch, so the gate computes its own added-module set from `git diff` as it does in CI."""
    parent = root / CLONE_PARENT
    try:
        parent.mkdir(exist_ok=True)
        for name, build, expected in GIT_CASES:
            clone = pathlib.Path(tempfile.mkdtemp(dir=str(parent))) / "clone"
            proc = subprocess.run(("git", "clone", "--no-hardlinks", "--quiet", str(root), str(clone)),
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                raise ValueError(f"git clone of {root}: {proc.stderr.strip() or proc.returncode}")
            build(clone, allowlist_file)
            _git(clone, *IDENT, "commit", "--no-verify", "--quiet", "-m", f"prove-red: {name}")
            yield name, clone, expected
    finally:
        shutil.rmtree(parent, ignore_errors=True)


# ------------------------------------------------------------------------------------------- the runner

def _run(gate, *argv: str) -> int:
    """The gate's shipping entry point, stdout swallowed. Never a helper, never a copy of its logic."""
    with contextlib.redirect_stdout(io.StringIO()):
        return gate.main(list(argv))


def run_proof(root: pathlib.Path, gate) -> int:
    sandbox = CASES + (pin_deleted_case(gate.PIN_ID, gate.PINS_FILE),)
    known = gate.modules(root)
    rows: list[tuple[str, int, int]] = []
    print(f"{gate.PIN_ID} --prove-red: {len(sandbox)} sandbox + {len(GIT_CASES)} real-git cases at {root}")
    print(f"  {'case':<48} {'expect':>6} {'got':>4}  verdict")
    try:
        for name, edits, added, expected in sandbox:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp = pathlib.Path(tmpdir)
                build_sandbox(root, tmp, known, (gate.PINS_FILE, gate.ALLOWLIST_FILE), gate.MUTATE_DIR)
                for kind, target, arg in edits:
                    apply_mutation(tmp, kind, target, arg, gate.ALLOWLIST_FILE)
                rows.append((name, expected, _run(gate, "--root", str(tmp), "--added", *added)))
        for name, clone, expected in git_clones(root, gate.ALLOWLIST_FILE):
            rows.append((name, expected, _run(gate, "--root", str(clone))))
    except ValueError as exc:
        raise gate.Refusal(f"--prove-red: {exc}") from exc
    bad = 0
    for name, expected, got in rows:
        ok = got == expected
        bad += 0 if ok else 1
        print(f"  {name:<48} {expected:>6} {got:>4}  {'ok' if ok else 'NOT DISCRIMINATING'}")
    if bad:
        print(f"{gate.PIN_ID} --prove-red: {bad} case(s) did not behave as stated. The check is not a check.")
        return 1
    print(f"{gate.PIN_ID} --prove-red: all {len(rows)} cases behaved as stated")
    return 0
