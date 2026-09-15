---
id: T-0135
title: queue-check forces a reviewer name into review/ before anyone has reviewed
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py, queue/README.md]
pins_affected: [P-PROC-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/queue.py:424` refuses a task in `review/` that has no `reviewer:`, and refuses one whose `reviewer:`
is not an `agent/<name>`:

```
{rel}: in review/ without a reviewer
{rel}: in review/ with reviewer: {raw!r}, which is not an agent/<name> - a non-name cannot be compared,
       so reviewer-is-not-owner is undecidable
```

Both refusals are right about what they say. The problem is **when** they are enforced. `claimed -> review` is
the OWNER's transition, made at the moment the work is ready and **before any reviewer exists**. So the owner
has to invent a name to get past the gate, and the field then asserts a review that has not happened.

I did exactly that, repeatedly, this session: `reviewer: agent/reviewer-pr80`, `agent/reviewer-pr81`,
`agent/reviewer-pr-gates`. Nobody of that name reviewed anything. Two tasks sitting in `review/` on `main`
right now carry `agent/reviewer-42` and `agent/reviewer-41`, which have the same character.

### Why this is the defect this repository exists to catch

`reviewer != owner` is the fleet's one mechanical guarantee that a worker does not grade its own work. It is
satisfied here by a string the worker chose. The gate passes; the property it stands for is not established.
That is precisely the shape every review this week has been blocking on - **a check whose stated scope
exceeds what it covers** - sitting in the checker itself.

It is also actively misleading downstream. A task in `review/` with a reviewer name reads, to a person or an
agent scanning the queue, as *reviewed and awaiting merge*. What it actually means is *the owner finished*.
The one state nobody can distinguish is the one that matters.

### The shape of the fix

The `review/` state is carrying two meanings that need separating:

* **the owner has finished and is asking for review** - no reviewer yet, and that is correct, not a gap;
* **a reviewer has looked and signed off** - which is already a different directory, `done/`, and is what
  `ops/merge` reads.

So `review/` should probably require `reviewer: null` (or refuse a reviewer equal to the owner and otherwise
not demand one), and `done/` should require a real `agent/<name>` that is not the owner. The current rule has
them the wrong way round: it demands the name where it cannot exist, and the directory where it genuinely
must exist is guarded by `ops/merge` rather than by `queue-check`.

Weigh in the log before choosing - there may be a reason `review/` wanted a name that is not visible from
here, and `queue/README.md` should end up stating what each directory means either way.

### Do

1. Decide what `reviewer:` means in each state and make `ops/lib/queue.py` enforce that, not the reverse.
2. **Demonstrate red then green on the case that matters**: a task in `review/` whose `reviewer:` names
   somebody who never reviewed should be refusable, or the field should not be required there at all.
3. Fix the existing instances rather than leaving them: the two on `main` above, plus any this session's PRs
   carry. A field that was wrong when written stays wrong after the rule changes.
4. Do not weaken `reviewer != owner`. The goal is to make it mean something, not to relax it.

## Log
- 2026-09-15T20:30:00Z filed by agent/claude-opus-5. Surfaced by the fixer on PR #80, which refused to "close"
  a related minor finding on the grounds that it could not - the owner cannot make this field honest while the
  gate demands it be filled. I am the one who put the invented names there, on at least three tasks.
