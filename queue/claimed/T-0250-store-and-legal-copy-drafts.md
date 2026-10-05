---
id: T-0250
title: store and legal copy drafts - privacy policy, support page, terms of use, App Store description (with the 3.1.2 subscription text), App Review notes - committed as reviewable Markdown under docs/store/, true to what the app does today
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T07:15:22Z
lease_expires_at: 2026-10-05T13:15:22Z
worktree: .worktrees/T-0250
branch: task/T-0250
exclusive: []
touches: [docs/store/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "docs/store/{privacy,support,terms,app-store-description,review-notes}.md exist; every factual claim about data handling is traceable to the code or the plan's invariants and cited inline by path (the server never receives more than one coordinate per user action, never more than 2 decimal places; learned speeds never leave the device; no account required; telemetry is H3-5 cells and durations only; OpenStreetMap ODbL attribution) - a claim the code does not yet implement is marked PLANNED, never stated as fact"
  - "the App Store description uses the owner's positioning and tagline verbatim ('calm adventure', 'Take the long way. Unwind.'), no thrill words, US-only, and the Apple 3.1.2 auto-renewing subscription disclosure for the plan's $29.99/yr with 7-day trial; review notes explain the safety disclaimer, the location-denied path and how to reach the paid features - each marked DRAFT FOR THE OWNER (a lawyer reviews privacy/terms; plan M0)"
---
## Brief

Milestone survey 2026-10-04: M0's privacy/support/terms pages and M6/M8's listing copy are MISSING and need no device or
account to draft. The owner hosts them on their domain later.

## Log
- 2026-10-05T07:12:33Z filed by agent/claude-opus-5 (orchestrator) from the milestone survey.
- 2026-10-05T07:15:22Z claimed by agent/claude-opus-5; lease until 2026-10-05T13:15:22Z
- 2026-10-05T07:29:21Z agent/claude-opus-5: drafts written - docs/store/{privacy,support,terms,app-store-description,
  review-notes}.md, each headed `**DRAFT FOR THE OWNER.**`, each claim cited inline by path, unbuilt features marked
  PLANNED. Text only: no swift test / prove-red / mutation run (contended box; the task touches only docs/store/).
  Rulings (plan vs code vs Brief), made before writing:
  - R1 Paid tier "unlimited" (plan "What we're building") vs `DAILY_PLAN_QUOTA.paid = 200`
    (services/api/src/quota.ts): copy says "more plans each day"; the owner rules. Recorded in the description's notes.
  - R2 Plan "SF Bay Area first" vs the build's drives (two LA, one SF Peninsula) and the owner's LA memory: copy names
    both regions, as the build does.
  - R3 Plan Decisions "Scenic data" names USFS TCC + NLCD; LICENSE-DATA says ESA WorldCover replaced them. Drafts cite
    LICENSE-DATA, not the plan, for data sources.
  - R4 Tiers `anon`/`free` in quota.ts have no code saying who is which; review notes say so rather than guess.
  - R5 "No account required" holds today (no sign-in screen) and in the plan (App Attest anon-first); Sign in with
    Apple is written as optional + PLANNED.
  Claim -> source:
  - server gets <=1 coordinate per action, <=2 dp (PLANNED: no /plan route yet) -> CLAUDE.md Product invariants;
    services/api/src/index.ts ROUTES = /__health /__version /__ro (so today: nothing from the app)
  - learned speeds never leave the device (PLANNED) -> plan Decisions "ETA honesty" (on-device), M7
  - saved drives on-device only (PLANNED) -> plan Runtime lifecycles "Saved drives"
  - no account required -> FeatureScenicHome/ has no sign-in; plan Decisions "Auth" (anon-first)
  - telemetry = feature ids + H3-5 cell + durations only (PLANNED; Sources/Telemetry absent) -> plan Runtime
    lifecycles "Telemetry"
  - OSM ODbL attribution, Protomaps credit -> LICENSE-DATA; MapStyle.swift protomapsAttribution; CreditLine.swift;
    CLAUDE.md Product invariants (every detent); plan Decisions "ODbL posture" (published on request)
  - app requests no location today -> apps/ios/ScenicDrive/Info.plist (no NSLocation* key)
  - Apple Maps handoff has no start point -> Sources/Handoff/HandoffDrive.swift `AppleMapsDirections(source: nil`
  - disclaimer copy, blocking sheet, persistent line, device-only flag -> SafetyDisclaimer.swift Copy.*,
    interactiveDismissDisabled(); ScenicHomeScreen.swift Copy.conditions, @AppStorage
    "safety.disclaimer.acknowledged.v1"; GatedHandoffButton.swift (gate, label "Open in Apple Maps")
  - demo basemap from demotiles.maplibre.org when la.pmtiles absent -> MapAdapter/MapStyle.swift
  - only third-party SDK is MapLibre (no ads/tracking) -> apps/ios/Packages/ScenicApp/Package.swift
  - quotas 3/10/200, kill switch (PLANNED: not wired) -> services/api/src/quota.ts DAILY_PLAN_QUOTA, killSwitchTripped
  - $29.99/yr, 7-day trial; Free/Paid split -> plan "What we're building"
  - StoreKit 2, SubscriptionStoreView + Terms/Privacy links, Restore, /asn, iCloud keychain token (PLANNED) -> plan
    Decisions "Entitlement"; SIWA + /auth/revoke (PLANNED) -> plan Decisions "Auth"
  - Location-denied typed-address path (PLANNED) -> plan "What we're building" (5.1.1(iv))
  - US-only -> plan Decisions "Launch scope"; regions -> services/etl/regions/{la,sfbay}
  - no closure-report button -> plan "Explicitly not building"; no live traffic -> same
  - lawyer review, LLC + E&O -> plan M0, Risks "Personal liability", Open question 3
  - tagline/positioning verbatim -> plan Context "Positioning"; description has 'Take the long way. Unwind.' and
    'calm adventure', no thrill words (grep over the five files: none of thrill/adrenaline/epic/extreme/conquer)
  - description body ~2.7k chars (limit 4000); subtitle 26 (limit 30); keywords 91 (limit 100)
- 2026-10-05T07:42:39Z agent/claude-opus-5: PR #140 opened (base main). Acceptance re-run on d581c49 (contains
  origin/main after `git fetch origin`; main had not moved):
  - (1) `ls docs/store` -> app-store-description.md privacy.md review-notes.md support.md terms.md (5/5). PLANNED
    markers per file: description 9, privacy 10, review-notes 5, support 6, terms 4. Each listed data claim is cited
    inline (claim -> source table above).
  - (2) description: 'Take the long way. Unwind.' x2, 'calm adventure' x2, '3.1.2' x1, '$29.99 per year' x1,
    '7-day' x2; storefront "United States only"; thrill/adrenaline/epic/extreme/conquer: 0 hits in all five files.
    review-notes covers the safety disclaimer, location (5 lines), paid features (PLANNED). `**DRAFT FOR THE OWNER.**`
    heads 5/5 files.
  - `bash ops/queue-check` -> QUEUE OK (243 tasks), exit 0.
