"""The red half of P-DATA-03's TILES check: six defects in the shipping checker, each refused BY NAME.

    python ops/lib/check-pmtiles-provenance-mutations.py
    python ops/lib/check-pmtiles-provenance.py --prove-red      (the same thing; this is what it runs)

A check that has never been seen red is untested (CLAUDE.md). Until T-0233 the tiles half had no table at all
(T-0233 R9). Each row applies one mutation to a COPY of services/tiles/check_pmtiles.py - the shipping
decision build-la.sh step 6 and ops/publish-tiles run - then runs a COPY of ops/lib/check-pmtiles-provenance.py
whose two redirect sites point it at the mutant and at this repository, and requires the harness to exit
non-zero AND name the fixture that caught it. The tracked files are never written; an interrupted run leaves
the tree as it was. Every site, mutation and redirect alike, must occur EXACTLY ONCE in the file it edits, so a
table that has drifted from the code is a failure rather than a pass. SCENIC_LA_PMTILES is removed from the
copies' environment so a verdict is decided by the in-process fixtures on every box alike.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "services/tiles/check_pmtiles.py"
HARNESS = ROOT / "ops/lib/check-pmtiles-provenance.py"
ARCHIVE_ENV = "SCENIC_LA_PMTILES"

# (label, the text replaced in a copy of check_pmtiles.py, its replacement, the fixture that must be named).
MUTANTS = (
    ("the region comparison deleted",
     'if region is not None and meta.get("region") != region:',
     'if False:',
     "stamped region 'bay'"),
    ("an absent region key defaults to the expected value (T-0197 B4)",
     'if region is not None and meta.get("region") != region:',
     'if region is not None and meta.get("region", region) != region:',
     "no meta.region at all"),
    ("the 30-day comparison flipped",
     'if built < reference - timedelta(days=max_age_days):',
     'if built > reference - timedelta(days=max_age_days):',
     "stamped 40 days ago"),
    ("the cover limb deleted",
     'if header["min_lon"] > min_lon or header["min_lat"] > min_lat \\\n'
     '                or header["max_lon"] < max_lon or header["max_lat"] < max_lat:',
     'if False:',
     "bounds short of la's east edge"),
    # T-0233's two: the containment widened to a no-op (the acceptance's second mutant), and deleted.
    ("the containment widened to a no-op",
     'MAX_BOUNDS_OVERHANG_E7 = 219727',
     'MAX_BOUNDS_OVERHANG_E7 = 3_600_000_000',
     "California-wide bounds stamped la"),
    ("the containment deleted",
     'if head[0] < edge[0] - max_overhang_e7 or head[1] < edge[1] - max_overhang_e7 \\\n'
     '                or head[2] > edge[2] + max_overhang_e7 or head[3] > edge[3] + max_overhang_e7:',
     'if False:',
     "Bay Area bounds stamped la"),
)

# The literal floor (PR #94's shape): a table emptied by a bad merge must print a refusal, not "0/0 refused".
# Raise it when rows are added; never lower it to make a run pass.
MUTANT_FLOOR = 6


def redirected_harness(source: str, mutant: Path) -> str | None:
    """The harness pointed at the mutant and at ROOT; None when a redirect site is not exactly once."""
    sites = (('ROOT = Path(__file__).resolve().parents[2]', f'ROOT = Path({str(ROOT)!r})'),
             ('CHECKER = TILES / "check_pmtiles.py"', f'CHECKER = Path({str(mutant)!r})'))
    for old, new in sites:
        if source.count(old) != 1:
            return None
        source = source.replace(old, new)
    return source


def main() -> int:
    if len(MUTANTS) < MUTANT_FLOOR:
        print(f"P-DATA-03 (tiles half): --prove-red carries {len(MUTANTS)} mutants, below the floor of "
              f"{MUTANT_FLOOR}. A table that has lost rows must never read as 'every mutant refused'.")
        return 1
    for path in (CHECKER, HARNESS):
        if not path.is_file():
            print(f"P-DATA-03 (tiles half): {path} is missing; there is nothing to mutate")
            return 1
    source = CHECKER.read_text(encoding="utf-8")
    harness = HARNESS.read_text(encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != ARCHIVE_ENV}
    failures: list[str] = []
    lines: list[str] = []
    with TemporaryDirectory() as tmp:
        for index, (label, old, new, expected) in enumerate(MUTANTS):
            found = source.count(old)
            if found != 1:
                failures.append(f"{label}: its mutation site occurs {found} times in {CHECKER.name}, not "
                                "exactly once - this table no longer describes the code it claims to mutate")
                continue
            mutant = Path(tmp) / f"mutant{index}" / "check_pmtiles.py"
            mutant.parent.mkdir()
            mutant.write_text(source.replace(old, new), encoding="utf-8")
            redirected = redirected_harness(harness, mutant)
            if redirected is None:
                failures.append(f"{label}: a redirect site in {HARNESS.name} is not exactly once")
                continue
            copy = mutant.parent / "harness.py"
            copy.write_text(redirected, encoding="utf-8")
            proc = subprocess.run([sys.executable, str(copy)], capture_output=True, text=True,
                                  cwd=str(ROOT), env=env)
            out = proc.stdout + proc.stderr
            if proc.returncode == 0:
                failures.append(f"{label}: SURVIVED - the harness over the mutant exited 0")
            elif expected not in out:
                said = out.strip().splitlines()[-1] if out.strip() else "<nothing>"
                failures.append(f"{label}: exited {proc.returncode} but never named {expected!r}; "
                                f"it said: {said}")
            else:
                lines.append(f"  {label}: exit {proc.returncode}, refused naming {expected!r}")

    if failures:
        print(f"P-DATA-03 (tiles half): --prove-red: {len(failures)} of {len(MUTANTS)} mutants not caught:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"P-DATA-03 (tiles half): --prove-red {len(lines)}/{len(MUTANTS)} mutants refused by name:")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
