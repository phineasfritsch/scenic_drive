"""P-PROC-06's mutations: the eight ways ops/lib/check-mutate-population.py stops being a check.

Split off at the 300-line cap along a boundary of meaning rather than at a line number, the way
ops/mutate/budget.py is split from budget_mutations.py: that file is the CHECK, this one is the population
it is run against. Underscores in the name because it is imported; the gate itself keeps the dashed
check-* spelling every other gate under ops/lib/ uses.

Each case is `(name, edits, added, expected_exit)`. An edit is `(kind, target, arg)`:

    rm     delete <target>                     a population file deleted
    add    create an empty <target>            a module added by a branch
    edit   replace arg[0] with arg[1], once    a driver narrowing SUBJECT_MODULES; the pin id deleted
    allow  set allowlist[<target>] = arg       the allowlist widened, or widened with no reason

The sandbox is a copy with only what the gate reads - the drivers, the allowlist, PINS.yaml, and an EMPTY
file per module, because the gate reads module NAMES and never module contents.
"""
from __future__ import annotations

import json
import pathlib
import shutil

NEW_MODULE = "services/etl/etl/newterm.py"
ALLOWED_NEW = "services/etl/etl/terms.py"
GEOMETRY = "ops/mutate/geometry.py"
SINUOSITY = "services/etl/etl/sinuosity.py"

CASES = (
    ("control: the tree as committed", (), [], 0),
    ("a population file deleted (geometry.py)", (("rm", GEOMETRY, ""),), [], 2),
    ("a driver narrows SUBJECT_MODULES", (("edit", GEOMETRY, ('"%s", ' % SINUOSITY, "")),), [], 1),
    ("a new module added with no population", (("add", NEW_MODULE, ""),), [NEW_MODULE], 1),
    ("a new module that IS allowlisted", (), [ALLOWED_NEW], 0),
    ("the allowlist widened to a covered module", (("allow", SINUOSITY, "looks harmless"),), [], 2),
    ("an allowlist entry with no reason", (("allow", "services/etl/etl/fetch.py", "  "),), [], 2),
)


def pin_deleted_case(pin_id: str, pins_file: str) -> tuple:
    """The eighth case: the only thing that runs this gate is its pin, so deleting it must refuse."""
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