- 2026-10-05T08:05:46Z agent/claude-opus-5: round 2 on PR #140, review rv1-t0250. Ruling first: the reviewer is
  right and the drafts were wrong. The credit shown is per drive and per basemap: DriveBasemap.resolve sends
  .skyline to MapStyle.maplibreDemoTiles (credit MapStyle.demoAttribution, "© MapLibre · Natural Earth") on every
  device; .saddlePeak and .santaMonicaMountains ask BasemapResolver.losAngeles (Protomaps credit with la.pmtiles,
  demo tiles without); HandoffDrive.routeGeometryResource is nil for .skyline and .santaMonicaMountains, so only
  Saddle Peak adds an OSM route credit; the footer is CreditLine.composed(basemap:routeData:) in
  ScenicHomeScreen.swift. The CLAUDE.md invariant text is the target for the shipping map, not todays build.
  Fixes:
  - B1 review-notes Map credit: states todays per-drive credit (basemap credit + OSM when an OSM route line is
    drawn), names the demo-tiles cases, cites CreditLine.composed / DriveBasemap.resolve / routeGeometryResource /
    demoAttribution; the OSM+Protomaps-on-every-screen state is now PLANNED.
  - B2 privacy Map tiles: demotiles is loaded for the SF Peninsula (Skyline) drive on every phone AND for the LA
    drives without the LA file; cites DriveBasemap.resolve. Map data section names the demo credit.
  - B3 support map-credit answer: truthful per-screen credit, demo-tiles case named, every-drive OSM map PLANNED.
    terms 7 and the description credit line carry the same correction (description credit marked PLANNED).
  - Recordables: (1) handoff "every turn kept" -> "the scenic stretch pinned by waypoints"; (2) "five drives
    worth" -> "at least five learned samples on that stretch" (support, terms); (3) "per request" -> "per action";
    (4) review-notes quota line reworded: table tiers anon 3 / free 10 / Pro 200, no code decides anon vs free;
    (5) Copy.conditions cited at SafetyDisclaimer.swift:106 (review-notes had it in ScenicHomeScreen.swift;
    description, terms); (6) terms 7 publish-on-request is now "PLANNED - the plans ODbL posture" with a LAWYER
    NOTE on whether on-request meets the ODbL offer terms.
  Re-measured: wc -l description 105, privacy 87, review-notes 60, support 61, terms 76. PLANNED markers:
  description 10, privacy 10, review-notes 6, support 7, terms 5. DRAFT head 5/5. thrill/adrenaline/epic/extreme/
  conquer 0 hits; "five drives", "every turn", "per request", "we publish it on" 0 hits in all five files.
