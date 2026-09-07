"""The curvature oracle's agreement figures, with the platform that produced them stated on every line.

This module exists because the numbers this task was built on were only ever computed on Windows, while the
toolchain the repo pins and trusts is `services/etl/Dockerfile`'s Linux image - and the two disagree by up to
a point, because `circum_circle_radius` amplifies libm's implementation-defined last-bit rounding into
radius differences large enough to cross a curvature band. See `tests/test_curvature.py`'s MIN_AGREEMENT
comment for the measured chain. An agreement rate quoted without its platform is not a fact about the code.

    python -m etl.oracle_report                        the fixture, whatever interpreter is running
    python -m etl.oracle_report --export PATH          also the full eligible population from an export
    ops/etl-oracle-report                              the same, in the pinned image, which is what to quote
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from . import curvature as cv

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "curvature_oracle.json"
TOLERANCE = 0.02


def this_platform() -> str:
    return f"{platform.system()}/{platform.machine()} python {platform.python_version()}"


def agreement(ways: list[dict]) -> dict:
    """Agreement statistics over ways carrying `coords` and `oracle_curvature`.

    Reports the median and p90 alongside the pass rate on purpose. The pass rate is a threshold on a
    quantity that is not portable in about 3% of cases, so it moves by a point between operating systems;
    the median moved by 0.0001 points across the same pair, which makes it the statistic to watch when
    asking whether the ALGORITHM changed.
    """
    errs = []
    for way in ways:
        coords = [(float(lat), float(lon)) for lat, lon in way["coords"]]
        ours = cv.way_curvature(coords, way.get("way_id"))
        theirs = float(way["oracle_curvature"])
        errs.append(abs(ours - theirs) / theirs if theirs else (0.0 if ours == 0 else float("inf")))
    errs.sort()
    n = len(errs)
    agree = sum(1 for e in errs if e <= TOLERANCE)
    return {
        "platform": this_platform(),
        "n": n,
        "agree": agree,
        "share": agree / n if n else 0.0,
        "median": errs[n // 2] if n else 0.0,
        "p90": errs[int(0.9 * n)] if n else 0.0,
    }


def fixture_report(path: Path = FIXTURE) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    out = agreement(doc["ways"])
    out["what"] = f"fixture ({path.name})"
    out["funnel"] = doc.get("funnel")
    return out


def population_report(export: Path) -> dict:
    """Every eligible way, not just the sampled 400.

    A 400-way sample carries about 1.1 points of binomial standard error at p=0.95, so a floor set close to
    a sample rate is being asked to absorb sampling noise and platform noise at once. The population has
    only the second.
    """
    from . import oracle_select as sel        # imported here: only this path needs the export reader
    kept, stages = sel.eligible(export)
    out = agreement(kept)
    out["what"] = f"population ({export.name})"
    out["funnel"] = stages
    return out


def format_report(r: dict) -> str:
    return (f"  {r['what']:34s} {r['agree']:5d}/{r['n']:<5d} = {100 * r['share']:7.3f}%"
            f"   median {100 * r['median']:8.5f}%   p90 {100 * r['p90']:7.4f}%")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", type=Path, help="osmium geojsonseq export, to also report the population")
    ap.add_argument("--json", action="store_true", help="machine-readable, for diffing two platforms")
    args = ap.parse_args(argv)

    reports = [fixture_report()]
    if args.export:
        if not args.export.exists():
            print(f"no such export: {args.export} - run ops/etl-curvature-fixture first", file=sys.stderr)
            return 2
        reports.append(population_report(args.export))

    # An empty population is not a 0% agreement rate, it is the absence of a measurement, and printing
    # `0/0 = 0.000%` and exiting 0 hands somebody a number to quote. Refuse instead.
    for r in reports:
        if r["n"] == 0:
            print(f"REFUSING TO REPORT: {r['what']} has no ways in it at all. "
                  f"Rebuild with ops/etl-curvature-fixture.", file=sys.stderr)
            return 2

    if args.json:
        print(json.dumps(reports, indent=1))
        return 0
    print(f"ORACLE {this_platform()}")
    for r in reports:
        print(format_report(r))
        if r.get("funnel"):
            print(f"    funnel: {r['funnel']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
