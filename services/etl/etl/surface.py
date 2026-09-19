"""The three-state surface column: what -1, 0 and 1 mean, and the one rule that decides which one a way gets.

WHY THREE STATES. A two-valued `paved` column erases the state the product is built on. Most rural lanes
carry no `surface` tag at all, so "not known to be paved" and "known to be unpaved" are different facts about
different roads, and collapsing them costs one of two things: either unsurveyed lanes are treated as unpaved
and the router refuses the roads this app exists to find, or they are treated as surveyed and the driver is
never told. The plan takes the third option - score x0.8 and a `surface_unknown` flag on the hazard strip -
and that needs a column that can say "unknown".

    -1  UNKNOWN   no surface tag, on a class where an absent tag means we do not know
     0  UNPAVED   positive evidence of an unpaved road
     1  PAVED     everything else

THE RULE IS score.py's, CALLED, NOT COPIED. `score.raises_surface_unknown_flag` (score.py:116) is
`surface is None and highway in UNSURVEYED_CLASSES`, and `surface_state` invokes it rather than restating
its condition. The corpus and the scorer must not be able to disagree about the same way while each file is
internally consistent - that is precisely the defect this column exists to fix, and a second copy of the
rule would reintroduce it one edit later.

-1 IS THE FLAG, NOT THE RAW FACT. An absent tag on primary/secondary/tertiary is PAVED, because score.py
says so in those words (score.py:67-68: the plan's other half "is this set's complement and is expressed by
omission"). So the corpus cannot afterwards distinguish an untagged primary from one tagged `asphalt`.
Nothing needs that distinction: the score treats them identically and the flag fires for neither. The
alternative - store "no tag at all" and let the device re-derive the flag from (surface, highway) - was
rejected because it puts score.py:116 on the device as a second implementation of the same rule.

A PRESENT TAG THAT IS NOT UNPAVED IS PAVED. `cobblestone`, `sett`, `asphalt`, `concrete` and every value
nobody has thought of are all 1. That is not laziness: `Gates` refuses only on positive unpaved evidence
(Gates.swift:153) and the score flags only an absent tag, so a fourth state would be a state no consumer of
this column has a rule for.

UNPAVED_SURFACES IS A COPY ACROSS A LANGUAGE BOUNDARY, AND THAT IS A KNOWN DEFECT. score.py deliberately
holds no gate list (score.py:29-32: the safety gates "live in the GraphHopper profile and in
`ScenicKit.Gates`, never here"), so there is nothing in this package to import. The list below is the plan's
line 80, already typed out once at Sources/ScenicKit/Gates/Gates.swift:80-82 as `unpavedSurfaces`. P-PROD-01
is the pin that will drive one fixture set through the ETL, the routing profile and ScenicKit and assert
they agree; its assertion is still TODO. Until then the only defence is that both copies are seven literals
in one place each, asserted value by value in their own test suites.
"""
from __future__ import annotations

from .score import raises_surface_unknown_flag

# plan:80, verbatim. Mirrors Sources/ScenicKit/Gates/Gates.swift:80-82 `Gates.unpavedSurfaces`.
UNPAVED_SURFACES = frozenset({
    "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",
})

SURFACE_UNKNOWN = -1
SURFACE_UNPAVED = 0
SURFACE_PAVED = 1

# The CHECK constraint's domain, as data. schema.DDL spells the same three values as literal SQL text - the
# DDL is an ordered tuple of statements whose exact bytes are the artifact (schema.py, top) and must not be
# assembled from an f-string - so the test asserts the literal against this tuple instead.
SURFACE_STATES = (SURFACE_UNKNOWN, SURFACE_UNPAVED, SURFACE_PAVED)
SURFACE_STATE_NAMES = {SURFACE_UNKNOWN: "unknown", SURFACE_UNPAVED: "unpaved", SURFACE_PAVED: "paved"}


def surface_state(*, highway: str, surface: str | None) -> int:
    """-1, 0 or 1 for one way, from its `highway` class and its raw `surface` tag value (None = no tag).

    Order matters and is the plan's "positive evidence only": a tagged `surface=gravel` residential is
    UNPAVED, not UNKNOWN. The tag is there; it says something; it is believed.
    """
    if surface is not None and surface in UNPAVED_SURFACES:
        return SURFACE_UNPAVED
    if raises_surface_unknown_flag(highway=highway, surface=surface):
        return SURFACE_UNKNOWN
    return SURFACE_PAVED
