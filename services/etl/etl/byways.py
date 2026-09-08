"""Designated scenic byways, snapped to our ways.

A byway flag is somebody else's judgement rather than ours: a public agency looked at a road and said it is
scenic. That makes it the second external oracle in the plan, after Curvature, and it is only worth having
if we use their judgement rather than re-deriving one.

WHAT CALTRANS `Status` MEANS. The FeatureServer publishes no coded-value domain for the field (`domain:
null`, checked live), so this comes from the programme's own documents, not from inference:

  E   ELIGIBLE. The LEGISLATURE has listed the route in Streets & Highways Code 263.1-263.8. S&H 263: "The
      state scenic highway system is hereby established and shall be composed of the highways specified in
      this article", and the listed routes are "either eligible for designation as state scenic highways or
      have been so designated". Caltrans's Scenic Highway Guidelines: "Legislative action establishes and
      amends this list" and "Additions and deletions can only be made through legislative action."
      The list is neither arbitrary nor current. It descends from the 1963 Caltrans Master Plan, and the
      Assembly Transportation Committee analysis of AB 998 (Aguiar-Curry, 4/1/2019) records how it was
      built: the eligible highways "were selected by Caltrans based upon five factors" - intrinsic scenic
      value, diversity of experience, links between scenic, historical and recreational points, the
      relationship of the routes to urban areas, and opportunities for bypassing major trans-state routes.
      The Senate analysis of SB 169 (2013) gives the same account.
      So an eligible-only route HAS been screened for scenery: once, coarsely, at route level, in 1963, and
      never again. What it has never had is the per-segment VISUAL ASSESSMENT - vividness, intactness,
      unity, "not more then one-quarter of the proposed scenic highway should be impacted by visual
      intrusions" - which is STEP 1 OF THE NOMINATION a local governing body prepares AFTER the route is
      eligible, in order to apply for designation.

  OD  OFFICIALLY DESIGNATED. Eligible, and then: the local governing body prepared the visual assessment
      and a Scenic Highway Proposal, Caltrans reviewed it, the body adopted a Corridor Protection Program
      limiting development, outdoor advertising and earthmoving, the District Scenic Highway Coordinator
      recommended designation, the District Director concurred, the State Scenic Highway Coordinator
      concurred, and "If the Caltrans Director approves the scenic highway recommendation, the route
      becomes an official State Scenic Highway." Every one of those steps can decline.

TWO EARLIER VERSIONS OF THAT PARAGRAPH WERE WRONG IN OPPOSITE DIRECTIONS, both stated as fact with sources
named inline, which is what made them durable. The first said E was "assessed on the landscape itself" and
the E/OD gap was "administrative, not scenic": that oversold E. The second said flatly that an eligible-only
route "has never had one done": that undersold E by ignoring the 1963 selection. Screened once at route
level on five named factors, never revisited, never assessed per segment - that is the whole claim, and
this paragraph stays so neither correction can be quietly re-lost.

MEASURED, from the pinned pull (`inputs/manifest.yaml`, byways-caltrans.geojson):
  273 features, `Status` in {E: 207, OD: 66}, no other value.
  `DESIG_DATE` is set on all 66 OD rows and blank on 206 of the 207 E rows - designation is an event
    Caltrans records, eligibility is not. The dates run 1965..2007 and 9 of the 66 fall after 1990.
  `MILES` is unusable: 0 or null on 206/207 E rows and 41/66 OD rows. Length here is computed from geometry.
  By centreline length OD is 2512.5 km of 12880.4 km. Every OD route was eligible first, so that share -
    OD_SHARE_OF_SYSTEM below - is the base rate itself.

THE WEIGHTS, AND WHICH PART OF THEM IS A JUDGEMENT.
  OD = DESIGNATED_BONUS, the plan's 0.15: the only status that has cleared a substantive review.
  E  = ELIGIBLE_BONUS, bracketed by two CONSTANTS so this paragraph cannot drift from what is enforced -
       an earlier version of it recorded a ceiling twice as wide as the test's:
       ELIGIBLE_FLOOR = OD_SHARE_OF_SYSTEM x DESIGNATED_BONUS. What an eligible route is worth if it is
         worth only its chance of ever clearing the second gate. Too harsh: most eligible routes never
         clear it because no local government filed a Corridor Protection Program, and having no local
         government to file correlates with being rural, which is what this product exists to find.
       ELIGIBLE_CEILING = half of DESIGNATED_BONUS. Above that, E is being credited with the per-segment
         review that measurably never happened to it.
       ELIGIBLE_BONUS is 40% of OD and about twice the base rate. IT IS A JUDGEMENT. The evidence fixes the
       bracket; it does not fix the point inside it, and no amount of further reading will.

THE CAP. The plan says "+0.15 byway, capped". `capped` governs E's TOTAL, not the bonus term: the six base
E terms already sum to 1.00, so a way at E_base 0.95 that is also designated must land at 1.0, not 1.10.
`apply_to_e` is that cap and it is the only one that binds. MAX_BONUS is the plan's per-term allowance,
enforced by a test over the whole status table - a `min(MAX_BONUS, ...)` at the call site could never bind
at these values and only looked like a check.

MOTORWAYS ARE GATED HERE. S&H 263.3 lists Interstates - Routes 5, 8, 10, 15, 40, 57, 80 - as eligible, and
the pinned pull carries I-80, I-280, I-580 and I-680 rows at both statuses. The plan's invariant is that
motorway and trunk ways score 0 on scenery: penalised, never hard-excluded. A byway bonus on an Interstate
would put scenery back on exactly those roads, so `bonus_for` returns 0.0 for SCENIC_ZERO_CLASSES and takes
`way_class` as a REQUIRED argument: a caller that does not know the class has to find out rather than earn a
bonus by omission. `match` is deliberately NOT gated, so the designation stays visible in the data and only
the score is withheld.

WHICH MATCH WINS. Status first, overlap only as the tiebreak. The overlap gate is where "is this the same
road" gets decided; past it the remaining question is which designation to carry, and overlap fraction does
not answer that - it measures how much of the OSM way a corridor covers, which is a function of where OSM
chose to split the way. So a way running 60% along a designated corridor and 70% along an eligible one
carries the designated one. This file used to document that and do the opposite.

THE ROUTE KEY. A frontage road sits in the same distance band as the freeway's own second carriageway, so no
snap tolerance separates them and the match is gated on the route NUMBER instead. That key, the evidence for
it, and what to do when Caltrans's own `RTE` is wrong - which costs a real 28 km corridor inside the sfbay
extract its entire score, silently, if nobody checks - live in `byway_route_key`.

THE GEOMETRY - point-to-polyline distance, the cos(latitude) correction, overlap by length and the sampling
step that bounds the midpoint error - lives in `snap` and is re-exported here, so `byways.overlap_fraction`
and `byways.SNAP_TOLERANCE_M` still resolve. It left this file because it is arithmetic that should stop
changing while the paragraphs above are a record that has to keep growing.
"""
from __future__ import annotations

