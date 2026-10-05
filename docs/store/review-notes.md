# Scenic Drive - App Review notes

**DRAFT FOR THE OWNER.** Pasted into App Store Connect, App Review Information, at submission (plan M8: review
notes + 30-second recording). Lines marked **PLANNED** describe something not built yet; they are finished or
removed before submission. Paths in brackets are sources, not part of the notes.

---

Scenic Drive suggests longer, prettier drives - back roads instead of the fastest road. It is offered in the
United States only, and its drives are in California. [plan Decisions, "Launch scope"]

**Sign-in.** None is needed. Every screen works without an account, so no demo account is provided.
[the app has no sign-in screen - `apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/`]

**The safety notice (please expect it).** The first time you tap "Open in Apple Maps", a "Before you drive"
sheet appears. It cannot be swiped away; the only way on is "I understand". It says plainly that the app
suggests roads but does not check them. After that, "Conditions change. Verify locally." stays on the route
screen. We designed it this way on purpose: the app may route over small mountain roads, and we want drivers to
know what it does not know. Accepting it is remembered on the device only.
[`SafetyDisclaimer.swift`: `interactiveDismissDisabled()`, `Copy.title`, `Copy.accept`;
`ScenicHomeScreen.swift`, `Copy.conditions` and key `safety.disclaimer.acknowledged.v1`; `CLAUDE.md`, Product
invariants]

**Location (Guideline 5.1.1).** This build does not ask for location permission at all. To try a drive: pick
one of the drive chips at the top of the map (for example "Saddle Peak"), read the route in the sheet, and tap
"Open in Apple Maps". Apple Maps starts from the device's own position.
[`apps/ios/ScenicDrive/Info.plist`: no location usage key; `Sources/Handoff/HandoffDrive.swift`, `source: nil`;
`FeatureScenicHome/DriveCopy.swift`]
**PLANNED:** when planning your own drives arrives, location is asked for only when you first plan one, and if
you decline, every feature still works by typing an address. [plan "What we're building": each feature works
with Location denied (typed address) - App Review 5.1.1(iv)]

**Paid features - PLANNED.** Free users plan, preview and open drives in Apple Maps. "Scenic Drive Pro"
($29.99/year, 7-day free trial) adds in-app turn-by-turn navigation and higher daily limits. To reach the
purchase screen: [owner fills in the exact path once the paywall is built - e.g. tap "Navigate" on a route
preview]. The purchase screen is Apple's `SubscriptionStoreView`, with Terms of Use and Privacy Policy links and
a Restore Purchases row. Please use a Sandbox Apple Account to test it. [plan Decisions, "Entitlement"; plan
"What we're building"]

**Turn-by-turn navigation - PLANNED.** Navigation uses location in the background while a drive is under way;
a 30-second screen recording of a drive is attached. [plan M7, M8; Guideline 2.5.4]

**Daily limits - PLANNED.** Each device can plan a few drives a day for free (the server allows 3 without an
anonymous device, 10 on the free tier, 200 for Pro - which user lands on which of the first two tiers is not
decided in code yet). If you hit a limit, the app says when it resets.
[`services/api/src/quota.ts`, `DAILY_PLAN_QUOTA`; plan Runtime lifecycles, "Degraded states": `quotaExhausted`]

**Map credit.** "© OpenStreetMap contributors · Protomaps" is shown on every map screen at every sheet height,
as the data licenses require. [`CLAUDE.md`, Product invariants; `MapStyle.swift`, `protomapsAttribution`;
`LICENSE-DATA`]

**Contact for review:** [owner name, phone, email - owner to set]
