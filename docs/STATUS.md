# Project status: 2026-11-24 audit

## Where things stand

| Area | State |
|---|---|
| Cloudflare Worker API (`services/api`) | Deployed and healthy (`/__health` ok, sha `2edb7e60`). 20 routes. |
| Scenic router (GraphHopper) | **Down.** `scenic-router.phineasfritsch.com` answers 530 (the tunnel origin is offline), so live `/plan`, `/loop`, `/trip` can't plan. |
| Search (Photon) | **Down.** `/search` answers `search_unavailable`. |
| Region data | LA only: 5 curated seeds (`services/etl/regions/la/curated.yaml`), 2 recorded corridors (`Tests/Fixtures/t0239`). |
| iOS app | Builds only on the macOS CI runner. The dev box is Windows, so nobody can run it locally. In the latest screenshots the basemap shows no roads and the header chips overlap. |
| Web app | Did not exist. Now `apps/web` (see below). |

## Problems found

1. **The process outweighs the product.** Of the 2,634 non-merge commits on `main`, 1,681 (64%) only move
   queue files, 441 (17%) only touch ops, pins or tests, and 512 (19%) touch product code. `ops/` (48k lines)
   and `queue/` (74k lines) together are about four times the size of `Sources/` + `apps/` + `services/api/src`
   combined (~34k lines). 437 tasks were filed in about 6 weeks.
2. **Work stalled.** There were up to 385 commits a day through Oct 18, and none since. Nothing can be demoed
   end to end, because the router and search hosts are offline and the app needs a Mac.
3. **Version-control sprawl** (fixed today, see below): 94 worktrees, 115 local and 316 remote branches,
   32 open PRs (29 of them untouched since Sept 8), and uncommitted company files on `main`.
4. **The queue's records don't match reality.** `queue/claimed/` holds 52 tasks, but only 3 PRs are open.
   Most claims belong to PRs that were abandoned.
5. **The full plan lives outside the repo** (`~/.claude/plans/i-want-to-make-synthetic-twilight.md`) and is
   missing on this machine. A new agent has only `CLAUDE.md` to go on.
6. **Mobile-first on a Windows dev box.** Every UI iteration costs a CI round trip to see a screenshot.

## Done in the 2026-11-24 cleanup

- Wrote every ref tip to `.git/refs-backup-2026-11-24.txt` before deleting anything.
- Removed the 29 worktrees that were clean and fully merged. 5 merged ones still have untracked files and were kept.
- Deleted 53 fully merged local branches (`git branch -d`) and 249 fully merged remote branches.
  None had an open PR.
- Closed 29 PRs with no activity since Sept 8, each with a comment. Their branches were kept, so they can be reopened.
- Committed the Handoff company files (`AGENTS.md`, `handoff.json`, `.cursor/rules/handoff.mdc`).
  Ignored `.shots-*/` screenshot scratch (51 MB).

Remaining: 3 open PRs (#305, #302, #145), 62 local branches, 67 remote branches, 65 worktrees.
These are unmerged work and are left for the owner to decide on.

## New direction: web first

The owner decided on 2026-11-24: build a working web app first, then port it to mobile. The web app can be a
demo, but it has to look good.

- `apps/web` is a Vite + React + TypeScript + MapLibre GL app. It runs on the dev box with `npm run dev`,
  with no Mac and no router.
- Until the router is back online, the demo replays the scenic router's recorded outputs
  (`Tests/Fixtures/t0239`: GraphHopper 11 over the real LA graph, fastest route plus lambda 0 to 8).
  A `PlanSource` interface lets the live `/plan` replace the recordings without changing the UI.
- Lightweight process for `apps/web` (owner, 2026-11-24): normal branch, commits, PR and CI.
  No queue tasks, pins or mutation floors.
- The product invariants in `CLAUDE.md` still apply to the web app: attribution, safety disclaimer,
  the budget as a ceiling, and the no-traffic-data badge.
