"""The scenic score: GATE x M^0.35 x E^0.65.

    M = 0.45*curv + 0.20*elev_gain + 0.20*speed_fit + 0.15*sinuosity
    E = 0.24*canopy + 0.22*relief + 0.16*(1-impervious) + 0.14*poi + 0.12*water + 0.12*(1-furniture)
        + byway bonus, capped

Three decisions in that expression carry the whole product, and each is easy to "simplify" into something
that scores plausibly and ranks wrongly.

**The geometric mean.** A weighted SUM lets one strong term carry a road that is otherwise dull: a curvy
industrial service road maxes `curv` and rides it to a good score. The product cannot - a road has to be
*both* fun to drive and pleasant to look at, because M near zero drags the whole thing down however high E
is. That is the entire reason the score is a product of two means rather than one mean of eight terms, and
the rank-order fixture exists to catch anyone flattening it.

**alpha = 0.35 on M, 0.65 on E.** Scenery-led, because this is a car product and not a motorcycle one. A
motorcycle app would invert those. The exponents also mean a middling road cannot be rescued by either half.

**The gates are POSITIVE EVIDENCE only, and they are SAFETY only.** Unpaved with evidence, private, no
access, track: those zero the score, because sending a sedan there is a safety failure. Motorway and trunk
score 0 on scenery and are NOT gated - they are penalised by the router instead. Almost every Bay Area
commute over 15 km needs freeway shoulders around a scenic middle, and gating them makes those routes
unroutable rather than unattractive. CLAUDE.md states this as a product invariant; it is restated here
because this file is where somebody would "tidy" it.
"""
from __future__ import annotations

import math

ALPHA_M = 0.35
ALPHA_E = 0.65

# The M terms: how the road drives.
M_WEIGHTS = {
    "curv": 0.45,
    "elev_gain": 0.20,
    "speed_fit": 0.20,
    "sinuosity": 0.15,
}
# The E terms: what there is to look at. `impervious` and `furniture` enter inverted - the score wants the
# ABSENCE of parking lot and the ABSENCE of signage clutter.
E_WEIGHTS = {
    "canopy": 0.24,
    "relief": 0.22,
    "impervious_inv": 0.16,
    "poi": 0.14,
    "water": 0.12,
    "furniture_inv": 0.12,
}
INVERTED_TERMS = {"impervious_inv": "impervious", "furniture_inv": "furniture"}

BYWAY_CAP = 0.15

# Road classes that score zero on scenery but are NEVER gated.
ZERO_SCORE_CLASSES = frozenset({"motorway", "motorway_link", "trunk", "trunk_link"})

# Gates. Every one is POSITIVE evidence of a hazard, never an absence of evidence: a way with no `surface`
# tag is not gated, because "unknown" is not "unpaved", and gating on absence would remove most rural roads
# in the region - the ones this product exists to find.
UNPAVED_SURFACES = frozenset({
    "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel", "earth", "mud", "grass",
})
BLOCKED_ACCESS = frozenset({"private", "no", "permit", "destination"})
GATED_SERVICE = frozenset({"driveway", "parking_aisle", "drive-through", "parking", "emergency_access"})


def gate_reasons(tags: dict) -> list[str]:
    """Every reason this way is unsafe to route a standard car onto. Empty means passable.

    Reasons rather than a boolean, so `ops/route-autopsy` can say WHY a road was excluded. A gate that
    reports only "0" is a gate nobody can argue with, and this set will be argued with.
    """
    out = []
    surface = (tags.get("surface") or "").strip().lower()
    if surface in UNPAVED_SURFACES:
        out.append(f"surface={surface}")
    tracktype = (tags.get("tracktype") or "").strip().lower()
    if tracktype in {"grade3", "grade4", "grade5"}:
        out.append(f"tracktype={tracktype}")
    if (tags.get("highway") or "").strip().lower() == "track":
        out.append("highway=track")
    for key in ("access", "motor_vehicle", "vehicle"):
        value = (tags.get(key) or "").strip().lower()
        if value in BLOCKED_ACCESS:
            out.append(f"{key}={value}")
    if (tags.get("highway") or "").strip().lower() == "service":
        service = (tags.get("service") or "").strip().lower()
        if service in GATED_SERVICE:
            out.append(f"service={service}")
    if (tags.get("barrier") or "").strip().lower() == "gate" and \
            (tags.get("locked") or "").strip().lower() == "yes":
        out.append("barrier=gate+locked=yes")
    if (tags.get("ford") or "").strip().lower() in {"yes", "stream"}:
        out.append("ford=yes")
    return out


