---
id: T-0085
title: the ratchet check scans any file, so prose that quotes a constant reads as a binding
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T04:04:58Z
lease_expires_at: 2026-09-08T10:04:58Z
worktree: wt/T-0085
branch: task/T-0085
exclusive: []
touches: [.githooks/commit-msg]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

[[T-0079]] added a ratchet guard to `.githooks/commit-msg`: lowering a `MIN_*` / `MAX_*` / `REQUIRED*` /
`EXEMPT*` binding needs a `ratchet-lower: <reason>` line. Its header states the scan covers **"any file"**, and
that was a deliberate, well-argued choice — a ratchet can live anywhere, and `services/api/src/ro.ts` holding
`MAX_SQL_LENGTH` proves it.

**The consequence was found by using the hook, not by attacking it.** The commit that recorded T-0079's own
adversarial verification was refused:

    commit-msg: ratchet lowered without a 'ratchet-lower: <reason>' line in the commit body:
      queue/claimed/T-0079-...md: MAX_SQL_LENGTH is gone - no binding of that name at
      queue/claimed/T-0079-...md, so nothing constrains it any more

Nothing was lowered. The staged change appends a report to a **markdown task file** whose log quotes
`MAX_SQL_LENGTH = 4000` inside a transcript. Prose that quotes a constant is indistinguishable, to this scan,
from code that defines one.

**Why this outranks a nuisance.** The hook's stated escape is `--no-verify`, and T-0079's own report admits
that route stays open. A guard that fires on documentation teaches exactly one habit — pass `--no-verify` —
and the next *real* lowering then goes through unremarked. The ratchet ends up worse guarded than before,
which is the "a guard that only ever refuses is an outage, not a repair" failure arriving through false
positives instead of through strictness. Task logs in this repo quote constants constantly, because that is
what a red-then-green demonstration looks like.

- **Do not narrow the scan to `ops/lib`.** That discards the reason the scan was broad, and `ro.ts` is the
  counter-example.
- Exclude paths that cannot define a binding: `queue/**/*.md` is documentation by construction, and so is any
  fenced code block or indented transcript inside a `.md`.
- Consider requiring the binding to look like a definition in a language the repo actually uses — an
  assignment at the start of a line in `.py` / `.ts` / `.sh` / a shell `declare` — rather than any occurrence
  of `NAME` near a number.
- **Demonstrate the false positive first**, then show it gone, and show a real lowering in `ops/lib/pins.py`
  and in `services/api/src/ro.ts` still refused. The last part is the one that matters: it is easy to fix a
  false positive by breaking the check.
- The refusal is preserved in history at `685ec8a`, committed with a truthful `ratchet-lower:` line explaining
  it was a false positive, so the case can be replayed.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after this hook refused the commit recording its own verification.
- 2026-09-08T04:04:58Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:04:58Z
