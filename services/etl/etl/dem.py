"""Sampling elevation out of the 3DEP tiles.

Split deliberately: the tile arithmetic and the output parsing are pure and tested here, and the only
impure part is one subprocess call per tile. That is the same split as `curvature.py` versus `extract.py`,
for the same reason - the parts most likely to be wrong are the index arithmetic and the nodata handling,
and neither should need a 2.3 GB download to test.

`gdallocationinfo` rather than the Python GDAL bindings, because the pinned ETL image installs `gdal-bin`
(the CLI) and not `python3-gdal`. Adding the bindings would mean editing services/etl/Dockerfile, which is
another task's file and currently in review. It reads coordinate pairs from stdin, so this is one process per
TILE, not one per point.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"

# The eight tiles the sfbay bbox needs. n37w124 is deliberately absent: it is entirely ocean and USGS
# returns 404 for it. A point there has NO elevation, which is not the same as 0 m - zero is sea level, a
# real elevation, and would flatten every coastal way's relief.
TILES = frozenset({
    "n37w122", "n37w123",
    "n38w122", "n38w123", "n38w124",
    "n39w122", "n39w123", "n39w124",
})

# 3DEP publishes a large negative nodata. Anything at or below this is absence, not depth.
NODATA_BELOW_M = -1000.0
# Nothing in the Bay Area is above Mount Hamilton (1330 m) by much; a value past this is a corrupt read,
# not a mountain.
IMPLAUSIBLE_ABOVE_M = 5000.0


def tile_for(lat: float, lon: float) -> str | None:
    """The 3DEP tile covering a point, or None if we do not have one.

    A tile nXXwYYY covers latitude [XX-1, XX] and longitude [-YYY, -YYY+1], so the name comes from the
    NORTH-WEST corner: ceil the latitude, ceil the absolute longitude. Getting this backwards produces a
    name that exists, for the wrong square, and every elevation is then plausibly wrong rather than missing.
    """
    if lat != lat or lon != lon:          # NaN
        return None
    name = f"n{math.ceil(lat):02d}w{math.ceil(abs(lon)):03d}"
    return name if name in TILES else None


def tile_path(name: str) -> Path:
    return INPUTS / f"3dep-{name}.tif"


def group_by_tile(points: list[tuple[float, float]]) -> dict[str | None, list[int]]:
    """Point indices grouped by the tile that covers them, preserving order within each group.

    Indices rather than coordinates, because the caller needs to put the answers back in the original order -
    a sampler that returns values in tile order and lets someone else line them up is a sampler that will
    eventually line them up wrong.
    """
    groups: dict[str | None, list[int]] = {}
    for i, (lat, lon) in enumerate(points):
        groups.setdefault(tile_for(lat, lon), []).append(i)
    return groups


def parse_values(text: str, expected: int) -> list[float | None]:
    """Parse `gdallocationinfo -valonly` output: one value per line, blank or non-numeric for a miss.

    Raises when the count does not match. A short read means some points silently got another point's
    elevation, and every downstream number would be wrong in a way that still looks like terrain.
    """
    values: list[float | None] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            values.append(None)
            continue
        try:
            v = float(line)
        except ValueError:
            values.append(None)
            continue
        values.append(None if (v <= NODATA_BELOW_M or v >= IMPLAUSIBLE_ABOVE_M) else v)
    if len(values) != expected:
        raise ValueError(f"gdallocationinfo returned {len(values)} values for {expected} points")
    return values


def sample_tile(name: str, points: list[tuple[float, float]],
                runner=None) -> list[float | None]:
    """Elevation for points that all fall in one tile. `runner` is injectable so tests need no GDAL."""
    path = tile_path(name)
    if not path.is_file():
        return [None] * len(points)
    stdin = "".join(f"{lon} {lat}\n" for lat, lon in points)
    argv = ["gdallocationinfo", "-valonly", "-wgs84", str(path)]
    run = runner or (lambda a, s: subprocess.run(a, input=s, capture_output=True, text=True, check=False))
    proc = run(argv, stdin)
    if getattr(proc, "returncode", 1) != 0:
        raise RuntimeError(f"gdallocationinfo failed on {name}: {(proc.stderr or '').strip()[:200]}")
    return parse_values(proc.stdout, len(points))


def sample(points: list[tuple[float, float]], runner=None) -> list[float | None]:
    """Elevation for every point, in the order given. Points with no tile come back as None."""
    out: list[float | None] = [None] * len(points)
    for name, indices in group_by_tile(points).items():
        if name is None:
            continue
        values = sample_tile(name, [points[i] for i in indices], runner=runner)
        for i, v in zip(indices, values):
            out[i] = v
    return out

# One 1/3 arc-second cell is 1/10800 of a degree: about 10.3 m north-south, and 10.3/cos(lat) east-west.
CELL_DEG = 1.0 / 10800.0


def neighbourhood(lat: float, lon: float) -> list[tuple[float, float]]:
    """The nine sample positions of a 3x3 cell neighbourhood centred on a point.

    The east-west offset is divided by cos(latitude) so the box is square on the ground rather than square in
    degrees. At 38N a degree of longitude is 79% of a degree of latitude, so skipping that makes the
    neighbourhood a rectangle stretched north-south and the smoothing directional - it would blur ridges
    running one way more than the other, which is precisely the feature relief is meant to measure.
    """
    dlon = CELL_DEG / max(math.cos(math.radians(lat)), 1e-6)
    return [(lat + dy * CELL_DEG, lon + dx * dlon)
            for dy in (-1, 0, 1) for dx in (-1, 0, 1)]


def sample_smoothed(points: list[tuple[float, float]], runner=None) -> list[float | None]:
    """Elevation with the 3x3 smoothing the brief asks for, applied at sample time.

    `terrain.smooth3x3` smooths a GRID; this is the same operation for scattered points, which is what a road
    profile is. Sampling the raw cell instead leaves ~1 m of DEM noise in every value, and summing positive
    deltas over 25 m steps turns that into climb on ground that is flat - the Alviso failure.

    Nine positions per point, all sent to gdallocationinfo in ONE stream per tile, so this is the same number
    of processes as the unsmoothed version and nine times the rows. A point whose whole neighbourhood is
    nodata stays None: absence, not sea level.
    """
    expanded: list[tuple[float, float]] = []
    for lat, lon in points:
        expanded.extend(neighbourhood(lat, lon))
    values = sample(expanded, runner=runner)
    out: list[float | None] = []
    for i in range(len(points)):
        window = [v for v in values[i * 9:(i + 1) * 9] if v is not None]
        out.append(sum(window) / len(window) if window else None)
    return out
