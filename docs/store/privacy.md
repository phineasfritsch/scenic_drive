# Scenic Drive - Privacy Policy

**DRAFT FOR THE OWNER.** Not reviewed by a lawyer (plan M0 books that hour). Not published. Effective date:
[owner to set]. Hosted later on the owner's domain.

How to read this draft: a line marked **PLANNED** describes something the plan designs but the code does not do
yet. Before this page is published, every PLANNED line is either built and re-checked against the code, or
removed. Paths in brackets are the source for each claim; they come out of the published page.

## The short version

- You can use Scenic Drive without an account. [today: the app has no sign-in screen -
  `apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/`; plan Decisions, "Auth": anonymous first]
- The app does not ask for your location today. [`apps/ios/ScenicDrive/Info.plist` has no location usage key]
- We do not sell your data, show ads, or track you across other apps. [the only third-party code in the app is
  MapLibre - `apps/ios/Packages/ScenicApp/Package.swift`]

## What stays on your phone

- **Your safety acknowledgement.** When you accept the "Before you drive" notice, the app remembers that on this
  phone only. [`ScenicHomeScreen.swift`, key `safety.disclaimer.acknowledged.v1`, stored in UserDefaults]
- **PLANNED - learned road speeds.** To make arrival times more honest, the app will learn how fast traffic moves
  on the roads you drive, by area and hour of the week. These learned speeds never leave your phone.
  [plan Decisions, "ETA honesty": learned corridor speeds on-device; milestone M7]
- **PLANNED - saved drives.** Drives you save are kept on your phone only. [plan Runtime lifecycles, "Saved
  drives": on-device (GRDB) only]

## What our server receives

**Today:** nothing. The preview build does not contact our server. Our server, run on Cloudflare, answers only
health and version checks. [`services/api/src/index.ts`, `ROUTES`: `/__health`, `/__version`, `/__ro`]

**PLANNED - when you plan a drive:** the server receives no more than one location per thing you do, and never
more precisely than two decimal places - about one kilometre. Your exact position is not sent.
[`CLAUDE.md`, Product invariants: "The server never receives more than one coordinate per user action, never
more than 2 decimal places."]

**PLANNED - daily planning limits.** To keep the service affordable, the server counts how many drives each
device plans per day. Apple's App Attest lets us tell one real device from another without knowing who you are.
[`services/api/src/quota.ts`, `DAILY_PLAN_QUOTA` and `checkQuota` - written, not yet wired to any route; plan
Decisions, "Auth"]

**PLANNED - usage statistics.** To learn whether the app works, it will send a short, fixed list of events
(for example "a drive was planned", "a drive was finished", "was it prettier than your usual way?"). Each event
carries only which feature was used, a coarse area (an H3 resolution-5 cell, roughly 250 square kilometres), and
durations. No exact location, no route, no name. They are stored in Cloudflare Workers Analytics Engine.
[plan Runtime lifecycles, "Telemetry": closed enum of 14 events, payload = feature ids, H3-5 cell, durations
only; `Sources/Telemetry` does not exist yet]

**PLANNED - Sign in with Apple (optional).** If you choose to sign in, we receive the identifier Apple gives us,
and Apple's private relay email if you share one. You can delete your account in the app; deleting it also
revokes the sign-in with Apple. [plan Decisions, "Auth": Sign in with Apple only; deletion calls `/auth/revoke`]

**PLANNED - subscriptions.** Apple handles payment; we never see your card. We receive Apple's transaction
identifiers and a random purchase ID kept in your iCloud Keychain, so your subscription follows you to a new
phone, and Apple tells our server about renewals, refunds and cancellations. [plan Decisions, "Entitlement":
StoreKit 2, `originalTransactionID` + `appAccountToken` in iCloud keychain, App Store Server Notifications V2 to
`/asn`]

## Other services the app uses

- **Apple Maps.** When you tap "Open in Apple Maps", the app opens Apple Maps with the drive's destination and
  its fixed waypoints. It does not include your starting point; Apple Maps uses its own. What Apple Maps does
  is covered by Apple's privacy policy. [`Sources/Handoff/HandoffDrive.swift`, `AppleMapsDirections(source:
  nil, ...)`; `GatedHandoffButton.swift`, label "Open in Apple Maps"]
- **Map tiles.** When the Los Angeles map file is not on your phone, the preview build loads a demonstration map
  from `demotiles.maplibre.org`; that server sees an ordinary web request, including your IP address.
  [`apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapStyle.swift`] **PLANNED:** the shipping app downloads its
  map once from our own storage and then works offline. [plan Decisions, "Tiles"; Runtime lifecycles, "First run"]

## Where this applies

Scenic Drive is offered in the United States only. [plan Decisions, "Launch scope": US-only]

## Map data

Maps and road data © OpenStreetMap contributors, available under the Open Database License. See
`LICENSE-DATA` for every data source. [`LICENSE-DATA`]

## Open for the owner and the lawyer

- How long usage statistics and quota counters are kept. [not decided anywhere in the plan or code]
- Children's privacy wording, a contact address, and how changes to this policy are announced.
- The App Store privacy "nutrition label" must match this page (plan M8).
