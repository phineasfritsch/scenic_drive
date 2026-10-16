"""T-0181: ONE unpaved-surface set under services/etl/etl - `surface.UNPAVED_SURFACES` - and every other ETL
module imports it.

Two ETL copies of Gates.swift's `unpavedSurfaces` (assemble.py's gate and surface.py's corpus column) each
passed their own suite and neither imported the other, so nothing stopped them drifting apart: a corpus whose
gate refuses a value its surface column calls paved is the drift P-PROD-01 forbids. The guard is a WHITELIST
over code, never a list of bad spellings:

  (a) every str constant under services/etl/etl whose casefold is a value of the PARSED Swift set sits at an
      approved (file, module-level statement) site holding exactly the approved values, and a missing
      approved site is red; the owner's site must hold the Swift set and no other string;
  (b) every occurrence of the identifier `UNPAVED_SURFACES` is a read, a plain `from .surface import
      UNPAVED_SURFACES`, or the ONE module-level binding in surface.py;
  (c) every module that names it holds surface's object at runtime, and the shipping entry points
      (`assemble.gate_reason`, `surface.surface_state`, `surfacecoverage.coverage`) call unpaved exactly the
      Swift spelling: each Swift value x {exact, upper, title, leading/trailing space, trailing tab}, the
      exact row refused and every variant admitted, as Swift's exact-match `contains` does.

Comments are not code and are not read. The prove-red rows run the SAME functions over in-memory mutations of
the shipped sources; a row whose `old` does not occur exactly once fails, it never skips.
"""
from __future__ import annotations

import ast
import importlib
import pathlib
import re
import types

import pytest

from etl import assemble, surface, surfacecoverage

ROOT = pathlib.Path(__file__).resolve().parents[3]
ETL_DIR = ROOT / "services" / "etl" / "etl"
GATES_SWIFT = ROOT / "Sources" / "ScenicKit" / "Gates" / "Gates.swift"
OWNER_FILE, IDENT = "surface.py", "UNPAVED_SURFACES"
OWNER_MODULE, OWNER_LEVEL = "surface", 1
STATE_NAME = "unpaved"


def swift_unpaved() -> frozenset:
    """Gates.unpavedSurfaces, parsed from the Swift CODE (whole `//` lines dropped, never a doc comment)."""
    code = "\n".join(line for line in GATES_SWIFT.read_text(encoding="utf-8").splitlines()
                     if not line.lstrip().startswith("//"))
    found = re.findall(r"public static let unpavedSurfaces: Set<String> = \[(.*?)\]", code, re.S)
    assert len(found) == 1, "unpavedSurfaces is declared %d times in %s" % (len(found), GATES_SWIFT)
    values = frozenset(re.findall(r'"([^"]+)"', found[0]))
    assert values, "unpavedSurfaces parsed empty from %s" % GATES_SWIFT
    return values


def approved(swift: frozenset) -> dict:
    """(file, site) -> the sorted str constants allowed there; every row is a function of the Swift set."""
    names = sorted(v for v in (STATE_NAME,) if v.casefold() in {s.casefold() for s in swift})
    return {
        (OWNER_FILE, IDENT): sorted(swift),                         # the owner: ALL its strings
        (OWNER_FILE, "SURFACE_STATE_NAMES"): names,                 # the column state's name, not a tag set
        ("surfacecoverage.py", "UNPAVED"): names,                   # a coverage bucket's name
        ("profilegate.py", "SURFACES"): sorted(v.upper() for v in swift),  # GraphHopper's encoding (R3)
    }


def shipped() -> dict:
    sources = {p.relative_to(ETL_DIR).as_posix(): p.read_text(encoding="utf-8")
               for p in sorted(ETL_DIR.rglob("*.py"))}
    assert OWNER_FILE in sources and len(sources) > 1, sorted(sources)
    return sources


def _site(stmt: ast.stmt) -> str:
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        return stmt.targets[0].id
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return stmt.target.id
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return stmt.name
    return "<line %d>" % stmt.lineno


def literal_sites(sources: dict, swift: frozenset) -> dict:
    """(file, module-level site) -> sorted str constants that spell a Swift value (any case)."""
    folded, found = {v.casefold() for v in swift}, {}
    for name, text in sorted(sources.items()):
        for stmt in ast.parse(text, filename=name).body:
            site = (name, _site(stmt))
            for node in ast.walk(stmt):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and (
                        site == (OWNER_FILE, IDENT) or node.value.casefold() in folded):
                    found.setdefault(site, []).append(node.value)
    return {site: sorted(values) for site, values in found.items()}


def literal_violations(sources: dict, swift: frozenset) -> list:
    found, allowed = literal_sites(sources, swift), approved(swift)
    out = ["%s %s spells %s; the one approved unpaved set is %s %s" % (f, s, v, OWNER_FILE, IDENT)
           for (f, s), v in sorted(found.items()) if allowed.get((f, s)) != v]
    out += ["approved site %s %s is gone (expected %s)" % (f, s, v)
            for (f, s), v in sorted(allowed.items()) if v and (f, s) not in found]
    return out


