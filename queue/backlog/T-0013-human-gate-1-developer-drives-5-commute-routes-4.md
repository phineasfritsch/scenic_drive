---
id: T-0013
title: "Human gate 1: developer drives 5 commute routes, >=4 beat the freeway, 0 rat-runs; evidence in pins/evidence/P-HUMAN-01.md"
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/evidence/]
pins_affected: [P-HUMAN-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**This task cannot be done by an agent.** It is the one gate in the whole plan that no amount of test
coverage substitutes for: a person drives five routes this thing planned and says whether they were better
than the freeway. Everything in `ops/` exists to stop agents reporting success on broken work, and this is the
check that stops the FLEET reporting success on a product nobody would use.

`P-HUMAN-01`'s assertion is `test -f pins/evidence/P-HUMAN-01.md`, and it expires after 30 days. The file is
the deliverable.

**The gate:** five real commutes, driven. At least four better than the freeway route the driver would
otherwise have taken. Zero rat-runs — no route that sends a car through a residential street as a cut-through.
One rat-run on the developer's own commute is the failure mode the plan calls fatal, because it is the one
that ends the relationship with the product.

**What the evidence file must contain**, per route, written at the time and not reconstructed afterwards:

    date, time of day, origin and destination (5 dp is fine, this file is not published)
    the extra-time budget asked for, and the ETA the app promised
    the actual door-to-door time
    better than the freeway? yes / no / about the same
    what made it better or worse, in a sentence - the answer that tunes the weights later
    any rat-run: street name, and why it was one
    any hazard the strip did not warn about

**What makes it honest:** the routes are chosen before driving, not after; a route that turns out badly still
counts as one of the five. Picking five and reporting the best four is how this gate becomes decoration.

**If it fails**, the playbook is `ops/route-autopsy <plan-id>`, which dumps the per-edge GATE/M/E terms and the
lambda trace. A bad drive becomes a PINNED NEGATIVE FIXTURE before any weight is touched — otherwise the
weights get tuned until that one drive looks good and the next five are worse. Two weeks of slack are in the
calendar for exactly two of these re-gate cycles.

**Blocked on:** M4. There is no app to drive yet — the plan puts this after the plan-and-preview milestone,
with the handoff to Apple Maps working. `ops/plan <O> <D> <B>` printing a maps.apple.com URL (M3) is enough to
drive from, and driving it that way is worth more than waiting for the UI.

Whoever picks this up: the deliverable is the file, and the file is only worth writing if the driving was
honest.

## Log
- 2026-09-19T02:11:14Z LA REWRITE, by agent/claude-fable-5-1 (19:13 panel, grounded): the owner lives in Westwood (regions/la, T-0107);
  human gate #1 (plan:231, "five commute routes, four better than the freeway, zero rat-runs") is five WESTWOOD
  commutes with an origin and destination the owner names - nothing in the plan or any Log records the
  destination, and the LA bbox (-119.00..-117.85 x 33.70..34.45) was argued around PCH, Angeles Crest and Palos
  Verdes, not around a commute. Before this gate is claimed: (1) the owner names the commute; (2) a check that
  both ends fit regions/la's bbox, red on a point outside; (3) T-0182 (`ops/plan`) is the tool that makes the
  five routes. This is the rewrite of this id, not a new task.
