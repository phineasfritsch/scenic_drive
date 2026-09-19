"""The access rule: whether a way's own tags refuse the public, in ONE place, for every consumer.

WHY IT IS ITS OWN MODULE (T-0217, ruling R3). Two things in this package have to answer "does this way
refuse the public": `assemble.gate_reason`, which gates the SCORE for safety, and `extractadapter`, which
fills the corpus's `access_ok` column - the column the hazard strip and the device router read. Until
T-0217 the rule was spelled inside `gate_reason` only, as two branches, and the converter that fed
`corpus.build` real ways was a throwaway outside the tree with its own, WIDER list. Two spellings of a
safety rule in one repository is the defect; this module is the one spelling both import.

TWO BRANCHES, ONE ANSWER, and both are `Gates.verdict`'s (Sources/ScenicKit/Gates/Gates.swift:160 and
:161). `GateReason.swift:31` writes them as a single case - "`access` forbids the public, or
`motor_vehicle = no`" - and `assemble.GATE_NO_ACCESS` is that one name.

`motor_vehicle` REFUSES ON ONE VALUE, NOT ON THE SET. `motor_vehicle=destination` and `=permit` are NOT
refused by `Gates.verdict`, and widening this key to `CLOSED_ACCESS` would refuse roads ScenicKit routes -
a gate stricter in the corpus than in the router is the same drift in the other direction. T-0206's
measurement adapter widened it exactly that way, over one list read against both keys, and on the canyon
window alone that refused 85 `access=customers` ways and 54 `motor_vehicle=private` ways the router allows
while letting through the 22 `access=destination` ways it refuses.

THE RULE IS ASKED ON ITS OWN. `gate_reason` returns the FIRST rule that fires, in `Gates.verdict`'s order,
so a private dirt road answers `unpaved_surface` and a private track answers `track`. Anything deriving
"may the public drive here" from that answer grants both of them access - the defect the 06:13 panel
corrected on this task's acceptance, and way 1206170836 of the canyon window is exactly such a road.
"""
from __future__ import annotations

ACCESS_KEY = "access"
# Gates.swift:89, verbatim.
CLOSED_ACCESS = frozenset({"private", "no", "permit", "destination"})
# Gates.swift:161, the other half of the `noAccess` rule. One value, not a set - see the docstring.
MOTOR_VEHICLE_KEY = "motor_vehicle"
MOTOR_VEHICLE_REFUSED = "no"


def access_refused(tags: dict) -> bool:
    """True when these tags refuse the public. Absent keys are not a refusal: positive evidence only."""
    return (tags.get(ACCESS_KEY) in CLOSED_ACCESS
            or tags.get(MOTOR_VEHICLE_KEY) == MOTOR_VEHICLE_REFUSED)
