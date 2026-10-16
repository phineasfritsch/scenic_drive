"""T-0188: `assemble.gate_reason` refuses every rule `Gates.verdict` refuses, in its order, by its reasons.

P-PROD-01 is parity with `Sources/ScenicKit/Gates/Gates.swift`, so every expected answer here is READ from the
Swift CODE (comment lines dropped, whole lines compared - never a doc comment): the refused values from its
`Set<String>` literals, the reason each branch returns and the branch order from its `return .refused(.x)`
lines, the reason names from `GateReason.swift`'s cases. A rule added on either side without the other is red
in `test_the_etl_has_exactly_the_swift_rule_count`, and a reason added to the enum in
`test_the_reason_names_are_gate_reasons_cases`. Near-misses are tabled beside every refusal: a widened set
or a dropped conjunct gates one of them.
"""
from __future__ import annotations

import inspect
import itertools
import pathlib
import re

import pytest

from etl import accessrule, assemble

ROOT = pathlib.Path(__file__).resolve().parents[3]
GATES_SWIFT = ROOT / "Sources" / "ScenicKit" / "Gates" / "Gates.swift"
GATE_REASON_SWIFT = ROOT / "Sources" / "ScenicKit" / "Gates" / "GateReason.swift"
REFUSAL = "return .refused("
SWIFT_BRANCHES = 9

# One way per `Gates.verdict` branch, in its order; the reason each must get is read from the Swift.
WITNESSES = (
    {"highway": "residential", "surface": "gravel"},
    {"highway": "track"},
    {"highway": "unclassified", "tracktype": "grade3"},
    {"highway": "residential", "smoothness": "bad"},
    {"highway": "residential", "access": "private"},
    {"highway": "residential", "motor_vehicle": "no"},
    {"highway": "residential", "barrier": "gate", "locked": "yes"},
    {"highway": "residential", "ford": "yes"},
    {"highway": "service", "service": "driveway"},
)
TRACK_INDEX, SERVICE_INDEX = 1, 8

# Each Swift set, the tag set one of its values is tried on, and the GateReason case it must refuse with.
SET_RULES = (
    ("unpavedSurfaces", lambda v: {"highway": "residential", "surface": v}, "unpavedSurface"),
    ("refusedTracktypes", lambda v: {"highway": "unclassified", "tracktype": v}, "track"),
    ("refusedSmoothness", lambda v: {"highway": "residential", "smoothness": v}, "tooRough"),
    ("closedAccess", lambda v: {"highway": "residential", "access": v}, "noAccess"),
    ("refusableBarriers", lambda v: {"highway": "residential", "barrier": v, "locked": "yes"},
     "lockedBarrier"),
    ("refusedServiceValues", lambda v: {"highway": "service", "service": v}, "serviceWay"),
)
# The module's own copy of each set, compared to the Swift literal of the same name.
ETL_SETS = {"unpavedSurfaces": "UNPAVED_SURFACES", "refusedTracktypes": "REFUSED_TRACKTYPES",
            "refusedSmoothness": "REFUSED_SMOOTHNESS", "closedAccess": "CLOSED_ACCESS",
            "refusableBarriers": "REFUSABLE_BARRIERS", "refusedServiceValues": "REFUSED_SERVICE_VALUES"}

# Ungated: the neighbour of every refusal (measured on the LA window where it occurs - see the T-0188 Log).
NEAR_MISSES = (
    {"highway": "unclassified", "tracktype": "grade2"},
    {"highway": "unclassified", "tracktype": "grade1"},
    {"highway": "residential", "smoothness": "intermediate"},
    {"highway": "residential", "smoothness": "good"},
    {"highway": "residential", "barrier": "gate", "locked": "no"},
    {"highway": "residential", "barrier": "gate"},
    {"highway": "residential", "barrier": "bollard", "locked": "yes"},
    {"highway": "residential", "locked": "yes"},
    {"highway": "residential", "ford": "no"},
    {"highway": "residential"},
    {"highway": "service", "service": "alley"},
    {"highway": "service", "service": "slipway"},
    {"highway": "service"},
    {"highway": "residential", "service": "driveway"},
)

