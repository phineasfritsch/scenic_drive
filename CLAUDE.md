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
- New scripts under `ops/` or `.githooks/` must be committed executable: `git update-index --chmod=+x <path>`.
  `core.filemode` is false on the Windows checkout, so git will not notice on its own and CI (`bash ops/x`) stays
  green while direct invocation breaks. Pin P-OPS-01 enforces it; data files there stay 100644.
- Every `xcodebuild` passes `-derivedDataPath` under the worktree. Every `swift build/test` on a shared box
  uses its own `--scratch-path`.

## The checkout is on NTFS, and that is a rule, not an accident
The plan's Dev box row says *"Repo in WSL2 ext4 home, never `/mnt/c`  |  CRLF and NTFS break every `ops/*`
script"*. The repo is at `C:/Users/phineasf/Documents/GitHub/scenic_drive` — NTFS, reached from WSL as
`/mnt/c/...`. **Until the owner runs the migration, NTFS is the operative reality and these rules bind.**
Moving the checkout invalidates every `worktree:` path in every claimed task file and needs a ~2.5 GB re-fetch,
so it is an owner-run migration, not an agent task (T-0060). Do not file this again; add evidence to T-0060.

- **Never `git rev-parse --show-toplevel` in anything under `ops/` or `.githooks/`.** A Windows worktree's
  `.git` file says `gitdir: C:/...`, which WSL's git cannot follow, so it fails — and without `set -e` it fails
  *silently* and the script continues in whatever directory it started in (T-0025). Resolve the root from
  `${BASH_SOURCE[0]}` and assert a marker file. T-0055 fixed the wrappers; T-0077 fixes how they locate their
  module, which is the same bug one layer down.
- **A python heredoc's stdout carries CRLF.** Strip `
` before comparing or `rev-parse`-ing anything that came
  out of one. `ops/merge-rehearse` reported *"0 conflicts, 0 gate failures"* having merged one branch of
  thirty-one, because every branch name arrived as `task/T-0014
` and the loop skipped it silently.
- **Write scripts to a file before running them.** Inline shell quoting here eats backslash escapes: three
  separate attempts to patch a script through a heredoc left literal control bytes in it.
- **MSYS rewrites POSIX-looking literals in argv.** `/bin/true` becomes a Windows path with a space in it, so
  the command fails for the wrong reason and reads as *"the guard caught it"*. Use `MSYS_NO_PATHCONV=1` when a
  payload contains a leading-slash token.
- **`python3` and `python` may be different installations.** Here `python3` is 3.14.5 with no pytest and
  `python` is 3.10.11 with it, so `ops/test` runs an interpreter that cannot run the suite and blames the
  suite (T-0076). Pass `PYTHON=$(command -v python)` until that lands.
- **Never edit a script while it is executing.** Bash reads scripts incrementally from a byte offset, so the
  running process breaks with what looks like a syntax error in a file that is fine.
- **Never `git reset --hard` in a worktree with uncommitted work.** Use `--soft` plus
  `git checkout HEAD -- <path>`. A `--hard` here discarded an hour of edits across four files.

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
