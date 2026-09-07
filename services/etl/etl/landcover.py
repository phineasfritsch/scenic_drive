"""Land cover fractions around a road, from ESA WorldCover 2021 v200.

`canopy` and `1 - impervious` are the two largest terms in E, and between them they are what separates a
redwood road from a strip-mall arterial. Both are FRACTIONS of the land within a buffer of the road, not
properties of the road itself: a lane with trees on one side and a parking lot on the other is genuinely
half of each, and the score should say so rather than pick a winner.

`is_wooded`/`is_built_up` are the other thing and must not be confused with the fractions. They answer one
question - which of the two kinds of road is this - and a road that is half trees and half roofs is neither
of them. Nothing in the scoring path calls them yet; they exist so the fixtures can state what a road IS,
and that is exactly why they have to be one verdict rather than two independent cutoffs.

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

# Tree cover and shrubland both read as green enclosure from a car. Grassland does not, and the measurement
# says why: Mines Road (Diablo Range oak savanna) is canopy 0.47 / grassland 0.53, and Morgan Territory Road,
# oak woodland half a mile away, is canopy 0.71. Fold grassland into canopy and Mines Road reads ~1.0 -
# above Skyline's 0.85 - so the one term that exists to tell a redwood road from an open hill would rank a
# treeless one first. Open land is a real thing that is neither trees nor buildings; it gets its own term.
CANOPY_CLASSES = frozenset({10, 20})
IMPERVIOUS_CLASSES = frozenset({50})
WATER_CLASSES = frozenset({80, 90, 95})
OPEN_CLASSES = frozenset({30, 40, 60, 70, 100})

# The four terms partition CLASSES: every class is in exactly one, so a road can never be mostly something
# the score has no name for. cropland was in none of them until agent/reviewer-32 sampled a Delta levee road
# whose dominant class produced no signal at all.
TERM_CLASSES = {"canopy": CANOPY_CLASSES, "impervious": IMPERVIOUS_CLASSES,
                "water": WATER_CLASSES, "open_land": OPEN_CLASSES}

TILE_DEG = 3.0
BUFFER_M = 150.0          # the plan's buffer: what you can see from the road, not what you drive on

# 20 m, not 50. WorldCover pixels are 10 m; a 50 m lattice beats against a suburban street grid, and the
# measurement is that moving the grid half a step - the land underneath untouched - moved canopy by up to
# 0.2759 on a real San Ramon street and flipped alviso_flat2, a curated archetype, between BUILT_UP and
# neither. At 20 m the worst phase swing over the same nine roads is 0.0847. The cost is 177 samples per
# point instead of 29; see tests/fixtures/landcover_boundary_fixture.json, which records both.
BUFFER_STEP_M = 20.0

# How far the dominant term has to be ahead before the verdict is a verdict. Above 1 is what makes the two
# predicates mutually exclusive, and it has to be strictly above: a 29-sample buffer that lands 15/14 is one
# sample from an exact 50/50 tie, and at a ratio of 1 an exact tie satisfies both.
DOMINANCE_RATIO = 2.0


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

    NODATA is not the ocean. WorldCover codes the open Pacific as class 80, continuously to 3 km offshore
    and beyond - agent/reviewer-32 marched west from the San Mateo coast and measured `coverage` 1.0000 on
    every shoreline buffer - so a coastal way's water IS counted, as water, and its canopy IS diluted by it.
    That is the right answer and T-0029 has to weight it; the rationale recorded here before said the
    opposite and described a case that does not occur.

    What NODATA actually is: a sample with no tile (a buffer reaching past the tiles we hold, or a point
    outside the region) and the raster's own 0 fill. Those must not dilute the classes we did read, so they
    leave the denominator, and the caller gets `coverage` to decide whether there were enough samples to
    trust. Every class fraction uses the same denominator as the four terms, or a partly unreadable buffer
    would report half its real canopy.
    """
    valid = [c for c in codes if c is not None]
    if not valid:
        return {"coverage": 0.0}
    out: dict[str, float] = {"coverage": len(valid) / len(codes)}
    for code, name in CLASSES.items():
        out[name] = sum(1 for c in valid if c == code) / len(valid)
    for term, classes in TERM_CLASSES.items():
        out[term] = sum(1 for c in valid if c in classes) / len(valid)
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
    for key in (*TERM_CLASSES, "coverage"):
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
    terms = [k for k in TERM_CLASSES if k in summary]
    if len(terms) == len(TERM_CLASSES):
        total = sum(summary[k] for k in terms)
        if not 0.99 <= total <= 1.01:
            out.append(f"the four terms sum to {total:.3f}, not 1 - a class is in two of them or in none")
    return out


