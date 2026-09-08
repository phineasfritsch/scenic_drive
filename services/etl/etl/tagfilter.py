"""What the Bay Area extract keeps, expressed as osmium tags-filter expressions.

The load-bearing decision here is what is NOT dropped. Motorway and trunk ways score 0 and are penalised by
the router, but they are never excluded: almost every Bay Area commute over 15 km needs freeway shoulders
around a scenic middle, and an extract that "cleans up" motorways makes those routes unroutable rather than
unattractive. Same for track and private ways - they are SAFETY gates in the routing profile, applied to tags
that must therefore still be in the graph. A filter that drops them moves a gate from the router (where it is
tested) into the data (where it is invisible).
"""
from __future__ import annotations

# highway= values kept, grouped into the classes the counts are reported per. The grouping is the reporting
# unit, not a routing concept: it exists so "residential collapsed by 40%" is a sentence someone can read.
WAY_CLASSES: dict[str, tuple[str, ...]] = {
    "motorway": ("motorway", "motorway_link"),
    "trunk": ("trunk", "trunk_link"),
    "primary": ("primary", "primary_link"),
    "secondary": ("secondary", "secondary_link"),
    "tertiary": ("tertiary", "tertiary_link"),
    "unclassified": ("unclassified",),
    "residential": ("residential",),
    "living_street": ("living_street",),
    "service": ("service",),
    # Kept deliberately: `road_class == TRACK` is a zero-gate in the routing profile (P-SAFE-01). A gate can
    # only be tested against data that still contains the thing being gated.
    "track": ("track",),
    "road": ("road",),
}

# Places the Surprise Me corpus draws from. Deliberately narrow: an allowlist, never "everything tagged
# tourism". Each entry is (osmium object types, key, values).
POI_CLASSES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "viewpoint": ("n", "tourism", ("viewpoint",)),
    "picnic_site": ("nw", "tourism", ("picnic_site",)),
    "attraction": ("nw", "tourism", ("attraction",)),
    "peak": ("n", "natural", ("peak",)),
    "waterfall": ("n", "waterway", ("waterfall",)),
    "beach": ("nw", "natural", ("beach",)),
    "park": ("wr", "leisure", ("park",)),
    "nature_reserve": ("wr", "leisure", ("nature_reserve",)),
}

# The classes whose disappearance would break routing rather than merely thin the corpus. Named here so the
# check is a list someone can extend, not a comment someone can ignore.
ROUTING_CRITICAL = ("motorway", "trunk", "primary", "secondary", "tertiary", "residential")


def way_expression(cls: str) -> str:
    """osmium tags-filter expression for one way class, e.g. `w/highway=motorway,motorway_link`."""
    return "w/highway=" + ",".join(WAY_CLASSES[cls])


def poi_expression(cls: str) -> str:
    types, key, values = POI_CLASSES[cls]
    return f"{types}/{key}=" + ",".join(values)


def class_expression(cls: str) -> str:
    """The expression that isolates one reporting class, whichever kind it is."""
    if cls in WAY_CLASSES:
        return way_expression(cls)
    if cls in POI_CLASSES:
        return poi_expression(cls)
    raise KeyError(f"unknown feature class: {cls!r}")


def class_spec(cls: str) -> tuple[str, str, tuple[str, ...]]:
    """(object types, key, values) for any class. Way classes are `w/highway=...` in the same shape."""
    if cls in WAY_CLASSES:
        return "w", "highway", WAY_CLASSES[cls]
    if cls in POI_CLASSES:
        return POI_CLASSES[cls]
    raise KeyError(f"unknown feature class: {cls!r}")


def class_types(cls: str) -> tuple[str, ...]:
    """The osmium object types a class can match, one character each."""
    return tuple(class_spec(cls)[0])


def typed_expression(cls: str, obj_type: str) -> str:
    """One class restricted to ONE object type, e.g. `w/natural=beach`.

    Counting needs this. `osmium tags-filter` keeps the nodes a matching way refers to - correctly, since the
    output has to stay a usable OSM file - so the node count of an `nw/...` filter is tagged nodes PLUS way
    geometry, which is not a count of anything. Filtering one type at a time and reading only that type's
    tally gives the real number, and `--omit-referenced` is not the way to get it: it strips the locations
    `osmium fileinfo --extended` needs, which fails with "Geometry error: Invalid location".
    """
    types, key, values = class_spec(cls)
    if obj_type not in types:
        raise KeyError(f"{cls} does not match object type {obj_type!r} (only {types!r})")
    return f"{obj_type}/{key}=" + ",".join(values)


def all_classes() -> tuple[str, ...]:
    return tuple(WAY_CLASSES) + tuple(POI_CLASSES)


def keep_expressions() -> list[str]:
    """Every expression the single keep-pass uses. One filter run, not one per class."""
    return [way_expression(c) for c in WAY_CLASSES] + [poi_expression(c) for c in POI_CLASSES]


def problems() -> list[str]:
    """Structural checks on the filter itself, so a bad edit fails here rather than in a route.

    Not a comment: a routing-critical class deleted from WAY_CLASSES makes this return a problem, and the
    test suite fails. The product invariant is that motorways are penalised, never excluded.
    """
    out = []
    for cls in ROUTING_CRITICAL:
        if cls not in WAY_CLASSES:
            out.append(f"{cls} is missing from WAY_CLASSES - routing needs it even when it scores 0")
        elif not WAY_CLASSES[cls]:
            out.append(f"{cls} keeps no highway values")
    seen: dict[str, str] = {}
    for cls, values in WAY_CLASSES.items():
        for v in values:
            if v in seen:
                out.append(f"highway={v} is claimed by both {seen[v]} and {cls}; counts would double-count it")
            seen[v] = cls
    for cls, (types, key, values) in POI_CLASSES.items():
        if not types or set(types) - set("nwr"):
            out.append(f"{cls}: object types {types!r} must be a non-empty subset of n, w, r")
        if not key or not values:
            out.append(f"{cls}: needs a key and at least one value")
    return out
