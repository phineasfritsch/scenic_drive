---
id: T-0220
title: P-ATTR-01 - a second map-mounting type declared inside MapAdapter/MapView.swift (the one file limb (f) excludes) and mounted at a feature surface with no footer is green: whitelist MLNMapView( over the tree, or pin the UIViewRepresentable conformances under MapAdapter
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, pins/PINS.yaml]
pins_affected: [P-ATTR-01]
reviewer: null
depends_on: [T-0197]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/lib/check-map-attribution gains the whitelist: every occurrence of 'MLNMapView(' under apps/ios is at the one definition site (MapAdapter/MapView.swift(1)) and every ': UIViewRepresentable' under apps/ios is one of the conformances typed into the check (today MapView only) - a --prove-red row that declares a second UIViewRepresentable inside MapView.swift wrapping MLNMapView and mounts it under FeatureScenicHome with no footer, refused BY NAME; the line budget: the readers go in check-map-attribution-lib"
  - "the pin text's disclosed blind spot 'a map mounted through some wrapper that is not MapView(' is narrowed to what is still unseen after this; --prove-red count re-quoted; bash ops/check-pins --source-only, check-exec-bits, queue-check bare"
---
## Brief

rv2-pr119's survivor 2b: limb (f) excludes the definition file and pins it by 'struct MapView' and 'public init(styleURL'
occurring once, which guards a second struct MapView or a moved definition - not a second UIViewRepresentable in
the same file. Disclosed in the pin, so recordable; beside T-0180 (the XCUITest half).

## Log
- 2026-09-19T16:59:37Z filed by agent/claude-fable-5-1 (orchestrator, from rv1/rv2-pr119's recordables on T-0197). Not started; two review rounds (harness PR).
