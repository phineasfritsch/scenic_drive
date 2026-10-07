/// What the user drives (T-0309; plan Decisions: "VehicleProfile enum, only .standard enabled | Liability floor").
///
/// Closed on purpose: every vehicle the app can name is a case here, and only `.standard` can be chosen. The other
/// cases are present so the onboarding can say plainly what is not built yet and why, instead of pretending the
/// routes it plans are fit for a trailer or a motorcycle. Stored on the device only (ruling R2): the Worker's /plan
/// body has no vehicle field yet.
public enum VehicleProfile: String, CaseIterable, Equatable, Sendable {
    case standard
    case lowClearance
    case motorcycle
    case trailer
    case rv

    /// The device store key the onboarding writes and Settings reads.
    public static let storageKey = "vehicle.profile.v1"

    /// The vehicle's name as the onboarding and Settings show it.
    public var name: String {
        switch self {
        case .standard: return "Standard car"
        case .lowClearance: return "Low-clearance car"
        case .motorcycle: return "Motorcycle"
        case .trailer: return "Towing a trailer"
        case .rv: return "RV or camper"
        }
    }

    /// Whether the vehicle can be chosen today.
    public var isEnabled: Bool {
        disabledReason == nil
    }

    /// Why a vehicle cannot be chosen yet; nil for the one that can.
    public var disabledReason: String? {
        switch self {
        case .standard: return nil
        case .lowClearance:
            return "Not yet. The map has no ground-clearance data, so it cannot steer you around rough roads."
        case .motorcycle: return "Not yet. Two wheels need their own road rules, and those are still being written."
        case .trailer: return "Not yet. The map has no weight or grade limits, so it cannot plan around them."
        case .rv: return "Not yet. The map has no height or length limits, so it cannot plan around them."
        }
    }

    /// The stored raw value read back: absent, unknown or not enabled is `.standard`, never a disabled case.
    public static func stored(_ raw: String?) -> VehicleProfile {
        guard let raw, let profile = VehicleProfile(rawValue: raw), profile.isEnabled else { return .standard }
        return profile
    }
}
