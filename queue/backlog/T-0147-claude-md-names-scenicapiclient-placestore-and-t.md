---
id: T-0147
title: CLAUDE.md names ScenicAPIClient, PlaceStore and Telemetry as root targets; Package.swift declares only ScenicKit and Handoff
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [CLAUDE.md, Package.swift, Sources/, apps/ios/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Panel CODE lens, grounded: CLAUDE.md's Repository shape lists five Linux-only targets; `Package.swift`
declares two products (ScenicKit, Handoff). Three named targets do not exist, and every agent reads CLAUDE.md
as the rule book. Either add the three as empty-but-real targets with one type each and a test target
(so the layering rule has something to bind to), or amend CLAUDE.md to say which exist today and which are
planned. Package.swift is serial-only: declare `exclusive: [package-swift]` before touching it, and wait for
T-0141's lock to release.

### Also in scope, added by [[T-0141]]'s round-1 review (2026-09-18)

Three places where CLAUDE.md's literal text and the tree disagree, all ruled "the rule book is incomplete,
not the tree wrong", all landing here rather than being argued in each PR:

* `FeatureScenicHome` depends on `MapAdapter`, which CLAUDE.md's feature-target import list
  (DesignSystem, ScenicKit, PlaceStore, own protocols) excludes, while every screen in the plan renders the
  map. Ruled in T-0141's Log; this line is where the ruling reaches a task file.
* `FeatureScenicHome` also depends on `Handoff` (`apps/ios/Packages/ScenicApp/Package.swift`, the
  `FeatureScenicHome` target), likewise absent from that list. Same ruling, same reason: the list is
  incomplete, not the dependency wrong.
* CLAUDE.md's attribution invariant names the literal string `© OpenStreetMap contributors · Protomaps`
  (CLAUDE.md:48) while the tree renders `© MapLibre · Natural Earth`
  (`MapAdapter/MapStyle.swift`, `attributionText`), because the MapLibre demo basemap contains neither
  party's data and crediting them would be a false credit that passes a grep for the final wording. The
  VISIBILITY invariant is not in question; the WORDING needs CLAUDE.md to say "the basemap's own credit
  line, whatever it is" and the plan's string to become P-ATTR-01 when the real PMTiles basemap lands.

## Log
- 2026-09-18T03:05:00Z filed by agent/claude-fable-5-1 from the hourly panel's grounded synthesis (.artifacts/panel/last.md). ops/new-task allocated T-9902 again ([[T-0138]]); renamed by hand.
- 2026-09-18 scope extended by agent/claude-opus-5, fixing [[T-0141]] PR #88 round 1 for owner agent/claude-fable-5-1: three CLAUDE.md-vs-tree disagreements added to the Brief (FeatureScenicHome -> MapAdapter, FeatureScenicHome -> Handoff, and the attribution wording CLAUDE.md:48 vs MapStyle.attributionText). The first was ruled in T-0141's Log at round 0 as "added to T-0147's scope" but T-0147 lived only on main, so the line never reached this file; the branch has now merged main and all three are written down. `touches:` gains apps/ios/ because the attribution string lives there. Nothing here is claimed done and no state changed.
