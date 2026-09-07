# Scenic Drive — rules for agents

The full plan lives outside the repo (`~/.claude/plans/i-want-to-make-synthetic-twilight.md`). This file is the
part every agent must obey on every task. `ops/check-pins --source-only` enforces the mechanical parts.

## The premise
Agents report success on broken work. Everything in `ops/`, `pins/` and `queue/` exists to contradict you.
Run `ops/agent-preflight` first thing in every session. A smaller honest result beats a larger claimed one.

## Repository shape
- `Package.swift` (root) — **Linux-only** targets: ScenicKit, ScenicAPIClient, PlaceStore, Handoff, Telemetry.
  These may import Foundation (and GRDB in PlaceStore) and nothing else. Never `CoreLocation`, `MapKit`, `UIKit`,
  `SwiftUI`, `MapLibre`, `Ferrostar*`. Own `Coordinate` struct instead of `CLLocationCoordinate2D`.
- `apps/ios/Packages/ScenicApp/Package.swift` — Apple-only targets. `MapAdapter` is the only importer of MapLibre;
  `NavAdapter` the only importer of Ferrostar. Feature targets import only DesignSystem, ScenicKit, PlaceStore
  and their own protocols; feature targets never import each other.
- `apps/ios/ScenicDrive.xcodeproj` — thin shell with Xcode 26 buildable folders. It changes ~10 times ever.
- `services/api` (Cloudflare Worker, TS) · `services/routing` (GraphHopper) · `services/search` (Photon) ·
  `services/tiles` (Protomaps) · `services/etl` (Python).

## File discipline
- One type per file, filename == type name, **300-line cap**.
- **Serial-only files** (declare `exclusive:` in your queue task before touching): both `Package.swift`,
  `project.pbxproj`, `Package.resolved`, `services/routing/profiles/*.json`, `services/routing/config.yml`,
  per-package `*.xcstrings`, `services/etl/regions/*/curated.yaml`, `pins/floor_*.txt`.
- Never `git add -A`. Stage explicit paths. The pre-commit hook rejects paths outside your task's `touches:`.
- Never anchor a pin, a test, or a guard on a comment. Comments get stripped. Anchor on identifiers, built
  artifacts, config files, API fields or DB constraints.
- No secrets in the tree: no `sk.`-style tokens, `.p8`, `.p12`, `.netrc`, `.env`. The hook greps for them.
- Every `xcodebuild` passes `-derivedDataPath` under the worktree. Every `swift build/test` on a shared box
  uses its own `--scratch-path`.

## Verification
- `ops/test` — one command, prints `TESTS linux=N/F ios=N/F`, exits non-zero if failing or below floor.
- `ops/sane` — is the state sane; distinct exit codes; never mutates.
- `ops/check-pins` — every load-bearing property in `pins/PINS.yaml`; `TODO` assertions fail.
- A check that has never been seen red is untested. New checks are demonstrated red, then green, in the task log.
- Testers find and do not fix. Fixers open PRs. The reviewer of a task is never its owner (`ops/queue-check`).
- Snapshot references are re-recorded only by a human-initiated commit reviewed by a different agent.

## Product invariants you must not "optimize away"
- Motorway/trunk ways carry `scenic_score = 0`; they are penalized, **not** hard-excluded (freeway shoulders,
  scenic middle). Hard gates are safety only: unpaved (positive evidence), private/no access, track.
- The extra-time budget is a **ceiling**: returned ETA ≤ fastest + budget. Always.
- Attribution (`© OpenStreetMap contributors · Protomaps`) is visible on every map surface at every sheet detent.
- The safety disclaimer gates the first plan and stays visible on the route screen.
- ETAs show the *estimate · no traffic data* badge until a corridor has ≥ 5 learned samples.
- The server never receives more than one coordinate per user action, never more than 2 decimal places.
