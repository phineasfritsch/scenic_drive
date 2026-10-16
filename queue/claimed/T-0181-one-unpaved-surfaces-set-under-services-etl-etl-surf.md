---
id: T-0181
title: one UNPAVED_SURFACES set under services/etl/etl - surface.py owns it, assemble.py imports it, the Gates.swift anchor moves with the set
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T19:37:00Z
lease_expires_at: 2026-10-17T19:37:00Z
worktree: .worktrees/T-0181
branch: task/T-0181
exclusive: []
touches: [services/etl/etl/assemble.py, services/etl/etl/surface.py, services/etl/tests/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0146, T-0173]
verify: [ops/test, ops/check-pins]
acceptance:
  - "grep -rn 'UNPAVED_SURFACES' services/etl/etl prints exactly ONE definition (surface.py) and imports elsewhere; test_assemble.py's _swift_set anchor on Sources/ScenicKit/Gates/Gates.swift asserts the SAME set - RED by name when one value is removed from either side"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From the 18:13 panel (CODE F2, grounded): main has exactly one unpaved list (Gates.swift:80-82); PR #102 adds
`assemble.UNPAVED_SURFACES` (anchored on Gates.swift by regex) and T-0173 adds `surface.UNPAVED_SURFACES`
(anchored on a typed plan:80 list); neither imports the other, and P-PROD-01's assertion is still TODO. Decided
by merge order today; fixed here after both land, not as a round on either PR.

