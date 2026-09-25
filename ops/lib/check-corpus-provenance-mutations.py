"""The red half of P-DATA-03's corpus check: five defects, each refused BY NAME.

    python ops/lib/check-corpus-provenance-mutations.py
    python ops/lib/check-corpus-provenance.py --prove-red      (the same thing; this is what it runs)

A check that has never been seen red is untested (CLAUDE.md). This table applies each mutation to a COPY of
ops/lib/check-corpus-provenance.py, runs the COPY exactly as pins/PINS.yaml runs the original, and requires
that it exits non-zero AND names the fixture that caught it. Every mutation is a defect somebody could
plausibly write - the limb still runs, it just stops deciding - not a syntax error.

WHY A SEPARATE FILE (T-0219 R9), the shape ops/lib/check-map-attribution-mutations already has. Two reasons,
both mechanical. CLAUDE.md caps a file at 300 lines and the checker's own reasoning fills it. And a table that
QUOTES the code it mutates cannot live inside that code: `source.count(old)` would then count the table's own
copy of the site as well, and two rows here share a site, so the uniqueness guard - the thing that notices
when the table has drifted away from the code - would have to be written around itself.

WHY A COPY and not the tracked file: a driver that mutates the file it is running from leaves the tree
mutated when it is interrupted. The copy is run with cwd=ROOT, which is how the copy's own `_root()` still
finds the repository from a temp directory, and with SCENIC_LA_CORPUS removed from its environment so a
mutant's verdict is decided by the in-process fixtures on every box alike.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def _root() -> Path:
    here = Path(__file__).resolve()
    for base in [*here.parents, Path.cwd().resolve()]:
        if (base / "pins/PINS.yaml").is_file() and (base / "services/etl/etl/corpus.py").is_file():
            return base
    raise SystemExit("check-corpus-provenance-mutations: no repo root above this file or at the cwd")


ROOT = _root()
CHECKER = ROOT / "ops/lib/check-corpus-provenance.py"
CORPUS_ENV = "SCENIC_LA_CORPUS"

# (label, the text replaced in a copy of the checker, its replacement, the fixture that must then be named).
# Mutants 1-3 are the ones T-0219 filed. Mutant 4 is why the `no meta.built_at at all` fixture exists and
# mutant 5 why the future-stamped one does: both survive a population without them (T-0219 R6, R7).
MUTANTS = (
    ("the region comparison deleted",
     'if meta.get("region") != region:',
     'if False:',
     "stamped region 'bay'"),
    ("an absent region key defaults to the expected value (T-0197 B4)",
     'if meta.get("region") != region:',
     'if meta.get("region", region) != region:',
     "no meta.region at all"),
    ("the 30-day comparison flipped",
     'if built < reference - timedelta(days=max_age_days):',
     'if built > reference - timedelta(days=max_age_days):',
     "stamped 40 days ago"),
    ("an absent built_at treated as fresh",
     '        failures.append("meta.built_at is missing (P-DATA-03)")\n    else:',
     '        pass\n    else:',
     "no meta.built_at at all"),
    ("the future-skew limb deleted",
     'elif built > reference + max_future_skew:',
     'elif False:',
     "stamped 2 days in the future"),
)


# The literal floor, in the shape ops/mutate/ populations carry. Without it a table emptied - by a bad merge,
# or by somebody deleting the row that caught them - prints "0/0 mutants refused by name" and exits 0, which
# is a green over nothing (PR #94's shape). Raise it when rows are added; never lower it to make a run pass.
MUTANT_FLOOR = 5


def main() -> int:
    if len(MUTANTS) < MUTANT_FLOOR:
        print(f"P-DATA-03 (corpus half): --prove-red carries {len(MUTANTS)} mutants, below the floor of "
              f"{MUTANT_FLOOR}. A table that has lost rows must never read as 'every mutant refused'.")
        return 1
    if not CHECKER.is_file():
        print(f"P-DATA-03 (corpus half): {CHECKER} is missing; there is nothing to mutate")
        return 1
    source = CHECKER.read_text(encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != CORPUS_ENV}
    failures: list[str] = []
    lines: list[str] = []
    with TemporaryDirectory() as tmp:
        for label, old, new, expected in MUTANTS:
            found = source.count(old)
            if found != 1:
                failures.append(f"{label}: its mutation site occurs {found} times in {CHECKER.name}, not "
                                "exactly once - this table no longer describes the code it claims to mutate")
                continue
            copy = Path(tmp) / "mutant.py"
            copy.write_text(source.replace(old, new), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(copy)], capture_output=True, text=True,
                                  cwd=str(ROOT), env=env)
            out = proc.stdout + proc.stderr
            if proc.returncode == 0:
                failures.append(f"{label}: SURVIVED - the mutated check exited 0")
            elif expected not in out:
                said = out.strip().splitlines()[-1] if out.strip() else "<nothing>"
                failures.append(f"{label}: exited {proc.returncode} but never named {expected!r}; "
                                f"it said: {said}")
            else:
                lines.append(f"  {label}: exit {proc.returncode}, refused naming {expected!r}")

    if failures:
        print(f"P-DATA-03 (corpus half): --prove-red: {len(failures)} of {len(MUTANTS)} mutants not caught:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"P-DATA-03 (corpus half): --prove-red {len(lines)}/{len(MUTANTS)} mutants refused by name:")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
