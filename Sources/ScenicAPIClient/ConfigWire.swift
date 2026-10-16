import Foundation

/// The /config fields on the wire (T-0357 R1, R2; T-0364 R1): `min_app_build` a JSON integer and `planning_paused` a
/// JSON boolean, both required; each `feature_*` the JSON boolean when it is one, else the Worker's default (true) for
/// that flag alone. Every other key of the answer is ignored; the cache stores this shape back.
struct ConfigWire: Codable {
    let minAppBuild: Int
    let planningPaused: Bool
    let featureLoop: Bool
    let featureTrip: Bool
    let featureSurprise: Bool

    enum CodingKeys: String, CodingKey {
        case minAppBuild = "min_app_build"
        case planningPaused = "planning_paused"
        case featureLoop = "feature_loop"
        case featureTrip = "feature_trip"
        case featureSurprise = "feature_surprise"
    }

    init(minAppBuild: Int, planningPaused: Bool, featureLoop: Bool, featureTrip: Bool, featureSurprise: Bool) {
        self.minAppBuild = minAppBuild
        self.planningPaused = planningPaused
        self.featureLoop = featureLoop
        self.featureTrip = featureTrip
        self.featureSurprise = featureSurprise
    }

    init(from decoder: any Decoder) throws {
        let fields = try decoder.container(keyedBy: CodingKeys.self)
        minAppBuild = try fields.decode(Int.self, forKey: .minAppBuild)
        planningPaused = try fields.decode(Bool.self, forKey: .planningPaused)
        featureLoop = Self.flag(fields, .featureLoop)
        featureTrip = Self.flag(fields, .featureTrip)
        featureSurprise = Self.flag(fields, .featureSurprise)
    }

    /// R1: the flag's boolean, else the Worker's default - absent, null or any other value never refuses the answer.
    static func flag(_ fields: KeyedDecodingContainer<CodingKeys>, _ key: CodingKeys) -> Bool {
        (try? fields.decodeIfPresent(Bool.self, forKey: key)) ?? true
    }
}
