---
id: T-0301
title: pins/PINS.yaml parses under a strict YAML loader - line 213's unquoted scalar with ': ' is quoted, and a check refuses any future line a strict loader rejects
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T14:15:55Z
lease_expires_at: 2026-10-07T22:15:55Z
worktree: .worktrees/T-0301
branch: task/T-0301
exclusive: []
touches: [pins/PINS.yaml, ops/lib/, .github/workflows/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "MEASURE FIRST: python -c 'import yaml; yaml.safe_load(open(\"pins/PINS.yaml\"))' on main fails with 'mapping values are not allowed here ... line 213, column 344' (the why_no_test_catches_it of the pin whose text contains 'refused with 41 paths, every one a file main change...'); list every line a strict loader rejects (fix one, re-run, repeat) and quote them"
  - "Each rejected value is made a valid YAML scalar WITHOUT changing its text (wrap in double quotes with inner quotes/backslashes escaped, or a block scalar) - a script compares the parsed string to the exact original characters after the key and prints equal for every changed line; the line-based ops/lib/pins.py reader still reads every pin identically (diff its parsed records before/after: equal)"
  - "A check (ops/lib/check-pins-yaml.py, 100755, wired into the pins-source-only CI job or ops/check-pins --source-only) loads PINS.yaml with yaml.safe_load and exits non-zero naming the line on failure; seen RED on the unfixed file by name, then green"
---
## Brief

Agents on T-0287, T-0298 and others reported PINS.yaml fails yaml.safe_load at line 213 col 344 (pre-existing). The
repo's own pins.py parses it line-wise, so nothing noticed; any tool using a real YAML loader (check-ios-compile-
guardrails.py imports yaml) cannot read the pins file. Text must not change - dated prose is append-only (memory
never-edit-dated-record-output).

## Log
- 2026-10-07T14:14:05Z filed by agent/claude-opus-5 (orchestrator) from repeated agent reports (T-0287 r2, T-0298).
- 2026-10-07T14:15:55Z claimed by agent/claude-opus-5; lease until 2026-10-07T22:15:55Z
- 2026-10-07T14:21:06Z agent/claude-opus-5 - rulings, measurement, fix, check.
  RULING 1 (Brief vs reality): the Brief names one bad line (213); the fix-one-rerun-repeat loop found TWO. Line 345
  (P-COST-01 why_no_test_catches_it) is already a "..." scalar but carries two bare inner quotes (index.ts
  `"/loop": ...`), so a strict loader ends the scalar early. Both are fixed here.
  RULING 2 ("exact original characters after the key"): for line 213 (plain) that is the raw value; for line 345 the
  outer quotes are delimiters, so the original text is what ops/lib/pins.py `_scalar` reads from the line (quotes
  stripped, `\"` `\\` unescaped - it had 0 backslashes, so that is the raw inner characters). The script compares
  the yaml.safe_load value (whole fixed file, and the line parsed alone) to that text.
  RULING 3 (wiring): new CI step `PINS.yaml parses as YAML` in linux-core.yml's pins-source-only job, after the
  existing PyYAML step, so PyYAML is guaranteed there; ops/check-pins is not changed.
  MEASURE (main 3515b844): `python -c 'import yaml; yaml.safe_load(open("pins/PINS.yaml", encoding="utf-8"))'`
  -> `yaml.scanner.ScannerError: mapping values are not allowed here / in "pins/PINS.yaml", line 213, column 344`.
  Loop (.artifacts/t0301/requote.py, gitignored; requotes each named line as a double-quoted scalar with `\` and
  `"` escaped, then re-loads):
    REJECTED line 213, column 344: mapping values are not allowed here
      key=why_no_test_catches_it form=plain chars=602 backslashes=0 bare_inner_quotes=0
    REJECTED line 345, column 1252: expected <block end>, but found '<scalar>'
      key=why_no_test_catches_it form=double-quoted with bare inner quotes chars=10281 backslashes=0 bare_inner_quotes=2
    REJECTED LINES: 2 -> [213, 345]
  TEXT PRESERVED:
    line 213 pin P-GIT-02 why_no_test_catches_it: equal (602 chars)
    line 345 pin P-COST-01 why_no_test_catches_it: equal (10281 chars)
    pins.py records before=44 after=44: equal
  `git diff --stat`: pins/PINS.yaml | 4 ++-- (2 lines changed, nothing else).
  CHECK ops/lib/check-pins-yaml.py (100755): exit 1 names the line on a load failure, exit 1 on a non-list/empty load
  or when the yaml ids differ from pins.py ids, exit 2 (cannot tell) without PyYAML or the file.
  RED on the unfixed file, by name:
    PINS-YAML FAIL: ...\pins\PINS.yaml line 213, column 344: mapping values are not allowed here   exit=1
  RED with only line 213 fixed (line 345 alone):
    PINS-YAML FAIL: only345.yaml line 345, column 1252: expected <block end>, but found '<scalar>'  exit=1
  RED on fail-closed paths: empty file -> `loads to NoneType, not a non-empty list of mappings` exit=1; missing file
  -> `CANNOT TELL ... is missing` exit=2; trailing `- id: P-X-01 # trailing` -> `item 44: yaml='P-X-01'
  pins.py='P-X-01 # trailing'` exit=1.
  GREEN after the fix: `PINS-YAML ok pins=44` exit=0; strict safe_load prints `safe_load ok`.
