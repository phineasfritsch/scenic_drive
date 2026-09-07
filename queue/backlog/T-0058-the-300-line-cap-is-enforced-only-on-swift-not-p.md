---
id: T-0058
title: the 300-line cap is enforced only on Swift, not Python or TypeScript
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-line-cap, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

CLAUDE.md states the rule without qualification:

    One type per file, filename == type name, **300-line cap**.

`ops/lib/check-line-cap` (P-SRC-02) enforces it over `git ls-files '*.swift'` and nothing else. Python,
TypeScript and shell are unenforced, and that is where most of the code now lives - the Swift tree is a
skeleton while `services/etl/etl/` and `services/api/src/` are where every M2 task is working.

Found by agent/reviewer-33 while reviewing T-0028, whose `byways.py` sits at **296 lines** - four short of a
cap that would not have stopped it anyway. That is the shape of the problem: the file that is closest to
breaking the rule is in the language the rule is not checked in, and nobody would have known.

- Extend the check to the languages the repo actually writes. At minimum `*.py` and `*.ts`; decide about
  shell, where `ops/*` scripts are legitimately long and mostly comment, and say what you decided.
- Measure the tree FIRST and put the numbers in the log before changing anything. If files already exceed the
  cap, that is a finding about the cap or about those files, and it has to be settled before the check can go
  green - do not quietly raise the limit to whatever the current maximum happens to be, and do not split a
  file solely to satisfy a number.
- The existing coverage guard is the interesting part to copy correctly, not the line count: P-SRC-02 already
  refuses to pass vacuously over an empty or renamed tree (`MIN_FILES`, and a per-package check that a
  package contributing only a manifest is caught). Whatever set you add needs the same, or it will pass
  cheerfully on the day somebody moves `services/etl` and nothing matches the glob.
- Demonstrate red per language: a >300-line file of each kind, shown passing before and failing after, naming
  the file.
- Note that `--source-only` mode exists for the push gate; keep the added work inside it only if it is fast.

Related and already filed: T-0043 (the coverage guard does not recognise `Package@swift-6.0.swift`) touches
the same script. Whichever lands first, the other rebases.

## Log
