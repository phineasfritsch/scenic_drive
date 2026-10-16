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
touches: [services/etl/etl/assemble.py, services/etl/etl/surface.py, services/etl/tests/, ops/mutate/surfacecoverage.py]
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
- 2026-10-16T19:43:30Z RED FIRST (A4c): test_unpaved_surfaces_owner.py written, run on main's assemble.py (the
  second literal still in place): `FAILED tests/test_unpaved_surfaces_owner.py::test_the_shipped_etl_has_one_
  unpaved_set` and `::test_every_module_naming_the_set_holds_the_owners_object` (`AssertionError: assemble.py`,
  not the owner's object). The guard's violations on main, verbatim: `assemble.py UNPAVED_SURFACES spells
  ['compacted', 'dirt', 'fine_gravel', 'gravel', 'ground', 'sand', 'unpaved']; the one approved unpaved set is
  surface.py UNPAVED_SURFACES` and `assemble.py:74 binds UNPAVED_SURFACES outside surface.py`. MEASURED literal
  population on main (casefold members of the parsed Swift set, by module-level site): assemble.py
  UNPAVED_SURFACES (7), profilegate.py SURFACES (7, uppercase), surface.py SURFACE_STATE_NAMES ['unpaved'],
  surface.py UNPAVED_SURFACES (7), surfacecoverage.py UNPAVED ['unpaved'] - five sites, the four R4 approves
  plus assemble's copy; nothing else under services/etl/etl spells a value.
- 2026-10-16T19:45:00Z GREEN: assemble.py now `from .surface import UNPAVED_SURFACES` (exported in __all__; 299
  lines), its literal and comment gone; test_assemble asserts `assemble.UNPAVED_SURFACES is
  surface.UNPAVED_SURFACES` and `set(surface.UNPAVED_SURFACES) == _swift_set("unpavedSurfaces")` (299 lines; a
  two-line docstring became one). The guard first flagged `assemble.py:73 names UNPAVED_SURFACES outside a read
  or the owner's import` - the `__all__` string; ruled an approved site (a module-level `__all__` constant) and
  row `bound-through-globals` added so a string-named binding elsewhere stays red. 26 passed. Each prove-red row's
  violations, verbatim heads: second-literal-list-elsewhere `score.py ROUGH_SURFACES spells ['dirt', 'gravel']`;
  import-replaced-by-a-literal-copy `assemble.py UNPAVED_SURFACES spells [...7]` + `assemble.py:62 binds`;
  import-replaced-by-a-frozenset-copy `assemble.py:63 binds UNPAVED_SURFACES outside surface.py`;
  reimported-from-assemble `surfacecoverage.py:59 imports UNPAVED_SURFACES other than ...`;
  another-object-under-the-name `assemble.py:62 imports ...`; inline-comparison-beside-the-set `assemble.py
  gate_reason spells ['Gravel']`; uppercase-copy `score.py _GH_ROUGH spells ['DIRT', 'GRAVEL']`; owner-narrowed
  (6 values), owner-widened (+cobblestone), owner-renamed (`surface.py UNPAVED_VALUES spells` + `approved site
  ... is gone`), owner-rebound-twice (+mud, `binds ... 2 times`), owner-assigned-from-another-module
  `surfacecoverage.py:61 assigns .UNPAVED_SURFACES`, bound-through-globals `score.py:70 names ...`. Controls
  a-comment-naming-the-values, a-docstring-sentence, a-non-member-literal -> [].
- 2026-10-16T19:47:13Z A4a: Gates.swift loses "sand" -> `FAILED tests/test_assemble.py::test_the_gate_sets_are_
  the_ones_scenickit_gates_on`, `FAILED tests/test_unpaved_surfaces_owner.py::test_the_shipped_etl_has_one_
  unpaved_set` (7 failed, 33 passed); restored by git checkout. A4b: surface.py loses "sand" (pycache purged, 1.1
  s) -> the same two plus `test_the_shipping_entry_points_refuse_every_swift_value[sand]` (9 failed, 32 passed);
  restored, `"sand"` back at surface.py:46.
- 2026-10-16T19:50:00Z A5 pre-merge: `python -m pytest tests -rs -q` -> `2030 passed in 97.58s`, no skips.
- 2026-10-16T19:58:43Z FINAL, on the merged head ad1ecf28 (`git fetch origin` in the main checkout; origin/main
  325c2cd3 merged - it brought only queue/LOCKS/routing-profiles.lock and the T-0381 task file):
  - A1 `services/etl/etl/surface.py:45:UNPAVED_SURFACES = frozenset({` - the only line.
  - A2 `services/etl/etl/assemble.py:62:from .surface import UNPAVED_SURFACES` and
    `services/etl/etl/surfacecoverage.py:59:from .surface import UNPAVED_SURFACES`.
  - A3 `236 passed in 5.50s`, no skip lines. wc -l: assemble.py 299, surface.py 70, test_assemble.py 299,
    test_surface_state.py 119, test_unpaved_surfaces_owner.py 223.
  - A4 as quoted at 19:43:30Z and 19:47:13Z (no code changed since; the merge touched queue/ only).
  - A5 `2030 passed in 79.07s (0:01:19)`, no skips.
  - A6 check-line-cap rc=0 (`P-SRC-02: 682 Swift files tracked ... none over 300 lines`), check-pins-yaml.py
    rc=0 (`PINS-YAML ok pins=52 fields=418`), check-exec-bits rc=0 (`P-OPS-01: 235 files, 23 required present,
    all modes correct`), check-safety-disclaimer rc=0, check-mutate-population.py rc=0 (`P-PROC-06: every added
    module is covered or allowlisted; the floor of 169 holds`), check-mutate-only.py rc=0 (`NAME-PAIRS OK`),
    queue-check rc=0 (`QUEUE OK (371 tasks)`).
  - OPEN (R5): the new tests are not in P-PROD-01's named list (ops/lib/named-tests.json + PINS.yaml are outside
    touches:); they run in ops/test's ETL pytest.
