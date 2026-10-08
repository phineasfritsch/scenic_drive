import Foundation
import ScenicAPIClient

/// A test's session: the one token (or nil) it was built with, every time (T-0307 R2); a rejection changes nothing.
struct FixedLedgerSession: LedgerSessionProvider {
    let token: String?

    func sessionToken() async -> String? { token }

    func sessionRejected(_ token: String) async {}
}
