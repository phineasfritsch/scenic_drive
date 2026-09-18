"""Elevation gain and relief per way, from 3DEP bare-earth elevation.

Two numbers feed the scenic score from here: `elev_gain` (a term in M, how much climbing the road does) and
`relief` (a term in E, how much the land around it moves). Both are computed from a profile sampled along the
way, and both are trivially wrong in the same way - noise.

3DEP at 1/3 arc-second is bare-earth, which is the right product: a canopy-top DSM would put 30 m of "gain"
under every redwood road. But at ~10 m it still carries enough vertical noise that summing raw positive
deltas invents climb on ground that is flat. Alviso, on the bay margin, is the fixture for that: it is
genuinely flat, and an implementation without smoothing scores it as a climb.

So: smooth the grid 3x3 first, sample at a fixed 25 m step so the answer does not depend on how finely the
way happens to be drawn, and only then accumulate.

Nothing here reads a GeoTIFF. Sampling needs GDAL and runs in the pinned image; everything that can be wrong
about the arithmetic is in this file and testable without a 2.3 GB download.
"""
from __future__ import annotations

import math

from .curvature import distance_on_earth

SAMPLE_STEP_M = 25.0      # the brief's sampling interval
RELIEF_WINDOW_M = 1000.0  # relief is (max - min) within 1 km
NODATA = None             # a coordinate with no tile: ocean, or outside the region

# 3DEP's own vertical accuracy is about 1 m RMSE in open terrain. Deltas below this are not climb, they are
# the DEM disagreeing with itself, and a 25 m step over a 1 m wobble is a 4% grade that never existed.
NOISE_FLOOR_M = 0.5


def smooth3x3(grid: list[list[float | None]]) -> list[list[float | None]]:
    """Mean of the 3x3 neighbourhood, skipping NODATA. Cells with no valid neighbour stay NODATA.

    Averaging over NODATA as if it were zero would pull every coastal cell towards sea level and invent a
    cliff at the shoreline - which is exactly the shape of feature this score is meant to reward, so it would
    be a bug that looks like a result.
    """
    if not grid or not grid[0]:
        return []
    rows, cols = len(grid), len(grid[0])
    out: list[list[float | None]] = [[None] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            total, n = 0.0, 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < rows and 0 <= cc < cols:
                        v = grid[rr][cc]
                        if v is not None:
                            total += v
                            n += 1
            out[r][c] = (total / n) if n else None
    return out


def resample(coords: list[tuple[float, float]], step_m: float = SAMPLE_STEP_M) -> list[tuple[float, float]]:
    """Points every `step_m` along the way, by linear interpolation between its nodes.

    A way drawn with a node every 5 m and the same road drawn with a node every 200 m must produce the same
    gain. Accumulating over the raw nodes instead makes the score a measurement of how carefully somebody
    mapped the road.
    """
    if len(coords) < 2:
        return list(coords)
    out = [coords[0]]
    carry = 0.0
    for (lat1, lon1), (lat2, lon2) in zip(coords, coords[1:]):
        seg = distance_on_earth(lat1, lon1, lat2, lon2)
        if seg <= 0:
            continue
        travelled = step_m - carry
        while travelled <= seg:
            f = travelled / seg
            out.append((lat1 + (lat2 - lat1) * f, lon1 + (lon2 - lon1) * f))
            travelled += step_m
        carry = (carry + seg) % step_m
    if out[-1] != coords[-1]:
        out.append(coords[-1])
    return out


def elevation_gain(profile: list[float | None], noise_floor_m: float = NOISE_FLOOR_M) -> float:
    """Total climb: the sum of positive steps that exceed the noise floor.

    Gaps are bridged rather than treated as a step. A NODATA cell in the middle of a way - a bridge over
    water, a tile edge - would otherwise register as a fall to nothing and a climb back out, which is a
    fabricated 2x of whatever the surrounding terrain does.
    """
    gain = 0.0
    previous = None
    for value in profile:
        if value is None:
            continue
        if previous is not None:
            delta = value - previous
            if delta > noise_floor_m:
                gain += delta
        previous = value
    return gain


def gain_per_km(profile: list[float | None], length_m: float,
                noise_floor_m: float = NOISE_FLOOR_M) -> float:
    if length_m <= 0:
        return 0.0
    return elevation_gain(profile, noise_floor_m) * 1000.0 / length_m


def relief(profile: list[float | None], step_m: float = SAMPLE_STEP_M,
           window_m: float = RELIEF_WINDOW_M) -> float:
    """The largest (max - min) over any 1 km window of the profile.

    Maximum over windows rather than over the whole way: a 40 km road that climbs steadily from sea level to
    600 m is not more dramatic than a 1 km road that does the same thing, and taking the whole-way range
    would say it is. Relief is about how much the land moves around you, not how far you eventually get.
    """
    values = [v for v in profile if v is not None]
    if len(values) < 2:
        return 0.0
    span = max(1, int(round(window_m / step_m)))
    if len(values) <= span:
        return max(values) - min(values)
    best = 0.0
    for i in range(len(values) - span + 1):
        window = values[i:i + span]
        best = max(best, max(window) - min(window))
    return best


def profile_length_m(points: list[tuple[float, float]]) -> float:
    return sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:]))


