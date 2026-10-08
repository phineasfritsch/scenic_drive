import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0306 acceptance 3, first two hops of R2 in ONE table: a Worker 200 (`PlanResponse`) through the shipping
/// `ClientPlanner.preview` (the preview the sheet shows) and `SavedDraft.of` (what Save keeps), compared by full
/// equality of the whole draft. The rounding to 5 dp happens here, once; PlaceStore refuses rather than rounds.
@Suite("SavedDraftTests")
struct SavedDraftTests {
    static let link = URL(string: "https://maps.apple.com/?daddr=34.04,-118.685")!

    static func response(route: [Coordinate], waypoints: [Coordinate], lambda: Double) -> PlanResponse {
        PlanResponse(route: route, distanceMeters: 41_000, etaSeconds: 3_120, fastestEtaSeconds: 2_280,
                     ceilingSeconds: 4_080, budgetSeconds: 1_800, lambda: lambda, evaluations: 4, usedBudget: true,
                     etaIsEstimate: true, hazards: [], waypoints: waypoints, appleMapsURL: link)
    }

    static func c(_ lat: Double, _ lon: Double) -> Coordinate { Coordinate(latitude: lat, longitude: lon) }

    static let rows: [(String, PlanResponse, SavedDraft?)] = [
        ("more than 5 dp on every axis and lambda: each rounded once to the nearest 1e-5, either sign",
         response(route: [c(34.0931249, -118.6007149), c(34.1, -118.7), c(34.0407851, -118.6851149)],
                  waypoints: [c(34.123456, -118.654321), c(34.000004, -118.123456)], lambda: 0.3333333),
         SavedDraft(name: "El Matador",
                    points: [c(34.09312, -118.60071), c(34.12346, -118.65432), c(34, -118.12346),
                             c(34.04079, -118.68511)],
                    lambda: 0.33333, budgetMinutes: 45, createdAt: 1_760_000_000)),
        ("exactly 5 dp kept as it is; no waypoints keeps the two ends",
         response(route: [c(34.00001, -118.00001), c(34.2, -118.3), c(34.5, -118.5)], waypoints: [], lambda: 1.5),
         SavedDraft(name: "El Matador", points: [c(34.00001, -118.00001), c(34.5, -118.5)], lambda: 1.5,
                    budgetMinutes: 45, createdAt: 1_760_000_000)),
        ("a one-point route is its own two ends",
         response(route: [c(34.1, -118.2)], waypoints: [], lambda: 0),
         SavedDraft(name: "El Matador", points: [c(34.1, -118.2), c(34.1, -118.2)], lambda: 0, budgetMinutes: 45,
                    createdAt: 1_760_000_000)),
        ("a half-way tie at the sixth decimal (exact in binary64) rounds away from zero on either sign",
         response(route: [c(34.000005, -118.000005), c(34.000025, -118.000025)], waypoints: [], lambda: 1),
         SavedDraft(name: "El Matador", points: [c(34.00001, -118.00001), c(34.00003, -118.00003)], lambda: 1,
                    budgetMinutes: 45, createdAt: 1_760_000_000)),
        ("an empty route is nothing to save", response(route: [], waypoints: [c(34.1, -118.2)], lambda: 2), nil),
    ]

    @Test("PlanResponse -> preview -> SavedDraft by full equality: >5 dp rounded once, 5 dp kept, the ends, empty")
    func table() {
        for (label, response, want) in Self.rows {
            let preview = ClientPlanner.preview(of: response, place: 42, budgetMinutes: 25)
            #expect(preview.waypoints == response.waypoints, "\(label)")
            #expect(preview.lambda == response.lambda, "\(label)")
            let got = SavedDraft.of(preview, budgetMinutes: 45, name: "El Matador", createdAt: 1_760_000_000)
            #expect(got == want, "\(label)")
        }
    }

    @Test("a saved point rounded once is not moved by rounding it again")
    func roundedOnce() {
        for value in [34.0931249, -118.6007149, 0.3333333, -118.123456] {
            let once = SavedDraft.fiveDecimals(value)
            #expect(SavedDraft.fiveDecimals(once) == once, "\(value)")
        }
    }
}
