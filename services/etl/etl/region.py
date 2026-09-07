"""A region is a bbox, a name, and the recorded shape of what came out of it last time.

The recorded counts are the point. An extract that silently stops emitting viewpoints, or a tag filter edited
to "clean up" motorways, produces a perfectly valid PBF that is simply missing things - and nothing downstream
notices until a route is wrong. Bounds turn that into a failing check at the stage that caused it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REGIONS = Path(__file__).resolve().parents[1] / "regions"

# The world, as coordinates. Anything outside this is a typo, not a region.
LON_RANGE = (-180.0, 180.0)
LAT_RANGE = (-90.0, 90.0)
# A region smaller than this is a mistake (a swapped pair, a truncated literal); larger than this is not an
# extract, it is the planet, and the 15-minute build promise stops being true.
MIN_SPAN_DEG = 0.1
MAX_SPAN_DEG = 12.0


@dataclass(frozen=True)
class BBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def problems(self) -> list[str]:
        out = []
        for name, value, (lo, hi) in (
            ("min_lon", self.min_lon, LON_RANGE), ("max_lon", self.max_lon, LON_RANGE),
            ("min_lat", self.min_lat, LAT_RANGE), ("max_lat", self.max_lat, LAT_RANGE),
        ):
            if not isinstance(value, (int, float)) or value != value:  # NaN is not a coordinate
                out.append(f"{name} is not a number: {value!r}")
            elif not lo <= value <= hi:
                out.append(f"{name}={value} is outside {lo}..{hi}")
        if out:
            return out
        if self.min_lon >= self.max_lon:
            out.append(f"min_lon {self.min_lon} is not west of max_lon {self.max_lon}")
        if self.min_lat >= self.max_lat:
            out.append(f"min_lat {self.min_lat} is not south of max_lat {self.max_lat}")
        if out:
            return out
        for axis, span in (("lon", self.max_lon - self.min_lon), ("lat", self.max_lat - self.min_lat)):
            if span < MIN_SPAN_DEG:
                out.append(f"{axis} span {span:.4f} deg is below the {MIN_SPAN_DEG} deg floor")
            elif span > MAX_SPAN_DEG:
                out.append(f"{axis} span {span:.4f} deg is above the {MAX_SPAN_DEG} deg ceiling")
        return out

    def as_osmium(self) -> str:
        """osmium extract's --bbox form: left,bottom,right,top."""
        return f"{self.min_lon},{self.min_lat},{self.max_lon},{self.max_lat}"


@dataclass(frozen=True)
class Region:
    id: str
    name: str
    counties: tuple[str, ...]
    bbox: BBox
    counts: dict[str, int] = field(default_factory=dict)

    def problems(self) -> list[str]:
        out = [f"bbox: {p}" for p in self.bbox.problems()]
        if not self.id or not self.id.replace("-", "").replace("_", "").isalnum():
            out.append(f"id is not a usable directory name: {self.id!r}")
        if not self.name:
            out.append("name is empty")
        if not self.counties:
            out.append("counties is empty - name what the bbox is meant to cover, so it can be argued with")
        for cls, n in self.counts.items():
            if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                out.append(f"counts[{cls}] is not a count: {n!r}")
        return out


def load(region_id: str, root: Path | None = None) -> Region:
    """Read regions/<id>/region.json. Raises ValueError listing every problem, not just the first."""
    path = (root or REGIONS) / region_id / "region.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    # Keys beginning with _ are prose for humans reading the file; they are never read back as data.
    unknown = [k for k in data if not k.startswith("_") and k not in
               {"id", "name", "counties", "bbox", "counts"}]
    if unknown:
        raise ValueError(f"{path}: unknown field(s): {unknown}")
    b = data.get("bbox") or {}
    region = Region(
        id=data.get("id", ""),
        name=data.get("name", ""),
        counties=tuple(data.get("counties") or ()),
        bbox=BBox(b.get("min_lon", float("nan")), b.get("min_lat", float("nan")),
                  b.get("max_lon", float("nan")), b.get("max_lat", float("nan"))),
        counts=dict(data.get("counts") or {}),
    )
    problems = region.problems()
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return region
