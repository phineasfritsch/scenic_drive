import Foundation

/// The two /config fields on the wire (T-0357 R1, R2): `min_app_build` a JSON integer, `planning_paused` a JSON
/// boolean. Every other key of the answer is ignored by the decoder; the cache stores this shape back.
struct ConfigWire: Codable {
    let minAppBuild: Int
    let planningPaused: Bool

    enum CodingKeys: String, CodingKey {
        case minAppBuild = "min_app_build"
        case planningPaused = "planning_paused"
    }
}
