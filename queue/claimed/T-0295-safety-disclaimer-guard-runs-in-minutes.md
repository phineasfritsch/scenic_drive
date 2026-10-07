---
id: T-0295
title: The P-SAFE-03 / P-ATTR-01 guards run in minutes on the Windows box, and the linked-tree pin lists tracked files so a Finder .DS_Store is not a false red
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T06:54:20Z
lease_expires_at: 2026-10-07T20:54:20Z
worktree: .worktrees/T-0295
branch: task/T-0295
exclusive: []
touches: [ops/lib/check-safety-disclaimer, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-linked, ops/lib/check-map-attribution, ops/lib/check-map-attribution-mutations, ops/lib/check-safety-disclaimer-mutations, ops/lib/check-safety-disclaimer-lib, ops/lib/check-safety-disclaimer-doors, ops/lib/check-map-attribution-sheet, .gitignore]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0289]
verify: [ops/check-pins]
acceptance:
  - "MEASURE FIRST: wall time of a bare 'bash ops/lib/check-safety-disclaimer' and 'bash ops/lib/check-map-attribution' on this box, alone, with a per-limb breakdown (rv1-t0289 measured ~72 min alone, 2.5 h with eight in parallel; CI pins-source-only takes ~2 min) - quote it and name the dominant limb before changing anything"
  - "Both guards finish under 10 minutes alone on this box with the same refusal set: the full --prove-red table refuses every row BY NAME exactly as before (quote the before and after summaries; any row whose printed reason changes is ruled)"
  - "-linked enumerates files via 'git ls-files' (tracked) plus untracked-but-not-ignored, so a .DS_Store ignored by .gitignore is not a refusal; a prove-red row shows an untracked, unignored file IS still refused by name"
---
## Brief

rv1-t0289 recordables (PR #179 sign-off): each full guard takes ~72 min alone on the Windows box (8944-9317 s under
load), which makes every review that touches apps/ios or Sources/ hours long; and -linked lists the working tree, so an
untracked .DS_Store on a Mac is a false red. Memory faster-verification-in-rounds.

## Log
- 2026-10-07T06:46:49Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0289's recordables on PR #179.
- 2026-10-07T06:54:20Z claimed by agent/claude-opus-5; lease until 2026-10-07T20:54:20Z
- 2026-10-07T07:35:20Z MEASURED FIRST (acceptance 1), before any change, on 49a8ef45: a bare
  `bash ops/lib/check-safety-disclaimer`, alone, under `bash -x` with PS4 `+|$EPOCHREALTIME|${FUNCNAME[*]}|` (xtrace
  forks nothing; seconds summed per limb = the function run_check called): `rc=0 wall=2121.6s`. Per limb:
  require_tracked_occurrences 615.2 s, occurrences_by_file 545.7 s (the two direct calls), require_ack_write 240.7 s
  (one more occurrences_by_file), require_pinned_app_swift 234.4 s (incl. -linked), require_pinned_surface 178.5 s,
  require_closed_doors 88.3 s, files_matching 86.4 s, count_fixed_in 45.9 s, run_check itself 42.6 s,
  require_frozen_blocks 14.5 s, require_feature_files 13.7 s, the rest < 4 s each. DOMINANT LIMB: -lib's per-file
  counters (1488 s, 70%) - `c="$(count_fixed_in ...)"` once per file per needle, each a subshell + sed + grep; the trace
  shows ~2 s per fork on this box, ~6 s per file. Second: -pinned's `pinned_digest` (subshell + sed + sha256sum + cut)
  once per pinned file, and pinned_shell's `grep -Fxq` per shell entry. Third: -doors' one awk per file per list.
  check-map-attribution measured the same way on a detached base worktree (.worktrees/T-0295-base at 49a8ef45), below.
