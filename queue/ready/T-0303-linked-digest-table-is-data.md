---
id: T-0303
title: The P-SAFE-03 -linked digest tables move out of the guard script into a data file, so every Swift PR edits data and the guard stays under the 300-line cap
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
