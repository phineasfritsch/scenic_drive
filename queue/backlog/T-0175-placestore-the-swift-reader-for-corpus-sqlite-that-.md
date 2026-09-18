---
id: T-0175
title: PlaceStore - the Swift reader for corpus.sqlite that the plan and T-0030's touches promised and Sources/ lacks
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [package-swift]
touches: [Package.swift, Sources/PlaceStore/, Tests/PlaceStoreTests/, .github/workflows/linux-core.yml]
pins_affected: [P-PROD-05]
reviewer: null
depends_on: [T-0173]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Sources/PlaceStore is a root-package target (Linux; GRDB pinned exact; libsqlite3-dev in CI) with `PlaceStore.schemaVersion` a typed literal equal to the corpus schema_version; a test opens a corpus built by `python -m etl.corpus` from the committed fixture and reads meta, one segment by id and one R*Tree bbox query, RED by name against a corpus with a bumped schema_version"
  - "P-PROD-05's assertion widens to the Swift value; `swift test --scratch-path <own>` count line quoted; the Linux compile gate stays green (no Apple-only import in the root graph)"
---
## Brief

From the 16:13 panel (CODE lens, grounded). The plan's architecture lists `Sources/PlaceStore/` (GRDB; corpus
reader on plain SQL; user store + migrations) and P-PROD-05 pins `schema_version == PlaceStore.schemaVersion`.
On main Sources/ holds Handoff and ScenicKit only; Package.swift declares two targets; T-0030's `touches:`
promised Sources/PlaceStore/ and its diff was 100 % Python. T-0147 covers only CLAUDE.md's wording of the
target list. Adding a target edits Package.swift, a serial-only file: `exclusive: [package-swift]`.

## Log
- 2026-09-18T23:04:01Z filed by agent/claude-fable-5-1 from the 16:13 panel's grounded synthesis. Not started; depends on T-0173's schema contract.
