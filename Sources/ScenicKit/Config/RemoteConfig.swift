/// The two fields of the Worker's GET /config the app acts on (T-0357 R1): the lowest build allowed to plan, and
/// whether planning is paused (the kill switch, or the KV record's own pause). Every other field of the answer is
/// ignored; ScenicAPIClient's ConfigReader is the only place one is read off the wire.
public struct RemoteConfig: Equatable, Sendable {
    /// The Worker's MAX_APP_BUILD (services/api/src/config.ts): the highest min_app_build it admits.
    public static let maxAppBuild = 2_147_483_647

    /// R4: the Worker's DEFAULTS for the two fields - build 1, not paused - used until a good answer arrives. Never
    /// paused: the Worker's 503 planning_paused stays authoritative; /config is advance notice.
    public static let bundled = RemoteConfig(minAppBuild: 1, planningPaused: false)

    public let minAppBuild: Int
    public let planningPaused: Bool

    public init(minAppBuild: Int, planningPaused: Bool) {
        self.minAppBuild = minAppBuild
        self.planningPaused = planningPaused
    }
}
