# Scenic Drive - Terms of Use

**DRAFT FOR THE OWNER.** A lawyer reviews this before it is published (plan M0, "lawyer hour booked"; plan
Risks, "Personal liability": LLC + E&O before the first paid subscription). Effective date: [owner to set].
Lines marked **PLANNED** describe something not built yet. Paths in brackets are sources and come out of the
published page.

## 1. What Scenic Drive is

Scenic Drive suggests longer, quieter drives on public roads. It is a planning aid, not a guarantee about any
road. [plan Context; `SafetyDisclaimer.swift`]

## 2. The roads are not checked by us

The app suggests roads. It does not check them. Roads close, surfaces wash out, gates lock and the weather turns.
Before and during every drive, follow posted signs, the law and your own judgement over anything the app shows.
Conditions change. Verify locally. [`apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/SafetyDisclaimer.swift`,
`Copy.body` and `Copy.conditions`]

You must accept the "Before you drive" notice before the app hands you a route, and the line "Conditions change.
Verify locally." stays on the route screen. [`CLAUDE.md`, Product invariants: "The safety disclaimer gates the
first plan and stays visible on the route screen"]

## 3. Drive safely

Do not handle your phone while driving. Set up a drive before you leave, or let a passenger do it. You are
responsible for how you drive.

## 4. Arrival times are estimates

**PLANNED:** arrival times are labelled *estimate · no traffic data* until the app has learned enough about a
road (five drives' worth of samples). The app does not use live traffic. [`CLAUDE.md`, Product invariants;
plan "Explicitly not building": live traffic is V1.1]

## 5. Subscription - PLANNED

Scenic Drive is free to plan. An optional yearly subscription ($29.99 per year, USD, with a 7-day free trial for
new subscribers) adds in-app turn-by-turn navigation and higher daily limits. [plan "What we're building": Paid
$29.99/yr, 7-day trial]

- Payment is charged to your Apple Account when you confirm the purchase, or when the free trial ends.
- The subscription renews automatically unless you cancel at least 24 hours before the end of the current period.
- Your account is charged for renewal within 24 hours before the end of the current period.
- You can manage or cancel the subscription in your App Store account settings.
- Any unused part of a free trial is forfeited when you buy a subscription.
- Refunds are handled by Apple.

Apple's standard Licensed Application End User License Agreement also applies [owner/lawyer: keep Apple's
standard EULA, or replace it with these terms in App Store Connect].

## 6. Fair use - PLANNED

To keep the service running, the number of drives one device can plan each day is limited, and planning may be
paused for everyone if the service is under strain. [`services/api/src/quota.ts`: `DAILY_PLAN_QUOTA`,
`killSwitchTripped` - written, not yet wired to any route]

## 7. Map data

Maps and road data © OpenStreetMap contributors, available under the Open Database License (ODbL). Basemap by
Protomaps. The scenic road data derived from OpenStreetMap is itself offered under the ODbL; we publish it on
request. [`LICENSE-DATA`; plan Decisions, "ODbL posture"; `MapStyle.swift`, `protomapsAttribution`]

## 8. Where the app is offered

The United States only. [plan Decisions, "Launch scope"]

## 9. For the lawyer

Disclaimer of warranties, limitation of liability, governing law and venue, changes to these terms, contact
address, and the legal entity name (plan open question 3: LLC before the first paid subscription).
