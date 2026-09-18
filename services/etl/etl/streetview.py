"""Street View links for scoring review: coordinates and a heading, turned into a URL a human clicks.

WHY THIS EXISTS. The slowest step in this product is a person driving somewhere. Human gate #1 is five real
commutes with a verdict on each and gate #2 is twenty more, both `runs_on: human` pins that expire after 30
days - so they recur, and every scoring change wants re-validation.

WHAT IT DOES NOT REPLACE. Gate #1 asks whether the ROUTE was better than the freeway: pacing, traffic,
whether the pretty part arrives while you still have the patience for it. No photograph answers that. What
this answers is the cheaper question that currently rides along with the drive - DOES THIS SEGMENT LOOK
ANYTHING LIKE ITS SCORE - and that is where the bad ones are: a 9.2 on an access road behind a business
park, a 2.1 on a lovely lane the canopy layer missed. Catching those before a drive is what makes the drive
worth doing.

THE LEGAL LINE, AND IT IS A REAL ONE. This product deliberately avoids Google: the Maps terms forbid showing
their imagery alongside a non-Google map, which is why the app uses MapLibre and Protomaps. THAT CONSTRAINT
IS ABOUT THE APP. This module emits a URL that a developer opens in a browser, which is a person using
Google Maps normally.

  * Links only. Never the Street View Static API, never fetched, never cached, never embedded, and nothing
    from this module ever ships inside the app.
  * It lives in services/etl, a build-time tool, and imports nothing from the app.

Anyone tempted to "helpfully" pull the imagery inline should read the paragraph above first: doing so would
make the product's map stack a licensing problem rather than a technical choice.
"""
from __future__ import annotations

import math
from urllib.parse import quote

# google.com/maps/@?api=1 is the documented, key-free URL form. `map_action=pano` opens Street View at the
# viewpoint; `heading` aims the camera. Deliberately not the Static API - that one takes a key, bills per
# request, and returns an IMAGE, which is the thing this must never do.
BASE = "https://www.google.com/maps/@"

# Below this the two points are effectively the same coordinate and any bearing computed from them is noise
# amplified to a direction. 1 m is well under a GPS fix and far under OSM node spacing on a road.
MIN_BEARING_SPAN_M = 1.0


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float | None:
    """Initial great-circle bearing from point 1 to point 2, in degrees clockwise from north.

    None when the two points are too close to define a direction. A panorama facing a wall is useless, and
    the wrong heading is worse than none: it looks like an answer. Callers must handle None by omitting the
    heading rather than substituting 0, which means due north and would be a silent lie.
    """
    for v in (lat1, lon1, lat2, lon2):
        if v != v:                       # NaN
            return None
    # A cheap span check first, in metres, using the local scale. Doing this in degrees would treat a
    # longitude step near the pole as far larger than it is.
    dlat_m = (lat2 - lat1) * 111_320.0
    dlon_m = (lon2 - lon1) * 111_320.0 * math.cos(math.radians((lat1 + lat2) / 2.0))
    if math.hypot(dlat_m, dlon_m) < MIN_BEARING_SPAN_M:
        return None

    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def pano_url(lat: float, lon: float, heading: float | None = None) -> str:
    """A Street View link at a point, optionally facing a bearing.

    Coordinates are emitted at 6 decimal places - about 0.1 m, past any precision this data has. They are
    NOT truncated to 2dp the way coordinates sent to our own server are (P-PRIV-05): that rule protects a
    USER's location, and this is a road in a build-time review sheet opened by the developer.
    """
    if lat != lat or lon != lon:
        raise ValueError(f"not a coordinate: {lat!r}, {lon!r}")
    if not -90.0 <= lat <= 90.0 or not -180.0 <= lon <= 180.0:
        raise ValueError(f"coordinate out of range: {lat}, {lon}")
    q = [f"api=1", "map_action=pano", f"viewpoint={lat:.6f},{lon:.6f}"]
    if heading is not None:
        if heading != heading:
            raise ValueError("heading is NaN")
        q.append(f"heading={heading % 360.0:.1f}")
    return BASE + "?" + "&".join(q)


def look_along(points: list[tuple[float, float]], at: int = 0) -> str:
    """A link that looks ALONG a road rather than at it, given the road's own geometry.

    `at` indexes the point to stand on. The heading comes from that point to the NEXT one, falling back to
    the previous one at the end of the way - a road drawn in either direction should aim the same way along
    itself, and a way with a single point gets no heading at all rather than a fabricated one.
    """
    if not points:
        raise ValueError("no geometry")
    if not 0 <= at < len(points):
        raise IndexError(f"point {at} of {len(points)}")
    lat, lon = points[at]
    b = None
    if at + 1 < len(points):
        b = bearing(lat, lon, *points[at + 1])
    if b is None and at > 0:
        b = bearing(*points[at - 1], lat, lon)
    return pano_url(lat, lon, b)


def midpoint_index(points: list[tuple[float, float]]) -> int:
    """The point nearest the middle of a way BY LENGTH, not by index.

    Reviewing the middle matters: the ends of an OSM way are junctions, which look like every other
    junction. And by index is the wrong middle - OSM node density varies wildly, so the index midpoint of a
    way with a dense curve at one end sits inside that curve rather than halfway along the road.
    """
    if not points:
        raise ValueError("no geometry")
    if len(points) < 3:
        return 0
    # Cumulative distance AT EACH POINT, starting at 0 for the first.
    cum = [0.0]
    for a, b in zip(points, points[1:]):
        d = math.hypot((b[0] - a[0]) * 111_320.0,
                       (b[1] - a[1]) * 111_320.0 * math.cos(math.radians((a[0] + b[0]) / 2.0)))
        cum.append(cum[-1] + d)
    if cum[-1] <= 0.0:
        return 0                      # every point identical: no middle to find
    half = cum[-1] / 2.0
    # The POINT nearest the half-length. The first draft returned the index of the SEGMENT containing the
    # half-way mark, which for an evenly drawn way is segment 0 - so `midpoint_index` returned the START of
    # the road while its docstring promised the middle. Found by running it on three points of Sunset and
    # getting index 0.
    return min(range(len(cum)), key=lambda i: abs(cum[i] - half))
