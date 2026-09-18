"""Compare a built extract's meta.json against the counts recorded in region.json. Never builds anything.

  python -m etl.checkbounds                 every region with a build under work/
  python -m etl.checkbounds --region sfbay  just that one

Exit 0 in bounds, 4 out of bounds (ops/sane's reserved code for corpus/graph bounds), 2 if it cannot tell.
"Cannot tell" is never 0: an unreadable meta.json and a perfect extract must not print the same thing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import counts as ct
from . import region as rg

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"


def check(region_id: str) -> tuple[int, list[str]]:
    meta_path = WORK / region_id / "meta.json"
    if not meta_path.is_file():
        return 2, [f"{region_id}: no build under work/{region_id}/ - run ops/etl-extract"]
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return 2, [f"{region_id}: cannot read {meta_path}: {e}"]
    found = meta.get("counts")
    if not isinstance(found, dict) or not found:
        return 2, [f"{region_id}: {meta_path} carries no counts"]
    try:
        region = rg.load(region_id)
    except (OSError, ValueError) as e:
        return 2, [f"{region_id}: {e}"]
    if not region.counts:
        return 2, [f"{region_id}: region.json records no counts yet - "
                   f"run ops/etl-extract --record-counts and review the diff"]
    problems = ct.check_bounds(found, region.counts)
    return (4, problems) if problems else (0, [])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="etl.checkbounds", description=__doc__)
    ap.add_argument("--region", default=None)
    args = ap.parse_args(argv)

    if args.region:
        regions = [args.region]
    else:
        regions = sorted(p.name for p in WORK.iterdir() if (p / "meta.json").is_file()) if WORK.is_dir() else []
    if not regions:
        print("BOUNDS skip  no extract has been built here")
        return 0

    rc = 0
    for region_id in regions:
        code, problems = check(region_id)
        if code == 0:
            print(f"BOUNDS ok    {region_id}: every recorded class within {ct.DEFAULT_TOLERANCE:.0%}")
        else:
            print(f"BOUNDS FAIL  {region_id}")
            for p in problems:
                print(f"  {p}")
            rc = max(rc, code)
    return rc


if __name__ == "__main__":
    sys.exit(main())
