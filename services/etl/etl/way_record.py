"""One way's terms on their way to `score.score`, and which state they are in.

WHY A RECORD AND NOT A DICT. `score.score` is keyword-only (score.py:119-122) and every term it takes must
already be in 0..1 (`out_of_range`, score.py:95-106). The producers on main do not hand over 0..1:
`curvature.way_curvature` returns a sum of weighted segment lengths (curvature.py:172), `terrain.
elevation_gain` metres of climb (terrain.py:85), `terrain.relief` metres of range (terrain.py:112), while
`landcover.fractions` is already a fraction (landcover.py:87). A dict cannot say which of those a number is,
so nothing stops a metre count being passed as a unit term - and `score.score` would answer None, three
stages downstream of the mistake. This record says it in the type: every term is declared RANKED (arrives
RAW, leaves as a region percentile rank), MAPPED (arrives and leaves 0..1) or DEFERRED, and the record
carries the `terms_state` it is in.

THE THREE STATES.
  raw         - the ranked fields hold producer units. `score_kwargs()` REFUSES in this state.
  normalised  - the ranked fields hold region percentile ranks in 0..1 (`normalise.normalise_region`).
  excluded    - the way is one of `byways.SCENIC_ZERO_CLASSES`. It was left out of the ranking population
                (15k motorway segments must not set the curve for back roads) and its ranked fields hold
                `EXCLUDED_RANK`, which is NOT a measurement.

WHY `excluded` IS A STATE AND NOT A PASS-THROUGH. `score.score` refuses out-of-range terms at score.py:131
BEFORE it reaches the zero-class branch at score.py:139. A motorway row that kept its raw metres therefore
returns None rather than 0.0 - the corpus would carry "unknown" for the one class the plan is most explicit
about (plan:83, CLAUDE.md "Product invariants"). So the ranked fields of an excluded way are pinned to one
named constant and the validator enforces that equality by field name.

WHY THE INVERSIONS ARE NOT HERE. `score.scenery_mean` enters `impervious` and `furniture` as `(1 - x)`
(score.py:89, :92). This record carries the term the way its producer states it - a furniture RATE, ranked -
because two inversions cancel and no single-module test would ever see it.

`points_of_interest` IS DEFERRED, NOT DEFAULTED. It is ranked within 50 km with its top decile penalised
(plan:89), which needs the road network, and it is T-0164. Until it lands the field is None, `flags()` says
so by name, and `score_kwargs()` substitutes `POI_ABSENT`. A silent 0.5 would be indistinguishable from a
measured 0.5 in the corpus.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace

from .byways import SCENIC_ZERO_CLASSES

# Arrives in producer units, leaves as a region percentile rank (see `normalise`). Ruling R1 in the task log.
RANKED_TERMS = ("curvature", "elevation_gain", "relief", "sinuosity", "furniture")
# Arrives in 0..1 and is passed through: a measured fraction, or a designed 0..1 function (speed_fit).
MAPPED_TERMS = ("canopy", "impervious", "water", "speed_fit")
# Not ours to produce yet. T-0164.
DEFERRED_TERMS = ("points_of_interest",)
# Every keyword `score.score` takes. The test asserts this against score.py rather than trusting the list.
SCORE_TERMS = RANKED_TERMS + MAPPED_TERMS + DEFERRED_TERMS
# What a caller must state. Everything else has a default that means something (no byway, no tunnel, no
# motorway anywhere near, `points_of_interest` not yet produced) - a term does not.
REQUIRED_FIELDS = ("way_id", "highway") + RANKED_TERMS + MAPPED_TERMS

RAW = "raw"
NORMALISED = "normalised"
EXCLUDED = "excluded"
TERM_STATES = (RAW, NORMALISED, EXCLUDED)
# The states in which the ranked fields are 0..1 and `score_kwargs()` will answer.
SCORABLE_STATES = (NORMALISED, EXCLUDED)

# What a zero-class way's ranked fields hold. Not a rank, not a measurement: the way was never in the
# population. Its score is 0.0 by class (score.py:139) whatever this value is.
EXCLUDED_RANK = 0.0
# What `score_kwargs()` passes for an absent `points_of_interest`, with `POI_ABSENT_FLAG` alongside it.
POI_ABSENT = 0.0
POI_ABSENT_FLAG = "points_of_interest_absent"


@dataclass(frozen=True)
class WayRecord:
    """The terms of one way, plus the tags and distances `score.score` reads directly.

    Frozen: a normalisation returns new records (`with_ranks`, `excluded_from_population`) so a half-ranked
    region cannot exist. Construct from untrusted input with `from_mapping`, which names unknown fields.
    """

    way_id: int
    highway: str
    curvature: float
    elevation_gain: float
    relief: float
    sinuosity: float
    furniture: float
    canopy: float
    impervious: float
    water: float
    speed_fit: float
    points_of_interest: float | None = None
    surface: str | None = None
    byway_status: str | None = None
    tunnel_meters: float = 0.0
    meters_to_nearest_motorway: float = math.inf
    terms_state: str = RAW

    @property
    def is_zero_class(self) -> bool:
        """plan:83 - scores 0 and is still routable. Imported from `byways`, never restated."""
        return self.highway in SCENIC_ZERO_CLASSES

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(f.name for f in fields(cls))

    @classmethod
    def from_mapping(cls, mapping: dict) -> "WayRecord":
        """A record from a plain mapping, naming every field it should not have set and every one it must.

        `WayRecord(**mapping)` raises TypeError with one field in the message; a fixture row or a producer
        dict that drifted usually has several, and finding them one run at a time is how a wrong column name
        survives an afternoon.
        """
        known = set(cls.field_names())
        unknown = sorted(set(mapping) - known)
        if unknown:
            raise ValueError("way record sets unknown field(s): %s" % ", ".join(unknown))
        missing = sorted(name for name in REQUIRED_FIELDS if name not in mapping)
        if missing:
            raise ValueError("way record is missing field(s): %s" % ", ".join(missing))
        return cls(**mapping)

    def problems(self) -> list[str]:
        """Everything wrong with this record, BY FIELD NAME. Empty means usable.

        Reported rather than raised, and never clamped, for `score.out_of_range`'s reason (score.py:97-99):
        a plausible number computed from a wrong input is the hardest kind of error to find later. The
        ranked fields are checked against the state the record says it is in, which is the only way a raw
        metre count can be told apart from a rank of 0.6.
        """
        out: list[str] = []
        if self.terms_state not in TERM_STATES:
            out.append("terms_state=%r is not one of %s" % (self.terms_state, ", ".join(TERM_STATES)))
        if not isinstance(self.way_id, int) or isinstance(self.way_id, bool) or self.way_id <= 0:
            out.append("way_id=%r is not a positive integer" % (self.way_id,))
        if not isinstance(self.highway, str) or not self.highway:
            out.append("highway=%r is not a highway class" % (self.highway,))
        for name in ("surface", "byway_status"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                out.append("%s=%r is neither a string nor None" % (name, value))
        out.extend(self._ranked_problems())
        for name in MAPPED_TERMS:
            out.extend(_unit_problem(name, getattr(self, name)))
        if self.points_of_interest is not None:
            out.extend(_unit_problem("points_of_interest", self.points_of_interest))
        tunnel = _as_float(self.tunnel_meters)
        if tunnel is None or not math.isfinite(tunnel) or tunnel < 0.0:
            # score.score refuses an infinite tunnel too (score.py:133): a tunnel of unknown length is not
            # a tunnel of every length.
            out.append("tunnel_meters=%r is not a finite non-negative length" % (self.tunnel_meters,))
        distance = _as_float(self.meters_to_nearest_motorway)
        if distance is None or math.isnan(distance) or distance < 0.0:
            out.append("meters_to_nearest_motorway=%r is not a non-negative distance or infinity"
                       % (self.meters_to_nearest_motorway,))
        return out

    def _ranked_problems(self) -> list[str]:
        out: list[str] = []
        for name in RANKED_TERMS:
            value = _as_float(getattr(self, name))
            if value is None or not math.isfinite(value):
                out.append("%s=%r is not a finite number" % (name, getattr(self, name)))
            elif self.terms_state == RAW:
                if value < 0.0:
                    out.append("%s=%r is negative; producer units are non-negative" % (name, value))
            elif self.terms_state == EXCLUDED:
                if value != EXCLUDED_RANK:
                    out.append("%s=%r is not EXCLUDED_RANK (%r); an excluded way holds no rank"
                               % (name, value, EXCLUDED_RANK))
            else:
                out.extend(_unit_problem(name, value))
        return out

    def flags(self) -> tuple[str, ...]:
        """The names of this record's explicit absences. What the hazard strip and `meta` are told."""
        return (POI_ABSENT_FLAG,) if self.points_of_interest is None else ()

    def with_ranks(self, ranks: dict) -> "WayRecord":
        """This record with its ranked fields replaced, `terms_state` -> normalised. Refuses by name."""
        self._require_raw("rank")
        missing = sorted(set(RANKED_TERMS) - set(ranks))
        unexpected = sorted(set(ranks) - set(RANKED_TERMS))
        if missing or unexpected:
            raise ValueError("way %d: ranks for %s, missing %s, unexpected %s"
                             % (self.way_id, ", ".join(RANKED_TERMS), missing or "nothing",
                                unexpected or "nothing"))
        return replace(self, terms_state=NORMALISED, **{n: float(ranks[n]) for n in RANKED_TERMS})

    def excluded_from_population(self) -> "WayRecord":
        """This record with its ranked fields pinned to `EXCLUDED_RANK`. Ruling R3. Refuses by name."""
        self._require_raw("exclude")
        if not self.is_zero_class:
            raise ValueError("way %d: highway=%s is scorable, so it belongs in the population"
                             % (self.way_id, self.highway))
        return replace(self, terms_state=EXCLUDED, **{n: EXCLUDED_RANK for n in RANKED_TERMS})

    def _require_raw(self, verb: str) -> None:
        if self.terms_state != RAW:
            raise ValueError("way %d: cannot %s a record whose terms_state is %s"
                             % (self.way_id, verb, self.terms_state))

    def score_kwargs(self) -> dict:
        """Exactly `score.score`'s keywords. Refuses while the terms are raw, rather than scoring metres."""
        if self.terms_state not in SCORABLE_STATES:
            raise ValueError("way %d: terms_state is %s; normalise the region before scoring"
                             % (self.way_id, self.terms_state))
        problems = self.problems()
        if problems:
            raise ValueError("way %d: %s" % (self.way_id, "; ".join(problems)))
        out = {name: float(getattr(self, name)) for name in RANKED_TERMS + MAPPED_TERMS}
        poi = self.points_of_interest
        out["points_of_interest"] = POI_ABSENT if poi is None else float(poi)
        out["highway"] = self.highway
        out["surface"] = self.surface
        out["byway_status"] = self.byway_status
        out["tunnel_meters"] = float(self.tunnel_meters)
        out["meters_to_nearest_motorway"] = float(self.meters_to_nearest_motorway)
        return out


def _as_float(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _unit_problem(name: str, value) -> list[str]:
    """`score.out_of_range`'s rule (score.py:104), reported by field name before the scorer ever sees it."""
    number = _as_float(value)
    if number is None:
        return ["%s=%r is not a number" % (name, value)]
    if not math.isfinite(number) or number < 0.0 or number > 1.0:
        return ["%s=%r is outside 0..1" % (name, number)]
    return []
