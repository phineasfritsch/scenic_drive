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
  artifacts, config files, API fields or DB constraints. Anchor a guard on a WHITELIST - every occurrence of
  the identifier must be at an approved site - never on a blacklist of spellings of the bad write (PR #101
  bought four rounds one spelling at a time). A test named for a defect binds to the shipping symbol - the
  entry point production runs - never to a helper, a literal, the module's own table, or a symbol no entry
  point calls (PR #109's main() was called by nothing; its source-layer guard compared a table to itself).
- No secrets in the tree: no `sk.`-style tokens, `.p8`, `.p12`, `.netrc`, `.env`. The hook greps for them.
- New scripts under `ops/` or `.githooks/` must be committed executable: `git update-index --chmod=+x <path>`.
  `core.filemode` is false on the Windows checkout, so git will not notice on its own and CI (`bash ops/x`) stays
  green while direct invocation breaks. Pin P-OPS-01 enforces it; data files there stay 100644.
- Never wait with a bare foreground `sleep` - the agent harness refuses it. Wait once with
  `python -c "import time; time.sleep(N)"`; never poll in a loop, never use `date` as a clock.
- Every `xcodebuild` passes `-derivedDataPath` under the worktree. Every `swift build/test` on a shared box
  uses its own `--scratch-path`.

## Verification
- `ops/test` — one command, prints `TESTS linux=N/F ios=N/F`, exits non-zero if failing or below floor.
- `ops/sane` — is the state sane; distinct exit codes; never mutates.
- `ops/check-pins` — every load-bearing property in `pins/PINS.yaml`; `TODO` assertions fail.
- A check that has never been seen red is untested. New checks are demonstrated red, then green, in the task log.
- The author rule: rule every disagreement between plan, Brief, code and reality in the Log before writing code;
  at the final pre-review commit re-run and re-quote the whole acceptance block. A correction commit that touches
  a measured file re-measures it (T-0162's `wc -l` 239 vs 242 cost a review round). Close the read-only
  verifier's findings before the review is bought. The final pre-review commit runs `git fetch origin` and merges
  `origin/main` as the LAST step before the push - re-run the acceptance block on the merged head, then push within
  minutes; a sign-off bought on a tree older than main's gate set is not a sign-off (PR #115 was refused at merge
  on P-PROC-06; PR #119 merged main first, spent 40 minutes, and main moved three times before its push).
- An acceptance predicate over real data is written AFTER the population it ranges over has been measured: the
  filer quotes the measurement (window, way count, the rows the predicate turns on) in the Brief; a predicate over
  a population nobody has looked at is filed as a measurement task, not an acceptance (T-0168's 8/10 could not
  fail inside one massif; T-0204's bbox edge ran along the Mulholland crest and cost a container run).
- Quote each container stage's count lines into the Log as the stage lands, not at the final commit: a session
  restart keeps the worktree and loses stdout (T-0204 re-ran every stage; T-0178 re-geocoded ten literals).
- A new numeric module (under `services/etl/etl/` or `Sources/`) ships its mutation population under `ops/mutate/`
  with a literal floor; an "equivalent mutant" ruling is an EQUIVALENT entry with a witness, never prose in a
  task file (PR #94 bought four review rounds one mutant class at a time).
- Testers find and do not fix. Fixers open PRs. The reviewer of a task is never its owner (`ops/queue-check`).
- Harness/ops PRs get two review rounds; after that the remaining finding is filed as its own task and the PR
  merges with the gap recorded in the Log - UNLESS the finding is a `P-SAFE-*` pin failing OPEN, which buys a
  round every time (a check that has never been seen red is untested; PR #101's B4/B5 is the precedent).
- Snapshot references are re-recorded only by a human-initiated commit reviewed by a different agent.

## Product invariants you must not "optimize away"
- Motorway/trunk ways carry `scenic_score = 0`; they are penalized, **not** hard-excluded (freeway shoulders,
  scenic middle). Hard gates are safety only: unpaved (positive evidence), private/no access, track.
- The extra-time budget is a **ceiling**: returned ETA ≤ fastest + budget. Always.
- Attribution (`© OpenStreetMap contributors · Protomaps`) is visible on every map surface at every sheet detent.
- The safety disclaimer gates the first plan and stays visible on the route screen.
- ETAs show the *estimate · no traffic data* badge until a corridor has ≥ 5 learned samples.
- The server never receives more than one coordinate per user action, never more than 2 decimal places.
