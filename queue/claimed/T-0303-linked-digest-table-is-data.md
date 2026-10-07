---
id: T-0303
title: The P-SAFE-03 -linked digest tables move out of the guard script into a data file, so every Swift PR edits data and the guard stays under the 300-line cap
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T18:00:54Z
lease_expires_at: 2026-10-08T08:00:54Z
worktree: .worktrees/T-0303
branch: task/T-0303
exclusive: []
touches: [ops/lib/check-safety-disclaimer-linked, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/check-safety-disclaimer-mutations, ops/lib/check-map-attribution-mutations, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0294, T-0300]
verify: [ops/check-pins]
acceptance:
  - "MEASURE FIRST: wc -l of ops/lib/check-safety-disclaimer-linked on main (after T-0294 and T-0300 it is ~307, over the 300 cap) and the line count of PINNED_ROOT_SOURCES / PINNED_APP_OTHER / ROOT_PATH_LINES / ROOT_TOP_FILES"
  - "The four tables live in ops/lib/check-safety-disclaimer-linked-digests.txt (100644, one 'path digest' or one approved line per row, sections named); -linked reads it fail-closed: a missing file, an unknown section, a duplicated path, a malformed row, or an empty section each refuse by name (prove-red rows for each); the guard script drops under 300 lines"
  - "Same refusal set: every existing prove-red row in both tables is refused by the same name before and after (run the touched rows one-row plus the whole tables once, quoting the N/N lines); both bare guards exit 0 on main's tree"
  - "The data file is itself pinned: a row that edits it without the matching tree change is refused (the digest of the edited file no longer matches), so moving the table does not weaken the pin"
---
## Brief

T-0294's merge with T-0300 (2026-10-07) took ops/lib/check-safety-disclaimer-linked to 307 lines, past CLAUDE.md's
300-line cap, because every Sources/ file adds one digest line (memory sources-digest-pin). Every Swift PR also
conflicts there. Moving the tables to data keeps the guard small and makes digest edits obviously data edits.

