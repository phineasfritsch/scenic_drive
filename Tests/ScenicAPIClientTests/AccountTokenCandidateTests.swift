import Foundation
import ScenicAPIClient
import Testing

/// T-0315 R3: the token the app sends is the most recent purchase's - live, expired or revoked alike - whatever
/// order StoreKit lists the transactions in. Every row is run in every permutation of its candidates, and the
/// purchase instants sit at exactly-equal and one-ulp-apart bounds.
@Suite("AccountTokenCandidateTests")
struct AccountTokenCandidateTests {
    static let a = UUID(uuidString: "0E6B9A4C-5F1D-4C2B-9A8E-3D7F1B2C4A5E")!
    static let b = UUID(uuidString: "A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")!
    static let t = Date(timeIntervalSinceReferenceDate: 800_000_000)
    static let tNext = Date(timeIntervalSinceReferenceDate: (800_000_000.0).nextUp)

    struct Row: Sendable {
        let label: String
        let candidates: [AccountTokenCandidate]
        let expected: UUID?
    }

    static func c(_ date: Date, _ token: UUID?) -> AccountTokenCandidate {
        AccountTokenCandidate(purchased: date, token: token)
    }

    static let rows: [Row] = [
        Row(label: "no transaction", candidates: [], expected: nil),
        Row(label: "a purchase without a token", candidates: [c(t, nil)], expected: nil),
        Row(label: "one purchase", candidates: [c(t, a)], expected: a),
        Row(label: "the later purchase, one ulp later", candidates: [c(t, a), c(tNext, b)], expected: b),
        Row(label: "the later purchase is a", candidates: [c(tNext, a), c(t, b)], expected: a),
        Row(label: "a newer purchase without a token is passed over", candidates: [c(tNext, nil), c(t, a)],
            expected: a),
        Row(label: "equal instants keep the greater token", candidates: [c(t, a), c(t, b)], expected: b),
        Row(label: "an older greater token loses to a newer one", candidates: [c(t, b), c(tNext, a), c(t, nil)],
            expected: a),
    ]

    static func permutations(_ items: [AccountTokenCandidate]) -> [[AccountTokenCandidate]] {
        guard items.count > 1 else { return [items] }
        return items.indices.flatMap { i -> [[AccountTokenCandidate]] in
            var rest = items
            let head = rest.remove(at: i)
            return permutations(rest).map { [head] + $0 }
        }
    }

    @Test("the latest purchase's token is the one sent, live or expired, in every StoreKit order",
          arguments: rows.map(\.label))
    func latest(_ label: String) {
        let row = Self.rows.first { $0.label == label }!
        for order in Self.permutations(row.candidates) {
            #expect(AccountTokenCandidate.latest(order) == row.expected, "\(label): \(order)")
        }
    }
}
