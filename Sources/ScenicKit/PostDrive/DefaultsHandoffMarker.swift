import Foundation

/// The device's handoff marker (T-0366 R1): one Int in UserDefaults under one key, read by nothing but
/// PostDriveNextOpen and never sent. `suiteName` is for tests; the app uses the standard defaults.
public struct DefaultsHandoffMarker: HandoffMarkerStoring {
    public static let key = "postDrive.handoffOpensLeft"

    private let suiteName: String?

    public init(suiteName: String? = nil) {
        self.suiteName = suiteName
    }

    private var defaults: UserDefaults {
        suiteName.flatMap { UserDefaults(suiteName: $0) } ?? .standard
    }

    public func opensLeft() -> Int {
        defaults.integer(forKey: Self.key)
    }

    public func setOpensLeft(_ value: Int) {
        defaults.set(value, forKey: Self.key)
    }
}
