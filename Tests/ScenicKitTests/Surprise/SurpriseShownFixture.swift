import Foundation
import ScenicKit

/// The shown-place values SurpriseShowingTests, SurpriseCardHistoryTests and SurpriseShownDayTests share. They live
/// in a file no mutation population empties: ops/mutate/session.py --prove-vacuity replaces SurpriseShowingTests.swift
/// with an empty suite, and a fixture defined there left the other two unable to build (T-0331).
enum SurpriseShownFixture {
    static let today = CivilDate(year: 2026, month: 10, day: 7)
    static let yesterday = CivilDate(year: 2026, month: 10, day: 6)

    static func place(_ id: String, _ category: SurpriseCategory, _ corridor: String) -> SurpriseCandidate {
        SurpriseCandidate(id: id, name: "Place \(id)", hook: "A hook.", category: category, corridor: corridor,
                          brand: nil, coordinate: Coordinate(latitude: 34.1, longitude: -118.6), quality: 3,
                          approachScore: 3, dwellMinutes: 30, opensMinute: nil, closesMinute: nil, hoursExempt: true,
                          lit: false, unpaved: false, privateApproach: false)
    }

    static let a = place("1234567", .viewpoint, "pch")
    static let b = place("7654321", .park, "topanga")

    static func shown(_ p: SurpriseCandidate, _ date: CivilDate) -> SurpriseHistory.Shown {
        SurpriseHistory.Shown(candidateId: p.id, category: p.category, corridor: p.corridor, date: date)
    }
}
