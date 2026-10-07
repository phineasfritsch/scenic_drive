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
