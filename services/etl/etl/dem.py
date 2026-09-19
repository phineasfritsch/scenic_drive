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
from collections.abc import Collection, Iterable
from pathlib import Path

from . import region as rg

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"

# The eight tiles the sfbay bbox needs, checked by hand when sfbay was the only region. It is the GOLDEN SET
# for the derivation (`test_the_sfbay_golden_set_is_exactly_what_the_derivation_serves`) and no longer what
# `tile_for` gates on - see `tiles_for_region`. n37w124 is deliberately absent: it is entirely ocean and USGS
# returns 404 for it. A point there has NO elevation, which is not the same as 0 m - zero is sea level, a
# real elevation, and would flatten every coastal way's relief.
TILES = frozenset({
    "n37w122", "n37w123",
    "n38w122", "n38w123", "n38w124",
    "n39w122", "n39w123", "n39w124",
})

# Tiles a bbox legitimately touches that nobody serves. USGS 404s n37w124 because it is entirely ocean;
# `tiles_for_bbox` cannot know that and says so, so the judgement lives here, once, with its reason - not
# once per region in a hand-typed list, which is the defect this module already has a docstring about.
UNSERVED = frozenset({"n37w124"})


def tile_name(lat: float, lon: float) -> str:
    """The 3DEP tile name whose square contains this point, with no opinion about whether we have it.

    Split out of `tile_for` so a region can be asked which tiles it NEEDS before any of them exist. The
    naming rule is the same one `tile_for` documents: a tile nXXwYYY covers latitude [XX-1, XX] and
    longitude [-YYY, -YYY+1], so the name comes from the north-west corner.
    """
    return f"n{math.ceil(lat):02d}w{math.ceil(abs(lon)):03d}"


def tiles_for_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> frozenset[str]:
    """Every 3DEP tile a bbox touches, derived rather than typed.

    TILES above listed sfbay's eight and `tile_for` GATED on it, so `tile_for` returned None for every point
    in any other region and every elevation there was absent - not wrong, ABSENT, which silently zeroes the
    terrain terms of the scenic score. [[T-0142]] wired this derivation into that decision via
    `tiles_for_region`; a hand-typed list for each new region would have been the same defect deferred.

    Walks the integer squares the bbox spans rather than sampling its corners: a bbox wider than one degree
    has interior squares that no corner is in, and a corner-only implementation would miss them and look
    correct on any small region.

    It does NOT know which tiles USGS actually serves. sfbay excludes n37w124 because it is entirely ocean
    and 404s; that judgement needs the region, so callers filter. Returning a tile that does not exist is
    recoverable - the fetcher reports it - while omitting one silently is not.
    """
    lo_lat, hi_lat = min(min_lat, max_lat), max(min_lat, max_lat)
    lo_lon, hi_lon = min(min_lon, max_lon), max(min_lon, max_lon)
    out = set()
    lat = math.floor(lo_lat)
    while lat <= math.ceil(hi_lat):
        lon = math.floor(lo_lon)
        while lon <= math.ceil(hi_lon):
            # The square [lat, lat+1] x [lon, lon+1] is touched only if it genuinely overlaps the bbox;
            # `<=` on the far edge would add a whole row of squares the bbox merely reaches the border of.
            if lat < hi_lat and lat + 1 > lo_lat and lon < hi_lon and lon + 1 > lo_lon:
                out.add(tile_name(lat + 1, lon))
            lon += 1
        lat += 1
    return frozenset(out)

# 3DEP publishes a large negative nodata. Anything at or below this is absence, not depth.
NODATA_BELOW_M = -1000.0
# Nothing in the Bay Area is above Mount Hamilton (1330 m) by much; a value past this is a corrupt read,
# not a mountain.
IMPLAUSIBLE_ABOVE_M = 5000.0


def tiles_for_region(region_id: str, root: Path | None = None) -> frozenset[str]:
    """The tiles one region actually has: derived from ITS OWN bbox, minus the ones nobody serves.

    This is what "the active region" means to `tile_for`. It reads the region's bbox out of
    regions/<id>/region.json rather than taking four numbers, so a bbox that moves moves the tile set with
    it and the two cannot drift apart - which is the same failure `counts_from` exists to stop.
    """
    b = rg.load(region_id, root=root).bbox
    return tiles_for_bbox(b.min_lon, b.min_lat, b.max_lon, b.max_lat) - UNSERVED


