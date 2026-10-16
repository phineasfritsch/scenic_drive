"""The routing profile's hard gates, evaluated on ONE OSM tag row (T-0012, P-PROD-01).

WHY THIS EXISTS. The same safety rule is written three times: `assemble.gate_reason` here, the `priority` block
of `services/routing/profiles/car_scenic_base.json`, and `Sources/ScenicKit/Gates/Gates.swift`. The parity
fixture (`tests/fixtures/gate_parity.json`) puts one row of tags through all three. GraphHopper is not on any
test box, so this module stands in for the two GraphHopper steps that turn a way's tags into the profile's
answer: the ENCODING (tags -> `road_class`, `road_access`, `surface`, `car_access`) and the EVALUATION of the
profile's `if` expressions over those values.

THE PROFILE IS THE SHIPPED FILE. `PROFILE` is the path of the one json GraphHopper is configured with
(`config.yml` `custom_model_files: [car_scenic_base.json]`), read on every call - never a copy, never a typed
restatement - so an edit to the shipped file is an edit to what the fixture evaluates.

THE ENCODING IS GRAPHHOPPER 11's (the version `plugins/scenic-score-parser/pom.xml` pins), restated for the
values the gates read:
  road_class   OSMRoadClassParser: `highway`, a `_link` suffix dropped, upper-cased; not an enum name -> OTHER
  road_access  OSMRoadAccessParser for CAR: the keys motorcar, motor_vehicle, vehicle, access; `permit` is
               PRIVATE, any other value its enum name or YES; the MOST restrictive (highest ordinal) wins
  surface      OSMSurfaceParser: the value upper-cased if it is an enum name, OTHER if not, MISSING if absent
  car_access   held TRUE. GraphHopper's own car access parser is not restated, on purpose: the parity is about
               the clauses this repository writes, and modelling `car_access` as already refusing a private
               road would hide the deletion of the profile's own `road_access` clause. Fail closed.

THE EVALUATOR is the subset of GraphHopper's custom-model language the base profile uses: `true`, `false`,
`!`, `&&`, `||`, parentheses, and `name == CONST` / `name != CONST`. Any other token, any unknown encoded
value, any rule key other than `if` + `multiply_by`, any `multiply_by` that is not a number refuses with
ValueError - an expression this module cannot read is never read as "does not fire".
"""
from __future__ import annotations

import json
import pathlib
import re

PROFILE = pathlib.Path(__file__).resolve().parents[2] / "routing" / "profiles" / "car_scenic_base.json"

ROAD_CLASSES = frozenset({
    "OTHER", "MOTORWAY", "TRUNK", "PRIMARY", "SECONDARY", "TERTIARY", "RESIDENTIAL", "UNCLASSIFIED", "SERVICE",
    "ROAD", "TRACK", "BRIDLEWAY", "STEPS", "CYCLEWAY", "PATH", "LIVING_STREET", "FOOTWAY", "PEDESTRIAN",
    "PLATFORM", "CORRIDOR", "CONSTRUCTION", "BUSWAY",
})
ROAD_ACCESS = ("YES", "DESTINATION", "CUSTOMERS", "DELIVERY", "FORESTRY", "AGRICULTURAL", "PRIVATE", "NO")
CAR_RESTRICTION_KEYS = ("motorcar", "motor_vehicle", "vehicle", "access")
PERMIT_VALUE = "permit"
PERMIT_ACCESS = "PRIVATE"
SURFACES = frozenset({
    "MISSING", "PAVED", "ASPHALT", "CONCRETE", "PAVING_STONES", "COBBLESTONE", "UNPAVED", "COMPACTED",
    "FINE_GRAVEL", "GRAVEL", "GROUND", "DIRT", "GRASS", "SAND", "WOOD", "OTHER",
})
LINK_SUFFIX = "_link"
RULE_KEYS = frozenset({"if", "multiply_by"})

_TOKEN = re.compile(r"\s*(\|\||&&|==|!=|!|\(|\)|[A-Za-z_][A-Za-z0-9_]*)")