import re

from .curvature import distance_on_earth  # noqa: F401  - re-exported, callers use byways.distance_on_earth
from .snap import (MIN_OVERLAP_FRACTION, SAMPLE_STEP_M, SNAP_TOLERANCE_M,  # noqa: F401  - re-exported
                   distance_to_line_m, length_m, overlap_fraction, overlap_m, point_to_segment_m)

DESIGNATED_BONUS = 0.15
# Measured, not quoted: officially designated centreline / all centreline in the pinned Caltrans pull.
OD_SHARE_OF_SYSTEM = 0.195
ELIGIBLE_FLOOR = OD_SHARE_OF_SYSTEM * DESIGNATED_BONUS
ELIGIBLE_CEILING = 0.5 * DESIGNATED_BONUS
ELIGIBLE_BONUS = 0.06
# The plan's per-term allowance. Enforced by a test over every known status, not by a min() that cannot bind.
MAX_BONUS = 0.15
# E is a 0..1 score; the six base terms already sum to 1.00. This is what "capped" governs.
E_CEILING = 1.0
# The plan's invariant: these score 0 on scenery, so no byway bonus reaches them. See the docstring.
SCENIC_ZERO_CLASSES = frozenset({"motorway", "motorway_link", "trunk", "trunk_link"})

DESIGNATED = "OD"
ELIGIBLE = "E"
KNOWN_STATUS = frozenset({DESIGNATED, ELIGIBLE})

