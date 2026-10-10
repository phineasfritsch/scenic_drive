#if DEBUG
import Foundation
import ScenicKit

/// The fixed sample data behind `PlanRehearsal` (T-0336 R3), compiled only in DEBUG: a release build carries none.
///
/// Every place is a row of the bundled corpus (apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite, `places`) by its
/// own id, name and coordinate; the preview's line follows Routes/saddle-peak.geojson's points, then the coast to Zuma.
/// Each state is reached through its machine's public API - search, choose, the gate's `startPlanning()`, `finish` -
/// so a rehearsal never holds a state the machine itself could not reach. Nothing here calls a planner.
enum PlanRehearsalFixtures {
    static let topanga = PlanPlace(id: 710_486_223_536_647_933, name: "Topanga",
                                   coordinate: Coordinate(latitude: 34.0897, longitude: -118.6029649))
    static let zuma = PlanPlace(id: 161_142_772_170_980_305, name: "Zuma Beach",
                                coordinate: Coordinate(latitude: 34.0188704, longitude: -118.8273532))
    static let griffith = PlanPlace(id: 3_980_501_968_317_559_019, name: "Griffith Observatory",
                                    coordinate: Coordinate(latitude: 34.1182471, longitude: -118.3003659))
    static let leoCarrillo = PlanPlace(id: 8_813_832_245_607_821_419, name: "Leo Carrillo State Beach",
                                       coordinate: Coordinate(latitude: 34.0441745, longitude: -118.939262))

    /// Topanga over Saddle Peak to Zuma Beach: 55 min against the fastest 35, inside the default 30 min budget; an
    /// estimate (the badge, P-SAFE-07) with a crossed closure and one access run on the hazard strip (T-0341).
    static let preview = PlanPreview(
        route: [
            Coordinate(latitude: 34.0897, longitude: -118.6030),
            Coordinate(latitude: 34.09435, longitude: -118.60129),
            Coordinate(latitude: 34.06864, longitude: -118.6128),
            Coordinate(latitude: 34.07396, longitude: -118.65191),
            Coordinate(latitude: 34.07291, longitude: -118.68708),
            Coordinate(latitude: 34.03652, longitude: -118.68706),
            Coordinate(latitude: 34.0300, longitude: -118.7500),
            Coordinate(latitude: 34.0200, longitude: -118.8000),
            Coordinate(latitude: 34.0189, longitude: -118.8274),
        ],
        etaSeconds: 3_300, fastestEtaSeconds: 2_100, etaIsEstimate: true,
        hazards: [PlanHazardRun(kind: "road_access", value: "destination", fromIndex: 2, toIndex: 3)],
        closures: ClosuresHazard(state: .fresh, crosses: true))

    /// The "nothing pretty" answer that made both offers (T-0334): nothing within the 25 min asked for; try 65; or all
    /// back roads, about 60 min, which needs 32 extra minutes.
    static let offer = PlanOffer(budgetMinutes: 25, moreTimeMinutes: 65, backRoadsEtaSeconds: 3_600,
                                 backRoadsBudgetMinutes: 32)

    /// A one-hour loop from Topanga: Saddle Peak, Malibu Canyon, Mulholland Highway, Old Topanga, home.
    static let loopPreview = LoopPreview(
        path: [
            Coordinate(latitude: 34.0897, longitude: -118.6030),
            Coordinate(latitude: 34.06864, longitude: -118.6128),
            Coordinate(latitude: 34.07396, longitude: -118.65191),
            Coordinate(latitude: 34.07291, longitude: -118.68708),
            Coordinate(latitude: 34.1000, longitude: -118.6900),
            Coordinate(latitude: 34.1160, longitude: -118.6500),
            Coordinate(latitude: 34.1100, longitude: -118.6200),
            Coordinate(latitude: 34.0897, longitude: -118.6030),
        ],
        waypoints: [Coordinate(latitude: 34.07, longitude: -118.65), Coordinate(latitude: 34.12, longitude: -118.65)],
        durationSeconds: 3_480, distanceMeters: 52_000, retraceFraction: 0.04, etaIsEstimate: true,
        closures: ClosuresHazard(state: .unavailable),
        hazards: [PlanHazardRun(kind: "road_access", value: "destination", fromIndex: 4, toIndex: 5)])