def region_ids(root: Path | None = None) -> list[str]:
    base = root or rg.REGIONS
    return sorted(p.name for p in base.iterdir() if (p / "region.json").is_file()) if base.is_dir() else []


def served_tiles(root: Path | None = None) -> frozenset[str]:
    """Every tile every region we serve needs - the answer when the caller names no region.

    The old default was sfbay's constant, so a pipeline run over any other region got no tile for any point
    and scored real roads as flat ground. A default that can produce silent absence is the defect, so the
    default is now the union: a caller that forgets to name its region gets that region's terrain anyway,
    and a caller that means "only this region" says so by passing `tiles`.

    Cached because `group_by_tile` asks per point and a region.json read per point would be thousands of
    file reads per way. Keyed by root so a test with its own regions directory is not served the real one.
    """
    key = str((root or rg.REGIONS).resolve())
    hit = _SERVED_CACHE.get(key)
    if hit is None:
        hit = frozenset().union(*[tiles_for_region(i, root=root) for i in region_ids(root)])
        _SERVED_CACHE[key] = hit
    return hit


_SERVED_CACHE: dict[str, frozenset[str]] = {}


def tile_for(lat: float, lon: float, tiles: Collection[str] | None = None) -> str | None:
    """The 3DEP tile covering a point, or None if we do not have one.

    A tile nXXwYYY covers latitude [XX-1, XX] and longitude [-YYY, -YYY+1], so the name comes from the
    NORTH-WEST corner: ceil the latitude, ceil the absolute longitude. Getting this backwards produces a
    name that exists, for the wrong square, and every elevation is then plausibly wrong rather than missing.

    `tiles` is the ACTIVE region's set, normally `tiles_for_region(region_id)`; `None` means every region we
    serve. Either way the flag semantics are unchanged: a point with no tile is None, which is absence, and
    absence is never 0 m.
    """
    if lat != lat or lon != lon:          # NaN
        return None
    name = f"n{math.ceil(lat):02d}w{math.ceil(abs(lon)):03d}"
    have = served_tiles() if tiles is None else tiles
    return name if name in have else None


def tile_path(name: str) -> Path:
    return INPUTS / f"3dep-{name}.tif"


def group_by_tile(points: list[tuple[float, float]],
                  tiles: Collection[str] | None = None) -> dict[str | None, list[int]]:
    """Point indices grouped by the tile that covers them, preserving order within each group.

    Indices rather than coordinates, because the caller needs to put the answers back in the original order -
    a sampler that returns values in tile order and lets someone else line them up is a sampler that will
    eventually line them up wrong.

    The active tile set is resolved ONCE here rather than per point: `served_tiles` reads region.json.
    """
    have = served_tiles() if tiles is None else tiles
    groups: dict[str | None, list[int]] = {}
    for i, (lat, lon) in enumerate(points):
        groups.setdefault(tile_for(lat, lon, have), []).append(i)
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


def sample(points: list[tuple[float, float]], runner=None,
           tiles: Collection[str] | None = None) -> list[float | None]:
    """Elevation for every point, in the order given. Points with no tile come back as None.

    `tiles` is the active region's set; see `tile_for`. It has to be threaded all the way down here, because
    a region-aware `tile_for` that the pipeline's actual entry point cannot reach is a fix on paper only.
    """
    out: list[float | None] = [None] * len(points)
    for name, indices in group_by_tile(points, tiles=tiles).items():
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


def sample_smoothed(points: list[tuple[float, float]], runner=None,
                    tiles: Collection[str] | None = None) -> list[float | None]:
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
    values = sample(expanded, runner=runner, tiles=tiles)
    out: list[float | None] = []
    for i in range(len(points)):
        window = [v for v in values[i * 9:(i + 1) * 9] if v is not None]
        out.append(sum(window) / len(window) if window else None)
    return out