- 2026-10-16T20:45:59Z rv1 FAIL (agent/rv1-t-0181, head 958c6580) - B1 surface.py:66 `surface.strip() in
  UNPAVED_SURFACES` survives the suite; B2 assemble.py:135 `surface.lower() in UNPAVED_SURFACES` is caught only by
  the anchor-text prove-red row. RULING: one root cause - guard (c) tested only that the exact Swift values are
  refused, never that every other spelling is admitted, and Swift's `unpavedSurfaces.contains` is exact-match.
  Fixed by CLASS in test_unpaved_surfaces_owner.py: VARIANTS (exact, upper, title, lead-space, trail-space,
  trail-tab) x every value of the PARSED Swift set (`variant_rows`, rows = f(parsed set)); through the shipping
  entry points `assemble.gate_reason`, `surface.surface_state`, `surfacecoverage.coverage` (the bucket counted
  in the returned table): unpaved iff the row is `exact`. Meta-test `test_the_variant_table_skips_no_variant`:
  the six names in order, the full cross product, ids unique, each non-exact spelling differs from v and is not
  in the Swift set. Old `test_the_shipping_entry_points_refuse_every_swift_value` replaced by
  `test_the_shipping_entry_points_refuse_exactly_the_swift_spelling` (42 rows). No product code changed.
  - RED on 958c6580's tests (driver .artifacts/t0181_rm.py: pycache purged + 1.1 s, touched files
    test_unpaved_surfaces_owner/test_assemble/test_surface_state/test_surfacecoverage/test_gate_port):
    `RM1 MISSED rc=0 165 passed`; `RM2 CAUGHT rc=1 1 failed, 164 passed` - only
    `test_each_prove_red_row_is_red[inline-comparison-beside-the-set]` (its `old` no longer occurs: anchor text,
    not behaviour - MISSED by behaviour); RM3 (added, surfacecoverage.bucket `surface.rstrip() in`)
    `RM3 MISSED rc=0 165 passed`.
  - GREEN with the table: `62 passed` (test_unpaved_surfaces_owner.py). Same driver:
    `RM1 CAUGHT rc=1 21 failed, 180 passed` - `refuse_exactly_the_swift_spelling[<v>-lead-space|trail-space|
    trail-tab]` for all 7 values (e.g. `[compacted-lead-space]`, `[dirt-trail-tab]`);
    `RM2 CAUGHT rc=1 15 failed, 186 passed` - `[<v>-upper|title]` x7 (e.g. `[gravel-upper]`, `[dirt-title]`) plus
    the anchor row; `RM3 CAUGHT rc=1 14 failed, 187 passed` - `[<v>-trail-space|trail-tab]` x7.
  - Meta-test red: the `("trail-tab", ...)` row deleted -> `FAILED
    tests/test_unpaved_surfaces_owner.py::test_the_variant_table_skips_no_variant`; restored -> `1 passed`.
  - wc -l test_unpaved_surfaces_owner.py 260. services/routing and profilegate untouched (T-0381).
