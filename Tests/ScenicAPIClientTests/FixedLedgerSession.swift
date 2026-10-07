import Foundation
import ScenicAPIClient

/// A test's session: the one token (or nil) it was built with, every time (T-0307 R2).
struct FixedLedgerSession: LedgerSessionProvider {
    let token: String?

    func sessionToken() -> String? { token }
}
