import Foundation
@testable import ScenicKit

/// T-0253 R8's synthetic LA-area candidates (Tests/Fixtures/surprise/candidates.tsv) and the Python oracle's
/// whole pick permutations (sequences.tsv). Every helper here calls `Surprise.pick`, the shipping entry point.
enum SurpriseFixture {
    static let june20 = CivilDate(year: 2026, month: 6, day: 20)
    static let june21 = CivilDate(year: 2026, month: 6, day: 21)
    static let losAngelesSummer = -420

    static func file(_ name: String) throws -> [[String]] {
        let url = URL(fileURLWithPath: #filePath)   // Tests/ScenicKitTests/Surprise/<this file>
            .deletingLastPathComponent()             // Tests/ScenicKitTests/Surprise
            .deletingLastPathComponent()             // Tests/ScenicKitTests
            .deletingLastPathComponent()             // Tests
            .appendingPathComponent("Fixtures/surprise/\(name)")
        return try String(contentsOf: url, encoding: .utf8)
            .split(separator: "\n").map { String($0) }
            .filter { !$0.hasPrefix("#") && !$0.isEmpty }
            .map { $0.split(separator: "\t", omittingEmptySubsequences: false).map { String($0) } }
    }

    private static func int(_ s: String) -> Int? { s == "-" ? nil : Int(s)! }

    static func candidates() throws -> [SurpriseCandidate] {
        try file("candidates.tsv").map { f in
            SurpriseCandidate(id: f[0], name: f[1], hook: f[17], category: SurpriseCategory(rawValue: f[2])!,
                              corridor: f[3], brand: f[4] == "-" ? nil : f[4],
                              coordinate: Coordinate(latitude: Double(f[5])!, longitude: Double(f[6])!),
                              quality: Int(f[7])!, approachScore: Int(f[8])!, dwellMinutes: Int(f[9])!,
                              opensMinute: int(f[10]), closesMinute: int(f[11]), hoursExempt: f[12] == "1",
                              lit: f[13] == "1", unpaved: f[14] == "1", privateApproach: f[15] == "1")
        }
    }

    static func roundTrips() throws -> [String: Int] {
        var out: [String: Int] = [:]
        for f in try file("candidates.tsv") { out[f[0]] = int(f[16]) }
        return out
    }

    static func context(user: String = "driver-a", date: CivilDate = june20, depart: Int = 840,
                        redFlag: Bool = false) -> SurpriseContext {
        SurpriseContext(userId: user, date: date, departureMinute: depart, utcOffsetMinutes: losAngelesSummer,
                        redFlag: redFlag)
    }

    /// Scenario B's history (R8): beach topanga-03 89 days, viewpoint malibu-02 90 days, cafe x griffith 29
    /// days, museum x arroyo 30 days, garden x ojai 200 days (novelty capped at 100) before 2026-06-21.
    static let historyB = SurpriseHistory(shown: [
        .init(candidateId: "topanga-03", category: .beach, corridor: "topanga",
              date: CivilDate(year: 2026, month: 3, day: 24)),
        .init(candidateId: "malibu-02", category: .viewpoint, corridor: "pch",
              date: CivilDate(year: 2026, month: 3, day: 23)),
        .init(candidateId: "griffith-x", category: .cafe, corridor: "griffith",
              date: CivilDate(year: 2026, month: 5, day: 23)),
        .init(candidateId: "arroyo-x", category: .museum, corridor: "arroyo",
              date: CivilDate(year: 2026, month: 5, day: 22)),
        .init(candidateId: "ojai-x", category: .garden, corridor: "ojai",
              date: CivilDate(year: 2025, month: 12, day: 3)),
    ])
    static let contextB = context(user: "driver-b", date: june21, depart: 600)

    static func pick(seed: UInt64, budget: Int = 180, history: SurpriseHistory = SurpriseHistory(),
                     context: SurpriseContext = context()) throws -> SurprisePick? {
        Surprise.pick(candidates: try candidates(),
                      reach: SurpriseReach(budgetMinutes: budget, roundTripMinutes: try roundTrips()),
                      history: history, context: context, seed: seed)
    }

    /// The picked ids for seeds `from ..< from + count` ("nil" when nothing was picked).
    static func ids(from: UInt64 = 0, count: Int = 300, budget: Int = 180,
                    history: SurpriseHistory = SurpriseHistory(),
                    context: SurpriseContext = context()) throws -> [String] {
        let candidates = try candidates()
        let reach = SurpriseReach(budgetMinutes: budget, roundTripMinutes: try roundTrips())
        return (0..<UInt64(count)).map { k in
            Surprise.pick(candidates: candidates, reach: reach, history: history, context: context,
                          seed: from + k)?.candidateId ?? "nil"
        }
    }

    static func sequence(_ scenario: String) throws -> [String] {
        try file("sequences.tsv").filter { $0[0] == scenario }.map { $0[2] }
    }

    static func category(_ id: String) throws -> SurpriseCategory? {
        try candidates().first { $0.id == id }?.category
    }

    /// The whole pick as one line of its PROPERTIES, compared to literals - never a pick built by the same init.
    static func render(_ p: SurprisePick?) -> String {
        guard let p else { return "nil" }
        return "\(p.candidateId) | \(p.name) | \(p.reason.hook) | \(p.reason.roundTripMinutes) min | "
            + (p.reason.goldenHourLine ?? "no golden hour")
    }
}
