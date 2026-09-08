---
id: T-0064
title: the curvature fixture's node set is member-nodes only, so 141 ways are wrongly eligible
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/, ops/etl-curvature-fixture]
pins_affected: []
reviewer: null
depends_on: [T-0025]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/etl-curvature-fixture` builds `work/curvature-oracle/subset.osm.pbf` with `osmium getid -r`, which
retains only the oracle ways' OWN MEMBER NODES. That is **650 of Vermont's 14,296 squash-tagged nodes**.

So the fixture's third selection condition - "no tagged node within 30 m" - is evaluated against 4.5% of the
nodes that actually exist. A stop sign 20 m away on a side street is invisible to it.

Measured while deciding T-0050: re-running the identical exposure test against all 14,296 nodes raises the
processor-4 hit count from **273 to 383 ways**, and the P4-or-P5 union from **305 to 446**. About **141 ways
currently sit in the 2384-way eligible pool that a correct test would exclude.**

T-0025's own log already suspected this and said so: *"The residual 5% is consistent with tagged nodes on
ADJACENT ways: `osmium getid -r` pulls only the nodes these ways reference, so a traffic signal 25 m away on
a cross street is not in the subset and cannot be excluded. Stated rather than chased."* It has now been
chased, and the number is 141.

**What it does and does not invalidate.** The agreement figures are not wrong - every way in the fixture is
still a way we computed correctly. What is wrong is the CLAIM the fixture makes about itself: that its 2384
ways are the ones no squash post-processor can reach. 141 of them are reachable, and they are exactly the
ways most likely to disagree with the published values, because a squash we do not implement was applied to
them upstream. So this most likely means the true agreement rate is **higher** than 94.42%, not lower - the
excluded set is contaminated with ways that were always going to miss.

- Rebuild the node set with `osmium tags-filter -R` over the full pinned extract instead of relying on
  `getid -r`'s member nodes, then re-run `ops/etl-curvature-fixture` and re-record.
- Expect the funnel's `no_squash` count to fall by roughly 141 and the agreement rate to move. Report the new
  figures FROM THE PINNED IMAGE, both platforms, per T-0025's own rule.
- The fixture is a snapshot re-record, so per CLAUDE.md it needs a different agent to review it than the one
  who re-records it.
- Check whether `MIN_AGREEMENT = 0.90` still has its stated margin afterwards. The floor was chosen against a
  worst-platform 93.75%; if the population changes, that sentence has to change with it or it becomes another
  number quoted from a run that no longer exists.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the T-0050 decision workflow, which measured the full-node
  exposure while sizing the squash processors and found the fixture's own selection condition is evaluated
  against 4.5% of the relevant nodes.
