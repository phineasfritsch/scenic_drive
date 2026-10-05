"""Pass 2: every tile's document scored AGAINST THE ONE REGION REFERENCE.

T-0208's pass2.sh: `python -m etl.assemble --input <tile>-doc.json --out <tile>-scored.json --reference
<region>-reference.json`, N tiles at a time, resume by file presence. The `--reference` IS the seam fix:
without it each tile is ranked against its own population and a way in two tiles takes two scores
(tests/test_region_build.py is red by name when this stage drops it).
"""
from __future__ import annotations

from . import sweep

TOTAL_NAMES = ("ways", "zero_class", "gated", "sinuosity_declined", "points_of_interest_absent", "null_score")


def run(layout, names, jobs: int) -> int:
    if not layout.reference.exists():
        print("SCORE REFUSED: no region reference at %s - run the reference stage" % layout.reference)
        return 2
    layout.scored.mkdir(parents=True, exist_ok=True)
    lines = {}

    def score(tile: str) -> tuple:
        out = layout.scored_of(tile)
        line, output = sweep.count_line(
            sweep.python_module("etl.assemble", "--input", layout.doc_of(tile), "--out", out,
                                "--reference", layout.reference), "ASSEMBLE")
        if line is None:
            out.unlink(missing_ok=True)
            return False, "assemble: %s" % output.strip().splitlines()[-1:]
        lines[tile] = line
        return True, line

    failed = sweep.run(names, layout.scored_of, score, jobs, "SCORED")
    present = sum(1 for name in names if layout.scored_of(name).exists())
    print("PASS2 SWEEP END %d scored of %d docs" % (present, len(names)), flush=True)
    totals = {name: 0 for name in TOTAL_NAMES}
    for line in lines.values():
        for pair in line.split()[1:]:
            key, _, value = pair.partition("=")
            if key in totals:
                totals[key] += int(value)
    print("PASS2 TOTALS tiles_this_run=%d %s"
          % (len(lines), " ".join("%s=%d" % (name, totals[name]) for name in TOTAL_NAMES)), flush=True)
    return 1 if failed or present != len(names) else 0
