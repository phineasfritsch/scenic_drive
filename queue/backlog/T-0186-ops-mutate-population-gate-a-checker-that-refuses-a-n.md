---
id: T-0186
title: ops/mutate population gate - a checker that refuses a new numeric module under services/etl/etl/ or Sources/ with no ops/mutate population, pinned; red on assemble.py and sinuosity.py first
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/, ops/lib/, pins/PINS.yaml, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0176, T-0146]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a checker (rule where it lives - ops/mutate/ beside the runners or ops/lib/ beside the other gates - and say why) that lists every module under services/etl/etl/ and Sources/ScenicKit/ whose name a git diff against main ADDS, and refuses by name when ops/mutate/ holds no population for it; RED BY NAME first on a copy of main where assemble.py (T-0146) and sinuosity.py (T-0161) have no population, then green once T-0176 and T-0187 land; an explicit allowlist for non-numeric modules (fetch.py, manifest.py, corpus.py) with the reason beside each"
  - "pins/PINS.yaml pin (anchor: process, runs_on: [linux], the P-GIT-02 interpreter style); --prove-red table (a population file deleted; a new module added with none; the allowlist widened to a numeric module)"
  - "bash ops/check-pins --source-only, bash ops/lib/check-line-cap, bash ops/queue-check bare at the final commit"
---
## Brief

From the 2026-09-19 21:13 panel (PROCESS, grounded). CLAUDE.md's Verification section already makes a new numeric
module ship its mutation population under ops/mutate/ with a literal floor and EQUIVALENT-with-witness entries -
"never prose in a task file". It is unenforced: ops/mutate/ holds sixteen files, all for Swift modules, zero for
Python; sinuosity.py merged via #94 after four rounds and assemble.py (#102) shipped without one; no check under
ops/ or .githooks/ references ops/mutate beyond comments. The population is simultaneously the fixer's brief and
the reviewer's must-enumerate list (T-0176's rationale). Lands after #102 and T-0176 so it does not add a fourth
blocking class to a fix pass in flight.

## Log
- 2026-09-19T03:29:43Z filed by agent/claude-fable-5-1 from the 21:13 panel's grounded synthesis. Not started.
