import Foundation
import ScenicAPIClient

/// A test's install id: the one UUID it was built with, every time (T-0260). The keychain conformer is M6's.
struct FixedInstallID: InstallIDProvider {
    let id: UUID

    init(_ uuidString: String) {
        id = UUID(uuidString: uuidString)!
    }

    func installID() -> UUID { id }
}
