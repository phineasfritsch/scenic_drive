import Foundation
import ScenicAPIClient
import ScenicKit

/// The T-0313 tests' one way to drive the shipping entry point, `TripClient.trip`, against a counting fake, and the
/// two /trip answers they read: a preview (legs null, the anon view the app gets today) and a full itinerary.
enum TripWire {
    static let base = URL(string: "https://scenic-api.test")!
    static let origin = Coordinate(latitude: 34.02, longitude: -118.49)

    static let previewBody = """
    {"view":"preview","route":{"coordinates":[[-118.49,34.02],[-119.2,34.4],[-121.81,36.27]],"distance_m":480000},\
    "eta_s":30000,"fastest_eta_s":24000,"ceiling_s":33600,"budget_s":9600,"extra_budget_pct":40,"lambda":0.75,\
    "evaluations":4,"eta_is_estimate":true,"places_searched":false,"days":[\
    {"day":1,"start":{"lat":34.02,"lon":-118.49},"end":{"lat":34.4,"lon":-119.2},"drive_s":15000,"distance_m":200000,\
    "ceiling_s":16800,"stops":[],"overnight":{"kind":"not_searched"},"leg":null},\
    {"day":2,"start":{"lat":34.4,"lon":-119.2},"end":{"lat":36.27,"lon":-121.81},"drive_s":15000,\
    "distance_m":280000,"ceiling_s":33600,"stops":[],"overnight":null,"leg":null}]}
    """

    static let fullBody = """
    {"view":"full","route":{"coordinates":[[-118.49,34.02],[-121.81,36.27]],"distance_m":480000},\
    "eta_s":31000,"fastest_eta_s":24000,"ceiling_s":33600,"budget_s":9600,"extra_budget_pct":30,"lambda":1.5,\
    "evaluations":5,"eta_is_estimate":true,"places_searched":false,"closures_hazard":{"state":"fresh"},"days":[\
    {"day":1,"start":{"lat":34.02,"lon":-118.49},"end":{"lat":36.27,"lon":-121.81},"drive_s":31000,\
    "distance_m":480000,"ceiling_s":33600,"stops":["Ojai"],"overnight":null,\
    "leg":{"coordinates":[[-118.49,34.02],[-119.2,34.4],[-121.81,36.27]],"eta_s":31000,"distance_m":480000}}]}
    """

    static let preview = TripResponse(
        isFull: false,
        route: [Coordinate(latitude: 34.02, longitude: -118.49), Coordinate(latitude: 34.4, longitude: -119.2),
                Coordinate(latitude: 36.27, longitude: -121.81)],
        distanceMeters: 480_000, etaSeconds: 30_000, fastestEtaSeconds: 24_000, ceilingSeconds: 33_600,
        budgetSeconds: 9_600, extraBudgetPercent: 40, lambda: 0.75, etaIsEstimate: true,
        days: [TripResponseDay(day: 1, start: Coordinate(latitude: 34.02, longitude: -118.49),
                               end: Coordinate(latitude: 34.4, longitude: -119.2), driveSeconds: 15_000,
                               distanceMeters: 200_000, ceilingSeconds: 16_800, stops: [], overnight: true, leg: nil),
               TripResponseDay(day: 2, start: Coordinate(latitude: 34.4, longitude: -119.2),
                               end: Coordinate(latitude: 36.27, longitude: -121.81), driveSeconds: 15_000,
                               distanceMeters: 280_000, ceilingSeconds: 33_600, stops: [], overnight: false,
                               leg: nil)])

    static let fullLeg = [Coordinate(latitude: 34.02, longitude: -118.49), Coordinate(latitude: 34.4, longitude: -119.2),
                          Coordinate(latitude: 36.27, longitude: -121.81)]

    static let full = TripResponse(
        isFull: true,
        route: [Coordinate(latitude: 34.02, longitude: -118.49), Coordinate(latitude: 36.27, longitude: -121.81)],
        distanceMeters: 480_000, etaSeconds: 31_000, fastestEtaSeconds: 24_000, ceilingSeconds: 33_600,
        budgetSeconds: 9_600, extraBudgetPercent: 30, lambda: 1.5, etaIsEstimate: true,
        days: [TripResponseDay(day: 1, start: Coordinate(latitude: 34.02, longitude: -118.49),
                               end: Coordinate(latitude: 36.27, longitude: -121.81), driveSeconds: 31_000,
                               distanceMeters: 480_000, ceilingSeconds: 33_600, stops: ["Ojai"], overnight: false,
                               leg: fullLeg)])

    static func reply(_ status: Int, _ body: String) -> PlanHTTPReply {
        PlanHTTPReply(status: status, body: Data(body.utf8))
    }

    static func trip(through transport: any PlanTransport, from origin: Coordinate = origin, to place: Int64 = 42,
                     days: Int = 2, extraBudgetPercent: Int = 40, vehicle: VehicleProfile = .standard,
                     install: Bool = true, account: (any AccountTokenProvider)? = nil)
        async -> Result<TripResponse, TripError> {
        let client = TripClient(base: base, transport: transport, installID: install ? PlanWire.install : nil,
                                accountToken: account)
        do {
            return .success(try await client.trip(from: origin, to: place, days: days,
                                                  extraBudgetPercent: extraBudgetPercent, vehicle: vehicle))
        } catch {
            return .failure(error)
        }
    }
}