# What `byway_route_key.reconcile` stamps on an entry, and the verdicts it can stamp. An entry with no
# KEY_VERDICT has never been checked, which `problems` reports: silence is what let a wrong key cost 28 km.
KEY_VERDICT = "key_verdict"
KEY_CORROBORATED = "corroborated"
KEY_REKEYED = "rekeyed"
# The key holds real evidence AND another number still outvotes it past the re-key bar. Two numbers with a
# case each: the key stays and this is reported, because choosing between them here would be a guess.
KEY_CONTESTED = "contested"
KEY_UNCLAIMED = "unclaimed"
KEY_UNKEYED = "unkeyed"

# One `;`-separated part of an OSM `ref`: a network prefix and a bare number, nothing after it. `US 101` and
# `I-280` parse; `US 101 Business` deliberately does not.
_REF_PART = re.compile(r"^[A-Za-z]{1,4}\s*-?\s*(\d{1,3})$")


def status_bonus(status: str | None) -> float:
    """The E bonus for a byway status. Unknown or absent statuses score nothing rather than guessing."""
    if status == DESIGNATED:
        return DESIGNATED_BONUS
    if status == ELIGIBLE:
        return ELIGIBLE_BONUS
    return 0.0


def apply_to_e(base_e: float, bonus: float) -> float:
    """E with the byway bonus added, capped. THIS is what the plan's "capped" governs.

    The composition site in T-0029 must go through here, and must get `bonus` from `bonus_for` rather than
    from `status_bonus` directly - the motorway gate lives in `bonus_for`, not here, because this function
    is not told what kind of road it is holding.
    """
    return min(E_CEILING, base_e + bonus)


def unknown_statuses(statuses: list[str | None]) -> set[str]:
    """Statuses outside the known set.

    The field has no published domain, so Caltrans can add a value without telling anyone. If that happens
    every new segment silently scores zero, which reads as "not a byway" rather than "we do not understand
    this data" - so it has to be detectable.
    """
    return {s for s in statuses if s is not None and s not in KNOWN_STATUS}


def route_numbers(ref: str | None) -> set[str]:
    """Route numbers an OSM `ref` claims. `'I 280;CA 35'` -> `{'280', '35'}`, `'US 101 Business'` -> set()."""
    if not ref:
        return set()
    out = set()
    for part in ref.split(";"):
        m = _REF_PART.match(part.strip())
        if m:
            out.add(str(int(m.group(1))))
    return out


def route_matches(entry_routes, way_ref: str | None) -> bool:
    """Whether a way's `ref` lets it be this byway entry's route.

    An entry with no route key (the FHWA layer carries a trail name and no route number) cannot use this
    test, and falls back to geometry alone - a weaker mode, named here so it is not mistaken for the strong
    one. An entry WITH a route key rejects a way that does not name that number, including a way with no
    `ref` at all: measured on the I-280 corridor, every unreffed way clearing the overlap gate was a
    frontage or parallel road, not an I-280 segment. That is only safe while the key is the RIGHT number,
    which is `byway_route_key`'s job to establish and not this function's to assume.
    """
    if not entry_routes:
        return True
    return bool(set(entry_routes) & route_numbers(way_ref))


