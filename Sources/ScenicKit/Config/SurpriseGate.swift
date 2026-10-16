/// What /config's feature_surprise does to Surprise Me on this device (T-0368 R2-R4): on, or switched off. Advisory -
/// Surprise Me plans on the device and sends the Worker nothing - so off only changes what the app offers: the home
/// shows `offLine` in place of the card, and the plan sheet's failures stop offering "Surprise me instead".
public enum SurpriseGate: String, CaseIterable, Equatable, Sendable {
    case on
    case off

    /// R2: the home's line in place of the Surprise card while the flag is off.
    public static let offLine = "Surprise Me is switched off for now. You can still plan a drive."

    /// R3: feature_surprise and nothing else.
    public static func of(_ config: RemoteConfig) -> SurpriseGate {
        config.featureSurprise ? .on : .off
    }

    /// The line the home shows in place of the card: nil exactly when on.
    public var homeLine: String? {
        switch self {
        case .on: return nil
        case .off: return Self.offLine
        }
    }
}