    /// Two days from Griffith Observatory to Leo Carrillo State Beach, 36% over the fastest (the 40% ceiling holds),
    /// a gravel stretch on day 2 (T-0340).
    static let itinerary = TripItinerary(
        isFull: true, etaSeconds: 9_000, fastestEtaSeconds: 6_600, etaIsEstimate: true,
        days: [
            TripItineraryDay(day: 1, driveSeconds: 5_400, distanceMeters: 70_000, overnight: true, path: nil),
            TripItineraryDay(day: 2, driveSeconds: 3_600, distanceMeters: 50_000, overnight: false, path: nil,
                             hazards: [PlanHazardRun(kind: "surface", value: "gravel", fromIndex: 3, toIndex: 6)]),
        ], closures: ClosuresHazard(state: .stale))

    /// Three kept drives, one of them needing a re-plan.
    static let savedRows = [
        SavedRow(id: 1, name: "Zuma Beach", createdAt: 1_790_000_000, needsReplan: false,
                 start: topanga.coordinate, end: zuma.coordinate, budgetMinutes: 30),
        SavedRow(id: 2, name: "Top of Topanga Overlook", createdAt: 1_790_100_000, needsReplan: false,
                 start: Coordinate(latitude: 34.09, longitude: -118.60),
                 end: Coordinate(latitude: 34.1397762, longitude: -118.6009737), budgetMinutes: 45),
        SavedRow(id: 3, name: "Mulholland Scenic Overlook", createdAt: 1_790_200_000, needsReplan: true,
                 start: Coordinate(latitude: 34.09, longitude: -118.60),
                 end: Coordinate(latitude: 34.1303863, longitude: -118.502505), budgetMinutes: 60),
    ]

    /// The rehearsal for a `-screen` value, or nil for any other value or a gate that refused.
    static func rehearsal(named name: String) -> PlanRehearsal? {
        switch name {
        case "preview": return plan(.preview(preview))
        case "nothingPretty": return plan(.failure(.nothingPretty))
        case "offered": return plan(.offered(offer), budgetMinutes: offer.budgetMinutes)
        case "loop": return loop()
        case "trip": return trip()
        case "saved": return PlanRehearsal(tab: .saved, sheet: PlanSheet(disclaimerAccepted: false),
                                           loop: LoopSheet(disclaimerAccepted: false),
                                           trip: TripSheet(disclaimerAccepted: false), savedRows: savedRows)
        case "paused": return degraded(.planningPaused)
        case "update": return degraded(.updateRequired)
        default: return nil
        }
    }

    /// T-0357 R8: the form with a start and a destination chosen and /config's degrade on it - the notice in place of Plan.
    private static func degraded(_ degrade: ConfigDegrade) -> PlanRehearsal {
        var sheet = PlanSheet(disclaimerAccepted: true)
        sheet.search("", for: .start)
        sheet.choose(topanga)
        sheet.search("", for: .destination)
        sheet.choose(zuma)
        sheet.setDegrade(degrade)
        return PlanRehearsal(tab: .plan, sheet: sheet, loop: LoopSheet(disclaimerAccepted: false),
                             trip: TripSheet(disclaimerAccepted: false), savedRows: [])
    }

    private static func plan(_ outcome: PlanOutcome, budgetMinutes: Int = 30) -> PlanRehearsal? {
        var sheet = PlanSheet(disclaimerAccepted: true, budgetMinutes: budgetMinutes)
        sheet.search("", for: .start)
        sheet.choose(topanga)
        sheet.search("", for: .destination)
        sheet.choose(zuma)
        guard let ticket = sheet.startPlanning() else { return nil }
        sheet.finish(ticket, with: outcome)
        return PlanRehearsal(tab: .plan, sheet: sheet, loop: LoopSheet(disclaimerAccepted: false),
                             trip: TripSheet(disclaimerAccepted: false), savedRows: [])
    }

    private static func loop() -> PlanRehearsal? {
        var loop = LoopSheet(disclaimerAccepted: true, minutes: 60)
        loop.search("")
        loop.choose(topanga)
        guard let ticket = loop.startPlanning() else { return nil }
        loop.finish(ticket, with: .preview(loopPreview))
        return PlanRehearsal(tab: .loop, sheet: PlanSheet(disclaimerAccepted: false), loop: loop,
                             trip: TripSheet(disclaimerAccepted: false), savedRows: [])
    }

    private static func trip() -> PlanRehearsal? {
        var trip = TripSheet(disclaimerAccepted: true, days: 2, extraBudgetPercent: 40)
        trip.search("", for: .start)
        trip.choose(griffith)
        trip.search("", for: .destination)
        trip.choose(leoCarrillo)
        guard let ticket = trip.startPlanning() else { return nil }
        trip.finish(ticket, with: .itinerary(itinerary))
        return PlanRehearsal(tab: .trip, sheet: PlanSheet(disclaimerAccepted: false),
                             loop: LoopSheet(disclaimerAccepted: false), trip: trip, savedRows: [])
    }
}
#endif
