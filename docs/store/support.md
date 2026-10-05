# Scenic Drive - Support

**DRAFT FOR THE OWNER.** Hosted later on the owner's domain (plan M0). Contact address: [owner to set]. Lines
marked **PLANNED** describe something not built yet. Paths in brackets are sources and come out of the published
page.

Scenic Drive: Take the long way. Unwind.

## Getting in touch

Email [support address - owner to set]. Tell us which drive you were on and what you saw. Please do not send
your home address or your exact location; we do not need either.

## Common questions

**Why do I have to accept a notice before my first drive?**
The app suggests roads; it does not check them. It has no closure feed, no surface evidence and no weather yet.
The notice says so, and you accept it once on your phone. [`SafetyDisclaimer.swift`, `Copy.body`;
`ScenicHomeScreen.swift`, key `safety.disclaimer.acknowledged.v1`]

**Does the app need my location?**
Not today: the app does not ask for it. When you tap "Open in Apple Maps", Apple Maps starts the drive from
where you are. [`apps/ios/ScenicDrive/Info.plist`; `Sources/Handoff/HandoffDrive.swift`, `source: nil`]
**PLANNED:** if you turn location off, you can still plan by typing an address. [plan "What we're building":
every feature works with Location denied (typed address)]

**Why does the arrival time say "estimate · no traffic data"?** - PLANNED
The app does not use live traffic. It learns how a road usually flows from your own drives, on your phone, and
drops the label once it has at least five learned samples on that stretch. [`CLAUDE.md`, Product invariants; plan Decisions, "ETA
honesty"]

**The map credit at the bottom - can I hide it?**
No. The credit line names the sources the map on screen is drawn from - the basemap's credit, plus
OpenStreetMap when an OpenStreetMap route line is drawn - and it stays visible on every map screen. In this
preview the SF Peninsula drive uses MapLibre's demonstration map, credited "© MapLibre · Natural Earth".
[`ScenicHomeScreen.swift`, `CreditLine.composed(basemap:routeData:)`; `DriveBasemap.swift`; `CLAUDE.md`,
Product invariants: attribution visible at every sheet detent; `LICENSE-DATA`]
**PLANNED:** every drive is drawn on our own OpenStreetMap-based map. [plan Decisions, "Tiles"]

**A road was closed, unpaved or gated.**
Please email us with the road name and date. There is no in-app report button yet: we would only add one with
someone watching it. [plan "Explicitly not building": closure-report button needs a monitored queue + 48-h SLA]

**How do I cancel or manage my subscription?** - PLANNED
Open Settings on your iPhone, tap your name, then Subscriptions, then Scenic Drive. Cancel at least 24 hours
before the period ends to avoid the next charge. Refunds are handled by Apple at reportaproblem.apple.com.

**I got a new phone. How do I get my subscription back?** - PLANNED
Tap Restore Purchases in the app's settings. [plan Decisions, "Entitlement": Restore row, `AppStore.sync()`]

**How do I delete my account?** - PLANNED
You only have an account if you chose Sign in with Apple. Delete it from the app's settings; this also revokes
the sign-in with Apple. [plan Decisions, "Auth": deletion calls `/auth/revoke`]

**Where does Scenic Drive work?**
In the United States, starting with Los Angeles and the San Francisco Bay Area.
[plan Decisions, "Launch scope"; `services/etl/regions/la`, `services/etl/regions/sfbay`]

## Privacy and terms

[Privacy Policy - link to be set] · [Terms of Use - link to be set]
