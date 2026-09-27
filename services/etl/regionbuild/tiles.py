"""The tile plan a region is built over: which tiles, and the one bbox each tile NAME means.

A tile is `t<row><col>` of a COLUMNS x ROWS grid over the region bbox, optionally cut in half by longitude
(`a` west, `b` east), optionally quartered (`q0` south-west, `q1` south-east, `q2` north-west, `q3`
north-east). T-0208 re-cut the LA grid three times to fit tiles into container calls (make_tiles.py,
make_splits.py, make_quarters.py); what shipped is the END STATE, and it is this module's LA plan: 152
tiles. The bbox of each is computed with those three scripts' own formulas and their rounding to six
places, so the rebuild cuts the same tiles osmium cut then.

A tile boundary never changes a way's score (the region reference and the region motorway set make every
seam way agree, and `merge` refuses the build when one does not), but it does change which tile documents a
way, and so which tile's row is the one first-tile-wins keeps. The plan is data, not a heuristic.
"""
from __future__ import annotations

import json
import pathlib
import re

# region -> (west, south, east, north, columns, rows). meta.json's LA bbox, ten by six.
GRIDS = {"la": (-119.0, 33.7, -117.85, 34.45, 10, 6)}
# region -> the (dlon, dlat) LITERALS make_splits.py and make_quarters.py cut halves and quarters with.
STEPS = {"la": (0.115, 0.125)}
PLACES = 6
# osmium holds every extract's buffers under complete_ways: sixty in one config was OOM-killed (T-0208).
EXTRACTS_PER_CONFIG = 12

LA_WHOLE = ("t04 t05 t11 t14 t20 t21 t22 t23 t30 t31 t32 t33 t40 t41 t42 t45 t46 t47 t48 t49 "
            "t50 t51 t52 t53 t54 t55 t56 t57 t58 t59 t16b t25b").split()
LA_QUARTERED = ("t06 t07 t08 t09a t09b t15a t15b t16a t17a t17b t18a t18b t19a t19b t24 t25a t26a t26b "
                "t27a t27b t28 t29 t34 t35 t36 t37 t38 t39 t43 t44").split()
PLANS = {"la": tuple(sorted(LA_WHOLE + ["%sq%d" % (base, q) for base in LA_QUARTERED for q in range(4)]))}

NAME = re.compile(r"^t(\d)(\d)([ab]?)(?:q([0-3]))?$")
QUARTERS = ((0, 0), (1, 0), (0, 1), (1, 1))


def plan(region: str) -> tuple:
    """The tile names of a region's build, in sorted order."""
    if region not in PLANS:
        raise ValueError("no tile plan for region %r (have %s)" % (region, sorted(PLANS)))
    return PLANS[region]


def bbox_of(region: str, name: str) -> dict:
    """`{"left", "bottom", "right", "top"}` of one tile name - osmium extract's config shape."""
    match = NAME.match(name)
    if match is None:
        raise ValueError("not a tile name: %r" % name)
    row, column, half, quarter = int(match.group(1)), int(match.group(2)), match.group(3), match.group(4)
    west, south, east, north, columns, rows = GRIDS[region]
    if row >= rows or column >= columns:
        raise ValueError("tile %r is outside the %dx%d grid" % (name, columns, rows))
    if not half and quarter is None:
        return _whole(region, row, column)
    dlon, dlat = STEPS[region]
    left, bottom, width = west + column * dlon, south + row * dlat, dlon
    if half == "a":
        width = dlon / 2
    elif half == "b":
        left, width = left + dlon / 2, dlon / 2
    if quarter is None:
        return _box(left, bottom, left + width, bottom + dlat)
    dx, dy = QUARTERS[int(quarter)]
    return _box(left + dx * width / 2, bottom + dy * dlat / 2,
                left + (dx + 1) * width / 2, bottom + (dy + 1) * dlat / 2)


def _whole(region: str, row: int, column: int) -> dict:
    """make_tiles.py's cell: the step is the bbox divided by the grid, not the literal."""
    west, south, east, north, columns, rows = GRIDS[region]
    dlon, dlat = (east - west) / columns, (north - south) / rows
    left, bottom = west + column * dlon, south + row * dlat
    return _box(left, bottom, left + dlon, bottom + dlat)


def _box(left: float, bottom: float, right: float, top: float) -> dict:
    return {"left": round(left, PLACES), "bottom": round(bottom, PLACES),
            "right": round(right, PLACES), "top": round(top, PLACES)}


def configs(region: str, names, directory: pathlib.Path) -> list:
    """`osmium extract -c` configs over the names, EXTRACTS_PER_CONFIG at a time."""
    extracts = [{"output": "%s.osm.pbf" % name, "bbox": bbox_of(region, name)} for name in names]
    return [{"directory": str(directory), "extracts": extracts[index:index + EXTRACTS_PER_CONFIG]}
            for index in range(0, len(extracts), EXTRACTS_PER_CONFIG)]


def read_list(path) -> tuple:
    """A tile list file: one name a line, blank lines and CRs ignored (a Windows-written list)."""
    text = pathlib.Path(path).read_text(encoding="utf-8").replace("\r", "")
    return tuple(sorted(line.strip() for line in text.splitlines() if line.strip()))


def write_configs(region: str, names, directory: pathlib.Path, config_dir: pathlib.Path) -> list:
    """Write the configs to disk; return their paths."""
    config_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, config in enumerate(configs(region, names, directory)):
        path = config_dir / ("tiles-%02d.json" % index)
        path.write_text(json.dumps(config, indent=1) + "\n", encoding="utf-8", newline="\n")
        paths.append(path)
    return paths
