"""The generated near-miss corpus over every gating literal of the T-0381 profile gates (rv2 B1).

WHY GENERATED. Two review rounds each added one hand-picked spelling family (case, then whitespace) and the next
round found the one after it. This module derives the whole class from every gating literal L instead:
  the barrier, locked, ford, highway and service literals are PARSED from GateFacts.java (the plugin the shipped
  profile's gate_* encoded values come from); the tracktype and smoothness literals are PARSED from the shipped
  car_scenic_base.json's zero-priority clauses (`track_type == GRADE3`, ...), lower-cased to their OSM spelling.
Nothing gating is typed here; the context tags around each literal (the other half of a two-tag fact, a highway
that gates nothing on its own) are typed and gate nothing alone.

FAMILIES per literal L: L; L.upper(), L.title(), L.swapcase(); every single-character deletion; each of
INSERTED at the start, the end and every interior position; L;L, L;paved, paved;L, Lx, xL, L[:-1], LL; "".

THE ORACLE. A GateFacts literal is the fact iff the value == L exactly (Java .equals / Set.contains, untrimmed,
case-sensitive). A tracktype or smoothness literal is the gate iff value.upper() == L.upper(): GraphHopper 11's
TrackType.find / Smoothness.find is valueOf(Helper.toUpperCase(name)) - no trim - so case variants ARE the enum
and the profile gates them (ruled in the T-0381 Log, rv2). Every other variant is not gated and encodes MISSING
(track_type, smoothness when blank) or OTHER (smoothness otherwise).

`python services/etl/tests/gate_near_miss.py` rewrites gate_encoding.json: the hand rows (no `family` key) kept
in order, then every generated row whose tags no earlier row holds. test_profilegate.py holds the file to
table() exactly, so the committed table is this generator's output.
"""
from __future__ import annotations

import json
import pathlib
import re

ROUTING = pathlib.Path(__file__).resolve().parents[3] / "services" / "routing"
PLUGIN = ROUTING / "plugins" / "scenic-score-parser" / "src"
GATE_FACTS = PLUGIN / "main" / "java" / "com" / "scenicdrive" / "routing" / "GateFacts.java"
PROFILE = ROUTING / "profiles" / "car_scenic_base.json"
TABLE = PLUGIN / "test" / "resources" / "gate_encoding.json"

INSERTED = {" ": "space", "\t": "tab", ";": "semicolon", "_": "underscore", "-": "hyphen", "x": "x", "|": "pipe",
            ",": "comma"}
FIXED_FAMILIES = ("identity", "upper", "title", "swapcase", "joined-self", "then-paved", "paved-then", "suffix-x",
                  "prefix-x", "truncated", "doubled", "empty")
ENUM_KEYS = {"tracktype": ("track_type", "MISSING"), "smoothness": ("smoothness", "OTHER")}
EXACT_KEYS = ("barrier", "locked", "ford", "highway", "service")
GENERATED_BY = ("services/etl/tests/gate_near_miss.py (T-0381 rv2): every row with a `family` is generated from "
                "a gating literal parsed from GateFacts.java or the shipped car_scenic_base.json; regenerate, "
                "never edit by hand.")


def java_facts(source: pathlib.Path = GATE_FACTS) -> dict:
    """GateFacts' String constants and Set.of literals, by field name."""
    text = source.read_text(encoding="utf-8")
    out = {name: value for name, value in re.findall(r'static final String (\w+) = "([^"]*)";', text)}
    for name, body in re.findall(r"static final Set<String> (\w+) =\s*Set\.of\(([^)]*)\);", text):
        out[name] = frozenset(re.findall(r'"([^"]*)"', body))
    for name in ("YES", "SERVICE_HIGHWAY", "REFUSABLE_BARRIERS", "REFUSED_SERVICE_VALUES"):
        if not out.get(name):
            raise ValueError("GateFacts.java carries no %s" % name)
    return out


def profile_enum_gates(profile: pathlib.Path = PROFILE) -> dict:
    """The enum constants the shipped profile's zero-priority clauses gate, by encoded value name."""
    gates = {"track_type": set(), "smoothness": set()}
    for rule in json.loads(profile.read_text(encoding="utf-8"))["priority"]:
        if float(rule["multiply_by"]) != 0.0:
            continue
        for name, constant in re.findall(r"\b(track_type|smoothness) == ([A-Z0-9_]+)", rule["if"]):
            gates[name].add(constant)
    if not all(gates.values()):
        raise ValueError("the shipped profile gates no %s" % [k for k, v in gates.items() if not v])
    return {name: frozenset(values) for name, values in gates.items()}


