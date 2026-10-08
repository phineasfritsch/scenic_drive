import Foundation
import ScenicAPIClient

/// A test's purchase id (T-0315): the one token it was built with, or nil for a device that never bought one; it
/// counts its reads so a device refusal can be shown to read nothing.
actor FixedAccountToken: AccountTokenProvider {
    let token: UUID?
    private(set) var reads = 0

    init(_ uuidString: String?) {
        token = uuidString.map { UUID(uuidString: $0)! }
    }

    func accountToken() -> UUID? {
        reads += 1
        return token
    }
}
