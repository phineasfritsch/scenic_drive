"""P-DATA-03's assertion: the PMTiles artifact's meta.region is the active region and built_at is fresh.

THE POPULATION PROBLEM, and how this is answered honestly (T-0197 ruling R1). The artifact the pin is
about - `services/tiles/work/la.pmtiles`, 63,520,949 bytes - is never committed and does not exist in CI,
so an assertion that only ran over it would be a TODO wearing a command: green because there was nothing
to look at. What DOES exist everywhere is the checker that decides both properties, and it is the shipping
entry point: `python services/tiles/check_pmtiles.py <archive> --region-json <region>` is the command
`services/tiles/build-la.sh` step 6 and `ops/publish-tiles` run and believe the exit code of.

So this runs THAT COMMAND, in a subprocess, over archives built in-process by the tests' own writer
(`services/tiles/tests/test_pmtiles_budget.py`: `write_pmtiles` / `good_metadata`, the same writer every
case in that suite uses), and requires all three verdicts:

    a fresh, region-`la` archive        ACCEPTED   (a checker that refuses everything proves nothing)
    the same archive stamped 40 days ago REFUSED   naming `older than 30 days (P-DATA-03)`
    the same archive stamped region `bay` REFUSED  naming `meta.region is 'bay'`

The fixtures are BUILT, not committed: a committed archive carries a frozen `built_at`, which goes stale in
thirty days and turns the age limb from an assertion into a calendar.

THE REAL ARTIFACT. When `SCENIC_LA_PMTILES` names a file, the same command is run over it and must exit 0 -
that is the pin over the real build, on the one box that has it. Set and naming nothing is a REFUSAL, never
a skip (the rule `services/tiles/tests/test_check_pmtiles_cli.py` already states for itself).

THE CORPUS HALF IS NOT HERE, AND IT IS NOW UNOWNED. P-DATA-03 also speaks about the corpus. `etl.corpus`
DOES stamp one - `services/etl/etl/corpus.py`, `writer.set_meta("region", region)` - but nothing anywhere
reads that value back against the active region, and T-0205, which the pin's text named as the task that
would grow this assertion's second half, merged as PR #116 writing `meta.surface_coverage` (P-DATA-04)
instead. No open task owns the corpus region comparison; one has to be filed. This file asserts the tiles
half only and says which half it is - a pin that quietly covers one of two populations is worse than one
that names the gap.

    python ops/lib/check-pmtiles-provenance.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
TILES = ROOT / "services/tiles"
CHECKER = TILES / "check_pmtiles.py"
REGION_JSON = ROOT / "services/etl/regions/la/region.json"
ARCHIVE_ENV = "SCENIC_LA_PMTILES"

sys.path.insert(0, str(TILES))
sys.path.insert(0, str(TILES / "tests"))


def refuse(reason: str, *extra: str) -> int:
    print(f"P-DATA-03: {reason}")
    for line in extra:
        print(f"  {line}")
    return 1


def run_checker(archive: Path) -> tuple[int, str]:
    """The command the recipe spells, as the recipe spells it."""
    proc = subprocess.run(
        [sys.executable, str(CHECKER), str(archive), "--region-json", str(REGION_JSON)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return proc.returncode, proc.stdout + proc.stderr


def stamp(days_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    for path in (CHECKER, REGION_JSON):
        if not path.is_file():
            return refuse(f"{path.relative_to(ROOT).as_posix()} is missing",
                          "The pin is a property of the committed tree; a missing checker or region file is",
                          "a refusal, never a pass.")
    try:
        from test_pmtiles_budget import LA_BBOX, good_metadata, write_pmtiles
    except ImportError as exc:  # the writer is the fixtures' one definition
        return refuse(f"the tests' PMTiles writer is unavailable: {exc}",
                      "services/tiles/tests/test_pmtiles_budget.py owns write_pmtiles/good_metadata.")

    def unstamped_region(built_at: str) -> dict:
        """An archive the recipe never stamped at all: the region key is ABSENT, not wrong.

        The wrong-region fixture below cannot catch a comparison that defaults the missing key to the
        expected value (`meta.get("region", region)`): with no region stamped, that reads 'la' and the
        archive is ACCEPTED - the whole failure this pin exists for, from an archive nobody stamped.
        The pre-review mutant pass of 2026-09-19 (B4) survived both this check and all 69 tests in
        services/tiles/tests with exactly that mutation.
        """
        meta = good_metadata(built_at=built_at)
        meta.pop("region")
        return meta

    cases = [
        ("a fresh region-la archive", good_metadata(built_at=stamp(0.001)), 0, "PMTILES OK"),
        ("stamped 40 days ago", good_metadata(built_at=stamp(40)), 1, "older than 30 days (P-DATA-03)"),
        ("stamped region 'bay'", good_metadata(built_at=stamp(0.001), region="bay"), 1,
         "meta.region is 'bay'"),
        ("no meta.region at all", unstamped_region(stamp(0.001)), 1, "meta.region is None"),
    ]

    failures: list[str] = []
    lines: list[str] = []
    with TemporaryDirectory() as tmp:
        for index, (label, meta, want_code, want_text) in enumerate(cases):
            archive = write_pmtiles(Path(tmp) / f"case{index}.pmtiles", LA_BBOX, meta)
            code, out = run_checker(archive)
            first = out.strip().splitlines()
            said = first[-1].strip() if first else "<nothing>"
            if code != want_code or want_text not in out:
                failures.append(f"{label}: exit {code} (expected {want_code}) and the output did not name "
                                f"{want_text!r}; it said: {said}")
            else:
                lines.append(f"  {label}: exit {code}, named {want_text!r}")

        named = os.environ.get(ARCHIVE_ENV)
        if named:
            real = Path(named)
            if not real.is_file():
                failures.append(f"{ARCHIVE_ENV}={named} names no file (set and absent is a refusal, "
                                "never a skip)")
            else:
                code, out = run_checker(real)
                if code != 0:
                    failures.append(f"the real artifact {named} was REFUSED: {out.strip()}")
                else:
                    lines.append(f"  {real.name}: exit 0 - {out.strip().splitlines()[-1]}")
        else:
            lines.append(f"  the real artifact was not checked: ${ARCHIVE_ENV} is unset "
                         "(it is not committed and does not exist in CI)")

    if failures:
        return refuse("the region/freshness limbs of the shipping checker do not decide:", *failures)
    print("P-DATA-03: services/tiles/check_pmtiles.py, run as build-la.sh step 6 runs it, over "
          f"{len(cases)} in-process fixtures:")
    for line in lines:
        print(line)
    print("  The corpus half is UNASSERTED and UNOWNED: etl.corpus stamps meta.region (corpus.py, "
          "set_meta(\"region\", ...)) and nothing reads it back against the active region; T-0205 merged "
          "as PR #116 writing meta.surface_coverage instead, so a task for it still has to be filed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
