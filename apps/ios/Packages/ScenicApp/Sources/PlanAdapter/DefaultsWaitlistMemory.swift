import Foundation
import ScenicAPIClient

/// The cells this install has counted on the waitlist (T-0360 R3), in UserDefaults `waitlist.joined.cells.v1`. It stays
/// on the device: nothing reads it but WaitlistClient, before a request and after a 200 {"waitlisted":true}.
struct DefaultsWaitlistMemory: WaitlistMemory {
    static let key = "waitlist.joined.cells.v1"

    func hasJoined(_ cell: String) -> Bool {
        (UserDefaults.standard.stringArray(forKey: Self.key) ?? []).contains(cell)
    }

    func rememberJoined(_ cell: String) {
        var cells = UserDefaults.standard.stringArray(forKey: Self.key) ?? []
        guard !cells.contains(cell) else { return }
        cells.append(cell)
        UserDefaults.standard.set(cells, forKey: Self.key)
    }
}
