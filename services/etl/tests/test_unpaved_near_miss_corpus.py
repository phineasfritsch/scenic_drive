"""T-0181 rv2: every shipping entry point that asks "is this tag unpaved?" agrees with Swift on a GENERATED corpus.

Swift's `Gates.verdict` asks `unpavedSurfaces.contains(surface)`: exact string equality, no case fold, no trim, no
split on `;`, no prefix. Two rounds each added a hand-picked spelling family (case, then whitespace) and the next
family (semicolon multi-values) survived. This closes the CLASS: for every gating literal L - parsed from
Gates.swift, never typed here - `near_misses(L)` yields

  identity L; L.upper(), L.title(), L.swapcase(); every single-character deletion of L; each of INSERTED
  inserted at the start, the end and every interior position; L;L, L;paved, paved;L, Lx, xL, L[:-1], LL;
  and the empty string,

and each entry point refuses / counts unpaved iff the value == L exactly (the identity row). The meta-test holds
the generator to every family for every literal and holds every non-identity value OUT of the Swift set, so the
equality oracle and Swift's set membership are the same predicate on this corpus.

Entry points (every one the task owns, the `surface` key each reads): `assemble.gate_reason`,
`surface.surface_state`, `surfacecoverage.bucket` and `surfacecoverage.coverage`.
"""
from __future__ import annotations

import types

import pytest

from etl import assemble, surface, surfacecoverage
from tests.test_unpaved_surfaces_owner import swift_unpaved

INSERTED = (" ", "\t", ";", "_", "-", "x", "|", ",")
SINGLE_FAMILIES = ("identity", "upper", "title", "swapcase", "semi-twice", "semi-paved", "paved-semi",
                   "x-suffix", "x-prefix", "drop-last", "doubled", "empty")


def near_misses(lit: str) -> list:
    """(family, detail, value) for one literal: a pure function of the literal's text."""
    rows = [("identity", "", lit), ("upper", "", lit.upper()), ("title", "", lit.title()),
            ("swapcase", "", lit.swapcase())]
    rows += [("delete", str(i), lit[:i] + lit[i + 1:]) for i in range(len(lit))]
    rows += [("insert", "%s@%d" % (repr(c), p), lit[:p] + c + lit[p:])
             for c in INSERTED for p in range(len(lit) + 1)]
    rows += [("semi-twice", "", lit + ";" + lit), ("semi-paved", "", lit + ";paved"),
             ("paved-semi", "", "paved;" + lit), ("x-suffix", "", lit + "x"), ("x-prefix", "", "x" + lit),
             ("drop-last", "", lit[:-1]), ("doubled", "", lit + lit), ("empty", "", "")]
    return rows


def corpus(swift: frozenset) -> list:
    """(id, literal, family, value) for every Swift literal x every near miss - rows are f(parsed set)."""
    return [("%s-%s%s-%d" % (lit, fam, "-" + detail if detail else "", n), lit, fam, value)
            for lit in sorted(swift) for n, (fam, detail, value) in enumerate(near_misses(lit))]


ROWS = corpus(swift_unpaved())


def test_the_generator_yields_every_family_for_every_literal():
    swift = swift_unpaved()
    assert len(ROWS) == sum(len(near_misses(lit)) for lit in swift) == len({r[0] for r in ROWS})
    for lit in sorted(swift):
        got = near_misses(lit)
        fams = [fam for fam, _, _ in got]
        for fam in SINGLE_FAMILIES:
            assert fams.count(fam) == 1, (lit, fam)
        assert fams.count("delete") == len(lit), lit
        assert fams.count("insert") == len(INSERTED) * (len(lit) + 1), lit
        assert len(got) == len(SINGLE_FAMILIES) + len(lit) + len(INSERTED) * (len(lit) + 1), lit
        deletions = {d: v for fam, d, v in got if fam == "delete"}
        assert sorted(deletions) == sorted(str(i) for i in range(len(lit))), lit
        for i, v in deletions.items():
            assert len(v) == len(lit) - 1 and v == lit[:int(i)] + lit[int(i) + 1:], (lit, i)
        inserts = {d: v for fam, d, v in got if fam == "insert"}
        assert set(inserts) == {"%s@%d" % (repr(c), p) for c in INSERTED for p in range(len(lit) + 1)}, lit
        for c in INSERTED:
            for p in range(len(lit) + 1):
                v = inserts["%s@%d" % (repr(c), p)]
                assert v[p] == c and v[:p] + v[p + 1:] == lit, (lit, c, p)
        assert ("empty", "", "") in got and ("semi-twice", "", lit + ";" + lit) in got, lit


def test_no_generated_value_equals_a_literal_except_the_identity_row():
    swift = swift_unpaved()
    for row_id, lit, fam, value in ROWS:
        assert (value == lit) == (fam == "identity"), row_id
        assert (value in swift) == (fam == "identity"), row_id   # oracle == Swift's `contains`


@pytest.mark.parametrize("row", ROWS, ids=[r[0] for r in ROWS])
def test_every_entry_point_gates_exactly_the_swift_literal(row):
    _, lit, _, value = row
    exact = value == lit
    reason = assemble.gate_reason({"highway": "residential", "surface": value})
    assert (reason == assemble.GATE_UNPAVED_SURFACE) == exact, ("gate_reason", value, reason)
    state = surface.surface_state(highway="residential", surface=value)
    assert (state == surface.SURFACE_UNPAVED) == exact, ("surface_state", value, state)
    assert (surfacecoverage.bucket(value) == surfacecoverage.UNPAVED) == exact, ("bucket", value)
    table = surfacecoverage.coverage([types.SimpleNamespace(highway="residential", surface=value)])
    assert table["residential"][surfacecoverage.UNPAVED] == (1 if exact else 0), ("coverage", value, table)