## Log
- 2026-10-07T17:44:38Z filed by agent/claude-opus-5 (orchestrator) during T-0294's merge with main.
- 2026-10-07T18:00:54Z claimed by agent/claude-opus-5; lease until 2026-10-08T08:00:54Z
- 2026-10-07T18:04:35Z MEASURE + RULINGS (owner, before any code; branch at 4ece8567 = main).
  MEASURED: `wc -l ops/lib/check-safety-disclaimer-linked` = 307. Tables: ROOT_PATH_LINES lines 37-50 (12 rows, 14
  lines with its delimiters), ROOT_TOP_FILES line 53 (one line, 8 names), PINNED_APP_OTHER lines 56-70 (13 rows, 15
  lines), PINNED_ROOT_SOURCES lines 73-218 (144 rows = Package.swift + the 143 *.swift under Sources/, 146 lines).
  176 of the 307 lines are table.
  R1 FORMAT. ops/lib/check-safety-disclaimer-linked-digests.txt, 100644 (ops/lib/check-exec-bits: *.txt is data).
  Every line is either a header `[NAME]` or a row of the section above it; NAME is one of the four table names
  (the identifiers the script already uses, so a grep for PINNED_ROOT_SOURCES finds the data). Row shapes:
  PINNED_APP_OTHER / PINNED_ROOT_SOURCES `PATH SHA256` (PATH no whitespace, 64 lowercase hex); ROOT_TOP_FILES one
  name per row (no whitespace, no `/`); ROOT_PATH_LINES the trimmed manifest line, no leading/trailing whitespace,
  containing `path:` or `sources:`. No comments, no blank lines - anything else is a malformed row (a CR at line end
  is dropped, as pinned_digest does, so a CRLF checkout reads the same). Row order is free (C sort kept by hand).
  R2 FAIL-CLOSED READER `linked_load`, called first inside require_pinned_linked (fail is defined by then; sourcing
  stays side-effect free). Each refuses by name under LINKED_REASON: `approved tables file ... is missing`,
  `unknown section [X]`, `section [X] duplicated`, `duplicated path in [X]: KEY` (key = PATH for the digest
  sections, the whole row otherwise), `malformed row in [X]` (a row before any header names `[no section]`),
  `empty section [X]` (covers an absent header too). The path is fixed, `ops/lib/...` relative to the repository
  top every caller already cd's to (the same anchor -pinned's `. ops/lib/check-safety-disclaimer-linked` uses) -
  no flag or variable can point it elsewhere.
  R3 HOW THE DATA FILE IS PINNED. Not by its own sha256 typed in -linked: that digest would be retyped by the same
  hand in the same commit as every data edit, a table compared to itself (CLAUDE.md, PR #109), and it would put a
  one-line conflict back into -linked on every parallel Swift PR - the thing this task removes. The data file is
  pinned AGAINST THE TREE, both ways, by the checks that already run: a digest row edited without the tree is
  `PATH content changed`; a digest row deleted is `root: added PATH` / `apps/ios: added PATH`; one added is
  `... missing PATH`; a ROOT_PATH_LINES row edited/added/deleted is `root manifest line not approved` / `root
  manifest lines missing`; the structure itself is R2. Two new prove-red rows show the first two (D6, D7). The one
  row class NOT bound both ways is ROOT_TOP_FILES, an ALLOWANCE since T-0289 (fm M1: "none is required but
  Package.swift" - .git is a directory in the main checkout, Package.resolved exists only after ops/test, and every
  mutation copy holds only Package.swift + Sources/); a name added there alone passes exactly as an edit to the
  array did. Unchanged strength, ruled, not widened. Review covers the file as it covered the array: it sits in
  ops/lib beside the script, and this commit names it in P-SAFE-03's statement as where re-approval goes.
  R4 PROVE-RED. check-safety-disclaimer-mutations gains a `%` row kind: the row runs the REAL entry point (bash
  ops/lib/check-safety-disclaimer) from a repository copy m<N>/ (ops/ copied beside apps/ios, Package.swift and
  Sources/, m<N> git-initialised so the check's own cd to the top lands there) with the copy's data file edited
  by the sed script (`rm` deletes it). Rows D1-D5 are R2's five branches, D6 a digest edited in data only, D7 a
  path row deleted in data only. Every other row runs unchanged from the real top, as before. The map table is not
  edited: none of its rows reach -linked (each refuses on an earlier limb, and its copies hold no root package);
  it is run whole once to show the same 46/46 refusal set. Table expectations for rows 44-52 are byte-unchanged
  by this diff, so "same name before and after" is shown by the after-run against unchanged substrings, with
  T-0295's/T-0294's full-table logs as the before.
  R5 PINS.yaml: P-SAFE-03's and P-ATTR-01's statements say re-approval goes "in ops/lib/check-safety-disclaimer-linked";
  they now name -linked-digests.txt (text only; quoted values kept double-quoted, check-pins-yaml.py run).
- 2026-10-07T18:22:50Z RESULTS (owner). Commit 83b14697 pushed early; this entry's commit adds row 60 and PINS.yaml.
  TABLES IDENTICAL: the four arrays sourced from 4ece8567's -linked and the four tables linked_load reads from the
  data file dump byte-identical (`cmp` silent, 17488 bytes; 12 / 8 / 13 / 144 rows). `wc -l`: -linked 307 -> 172,
  -mutations 241 -> 262, -linked-digests.txt 181 (data; 100644 in the index, -linked and -mutations stay 100755).
  R4 CORRECTION: the map table holds 47 rows, not the 46 R4 said (H6b landed with T-0294); measured below.
  RULING ADDED: R2's reader has a SIXTH branch, `section [X] duplicated` (a header repeated); it gets its own row 60
  rather than being dropped, so every branch the reader has is seen red.
  PROVE-RED, ONE-ROW (copies of the table filtered by label, .artifacts/t0303/filter.py; run from the worktree):
  18:07:50Z-18:08:39Z new rows 53-59: each `1 yes` - `prove-red: 7/7 mutations refused by name`.
  18:08:39Z-18:10:07Z existing rows 44-52 (T-0289 x5, T-0295 x4, the rows that exercise the tables): each `1 yes`
  - `prove-red: 9/9 mutations refused by name`. Their expected substrings are byte-unchanged by this diff (`git diff
  4ece8567 -- ...-mutations | grep -c '^-  "'` = 0), so the same names as T-0295's `prove-red: 52/52`.
  18:15:53Z-18:16:01Z row 60 `T-0303 a section header repeated 1 yes` - `prove-red: 1/1 mutations refused by name`.
  WHOLE TABLES (once each, background): `bash ops/lib/check-safety-disclaimer --prove-red` 18:16:15Z-18:20:28Z
  `prove-red: 60/60 mutations refused by name` rc=0 (60 `yes`, 0 UNREFUSED); `bash
  ops/lib/check-map-attribution-mutations` 18:07:50Z-18:10:18Z `prove-red: 47/47 mutations refused by name` rc=0.
  BARE GUARDS (unmerged head, main unmoved since 4ece8567): check-map-attribution 18:16:15Z-18:16:24Z rc=0;
  check-safety-disclaimer 18:22:35Z-18:22:44Z rc=0, `... LAST all 48 app .swift, then 144 root + pbxproj file(s)
  (-linked).` Re-run on the merged head before the push.
- 2026-10-07T18:35:30Z FINAL ACCEPTANCE BLOCK (owner, head 6972d74f; `git fetch origin` + `git merge origin/main`:
  main still at 4ece8567, merge a no-op, so this IS the merged head).
  1 MEASURE: -linked was 307 lines at 4ece8567; tables 14 + 1 + 15 + 146 lines (12 / 8 / 13 / 144 rows) - entry
    18:04:35Z.
  2 DATA + READER: ops/lib/check-safety-disclaimer-linked-digests.txt 100644, sections [ROOT_PATH_LINES]
    [ROOT_TOP_FILES] [PINNED_APP_OTHER] [PINNED_ROOT_SOURCES]; linked_load refuses missing file / unknown section /
    duplicated path / malformed row / empty section / repeated section by name - rows 53-57 and 60 each `1 yes`.
    `wc -l ops/lib/check-safety-disclaimer-linked` = 172 (< 300), re-measured on this head.
  3 SAME REFUSAL SET: rows 44-52 `prove-red: 9/9` one-row, expectations byte-unchanged; whole tables `prove-red:
    60/60` and `prove-red: 47/47`. Bare guards on this head: check-safety-disclaimer 18:34:44Z-18:34:50Z rc=0,
    check-map-attribution 18:34:50Z-18:34:58Z rc=0.
  4 DATA FILE PINNED AGAINST THE TREE: row 58 (a digest edited in the data only) `1 yes` naming
    `Sources/Handoff/AppleMapsDirections.swift content changed`; row 59 (a path row deleted in the data only)
    `1 yes` naming `root: added Sources/ScenicKit/Geo/Geo.swift`. ROOT_TOP_FILES stays an allowance (R3).
  GATES: `bash ops/queue-check` `QUEUE OK (295 tasks)` rc=0; `bash ops/check-pins --source-only` 18:23:24Z-18:29:08Z
  `PINS ok=17 skipped=26 pending=1 expired=0 failed=0 tier=linux source-only` rc=0; `python
  ops/lib/check-pins-yaml.py` `PINS-YAML ok pins=44 fields=355` rc=0.
  OPEN: the claimed -> review transition (ops/review with a reviewer who is not agent/claude-opus-5) is the
  orchestrator's; this session did not pick a reviewer.