def is_gated(tags: dict) -> bool:
    return bool(gate_reasons(tags))


def scores_zero(tags: dict) -> bool:
    """Motorway and trunk: dull, not dangerous. Zero scenery, never gated."""
    return (tags.get("highway") or "").strip().lower() in ZERO_SCORE_CLASSES


def weighted(terms: dict, weights: dict) -> float:
    """Weighted mean over the named terms. A missing term counts as 0 and its weight still counts.

    Not renormalised over the terms that happen to be present: a road we know nothing about must not score
    like a road we know is good. Renormalising would let a way with only `canopy` measured score as though
    every other term matched it.
    """
    total = 0.0
    for name, weight in weights.items():
        source = INVERTED_TERMS.get(name)
        if source is not None:
            value = terms.get(source)
            value = 0.0 if value is None else 1.0 - float(value)
        else:
            value = terms.get(name)
            value = 0.0 if value is None else float(value)
        total += weight * max(0.0, min(1.0, value))
    return total


def mean_m(terms: dict) -> float:
    return weighted(terms, M_WEIGHTS)


def mean_e(terms: dict, byway_bonus: float = 0.0) -> float:
    """E plus the capped byway bonus, clamped to 1.

    Clamped rather than allowed past 1, because E is a mean of fractions and the exponent is only meaningful
    on [0, 1]. A road already at 0.95 that is also a byway is not 1.10 scenic.
    """
    return min(1.0, weighted(terms, E_WEIGHTS) + min(BYWAY_CAP, max(0.0, byway_bonus)))


def score(terms: dict, tags: dict | None = None, byway_bonus: float = 0.0) -> float:
    """The scenic score in [0, 1]."""
    tags = tags or {}
    if is_gated(tags) or scores_zero(tags):
        return 0.0
    m = mean_m(terms)
    e = mean_e(terms, byway_bonus)
    if m <= 0.0 or e <= 0.0:
        return 0.0
    return (m ** ALPHA_M) * (e ** ALPHA_E)


def explain(terms: dict, tags: dict | None = None, byway_bonus: float = 0.0) -> dict:
    """The score with its parts, for `ops/route-autopsy` and for arguing with."""
    tags = tags or {}
    gates = gate_reasons(tags)
    zero = scores_zero(tags)
    m = mean_m(terms)
    e = mean_e(terms, byway_bonus)
    return {
        "score": 0.0 if (gates or zero) else round(score(terms, tags, byway_bonus), 4),
        "M": round(m, 4),
        "E": round(e, 4),
        "gated": bool(gates),
        "gate_reasons": gates,
        "zero_scored_class": zero,
        "byway_bonus": round(min(BYWAY_CAP, max(0.0, byway_bonus)), 4),
    }


def weight_problems() -> list[str]:
    """The weights must sum to 1 in each mean, and the exponents to 1.

    Anchored on the constants rather than on a comment, because a weight quietly edited from 0.24 to 0.34 is
    invisible in a diff review and changes every score in the region.
    """
    out = []
    for name, weights in (("M", M_WEIGHTS), ("E", E_WEIGHTS)):
        total = sum(weights.values())
        if not math.isclose(total, 1.0, abs_tol=1e-9):
            out.append(f"{name} weights sum to {total}, not 1")
    if not math.isclose(ALPHA_M + ALPHA_E, 1.0, abs_tol=1e-9):
        out.append(f"exponents sum to {ALPHA_M + ALPHA_E}, not 1")
    if ALPHA_E <= ALPHA_M:
        out.append("the score is meant to be scenery-led: ALPHA_E must exceed ALPHA_M")
    return out