- 2026-10-16T21:01:42Z rv1 fix FINAL on d19277a3 (origin/main 325c2cd3 merged: already up to date): touched tests
  (A3 set) `272 passed in 7.14s`, no skips; bare gates each rc=0 - check-safety-disclaimer, check-mutate-population.py
  (`the floor of 169 holds`), check-mutate-only.py (`NAME-PAIRS OK`), check-line-cap (`682 Swift files ... none over 300
  lines`), check-pins-yaml.py (`PINS-YAML ok pins=52 fields=418`), check-exec-bits (`235 files ... all modes correct`),
  queue-check (`QUEUE OK (371 tasks)`).
- 2026-10-16T22:07:58Z rv2 FAIL (agent/rv2-t-0181, head 029bd5a8) - B3 OWN3 surface.py:66 `surface.split(";")[0] in
  UNPAVED_SURFACES` and OWN4 surfacecoverage.py:104 `any(p in UNPAVED_SURFACES for p in surface.split(";"))` survive
  the ETL suite; B4 ancestry. RULING (orchestrator): close the CLASS, not the next spelling - the hand-picked VARIANTS
  table (case, whitespace) is replaced by a GENERATED near-miss corpus,
  services/etl/tests/test_unpaved_near_miss_corpus.py: for every literal L parsed from Gates.swift
  (`swift_unpaved()`, never typed) `near_misses(L)` yields identity; upper, title, swapcase; every single-char
  deletion; each of ' ', '\t', ';', '_', '-', 'x', '|', ',' inserted at every position 0..len(L); L;L, L;paved,
  paved;L, Lx, xL, L[:-1], LL; and ''. `test_every_entry_point_gates_exactly_the_swift_literal`: unpaved iff
  value == L at `assemble.gate_reason`, `surface.surface_state`, `surfacecoverage.bucket` AND
  `surfacecoverage.coverage`. Generator row count: 563 (compacted 101, dirt 56, fine_gravel 119, gravel 74,
  ground 74, sand 56, unpaved 83). Meta-tests: `test_the_generator_yields_every_family_for_every_literal` (every
  single family once, len(L) deletions, 8*(len(L)+1) insertions each re-derivable to L, total per literal) and
  `test_no_generated_value_equals_a_literal_except_the_identity_row` (non-identity values are not in the Swift set,
  so equality with L IS Swift's `contains` on this corpus). No product code changed.
  - Population: ops/mutate/surfacecoverage.py (T-0205's, added to touches:) gains SUBJECTS surface.py +
    assemble.py, EMPTIED test_unpaved_surfaces_owner.py + the corpus file, mutants OWN3, OWN4 and PREFIX
    (gate_reason rebinding a tag that is a PREFIX of an unpaved value - `grav`, `fine_grave` - to that value);
    MIN_MUTATIONS 25 -> 28. A first PREFIX form (`surface.startswith(u)`) was already caught on 029bd5a8's tests
    by `[compacted-trail-space]`, so it was replaced by the reverse prefix (a3009ae9).
  - RED on 029bd5a8's tests (driver at a3009ae9, run after 2026-10-16T21:43:16Z): `MISSED OWN3 ... (exit 0)`, `MISSED OWN4 ...
    (exit 0)`, `MISSED PREFIX ... (exit 0)`, `MUTATIONS: 25 caught, 3 missed, 0 skipped, of 28`, `MUTATE FAILED
    caught=25/28 equivalent_caught=0`.
  - GREEN at 84600771 (2026-10-16T22:01:44Z): `caught OWN3 <- ...::test_every_entry_point_gates_exactly_the_swift_
    literal[compacted-insert-';'@9-42]`, `caught OWN4 <- ...[compacted-insert-';'@0-33]`, `caught PREFIX <-
    ...[compacted-delete-8-12]`; `MUTATIONS: 28 caught, 0 missed, 0 skipped, of 28`, `EQUIVALENT: 0 caught, 2
    missed`, `MUTATE OK caught=28/28 equivalent_caught=0`. `--prove-vacuity`: `VACUITY: 0 caught, 28 missed, 0
    skipped, of 28` / `VACUITY PROVED`.
  - Meta red: the `("empty", "", "")` row dropped -> `FAILED ...::test_the_generator_yields_every_family_for_every_
    literal` (1 failed, 1 passed); `lit.swapcase()` -> `lit.swapcase().swapcase()` -> `FAILED ...::test_no_
    generated_value_equals_a_literal_except_the_identity_row`; restored -> `2 passed`.
  - Touched tests (corpus, owner, surfacecoverage, assemble, surface_state, gate_port): `723 passed in 34.29s`.
    wc -l: test_unpaved_surfaces_owner.py 218, test_unpaved_near_miss_corpus.py 96, ops/mutate/surfacecoverage.py
    265. Java (services/routing, T-0381) is not an entry point this task owns.
