import Foundation

/// Where the app-open fix comes from (T-0366 R3). The app's one conformer is NavAdapter's LiveOpenFix, which never
/// asks for a location permission: no permission, no fix (nil), and nil is moving.
public protocol OpenFixReading: Sendable {
    @MainActor func read() async -> PostDriveFix?
}