def match(way: list[tuple[float, float]], byways: list[dict], way_ref: str | None = None,
          tolerance_m: float = SNAP_TOLERANCE_M,
          min_overlap: float = MIN_OVERLAP_FRACTION) -> dict | None:
    """The best byway match for a way, or None.

    Best by STATUS, then by overlap. Both are applied only to entries that have already cleared the overlap
    gate and the route key, so the question at this point is not "is this the same road" - that is settled -
    but "which designation does it carry", and the stronger evidence is the one worth carrying. The overlap
    tiebreak then decides between two entries of EQUAL status, where it changes which corridor's name and
    coverage get recorded.
    """
    best = None
    best_key = None
    for entry in byways:
        line = entry.get("geometry") or []
        if len(line) < 2:
            continue
        if not route_matches(entry.get("routes"), way_ref):
            continue
        frac = overlap_fraction(way, line, tolerance_m)
        if frac < min_overlap:
            continue
        key = (status_bonus(entry.get("status")), frac)
        if best_key is None or key > best_key:
            best_key = key
            best = {"name": entry.get("name"), "status": entry.get("status"),
                    "source": entry.get("source"), "overlap": frac}
    return best


def bonus_for(way: list[tuple[float, float]], byways: list[dict], *, way_class: str | None, **kw) -> float:
    """The E bonus a way earns from byway designation. Add it to E through `apply_to_e`, never bare.

    `way_class` is the OSM `highway` value and is required with no default: a motorway or trunk earns
    nothing here whatever Caltrans says about the corridor, and a caller that does not know the class must
    find out rather than collect a bonus by omission.
    """
    if way_class in SCENIC_ZERO_CLASSES:
        return 0.0
    m = match(way, byways, **kw)
    return 0.0 if m is None else status_bonus(m["status"])


def problems(byways: list[dict]) -> list[str]:
    """Structural checks on a parsed byway set, so a bad pull fails loudly rather than flagging nothing."""
    out = []
    if not byways:
        out.append("no byways parsed at all - an empty overlay flags nothing and looks like a clean run")
        return out
    unknown = unknown_statuses([b.get("status") for b in byways])
    if unknown:
        out.append(f"unrecognised Status values {sorted(unknown)} - the field has no published domain, "
                   f"so a new value scores zero and reads as 'not a byway'")
    empty = sum(1 for b in byways if len(b.get("geometry") or []) < 2)
    if empty:
        out.append(f"{empty} byway(s) have no usable geometry")
    if not any(b.get("status") == DESIGNATED for b in byways):
        out.append("no officially designated byways at all - the pull is probably filtered wrong")
    keyless = sum(1 for b in byways if b.get("source") == "caltrans" and not b.get("routes"))
    if keyless:
        out.append(f"{keyless} Caltrans byway(s) have no route key - RTE is what tells a byway apart from "
                   f"the frontage road beside it, and without it they can only match on distance")
    blind = sum(1 for b in byways if b.get("routes") and not b.get(KEY_VERDICT))
    if blind:
        out.append(f"{blind} keyed byway(s) were never checked against the ways along them - Caltrans RTE "
                   f"is wrong on real corridors and a wrong key rejects the whole corridor in silence; "
                   f"run byway_route_key.reconcile")
    rekeyed = sorted({",".join(b.get("key_was") or []) for b in byways
                      if b.get(KEY_VERDICT) == KEY_REKEYED})
    if rekeyed:
        out.append(f"{len(rekeyed)} route number(s) {rekeyed} were claimed by no way along their own "
                   f"corridor - or by too little of one to be evidence - and re-keyed from the ways; "
                   f"the source's RTE field is wrong there")
    contested = sorted({",".join(sorted(b.get("routes") or ())) for b in byways
                        if b.get(KEY_VERDICT) == KEY_CONTESTED})
    if contested:
        out.append(f"{len(contested)} route key(s) {contested} are outvoted along their own corridor by "
                   f"another number that clears the re-key bar, while still holding evidence of their own "
                   f"- the key was kept and matched, so if it is the wrong one this is a silent loss")
    stranded = sum(1 for b in byways if b.get(KEY_VERDICT) == KEY_UNCLAIMED)
    if stranded:
        out.append(f"{stranded} byway(s) have a route key nothing along them claims and no consensus to "
                   f"replace it - they can match no way at all and will score zero")
    return out