# rv1 B1/B2: every `tags["k"] == "v"` conjunct of Gates.verdict is tried over this value space - OSM values and
# boolean spellings - plus its own parsed literal. A widened comparison (`not in (None, "no")`, `in (yes,
# true, 1)`) refuses one of them; ScenicKit routes every one.
VALUE_SPACE = ("yes", "no", "true", "false", "1", "0", "unknown", "stepping_stones", "boat", "permissive",
               "private", "designated", "residential", "")
# The way each conjunct's value is tried on, keyed by its branch's reason; every OTHER conjunct is satisfied.
EQUALITY_WAYS = {
    "track": lambda v: {"highway": v},
    "noAccess": lambda v: {"highway": "residential", "motor_vehicle": v},
    "lockedBarrier": lambda v: {"highway": "residential", "barrier": "gate", "locked": v},
    "ford": lambda v: {"highway": "residential", "ford": v},
    "serviceWay": lambda v: {"highway": v, "service": "driveway"},
}
EQUALITY = re.compile(r'tags\["(\w+)"\] == "([^"]*)"')
PROBE = "\x00probe"


def _code(path: pathlib.Path) -> list:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("//")]


def _swift_set(name: str) -> set:
    match = re.search(r"let %s: Set<String> = \[(.*?)\]" % name, "\n".join(_code(GATES_SWIFT)), re.S)
    assert match, "%s is not declared in %s" % (name, GATES_SWIFT)
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def _snake(case: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"_\1", case).lower()


def swift_refusals() -> list:
    """The reason of every refusing branch of `Gates.verdict`, in order. Fails closed on another spelling."""
    code = _code(GATES_SWIFT)
    reasons = [m for line in code for m in re.findall(r"return \.refused\(\.(\w+)\)", line)]
    assert len(reasons) == sum(line.count(REFUSAL) for line in code), "a refusal this parser cannot read"
    return reasons


def etl_rule_count() -> int:
    """`gate_reason`'s refusing branches, with its `access_refused` call counted as that predicate's clauses."""
    body = [line for line in inspect.getsource(assemble.gate_reason).splitlines()
            if not line.lstrip().startswith("#")]
    returns = sum(line.count("return GATE_") for line in body)
    calls = sum(line.count("access_refused(") for line in body)
    clauses = sum(line.count("tags.get(") for line in inspect.getsource(accessrule.access_refused).splitlines()
                  if not line.lstrip().startswith("#"))
    return returns - calls + calls * clauses


def test_the_etl_has_exactly_the_swift_rule_count():
    refusals = swift_refusals()
    assert len(refusals) == SWIFT_BRANCHES, "Gates.verdict has %d refusal branches, not %d" % (
        len(refusals), SWIFT_BRANCHES)
    assert etl_rule_count() == len(refusals) == len(WITNESSES), (etl_rule_count(), refusals)


def test_the_reason_names_are_gate_reasons_cases():
    cases = [m.group(1) for line in _code(GATE_REASON_SWIFT) for m in [re.match(r"\s*case (\w+)\s*$", line)] if m]
    assert assemble.GATE_REASONS == tuple(_snake(case) for case in cases), cases
    assert set(assemble.GATE_REASONS) == {_snake(r) for r in swift_refusals()}


@pytest.mark.parametrize("index", range(len(WITNESSES)))
def test_each_rule_refuses_with_the_swift_reason(index):
    want = _snake(swift_refusals()[index])
    got = assemble.gate_reason(WITNESSES[index])
    assert got == want, "Gates.verdict branch %d refuses %s as %s; the ETL says %s" % (
        index, WITNESSES[index], want, got)


def test_the_sets_are_the_swift_literals():
    for swift_name, etl_name in ETL_SETS.items():
        assert set(getattr(assemble, etl_name)) == _swift_set(swift_name), swift_name


@pytest.mark.parametrize("swift_name,tags_for,reason", SET_RULES, ids=[r[0] for r in SET_RULES])
def test_every_value_of_every_swift_set_is_refused(swift_name, tags_for, reason):
    for value in sorted(_swift_set(swift_name)):
        assert assemble.gate_reason(tags_for(value)) == _snake(reason), (swift_name, value)


