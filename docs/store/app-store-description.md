# Scenic Drive - App Store listing copy

**DRAFT FOR THE OWNER.** For App Store Connect (plan M6 listing task, M8 ship). Storefront: **United States
only** [plan Decisions, "Launch scope"].

Markers: **[PLANNED]** in the copy marks a feature the code does not do yet. A marked line is removed, or its
marker is dropped once the feature ships and has been checked against the code - it is never pasted as-is.
Paths in brackets are sources, not copy.

Voice: calm adventure, in quiet words. [plan Context, "Positioning" and "Tagline"]

---

## Name (30 max)

Scenic Drive

## Subtitle (30 max)

Take the long way. Unwind.

## Promotional text (170 max)

A little extra time and the right road turn a drive into a calm adventure. Scenic Drive finds the prettier way
there.

## Keywords (100 max)

scenic route,back roads,road trip,loop,canyon,coast,mountain road,golden hour,unwind,detour

## Description

Take the long way. Unwind.

Scenic Drive is for the days you have time to spare, or need to let the day go. Instead of the fastest road, it
gives you a quieter, prettier one: back roads over the hills, along the coast, through the canyons. A calm
adventure, then home.

DRIVES TO START WITH
Three hand-picked drives in Los Angeles and the San Francisco Bay Area: Saddle Peak from Topanga to Malibu, the
Skyline loop from San Francisco, and the Westwood loop to the coast and back. Pick one, read the route, and open
it in Apple Maps with the scenic stretch pinned by waypoints.
[`Sources/Handoff/HandoffDrive.swift`; `FeatureScenicHome/DriveCopy.swift`; `GatedHandoffButton.swift`]

[PLANNED] YOUR DRIVE HOME, THE LONG WAY
Tell it where you're going and how many extra minutes you have, from 10 to 60. It finds one route with a scenic
middle and tells you why it's pretty. Your arrival time never goes past the extra time you chose.
[plan "What we're building"; `CLAUDE.md`, Product invariants: budget is a ceiling]

[PLANNED] SURPRISE ME
Set how long you have and get one named place worth the drive, with the round-trip time and the golden-hour
light. [plan "What we're building", Surprise me]

[PLANNED] LOOPS
"Just drive 45 minutes and come back." [plan "What we're building", Loop]

[PLANNED] ROAD TRIPS
Several days from A to B, split into days with a few stops each and a town for the night.
[plan "What we're building", Road trip]

HONEST ABOUT THE ROAD
Scenic Drive suggests roads; it does not check them. Before your first drive it tells you what it doesn't know,
and "Conditions change. Verify locally." stays on screen. [`SafetyDisclaimer.swift`; `Copy.conditions` at `SafetyDisclaimer.swift:106`;
`ScenicHomeScreen.swift`]
[PLANNED] Arrival times are marked "estimate · no traffic data" until the app has learned your roads.
[`CLAUDE.md`, Product invariants]

PRIVATE BY DESIGN
No account needed. Your location is not sent to us today. [PLANNED] When planning arrives, our server sees
at most one rough location per action, never your exact position, and what the app learns about your roads
stays on your phone. [`CLAUDE.md`, Product invariants; plan Decisions, "ETA honesty"]

Maps and road data © OpenStreetMap contributors · Protomaps. [PLANNED as the credit on every map: today the
SF Peninsula drive, and any drive on a phone without the Los Angeles map file, uses MapLibre's demonstration
map, credited "© MapLibre · Natural Earth" - `DriveBasemap.swift`; `LICENSE-DATA`; `MapStyle.swift`]

[PLANNED] SCENIC DRIVE PRO
Free: plan and preview drives and open them in Apple Maps, a few each day.
Pro: in-app turn-by-turn navigation that keeps you on the scenic road, more plans each day, a Surprise Me that
won't repeat itself for 90 days, and full road-trip itineraries.
[plan "What we're building", Free / Paid columns; daily numbers in `services/api/src/quota.ts`]

[PLANNED] Subscription details (App Review Guideline 3.1.2):
- Scenic Drive Pro is an auto-renewing yearly subscription: $29.99 per year (USD). New subscribers get a 7-day
  free trial.
- Payment is charged to your Apple Account at confirmation of purchase, or when the free trial ends.
- The subscription renews automatically unless canceled at least 24 hours before the end of the current period.
- Your account is charged for renewal within 24 hours before the end of the current period, at the same price.
- Manage or cancel the subscription in your App Store account settings after purchase.
- Any unused portion of a free trial is forfeited when you purchase a subscription.
- Terms of Use: [link - owner to set]
- Privacy Policy: [link - owner to set]
[plan "What we're building": Paid ($29.99/yr, 7-day trial); plan Decisions, "Entitlement": `SubscriptionStoreView`
with Terms of Use + Privacy links]

---

## Notes for the owner

- "Scenic Drive Pro" is a placeholder product name; App Store Connect needs the real subscription group and name.
- The plan's Paid column says "unlimited"; the code caps a paid device at 200 plans a day
  (`services/api/src/quota.ts`, `DAILY_PLAN_QUOTA.paid`). The copy says "more plans each day" until the owner
  rules which one ships.
- The plan named the Bay Area first; the current build and the owner's own drives start in Los Angeles. The copy
  names both, matching the drives in the build.
