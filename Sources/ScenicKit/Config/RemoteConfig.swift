/// The fields of the Worker's GET /config the app acts on (T-0357 R1, T-0364 R1): the lowest build allowed to plan,
/// whether planning is paused (the kill switch, or the KV record's own pause), and the three feature flags. Every
/// other field of the answer is ignored; ScenicAPIClient's ConfigReader is the only place one is read off the wire.
public struct RemoteConfig: Equatable, Sendable {
    /// The Worker's MAX_APP_BUILD (services/api/src/config.ts): the highest min_app_build it admits.
    public static let maxAppBuild = 2_147_483_647

    /// R4: the Worker's DEFAULTS - build 1, not paused, every feature on - used until a good answer arrives. Never
    /// paused: the Worker's 503 planning_paused stays authoritative; /config is advance notice.
    public static let bundled = RemoteConfig(minAppBuild: 1, planningPaused: false)

    public let minAppBuild: Int
    public let planningPaused: Bool
    /// T-0364: `feature_loop`, `feature_trip`, `feature_surprise` - advisory (the Worker refuses nothing on them).
    public let featureLoop: Bool
    public let featureTrip: Bool
    public let featureSurprise: Bool

    public init(minAppBuild: Int, planningPaused: Bool, featureLoop: Bool = true, featureTrip: Bool = true,
                featureSurprise: Bool = true) {
        self.minAppBuild = minAppBuild
        self.planningPaused = planningPaused
        self.featureLoop = featureLoop
        self.featureTrip = featureTrip
        self.featureSurprise = featureSurprise
    }
}
