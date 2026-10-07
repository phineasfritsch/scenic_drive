---
id: T-0300
title: PlaceStore decides and stages a corpus OTA update - manifest gate (schema_version, min_app_build), sha256 + byte-count verify into a staging file, atomic rename, activation only at the next cold launch and never while a drive holds the store
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/PlaceStore/, Tests/PlaceStoreTests/, Tests/Fixtures/, ops/mutate/, ops/lib/check-safety-disclaimer-linked, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-PROD-05]
reviewer: null
depends_on: [T-0175, T-0270]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULE FIRST in a dated Log entry: the manifest shape the plan names ({version, schema_version, min_app_build, sha256, bytes}) as a Codable type with every field required and typed; where staged and active corpora live (paths under one directory the caller supplies - no FileManager singletons in the decision logic); and the seam: the download itself is a protocol the app implements (URLSession), PlaceStore owns the decision, the verify and the rename (Linux-testable with a fake fetcher)"
  - "Decision table through the shipped entry point, rows as functions of the manifest variant, each compared by full equality of the returned decision: schema_version == PlaceStore.schemaVersion accepted, +-1 refused; min_app_build == build accepted, build+1 refused; version equal to the active one is 'up to date' (no download); a missing / extra / mistyped field refuses with a typed error (never a crash); meta-test that no row ignores its variant"
  - "Verify: the staged file is accepted only when its byte count AND sha256 both equal the manifest's; a one-byte change, a truncated file, an extra trailing byte and a correct hash with the wrong byte count each leave the active corpus byte-identical (sha256 before == after) and delete the staged file; a passing stage is renamed atomically to the pending slot"
  - "Activation: openForLaunch(isColdLaunch:) swaps pending -> active only on a cold launch; a warm resume, or a store opened while a DriveSession token is held, keeps the old corpus; the swapped-in file must also pass PlaceStore's existing schema/build_complete checks or the swap is undone and the old corpus kept - full-equality table"
  - "Every new or changed Sources/PlaceStore file re-approves its digest in ops/lib/check-safety-disclaimer-linked in the same diff (memory sources-digest-pin); a mutation population under ops/mutate/ with a literal floor, three entries MISSED before and CAUGHT by name after; P-PROD-05 binds the decision-table test by name (seen red by name)"
---
## Brief

Plan, Runtime lifecycles, Corpus / tiles OTA: "R2 manifest {version, schema_version, min_app_build, sha256, bytes};
download only if schema_version == PlaceStore.schemaVersion && min_app_build <= build; to tmp/, verify sha256, rename(2),
activate at next cold launch (never while a Drive holds a connection)". Milestone M4 lists first-run download + OTA
lifecycle. This task is the Linux-testable decision/verify/activate core; the app's download sheet and the R2 publish
are later tasks. Swift is native on this box (memory swift-native-on-windows-box); GRDB suites run in CI's Linux core.

## Log
- 2026-10-07T13:53:57Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M4 first-run download / OTA).