## Log
- 2026-09-19T00:57:37Z filed by agent/claude-fable-5-1 from the 18:13 panel's grounded synthesis. Not started.
- 2026-10-16T19:37:00Z claimed by agent/claude-opus-5; lease until 2026-10-17T19:37:00Z
- 2026-10-16T19:40:37Z MEASURED on main 325c2cd3, every unpaved-surface list in the tree (grep -rn -i over
  services/etl, services/routing, Sources, Tests; `fine_gravel|"compacted"|"gravel"` and `UNPAVED_SURFACES`):
  - Sources/ScenicKit/Gates/Gates.swift:80-82 `public static let unpavedSurfaces: Set<String> = [` /
    `"gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",` / `]` - read at :153.
  - services/etl/etl/surface.py:45-47 `UNPAVED_SURFACES = frozenset({` same seven `})` - read at :66
    (surface_state); imported by surfacecoverage.py:59 `from .surface import UNPAVED_SURFACES` (read :104).
  - services/etl/etl/assemble.py:74 `UNPAVED_SURFACES = frozenset({"gravel", "dirt", "ground", "sand",
    "unpaved", "compacted", "fine_gravel"})` - a SECOND literal, read at :135 (gate_reason). Neither of the two
    ETL copies imports the other. assemble.py is 299 lines, surface.py 70.
  - services/etl/etl/profilegate.py:52-55 `SURFACES = frozenset({"MISSING", "PAVED", "ASPHALT", ... "UNPAVED",
    "COMPACTED", "FINE_GRAVEL", "GRAVEL", "GROUND", "DIRT", "GRASS", "SAND", "WOOD", "OTHER"})` - GraphHopper's
    16-value surface ENCODING vocabulary (the values the profile's expressions may name), not an unpaved list.
  - services/routing/profiles/car_scenic_base.json:8 priority `surface == GRAVEL || surface == DIRT || surface ==
    GROUND || surface == SAND || surface == UNPAVED || surface == COMPACTED || surface == FINE_GRAVEL` x0.
  - score.py: no unpaved list (score.py:29-32 says the gates live in the profile and ScenicKit.Gates).
  - Test-side expectations (not implementations): test_assemble.py:236-246 `_swift_set` parses Gates.swift and
    asserts `assemble.UNPAVED_SURFACES`; test_gate_port.py:53/96/148 parses Gates.swift (comment lines dropped)
    and asserts every ETL set on `assemble`; test_surface_state.py:28 PLAN_UNPAVED typed seven (plan:80);
    test_gate_parity.py:37 the seven as fixture class names; Tests/ScenicKitTests/GatesSetBoundaryTests.swift:94
    typed seven against Gates.unpavedSurfaces.
  - P-PROD-01's assertion is NOT TODO any more (T-0012: run-named-tests.py P-PROD-01, 133 pytest + 2 swift).
- 2026-10-16T19:40:37Z RULINGS.
  - R1 (owner): surface.py owns the ETL set, per the title. assemble.py IMPORTS it (`from .surface import
    UNPAVED_SURFACES`), so `assemble.UNPAVED_SURFACES is surface.UNPAVED_SURFACES`; surfacecoverage.py already
    imports it. No new module, no new number: nothing for ops/mutate (not a numeric module).
  - R2 (anchor): the ETL set stays bound to Gates.swift by IDENTIFIER - the parsed `unpavedSurfaces` Set<String>
    literal - never a comment. test_assemble.py's anchor moves to the owner: it asserts surface.UNPAVED_SURFACES
    == the parsed Swift set AND assemble's name is the owner's object. test_gate_port.py's ETL_SETS check on
    `assemble` is kept (it now reads the owner through the import). The Brief's "comment anchor" lines
    (`# Gates.swift:80-82, verbatim`, `# plan:80 ... Mirrors`) are reworded; nothing reads them.
  - R3 (profile): the router's list is the router's own. car_scenic_base.json and profilegate.SURFACES are not
    edited (T-0381 is in flight on services/routing; P-PROD-01's gate_parity fixture already holds the profile to
    the ETL row by row). profilegate.SURFACES is an approved site in the whitelist below as the encoding
    vocabulary, its seven unpaved members typed in the table as the measured uppercase spelling.
  - R4 (guard): a WHITELIST, new services/etl/tests/test_unpaved_surfaces_owner.py. AST over every .py under
    services/etl/etl: (a) every str constant whose casefold is a member of the parsed Swift set is at an approved
    (file, module-level statement) site with exactly the approved values - surface.py UNPAVED_SURFACES (all its
    str constants == the Swift set), surface.py SURFACE_STATE_NAMES ("unpaved", a column-state name),
    surfacecoverage.py UNPAVED ("unpaved", a bucket name), profilegate.py SURFACES (the seven uppercased);
    a missing approved site is red too; (b) every occurrence of the identifier UNPAVED_SURFACES is a Load, a
    `from .surface import UNPAVED_SURFACES` (no alias), or the one module-level store in surface.py; (c) every
    module naming it holds the owner's object at runtime. Prove-red rows run the same function over in-memory
    mutations of the shipped sources (second literal list, import replaced by a literal copy, by a frozenset()
    copy, re-import from assemble, an inline == comparison, an uppercase copy, the owner narrowed, widened,
    renamed); controls: the shipped tree, a comment, a docstring sentence. Every row's `old` must occur once.
  - R5 (scope): test literals under services/etl/tests are expectations, outside the whitelist (the task's
    words: services/etl/etl/). test_surface_state.py's typed plan:80 set stays as a deliberate widening tripwire;
    its docstring's "cannot close" paragraph is updated. Adding the new test to P-PROD-01's named list needs
    ops/lib/named-tests.json + PINS.yaml (outside touches:) - not done here; the guard runs in ops/test's pytest.
  - R6 (cap): test_assemble.py and assemble.py are both 299 lines; neither may grow net.
- 2026-10-16T19:40:37Z ACCEPTANCE (re-run and re-quoted at the final commit, on the merged head):
  - A1 `grep -rn "UNPAVED_SURFACES = " services/etl/etl` -> exactly one line, services/etl/etl/surface.py.
  - A2 `grep -rn "import UNPAVED_SURFACES" services/etl/etl` -> assemble.py and surfacecoverage.py, each
    `from .surface import UNPAVED_SURFACES`.
  - A3 `cd services/etl && python -m pytest -q -p no:cacheprovider -o addopts= tests/test_unpaved_surfaces_owner.py
    tests/test_assemble.py tests/test_gate_port.py tests/test_surface_state.py tests/test_gate_parity.py
    tests/test_surfacecoverage.py` -> all pass, 0 skipped.
  - A4 RED by name, each restored: (a) Gates.swift loses "sand" -> test_assemble
    test_the_gate_sets_are_the_ones_scenickit_gates_on red; (b) surface.py loses "sand" -> the same test and
    test_unpaved_surfaces_owner test_the_shipped_etl_has_one_unpaved_set red; (c) on main's assemble.py (the
    second literal) -> test_the_shipped_etl_has_one_unpaved_set red BEFORE the import lands, green after.
  - A5 `cd services/etl && python -m pytest tests -rs -q -p no:cacheprovider -o addopts=` -> count line, 0 skips.
  - A6 bare gates: check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check, check-safety-disclaimer,
    check-mutate-population.py, check-mutate-only.py -> each exit 0.