- 2026-10-07T07:35:20Z RULINGS before code (author rule):
  R1 TOUCHES. The dominant limb lives in ops/lib/check-safety-disclaimer-lib, which the filed touches omit; -doors and
     check-map-attribution-sheet carry the same one-fork-per-file loop; acceptance 3's relief needs `.DS_Store` in
     .gitignore. Ruled: touches add those four paths. Nothing else moves.
  R2 HOW, NOT WHAT. Every per-file loop becomes ONE awk over the population that reads each line exactly as the old
     reader did (code_of: trailing CR, then `//` to end of line; sheet_code_lines: CR, trim, `//`-leading without a
     backslash dropped) and applies the same predicate (grep -c -F = a line holding the fixed string; grep -c -E = a
     line matching the ERE; the index() occurrence loop), printing in ARGUMENT order; a file named twice is read twice
     and its total divided back, so even a duplicate argument prints what the loop printed. A needle the old code read
     through `awk -v` still is (escape processing kept); the rest go through ENVIRON as grep took them raw. Digests:
     ONE sha256sum over raw bytes as a FAST PATH only (pinned_raw, keyed by the printed NAME, never by position - the
     positional `raw[$i]` of linked_compare misaligned after a file sha256sum could not read); any name whose raw
     digest is not its approved one is re-hashed through pinned_digest and judged, and refused, exactly as before.
     pinned_shell's per-entry `grep -Fxq` becomes whole-line associative-array membership. Messages are untouched.
  R3 ACCEPTANCE 3 AS FILED FAILS OPEN. Enumerating -linked as "tracked + untracked-but-not-ignored" removes every
     IGNORED entry from the population: apps/ios xcuserdata/ and .swiftpm/ (.gitignore lines 9 and 11; -linked's own
     header names an xcuserdata scheme's pre-action as running shell at build time and refuses it by design), and any
     Sources/ file under a self-ignoring `.gitignore` (`*`) that SwiftPM still compiles - P-SAFE-03 failing OPEN.
     Ruled: the population stays every entry on disk; git (`check-ignore`, which honours .gitignore and the Mac's
     global excludes and never reports a TRACKED file) decides ignore status for exactly one basename, `.DS_Store`, and
     only an ignored one is dropped (linked_unfinder). `.DS_Store` joins .gitignore so the relief holds on every Mac.
     An unignored or tracked .DS_Store, any other ignored file, and anything outside a work tree are refused by name
     as before. New prove-red row 49 adds an untracked, unignored `Packages/ScenicApp/.DS_Store` and must be refused
     naming `apps/ios: added Packages/ScenicApp/.DS_Store`; each copy's repo gets `core.excludesFile` = an empty file
     so the row cannot depend on the running box's global excludes. Out of scope, recorded: a .DS_Store INSIDE
     FeatureScenicHome/, FeatureSurpriseMe/ or ScenicDrive/ is still refused by -pinned's module/shell whitelists.
  R4 THE "BEFORE" TABLE. A full before run of either --prove-red table is not runnable: each of 48 rows is a whole
     guard run, and T-0289 measured single late rows at 8944-9317 s. Ruled: "before" is the table's own per-row
     expected names (unchanged; only row 49 is added) with T-0289's per-row evidence; the after run of each table runs
     ONCE, in the background, and must print every row `yes` and N/N.
- 2026-10-07T10:06:52Z RESULTS (acceptance 1-3), quoted from the run logs.
  AFTER, alone, on 4579d661 (same tracer): safety rc=0 wall=2121.6s -> rc=0 wall=273.9s; map rc=0 wall=2060.4s -> rc=0 wall=214.2s;
  each guard's stdout byte-identical to its baseline (15 and 28 lines - every count, line number and file
  total the green summaries print). Slowest limbs after: require_pinned_app_swift (incl. -linked) and
  require_pinned_surface, ~70-110 s each; -lib's counters and require_sheet_mount now 2-17 s.
  .DS_Store relief, -linked alone over a table-shaped copy (m/apps/ios a git repo, core.excludesFile empty): (a) an
  untracked, unignored Packages/ScenicApp/.DS_Store -> `P-SAFE-03: the pinned linked trees changed: apps/ios: added
  Packages/ScenicApp/.DS_Store.`; (b) the same file ignored (info/exclude) -> PASS rc=0; (c) that ignored name TRACKED
  -> refused, same line; (d) an ignored file of another name (zz.log) -> `... apps/ios: added Packages/ScenicApp/zz.log.`
  PROVE-RED, both tables run ONCE, concurrently, in the background on 4579d661 (R4): check-safety-disclaimer
  36 rows `yes`, 0 `no`, 0 UNREFUSED/UNNAMED; summary `NOT FINISHED at this commit` . check-map-attribution 39 `yes`, 0 `no`,
  0 UNREFUSED/UNNAMED; summary `NOT FINISHED at this commit` . Every row prints the reason its table encodes, unchanged but row 49.
  MERGED origin/main (0436f71b; -linked auto-merged with T-0290's 13 PlaceStore digests): bare
  check-safety-disclaimer rc=0 wall=624.9s; bare check-map-attribution rc=0 wall=752.9s (both while the two tables and the gates ran - not
  alone). QUEUE OK (287 tasks); `bash ops/check-pins --source-only`: not finished.
- 2026-10-07T11:21:44Z PRE-REVIEW M3 SURVIVED (BLOCKING), closed by class. M3 replaced linked_unfinder's basename filter
  (`-linked` line 227) with `ds=("${all[@]}")` - every ignored entry dropped, acceptance 3 as filed - and the bare guard
  went rc=0 over an ignored xcuserdata scheme with a `curl ... sh` pre-action (shipped: rc=1 `apps/ios: added
  ScenicDrive.xcodeproj/xcuserdata/...`). No row could see it: row 49's .DS_Store is UNignored. Ruled: the class is
  the relief widened past an UNTRACKED, IGNORED, exactly-`.DS_Store` entry - three axes, one row each. New row kind
  `!RULE!PATH[!add]` in -mutations: writes PATH and the copy's OWN rule into its .git/info/exclude (an added .gitignore
  would be refused as an added entry - the wrong reason), proves the premise with `git check-ignore` (and, for `!add`,
  `ls-files --error-unmatch` + `check-ignore --no-index` matched + plain `check-ignore` silent) or the table exits.
  Row 50 = M3's defect tree (`xcuserdata/`); row 51 an ignored `Packages/ScenicApp/Shadow.DS_Store` (`*.DS_Store`);
  row 52 a TRACKED, ignored `Packages/ScenicApp/.DS_Store`. -linked unchanged; table 218 -> 241 lines.
  RUN (faster-verification-in-rounds: only the touched rows), six one-row tables concurrent, each its own git toplevel
  of 05999ae1's ops/ apps/ios Package.swift Sources (.build-t0295m/run.sh), mutants sed-applied and diffed:
  SHIPPED  row 50 `1 yes` 1/1 rc=0 959s; row 51 `1 yes` 1/1 rc=0 968s; row 52 `1 yes` 1/1 rc=0 977s.
  M3   (`ds=("${all[@]}")`)                    row 50 `0 no` UNREFUSED, full green summary, 0/1 rc=1 1007s.
  M3b  (`*/.DS_Store` -> `*.DS_Store`)          row 51 `0 no` UNREFUSED, 0/1 rc=1 1012s.
  M3c  (`check-ignore --no-index --stdin -z`)  row 52 `0 no` UNREFUSED, 0/1 rc=1 1010s.
  Each new row: the guard refuses it by name on the shipped script, and the mutant it targets lets it through (rc=0).
- 2026-10-07T11:35:14Z MERGED origin/main (63c8fdac, from 521a3feb; -linked auto-merged with two ScenicAPIClient digests,
  line 227 unchanged). On the merged head, run bare and concurrently: check-safety-disclaimer rc=0 wall=527s;
  check-map-attribution rc=0 wall=529s; queue-check `QUEUE OK (288 tasks)` rc=0. Pushed 63c8fdac.
