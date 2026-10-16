import Foundation
import ScenicAPIClient

/// A test's session provider (T-0362 A4): hands out `tokens` in order, one per ask, then nil; records every ask's
/// purchase and every token handed back after a 401.
actor FixedPlanSession: PlanSessionProvider {
    private var tokens: [String]
    private(set) var asked: [UUID?] = []
    private(set) var rejected: [String] = []

    init(_ tokens: [String]) {
        self.tokens = tokens
    }

    func planSession(account: UUID?) -> String? {
        asked.append(account)
        return tokens.isEmpty ? nil : tokens.removeFirst()
    }

    func planSessionRejected(_ token: String) {
        rejected.append(token)
    }
}