def literals() -> list:
    """(key, literal, context tags) for every gating literal, every key."""
    facts, enums = java_facts(), profile_enum_gates()
    barrier = sorted(facts["REFUSABLE_BARRIERS"])[0]
    service = sorted(facts["REFUSED_SERVICE_VALUES"])[0]
    out = [("barrier", b, {"highway": "tertiary", "locked": facts["YES"]}) for b in sorted(facts["REFUSABLE_BARRIERS"])]
    out.append(("locked", facts["YES"], {"highway": "tertiary", "barrier": barrier}))
    out.append(("ford", facts["YES"], {"highway": "unclassified"}))
    out.append(("highway", facts["SERVICE_HIGHWAY"], {"service": service}))
    out += [("service", s, {"highway": facts["SERVICE_HIGHWAY"]}) for s in sorted(facts["REFUSED_SERVICE_VALUES"])]
    out += [("tracktype", t.lower(), {"highway": "tertiary"}) for t in sorted(enums["track_type"])]
    out += [("smoothness", s.lower(), {"highway": "residential"}) for s in sorted(enums["smoothness"])]
    return out


def near_misses(literal: str) -> list:
    """(family, value) for every listed family of one literal, in a fixed order, duplicates kept."""
    out = [("identity", literal), ("upper", literal.upper()), ("title", literal.title()),
           ("swapcase", literal.swapcase())]
    out += [("delete@%d" % i, literal[:i] + literal[i + 1:]) for i in range(len(literal))]
    out += [("insert-%s@%d" % (name, i), literal[:i] + char + literal[i:])
            for char, name in INSERTED.items() for i in range(len(literal) + 1)]
    out += [("joined-self", literal + ";" + literal), ("then-paved", literal + ";paved"),
            ("paved-then", "paved;" + literal), ("suffix-x", literal + "x"), ("prefix-x", "x" + literal),
            ("truncated", literal[:-1]), ("doubled", literal + literal), ("empty", "")]
    return out


def is_gate(key: str, literal: str, value: str) -> bool:
    """The ruled oracle: exact equality for a GateFacts literal, GraphHopper's upper-cased valueOf for an enum."""
    if key in ENUM_KEYS:
        return value.upper() == literal.upper()
    return value == literal


def encoded(tags: dict) -> dict:
    """The five encoded values, for tags whose enum values are a gated constant or not an enum name at all."""
    facts, enums = java_facts(), profile_enum_gates()
    out = {}
    for key, (name, unknown) in ENUM_KEYS.items():
        raw = tags.get(key)
        if raw is None or not raw.strip():
            out[name] = "MISSING"
        else:
            out[name] = raw.upper() if raw.upper() in enums[name] else unknown
    out["gate_locked_barrier"] = tags.get("barrier") in facts["REFUSABLE_BARRIERS"] and tags.get("locked") == facts["YES"]
    out["gate_ford"] = tags.get("ford") == facts["YES"]
    out["gate_service_way"] = (tags.get("highway") == facts["SERVICE_HIGHWAY"]
                               and tags.get("service") in facts["REFUSED_SERVICE_VALUES"])
    return out


def corpus() -> list:
    """Every generated row before de-duplication: literal, family, tags, gated, encoded."""
    rows = []
    for key, literal, context in literals():
        for family, value in near_misses(literal):
            tags = {**context, key: value}
            rows.append({"literal": "%s=%s" % (key, literal), "family": family, "tags": tags,
                         "gated": is_gate(key, literal, value), "encoded": encoded(tags)})
    return rows


def _key(tags: dict) -> str:
    return json.dumps(tags, sort_keys=True)


def table(hand_rows: list) -> list:
    """The hand rows, then each generated row whose tags no earlier row holds."""
    seen = {_key(row["tags"]) for row in hand_rows}
    out = list(hand_rows)
    for row in corpus():
        if _key(row["tags"]) not in seen:
            seen.add(_key(row["tags"]))
            out.append({"tags": row["tags"], "encoded": row["encoded"], "literal": row["literal"],
                        "family": row["family"]})
    return out


def hand_rows(path: pathlib.Path = TABLE) -> list:
    return [row for row in json.loads(path.read_text(encoding="utf-8"))["rows"] if "family" not in row]


def main() -> int:
    data = json.loads(TABLE.read_text(encoding="utf-8"))
    rows = table(hand_rows())
    body = ",\n".join("    " + json.dumps(row) for row in rows)
    text = '{\n  "why": %s,\n  "generated_by": %s,\n  "rows": [\n%s\n  ]\n}\n' % (
        json.dumps(data["why"]), json.dumps(GENERATED_BY), body)
    TABLE.write_bytes(text.encode("utf-8"))
    print("gate_encoding.json: %d rows (%d hand, %d generated; corpus %d before de-duplication)"
          % (len(rows), len(hand_rows()), len(rows) - len(hand_rows()), len(corpus())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