def identifier_violations(sources: dict) -> list:
    out, owner_stores = [], 0
    for name, text in sorted(sources.items()):
        tree = ast.parse(text, filename=name)
        owner_targets = {id(stmt.targets[0]) for stmt in tree.body if name == OWNER_FILE
                         and isinstance(stmt, ast.Assign) and _site(stmt) == IDENT}
        # A module-level `__all__` may export the name (assemble re-exports the owner's object).
        exported = {id(n) for stmt in tree.body if isinstance(stmt, ast.Assign) and _site(stmt) == "__all__"
                    for n in ast.walk(stmt.value) if isinstance(n, ast.Constant)}
        for node in ast.walk(tree):
            where = "%s:%d" % (name, getattr(node, "lineno", 0))
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if IDENT not in (alias.name, alias.asname):
                        continue
                    plain = (isinstance(node, ast.ImportFrom) and node.module == OWNER_MODULE
                             and node.level == OWNER_LEVEL and alias.name == IDENT and alias.asname is None)
                    if not plain:
                        out.append("%s imports %s other than `from .surface import %s`" % (where, IDENT, IDENT))
            elif isinstance(node, ast.Name) and node.id == IDENT and not isinstance(node.ctx, ast.Load):
                if id(node) in owner_targets:
                    owner_stores += 1
                else:
                    out.append("%s binds %s outside %s" % (where, IDENT, OWNER_FILE))
            elif isinstance(node, ast.Attribute) and node.attr == IDENT and not isinstance(node.ctx, ast.Load):
                out.append("%s assigns .%s" % (where, IDENT))
            elif (isinstance(node, ast.arg) and node.arg == IDENT) or (
                    isinstance(node, ast.keyword) and node.arg == IDENT) or (
                    isinstance(node, (ast.Global, ast.Nonlocal)) and IDENT in node.names) or (
                    isinstance(node, ast.Constant) and node.value == IDENT and id(node) not in exported):
                out.append("%s names %s outside a read or the owner's import" % (where, IDENT))
    if owner_stores != 1:
        out.append("%s binds %s %d times at module level, not once" % (OWNER_FILE, IDENT, owner_stores))
    return out


def violations(sources: dict, swift: frozenset) -> list:
    return literal_violations(sources, swift) + identifier_violations(sources)


def test_the_shipped_etl_has_one_unpaved_set():
    assert violations(shipped(), swift_unpaved()) == []


def test_every_module_naming_the_set_holds_the_owners_object():
    namers = sorted(name for name, text in shipped().items() if any(
        isinstance(n, ast.Name) and n.id == IDENT for n in ast.walk(ast.parse(text))))
    assert {OWNER_FILE, "assemble.py", "surfacecoverage.py"} <= set(namers), namers
    for name in namers:
        module = importlib.import_module("etl." + name[:-len(".py")].replace("/", "."))
        assert getattr(module, IDENT) is surface.UNPAVED_SURFACES, name
    assert set(surface.UNPAVED_SURFACES) == swift_unpaved()


# Swift's `Gates.verdict` asks `unpavedSurfaces.contains(surface)` - exact match, no case fold, no trim. Each
# ETL entry point must agree with it on EVERY spelling: refuse the exact value, admit each variant (rv1 B1/B2).
VARIANTS = (
    ("exact", lambda v: v),
    ("upper", lambda v: v.upper()),
    ("title", lambda v: v.title()),
    ("lead-space", lambda v: " " + v),
    ("trail-space", lambda v: v + " "),
    ("trail-tab", lambda v: v + "\t"),
)


def variant_rows(swift: frozenset) -> list:
    """(id, swift value, variant name, spelled tag) for every Swift value x every variant - f(parsed set)."""
    return [("%s-%s" % (v, name), v, name, spell(v)) for v in sorted(swift) for name, spell in VARIANTS]


def test_the_variant_table_skips_no_variant():
    swift, rows = swift_unpaved(), variant_rows(swift_unpaved())
    assert [n for n, _ in VARIANTS] == ["exact", "upper", "title", "lead-space", "trail-space", "trail-tab"]
    assert {(v, name) for _, v, name, _ in rows} == {(v, n) for v in swift for n, _ in VARIANTS}
    assert len(rows) == len(swift) * len(VARIANTS) == len({r[0] for r in rows})
    for _, v, name, spelled in rows:
        assert (spelled == v) == (name == "exact"), (v, name)   # a variant equal to v would test nothing
        assert (spelled in swift) == (name == "exact"), (v, name)


@pytest.mark.parametrize("row", variant_rows(swift_unpaved()), ids=[r[0] for r in variant_rows(swift_unpaved())])
def test_the_shipping_entry_points_refuse_exactly_the_swift_spelling(row):
    _, value, _, spelled = row
    exact = spelled == value
    reason = assemble.gate_reason({"highway": "residential", "surface": spelled})
    assert (reason == assemble.GATE_UNPAVED_SURFACE) == exact, (spelled, reason)
    state = surface.surface_state(highway="residential", surface=spelled)
    assert (state == surface.SURFACE_UNPAVED) == exact, (spelled, state)
    way = types.SimpleNamespace(highway="residential", surface=spelled)
    table = surfacecoverage.coverage([way])
    assert table["residential"][surfacecoverage.UNPAVED] == (1 if exact else 0), (spelled, table)


