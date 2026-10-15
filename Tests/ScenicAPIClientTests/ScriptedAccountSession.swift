import Foundation
import ScenicAPIClient

/// A test's account session (T-0356 R4): hands out its tokens in order - the first, then after each rejection the
/// next one (the last repeated; an empty list is no session) - and records every rejection and every forget.
actor ScriptedAccountSession: AccountSessionProvider {
    private let tokens: [String?]
    private var index = 0
    private(set) var rejected: [String] = []
    private(set) var forgets = 0

    init(_ tokens: [String?]) {
        self.tokens = tokens
    }

    func accountSession() async -> String? {
        tokens.isEmpty ? nil : tokens[min(index, tokens.count - 1)]
    }

    func accountSessionRejected(_ token: String) async {
        rejected.append(token)
        index += 1
    }

    func forgetSession() async {
        forgets += 1
    }
}