def is_wooded(summary: dict, threshold: float = 0.5, ratio: float = DOMINANCE_RATIO) -> bool:
    """The Skyline property: a road through the redwoods must read as wooded.

    Not `canopy >= threshold` on its own. That is a statement about how much of the buffer is trees, and it
    is true of a leafy cul-de-sac with a house under every one of them - OSM way 7853452 in San Ramon reads
    canopy 0.508 / impervious 0.492 against these very tiles, which cleared the old wooded AND built-up
    cutoffs at the same time. Both fractions are honest; what is not honest is calling that road Skyline.
    So the two predicates are one verdict: the majority term wins, and only if it is `ratio` times the
    other. Any ratio above 1 makes them mutually exclusive - see test_no_pair_of_fractions_can_satisfy_both,
    which sweeps the whole simplex rather than four roads picked to sit far apart.
    """
    canopy = summary.get("canopy", 0.0)
    return canopy >= threshold and canopy >= ratio * summary.get("impervious", 0.0)


def is_built_up(summary: dict, threshold: float = 0.4, ratio: float = DOMINANCE_RATIO) -> bool:
    """The strip-mall property: an industrial arterial must read as built up. Same dominance rule as
    `is_wooded`, and for the same reason - a street with as many trees as roofs is not a strip mall."""
    impervious = summary.get("impervious", 0.0)
    return impervious >= threshold and impervious >= ratio * summary.get("canopy", 0.0)


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
    for key in (*TERM_CLASSES, "coverage"):
        if key in summary:
            summary[key] = round(summary[key], 4)
    return summary


# ---- sampling ---------------------------------------------------------------------------------------
# Same shape as etl.dem: one gdallocationinfo process per tile, injectable so the tests need no raster.
from pathlib import Path  # noqa: E402
import subprocess  # noqa: E402

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


def tile_path(name: str) -> Path:
    return INPUTS / f"worldcover-{name.lower()}.tif"


def sample_codes(points: list[tuple[float, float]], runner=None) -> list[int | None]:
    """WorldCover class code per point, in the order given. Points with no tile come back as None."""
    groups: dict[str, list[int]] = {}
    for i, (lat, lon) in enumerate(points):
        groups.setdefault(tile_for(lat, lon), []).append(i)
    out: list[int | None] = [None] * len(points)
    for name, indices in groups.items():
        path = tile_path(name) if name else None
        if not path or not path.is_file():
            continue
        stdin = "".join(f"{points[i][1]} {points[i][0]}\n" for i in indices)
        argv = ["gdallocationinfo", "-valonly", "-wgs84", str(path)]
        run = runner or (lambda a, s: subprocess.run(a, input=s, capture_output=True, text=True, check=False))
        proc = run(argv, stdin)
        if getattr(proc, "returncode", 1) != 0:
            raise RuntimeError(f"gdallocationinfo failed on {name}: {(proc.stderr or '').strip()[:200]}")
        lines = proc.stdout.splitlines()
        if len(lines) != len(indices):
            raise ValueError(f"gdallocationinfo returned {len(lines)} values for {len(indices)} points")
        for i, line in zip(indices, lines):
            line = line.strip()
            if not line:
                continue
            try:
                code = int(float(line))
            except ValueError:
                continue
            out[i] = None if code == 0 else code
    return out