@pytest.mark.parametrize("tags", NEAR_MISSES, ids=[",".join("%s=%s" % kv for kv in t.items()) for t in NEAR_MISSES])
def test_the_near_misses_are_not_gated(tags):
    assert assemble.gate_reason(tags) is None, tags


def test_every_ordered_pair_answers_the_earlier_swift_rule():
    """Order is behaviour (GatesOrderTests): a way two rules refuse gets the reason Gates.verdict tries first."""
    refusals = swift_refusals()
    for i, j in itertools.combinations(range(len(WITNESSES)), 2):
        tags = {**WITNESSES[j], **WITNESSES[i]}
        if TRACK_INDEX in (i, j):
            tags["highway"] = "track"
        elif j == SERVICE_INDEX:
            tags["highway"] = "service"
        assert assemble.gate_reason(tags) == _snake(refusals[i]), (i, j, tags)


def test_the_keys_the_etl_gate_reads_are_gates_considered_tag_keys():
    """Gates.swift's `consideredTagKeys`, exactly: a key the ETL gates on that ScenicKit cannot see is drift."""
    read = set(re.findall(r'tags\.get\("(\w+)"\)', inspect.getsource(assemble.gate_reason)))
    read |= {accessrule.ACCESS_KEY, accessrule.MOTOR_VEHICLE_KEY}
    assert read == _swift_set("consideredTagKeys"), sorted(read ^ _swift_set("consideredTagKeys"))


def swift_equalities() -> list:
    """`(key, literal, reason)` of every `tags["k"] == "v"` in `Gates.verdict`, the reason being the first
    refusal at or after it. Fails closed: any other `==` or any `!=` in the body is a spelling it cannot read."""
    code = _code(GATES_SWIFT)
    start = next(i for i, line in enumerate(code) if "func verdict(" in line)
    end = next((i for i in range(start + 1, len(code)) if " func " in code[i]), len(code))
    body = code[start + 1:end]
    found = []
    for i, line in enumerate(body):
        for key, literal in EQUALITY.findall(line):
            reason = next(m.group(1) for later in body[i:] for m in [re.search(r"return \.refused\(\.(\w+)\)", later)]
                          if m)
            found.append((key, literal, reason))
    assert sum(line.count("==") for line in body) == len(found), "an == this parser cannot read"
    assert not any("!=" in line for line in body), "a != this parser cannot read"
    return found


def equality_rows(literal: str) -> list:
    """`(value, refused)` over the value space and the literal: refused iff the value IS the literal."""
    return [(value, refused_under(value, literal)) for value in sorted(set(VALUE_SPACE) | {literal})]


def refused_under(value: str, literal: str) -> bool:
    return value == literal


def test_every_swift_equality_conjunct_has_a_way():
    found = swift_equalities()
    assert len(found) == len(EQUALITY_WAYS) == 5, found
    assert sorted(reason for _, _, reason in found) == sorted(EQUALITY_WAYS), found
    for key, _, reason in found:
        assert EQUALITY_WAYS[reason](PROBE)[key] == PROBE, (key, reason)


def test_no_equality_row_ignores_the_parsed_literal():
    for _, literal, _ in swift_equalities():
        rows = dict(equality_rows(literal))
        assert sum(rows.values()) == 1 and len(rows) > len(VALUE_SPACE) // 2, (literal, rows)
        for value, refused in rows.items():
            other = value if value != literal else literal + PROBE
            assert refused_under(value, other) != refused, (literal, value)


@pytest.mark.parametrize("key,literal,reason", swift_equalities(),
                         ids=["%s==%s" % (k, lit) for k, lit, _ in swift_equalities()])
def test_each_equality_conjunct_refuses_its_swift_literal_and_no_other_value(key, literal, reason):
    for value, refused in equality_rows(literal):
        tags = EQUALITY_WAYS[reason](value)
        assert assemble.gate_reason(tags) == (_snake(reason) if refused else None), (key, literal, value, tags)