def road_class(tags: dict) -> str:
    value = (tags.get("highway") or "").upper()
    if value.endswith(LINK_SUFFIX.upper()):
        value = value[: -len(LINK_SUFFIX)]
    return value if value in ROAD_CLASSES else "OTHER"


def road_access(tags: dict) -> str:
    worst = 0
    for key in CAR_RESTRICTION_KEYS:
        raw = tags.get(key)
        if raw is None:
            continue
        value = PERMIT_ACCESS if raw == PERMIT_VALUE else raw.upper()
        rank = ROAD_ACCESS.index(value) if value in ROAD_ACCESS else 0
        worst = max(worst, rank)
    return ROAD_ACCESS[worst]


def surface(tags: dict) -> str:
    raw = tags.get("surface")
    if raw is None:
        return "MISSING"
    value = raw.upper()
    return value if value in SURFACES else "OTHER"


def encode(tags: dict) -> dict:
    """The encoded values the base profile's expressions read, for one way's tags."""
    return {"road_class": road_class(tags), "road_access": road_access(tags), "surface": surface(tags),
            "car_access": True}


def tokens(expression: str) -> list:
    out, at = [], 0
    stripped = expression.rstrip()
    while at < len(stripped):
        match = _TOKEN.match(stripped, at)
        if match is None:
            raise ValueError("unreadable expression %r at %d" % (expression, at))
        out.append(match.group(1))
        at = match.end()
    return out


class _Parser:
    def __init__(self, expression: str, values: dict):
        self.toks = tokens(expression)
        self.at = 0
        self.values = values
        self.expression = expression

    def peek(self):
        return self.toks[self.at] if self.at < len(self.toks) else None

    def take(self):
        tok = self.peek()
        if tok is None:
            raise ValueError("expression %r ends early" % self.expression)
        self.at += 1
        return tok

    def parse(self) -> bool:
        value = self.disjunction()
        if self.peek() is not None:
            raise ValueError("expression %r has trailing %r" % (self.expression, self.peek()))
        return value

    def disjunction(self) -> bool:
        value = self.conjunction()
        while self.peek() == "||":
            self.take()
            right = self.conjunction()
            value = value or right
        return value

    def conjunction(self) -> bool:
        value = self.unary()
        while self.peek() == "&&":
            self.take()
            right = self.unary()
            value = value and right
        return value

    def unary(self) -> bool:
        if self.peek() == "!":
            self.take()
            return not self.unary()
        return self.atom()

    def atom(self) -> bool:
        tok = self.take()
        if tok == "(":
            value = self.disjunction()
            if self.take() != ")":
                raise ValueError("expression %r: unbalanced parenthesis" % self.expression)
            return value
        if tok in ("true", "false"):
            return tok == "true"
        if tok not in self.values:
            raise ValueError("expression %r names %r, which is not an encoded value here" % (self.expression, tok))
        value = self.values[tok]
        if self.peek() in ("==", "!="):
            op = self.take()
            constant = self.take()
            return (value == constant) if op == "==" else (value != constant)
        if not isinstance(value, bool):
            raise ValueError("expression %r reads %r as a boolean" % (self.expression, tok))
        return value


def fires(expression: str, values: dict) -> bool:
    """Whether one `if` expression is true over these encoded values."""
    return _Parser(expression, values).parse()


def priority(tags: dict, profile: pathlib.Path = PROFILE) -> float:
    """The product of every firing `priority` rule's `multiply_by`, for one way's tags, over the shipped file."""
    rules = json.loads(profile.read_text(encoding="utf-8"))["priority"]
    values = encode(tags)
    product = 1.0
    for rule in rules:
        if set(rule) != RULE_KEYS:
            raise ValueError("profile rule %r: only `if` + `multiply_by` is read here" % (rule,))
        factor = float(rule["multiply_by"])
        if fires(rule["if"], values):
            product *= factor
    return product


def gated(tags: dict, profile: pathlib.Path = PROFILE) -> bool:
    """True when the shipped profile gives this way priority 0 - GraphHopper will never route over it."""
    return priority(tags, profile) == 0.0