IMPORT = "from .surface import UNPAVED_SURFACES"
OWNER_VALUES = '"gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",'
SCORE_ANCHOR = 'UNSURVEYED_CLASSES = frozenset({"unclassified", "residential"})'
GATE_TEST = "    if surface is not None and surface in UNPAVED_SURFACES:"

# (id, file, old, new): each must be RED. Every one is a way a second set, or a copy of the one, gets back in.
PROVE_RED = (
    ("second-literal-list-elsewhere", "score.py", SCORE_ANCHOR,
     SCORE_ANCHOR + '\nROUGH_SURFACES = frozenset({"dirt", "gravel"})'),
    ("import-replaced-by-a-literal-copy", "assemble.py", IMPORT,
     "UNPAVED_SURFACES = frozenset({%s})" % OWNER_VALUES.rstrip(",")),
    ("import-replaced-by-a-frozenset-copy", "assemble.py", IMPORT,
     "from . import surface as _surface\nUNPAVED_SURFACES = frozenset(_surface.UNPAVED_SURFACES)"),
    ("reimported-from-assemble", "surfacecoverage.py", IMPORT, "from .assemble import UNPAVED_SURFACES"),
    ("another-object-under-the-name", "assemble.py", IMPORT,
     "from .surface import SURFACE_UNPAVED as UNPAVED_SURFACES"),
    ("inline-comparison-beside-the-set", "assemble.py", GATE_TEST,
     '    if surface is not None and (surface in UNPAVED_SURFACES or surface == "Gravel"):'),
    ("uppercase-copy", "score.py", SCORE_ANCHOR, SCORE_ANCHOR + '\n_GH_ROUGH = ("GRAVEL", "DIRT")'),
    ("owner-narrowed", OWNER_FILE, OWNER_VALUES, OWNER_VALUES.replace(' "sand",', "")),
    ("owner-widened", OWNER_FILE, OWNER_VALUES, OWNER_VALUES + ' "cobblestone",'),
    ("owner-renamed", OWNER_FILE, "UNPAVED_SURFACES = frozenset({", "UNPAVED_VALUES = frozenset({"),
    ("owner-rebound-twice", OWNER_FILE, "SURFACE_UNKNOWN = -1",
     "SURFACE_UNKNOWN = -1\nUNPAVED_SURFACES = UNPAVED_SURFACES | {\"mud\"}"),
    ("owner-assigned-from-another-module", "surfacecoverage.py", IMPORT,
     IMPORT + "\nfrom . import surface as _s\n_s.UNPAVED_SURFACES = frozenset()"),
    ("bound-through-globals", "score.py", SCORE_ANCHOR,
     SCORE_ANCHOR + '\nglobals()["UNPAVED_SURFACES"] = frozenset()'),
)
# Controls: each must stay GREEN - the scanner reads code, not prose, and not every string.
CONTROLS = (
    ("a-comment-naming-the-values", "assemble.py", IMPORT, IMPORT + '  # "gravel", "dirt" and the rest'),
    ("a-docstring-sentence", "score.py", SCORE_ANCHOR,
     SCORE_ANCHOR + '\n"""gravel and dirt are gated in surface.py, not here."""'),
    ("a-non-member-literal", "score.py", SCORE_ANCHOR, SCORE_ANCHOR + '\nSMOOTH = frozenset({"asphalt"})'),
)


def _mutated(file: str, old: str, new: str) -> dict:
    sources = shipped()
    assert sources[file].count(old) == 1, "%s: the row's `old` occurs %d times" % (file, sources[file].count(old))
    sources[file] = sources[file].replace(old, new)
    return sources


@pytest.mark.parametrize("row", PROVE_RED, ids=[r[0] for r in PROVE_RED])
def test_each_prove_red_row_is_red(row):
    _, file, old, new = row
    assert violations(_mutated(file, old, new), swift_unpaved()), row[0]


@pytest.mark.parametrize("row", CONTROLS, ids=[r[0] for r in CONTROLS])
def test_each_control_is_green(row):
    _, file, old, new = row
    assert violations(_mutated(file, old, new), swift_unpaved()) == [], row[0]


def test_the_name_rows_follow_the_swift_set():
    """Table rows are functions of the input: without `unpaved` in Swift the two name sites expect nothing."""
    swift = swift_unpaved()
    assert approved(swift)[(OWNER_FILE, "SURFACE_STATE_NAMES")] == [STATE_NAME]
    narrowed = approved(swift - {STATE_NAME})
    assert narrowed[(OWNER_FILE, "SURFACE_STATE_NAMES")] == [] == narrowed[("surfacecoverage.py", "UNPAVED")]
    assert narrowed[(OWNER_FILE, IDENT)] == sorted(swift - {STATE_NAME})
