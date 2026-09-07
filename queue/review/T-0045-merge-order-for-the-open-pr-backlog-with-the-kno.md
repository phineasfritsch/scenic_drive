---
id: T-0045
title: merge order for the open PR backlog, with the known ADD/ADD conflict on the gh stub
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:52:33Z
lease_expires_at: 2026-09-07T18:52:33Z
worktree: .
branch: task/T-0045
exclusive: []
touches: [queue/]
pins_affected: []
reviewer: agent/reviewer-27
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Twelve PRs are open and none can merge: GitHub Actions stopped executing at about 15:11 UTC on 2026-09-07
("recent account payments have failed or your spending limit needs to be increased"), and `ops/merge`
correctly refuses a PR whose checks are not green. Four of the twelve are stacked on each other, and
agent/reviewer-20 has already established that `ops/lib/gh-stub-for-merge-tests` will conflict ADD/ADD between
`task/T-0021` and `task/T-0022`.

Merging that backlog in an arbitrary order once Actions returns is how one of those diffs gets silently
dropped - which is the same failure the whole `ops/` harness exists to prevent, one level up.

Deliverable: `queue/MERGE-ORDER.md`, derived from the actual file overlaps rather than from memory, saying
what merges when and what has to be checked again at merge time rather than trusted from this document.

## Log

- 2026-09-07 claimed by agent/claude-opus-5; reviewer agent/reviewer-27.

- **Derived, not recalled.** The overlap table comes from
  `git diff --name-only origin/main...origin/task/<X>` for all twelve branches, with `queue/` filtered out,
  and the stack shape from `gh pr list --json number,headRefName,baseRefName`. Both are in the document so the
  next person can re-run them rather than believe them.

- **The order is about correctness, not priority.** T-0039 goes first because until it lands every other PR
  sits inside the window it fixes: a branch whose task is in `queue/done/` - which `ops/merge` REQUIRES on the
  PR head - can commit any path with the pre-commit hook exiting 0.

- **The one real conflict** is the stub, ADDed by both T-0021 and T-0022. reviewer-20 resolved it in advance
  with `git merge-tree --write-tree`: `ops/merge` itself auto-merges (T-0021 changes gate 2, T-0022 gate 1),
  and T-0022's stub is a strict superset whose `STUB_FLIP` block is byte-identical to the version accepted on
  T-0021 after two earlier reviewers rejected wrong ones. The document says to take T-0022's copy AND to
  re-verify that byte-identity at merge time, because a fix landing on either branch invalidates it. That file
  has a history of being "fixed" into testing something narrower than it claims.

- **T-0042 and T-0038 need no order between them**, which is worth stating because both branch from T-0023 and
  both show a large `git diff` against `main`. Their OWN changes are disjoint: T-0042 touches
  `ops/lib/junit_count.py` and `ops/lib/check-failure-naming`; T-0038 touches `services/etl/Dockerfile`,
  `test_dockerfile.py` and `test_manifest.py`. The overlap in the diff is inherited from their shared base.

- **Nothing in the document bypasses a gate.** Every merge still runs `ops/merge <n> --wait`, which requires
  the task in `queue/done/` on the PR head and every check SUCCESS. A PR that does not go green after its base
  lands is a finding, not an exception.

- Handing to agent/reviewer-27; state -> review. The reviewer should re-run the two commands the overlap table
  is built from and check the order against what they show, rather than reading the table.
