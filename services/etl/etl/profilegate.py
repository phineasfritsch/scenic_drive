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
  track_type   OSMTrackTypeParser (T-0381): `tracktype` on any way, Helper.isEmpty (trimmed) -> MISSING, else
               upper-cased if an enum name, MISSING if not
  smoothness   OSMSmoothnessParser: `smoothness`, blank -> MISSING, upper-cased if an enum name, OTHER if not
  gate_*       OUR GateFacts booleans (plugins/scenic-score-parser), exact like Gates.verdict: a locked gate on
               the way, ford=yes, a refused service value on highway=service. One table
               (plugins/scenic-score-parser/src/test/resources/gate_encoding.json) holds both encoders.

THE EVALUATOR is the subset of GraphHopper's custom-model language the base profile uses: `true`, `false`,
`!`, `&&`, `||`, parentheses, and `name == CONST` / `name != CONST`. Any other token, any unknown encoded
value, any rule key other than `if` + `multiply_by`, any `multiply_by` that is not a number refuses with
ValueError - an expression this module cannot read is never read as "does not fire". A comparison refuses
unless `name` is an enum value in DOMAINS and CONST one of its values (GraphHopper refuses both at load).

THE WHOLE MODEL IS READ (rv1 B1). GraphHopper never routes an edge whose priority OR speed is 0, so `gated` reads
both blocks: a firing `speed` rule with `limit_to` 0 or `multiply_by` 0 is an exclusion exactly as a priority 0
is. A speed rule is `if` + one of `limit_to` / `multiply_by`; its value is a number or an encoded speed in
SPEED_NAMES (read as never 0 - car_access is held true). `distance_influence` must be a number >= 0 (it adds a
per-km cost and never excludes). Any other top-level key, rule shape or speed value refuses with ValueError.
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
TRACK_TYPES = ("MISSING", "GRADE1", "GRADE2", "GRADE3", "GRADE4", "GRADE5")
SMOOTHNESS = ("MISSING", "EXCELLENT", "GOOD", "INTERMEDIATE", "BAD", "VERY_BAD", "HORRIBLE", "VERY_HORRIBLE",
              "IMPASSABLE", "OTHER")
REFUSABLE_BARRIERS = frozenset({"gate"})
REFUSED_SERVICE_VALUES = frozenset({"driveway", "parking_aisle", "drive-through", "emergency_access"})
SERVICE_HIGHWAY = "service"
YES = "yes"
DOMAINS = {"road_class": ROAD_CLASSES, "road_access": frozenset(ROAD_ACCESS), "surface": SURFACES,
           "track_type": frozenset(TRACK_TYPES), "smoothness": frozenset(SMOOTHNESS)}
LINK_SUFFIX = "_link"
RULE_KEYS = frozenset({"if", "multiply_by"})
MODEL_KEYS = frozenset({"speed", "priority", "distance_influence"})
SPEED_RULE_KEYS = (frozenset({"if", "limit_to"}), frozenset({"if", "multiply_by"}))
SPEED_NAMES = frozenset({"car_average_speed"})

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


def _enum_name(raw):
    """GraphHopper's Helper.isEmpty (null or blank after trim) as None, else Helper.toUpperCase."""
    if raw is None or not raw.strip():
        return None
    return raw.upper()


def track_type(tags: dict) -> str:
    value = _enum_name(tags.get("tracktype"))
    return value if value in TRACK_TYPES else "MISSING"


def smoothness(tags: dict) -> str:
    value = _enum_name(tags.get("smoothness"))
    if value is None:
        return "MISSING"
    return value if value in SMOOTHNESS else "OTHER"


def gate_locked_barrier(tags: dict) -> bool:
    return tags.get("barrier") in REFUSABLE_BARRIERS and tags.get("locked") == YES


def gate_ford(tags: dict) -> bool:
    return tags.get("ford") == YES


def gate_service_way(tags: dict) -> bool:
    return tags.get("highway") == SERVICE_HIGHWAY and tags.get("service") in REFUSED_SERVICE_VALUES


def encode(tags: dict) -> dict:
    """The encoded values the base profile's expressions read, for one way's tags."""
    return {"road_class": road_class(tags), "road_access": road_access(tags), "surface": surface(tags),
            "track_type": track_type(tags), "smoothness": smoothness(tags),
            "gate_locked_barrier": gate_locked_barrier(tags), "gate_ford": gate_ford(tags),
            "gate_service_way": gate_service_way(tags), "car_access": True}


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
            if constant not in DOMAINS.get(tok, ()):
                raise ValueError("expression %r compares %r to %r, not one of its values" % (self.expression, tok,
                                                                                             constant))
            return (value == constant) if op == "==" else (value != constant)
        if not isinstance(value, bool):
            raise ValueError("expression %r reads %r as a boolean" % (self.expression, tok))
        return value


def fires(expression: str, values: dict) -> bool:
    """Whether one `if` expression is true over these encoded values."""
    return _Parser(expression, values).parse()


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def model(profile: pathlib.Path = PROFILE) -> dict:
    """The shipped custom model, refused when it carries a key or a distance_influence this module cannot read."""
    data = json.loads(profile.read_text(encoding="utf-8"))
    unread = sorted(set(data) - MODEL_KEYS)
    if unread:
        raise ValueError("profile %s carries %s, which is not read here" % (profile.name, unread))
    influence = data.get("distance_influence", 0)
    if not _number(influence):
        raise ValueError("profile %s: distance_influence %r is not a number >= 0" % (profile.name, influence))
    return data


def _speed_value(rule: dict):
    raw = rule["limit_to"] if "limit_to" in rule else rule["multiply_by"]
    if raw in SPEED_NAMES:
        return None
    value = float(raw)
    if value < 0:
        raise ValueError("speed rule %r: a negative speed is not read here" % (rule,))
    return value


def speed_excludes(tags: dict, profile: pathlib.Path = PROFILE) -> bool:
    """True when a firing `speed` rule sets this way's speed to 0 (limit_to 0 or multiply_by 0)."""
    values = encode(tags)
    excluded = False
    for rule in model(profile).get("speed", []):
        if frozenset(rule) not in SPEED_RULE_KEYS:
            raise ValueError("speed rule %r: only `if` + `limit_to` or `multiply_by` is read here" % (rule,))
        value = _speed_value(rule)
        if fires(rule["if"], values) and value == 0.0:
            excluded = True
    return excluded


def priority(tags: dict, profile: pathlib.Path = PROFILE) -> float:
    """The product of every firing `priority` rule's `multiply_by`, for one way's tags, over the shipped file."""
    rules = model(profile).get("priority", [])
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
    """True when the shipped profile gives this way priority 0 or speed 0 - GraphHopper will never route over it."""
    return priority(tags, profile) == 0.0 or speed_excludes(tags, profile)