def coverage(profile: list[float | None]) -> float:
    """Fraction of the profile that has elevation at all.

    A way over water, or one that runs off the edge of the tiles, must be reported as uncovered rather than
    scored from the handful of cells that happened to hit land. The caller decides what to do with a low
    number; what it must never do is average NODATA into the answer as zero, which is sea level.
    """
    if not profile:
        return 0.0
    return sum(1 for v in profile if v is not None) / len(profile)


def grade_percent(profile: list[float | None], step_m: float = SAMPLE_STEP_M) -> float:
    """Steepest sustained grade over any 100 m of the profile, as a percentage."""
    values = [v for v in profile if v is not None]
    span = max(1, int(round(100.0 / step_m)))
    if len(values) <= span:
        return 0.0
    steepest = 0.0
    for i in range(len(values) - span):
        rise = abs(values[i + span] - values[i])
        run = span * step_m
        steepest = max(steepest, 100.0 * rise / run)
    return steepest


def summarise(coords: list[tuple[float, float]], profile: list[float | None]) -> dict:
    """Everything the scorer needs from one way's terrain, in one pass."""
    points = resample(coords)
    length = profile_length_m(points)
    return {
        "length_m": round(length, 1),
        "coverage": round(coverage(profile), 4),
        "gain_m": round(elevation_gain(profile), 1),
        "gain_per_km": round(gain_per_km(profile, length), 2),
        "relief_m": round(relief(profile), 1),
        "max_grade_pct": round(grade_percent(profile), 2),
    }


def is_flat(summary: dict, gain_per_km_threshold: float = 5.0) -> bool:
    """The Alviso property, as a predicate rather than a comment.

    Bay-margin roads climb essentially nothing. If an implementation scores them as climbing, the smoothing
    or the noise floor is not doing its job, and every flat road in the region is being rewarded for noise.
    """
    return summary["gain_per_km"] < gain_per_km_threshold


def is_steep(summary: dict, gain_per_km_threshold: float = 25.0) -> bool:
    """The Old La Honda property. A road that climbs 400 m in 5.5 km must not read as flat."""
    return summary["gain_per_km"] >= gain_per_km_threshold


def sanity_problems(summary: dict) -> list[str]:
    """Physical impossibilities, so a broken sampler fails loudly instead of scoring."""
    out = []
    if not 0.0 <= summary["coverage"] <= 1.0:
        out.append(f"coverage {summary['coverage']} is not a fraction")
    if summary["gain_m"] < 0:
        out.append(f"gain {summary['gain_m']} is negative")
    if summary["relief_m"] < 0:
        out.append(f"relief {summary['relief_m']} is negative")
    if summary["max_grade_pct"] > 60:
        out.append(f"max grade {summary['max_grade_pct']}% - no drivable road is that steep, the sampler is wrong")
    if summary["length_m"] > 0 and summary["gain_m"] > summary["length_m"]:
        out.append("gain exceeds length - a road cannot climb further than it travels")
    if math.isnan(summary["gain_per_km"]):
        out.append("gain_per_km is NaN")
    return out
