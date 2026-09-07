"""Land cover fractions around a road, from ESA WorldCover 2021 v200.

`canopy` and `1 - impervious` are the two largest terms in E, and between them they are what separates a
redwood road from a strip-mall arterial. Both are FRACTIONS of the land within a buffer of the road, not
properties of the road itself: a lane with trees on one side and a parking lot on the other is genuinely
half of each, and the score should say so rather than pick a winner.

Why WorldCover and not the USFS/NLCD layers the plan named: MRLC's S3 refuses all anonymous access (403,
Requester Pays), their landing pages carry no download link, and retrieval needs the interactive viewer or an
authenticated order. Checked live, not assumed. WorldCover is 10 m against NLCD's 30 m and gives both terms
from its class codes. What is lost is a calibrated continuous canopy percent; T-0029's rank-order fixtures
are where that would show up.

Nothing here reads a raster. Sampling is `dem`-style and runs in the pinned image; the class arithmetic and
the buffer geometry are pure and tested without a 92 MB download.
"""
from __future__ import annotations

import math

from .curvature import distance_on_earth

# WorldCover v200 class codes. The full set, so an unexpected value is recognised rather than silently
# bucketed as "other" - a raster that starts returning 0 everywhere would otherwise read as a valid mix.
CLASSES = {
    10: "tree_cover",
    20: "shrubland",
    30: "grassland",
    40: "cropland",
    50: "built_up",
    60: "bare_sparse",
    70: "snow_ice",
    80: "permanent_water",
    90: "herbaceous_wetland",
    95: "mangroves",
    100: "moss_lichen",
}

# Tree cover and shrubland both read as green enclosure from a car. Grassland does not - an open golden hill
# is scenic for a different reason, and it is `relief` and `water` that should pick that up, not `canopy`.
CANOPY_CLASSES = frozenset({10, 20})
IMPERVIOUS_CLASSES = frozenset({50})
WATER_CLASSES = frozenset({80, 90, 95})

TILE_DEG = 3.0
BUFFER_M = 150.0          # the plan's buffer: what you can see from the road, not what you drive on
BUFFER_STEP_M = 50.0      # a 7x7 grid across +/-150 m, so 49 samples per point


def tile_for(lat: float, lon: float) -> str:
    """The WorldCover tile covering a point.

    Tiles are 3x3 degrees named by their SOUTH-WEST corner, so N36W123 covers lat 36-39, lon -123..-120.
    Floor both to a multiple of three. Getting the longitude convention backwards names a tile three degrees
    away, which for this region is the difference between the Bay Area and the open Pacific - and the open
    Pacific tile exists, so the mistake returns data rather than an error.
    """
    if lat != lat or lon != lon:
        return ""
    south = math.floor(lat / TILE_DEG) * TILE_DEG
    west = math.floor(lon / TILE_DEG) * TILE_DEG
    ns = "N" if south >= 0 else "S"
    ew = "W" if west < 0 else "E"
    return f"{ns}{abs(int(south)):02d}{ew}{abs(int(west)):03d}"


def buffer_points(lat: float, lon: float, radius_m: float = BUFFER_M,
                  step_m: float = BUFFER_STEP_M) -> list[tuple[float, float]]:
    """A square grid of sample positions within `radius_m` of a point, clipped to a circle.

    Clipped to a circle rather than left square because the corners of a 300 m box are 212 m out, and a road
    running diagonally past a parking lot would pick it up from further away than one running north-south.
    The buffer has to be isotropic or the score depends on which way the road happens to point.
    """
    out = []
    n = int(radius_m // step_m)
    dlat = step_m / 111320.0
    dlon = dlat / max(math.cos(math.radians(lat)), 1e-6)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            if math.hypot(i, j) * step_m > radius_m:
                continue
            out.append((lat + i * dlat, lon + j * dlon))
    return out


def fractions(codes: list[int | None]) -> dict[str, float]:
    """Fraction of valid samples in each named class. NODATA is excluded from the denominator.

    Excluded, not counted as anything: a way at the coast has half its buffer in the ocean, and dividing by
    the full sample count would halve its canopy fraction purely for being near water. The caller gets
    `coverage` to decide whether there were enough samples to trust.
    """
    valid = [c for c in codes if c is not None]
    if not valid:
        return {"coverage": 0.0}
    out: dict[str, float] = {"coverage": len(valid) / len(codes)}
    for code, name in CLASSES.items():
        out[name] = sum(1 for c in valid if c == code) / len(valid)
    out["canopy"] = sum(1 for c in valid if c in CANOPY_CLASSES) / len(valid)
    out["impervious"] = sum(1 for c in valid if c in IMPERVIOUS_CLASSES) / len(valid)
    out["water"] = sum(1 for c in valid if c in WATER_CLASSES) / len(valid)
    return out


def unknown_codes(codes: list[int | None]) -> set[int]:
    """Codes that are not in the WorldCover class list.

    A raster read through the wrong band, or a tile that is not WorldCover at all, produces values outside
    the class set. Without this they would land in no bucket and every fraction would quietly be zero, which
    reads as "no trees and no buildings" rather than as "this is not land cover data".
    """
    return {c for c in codes if c is not None and c not in CLASSES}


def problems(summary: dict) -> list[str]:
    """Structural checks on a summary, so a broken sampler fails loudly instead of scoring."""
    out = []
    for key in ("canopy", "impervious", "water", "coverage"):
        v = summary.get(key)
        if v is None:
            out.append(f"{key} is missing")
        elif not 0.0 <= v <= 1.0:
            out.append(f"{key}={v} is not a fraction")
    named = [k for k in CLASSES.values() if k in summary]
    if named:
        total = sum(summary[k] for k in named)
        if not 0.99 <= total <= 1.01:
            out.append(f"class fractions sum to {total:.3f}, not 1 - samples are being lost or double-counted")
    return out


def is_wooded(summary: dict, threshold: float = 0.5) -> bool:
    """The Skyline property: a road through the redwoods must read as wooded."""
    return summary.get("canopy", 0.0) >= threshold


def is_built_up(summary: dict, threshold: float = 0.4) -> bool:
    """The strip-mall property: an industrial arterial must read as built up."""
    return summary.get("impervious", 0.0) >= threshold


def summarise(coords: list[tuple[float, float]], codes_per_point: list[list[int | None]]) -> dict:
    """One way's land cover: the fractions over every buffer sample along it, pooled.

    Pooled rather than averaged per point, so a long way through forest is not outvoted by a short built-up
    stretch with denser sampling. Every sample counts once.
    """
    pooled: list[int | None] = []
    for codes in codes_per_point:
        pooled.extend(codes)
    summary = fractions(pooled)
    summary["samples"] = len(pooled)
    summary["length_m"] = round(
        sum(distance_on_earth(a[0], a[1], b[0], b[1]) for a, b in zip(coords, coords[1:])), 1)
    for key in ("canopy", "impervious", "water", "coverage"):
        if key in summary:
            summary[key] = round(summary[key], 4)
    return summary
