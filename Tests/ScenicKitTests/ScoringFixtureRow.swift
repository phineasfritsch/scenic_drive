import Foundation

/// One row of `Tests/Fixtures/scoring/segment_terms.json`: an id, every input `SegmentScore` reads, and the
/// expected score.
///
/// `expected` was computed by a hand transcription of the plan's formula inside
/// `Tests/Fixtures/scoring/generate.py` - by neither this package nor the ETL. A fixture whose expectation
/// comes from the code it checks proves only that the code equals itself, and that is the defect this
/// repository exists to catch.
///
/// `bywayTier` is spelled in the fixture's own neutral vocabulary (`none` / `eligible` / `designated`),
/// which is neither side's enum and neither side's Caltrans status code: the two implementations each
/// translate it, so neither one's spelling can quietly become the contract.
struct ScoringFixtureRow: Decodable, Sendable, CustomStringConvertible {
    let id: String
    let curvature: Double
    let elevationGain: Double
    let speedFit: Double
    let sinuosity: Double
    let canopy: Double
    let relief: Double
    let impervious: Double
    let pointsOfInterest: Double
    let water: Double
    let furniture: Double
    let bywayTier: String
    let highway: String
    let surface: String?
    let tunnelMeters: Double
    let metersToNearestMotorway: Double
    let expected: Double

    var description: String { id }

    enum CodingKeys: String, CodingKey {
        case id, curvature, elevationGain, speedFit, sinuosity, canopy, relief, impervious
        case pointsOfInterest, water, furniture, bywayTier, highway, surface, tunnelMeters
        case metersToNearestMotorway, expected
    }

    /// Hand-written because of one field: JSON has no infinity literal, and `metersToNearestMotorway` is
    /// `.infinity` for a way with no motorway anywhere near it - the initialiser's default and the common
    /// case. The generator emits the string `"Infinity"` for it rather than a bare token no strict JSON
    /// parser would accept, and this is where it comes back.
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        curvature = try c.decode(Double.self, forKey: .curvature)
        elevationGain = try c.decode(Double.self, forKey: .elevationGain)
        speedFit = try c.decode(Double.self, forKey: .speedFit)
        sinuosity = try c.decode(Double.self, forKey: .sinuosity)
        canopy = try c.decode(Double.self, forKey: .canopy)
        relief = try c.decode(Double.self, forKey: .relief)
        impervious = try c.decode(Double.self, forKey: .impervious)
        pointsOfInterest = try c.decode(Double.self, forKey: .pointsOfInterest)
        water = try c.decode(Double.self, forKey: .water)
        furniture = try c.decode(Double.self, forKey: .furniture)
        bywayTier = try c.decode(String.self, forKey: .bywayTier)
        highway = try c.decode(String.self, forKey: .highway)
        surface = try c.decodeIfPresent(String.self, forKey: .surface)
        tunnelMeters = try c.decode(Double.self, forKey: .tunnelMeters)
        expected = try c.decode(Double.self, forKey: .expected)
        if let metres = try? c.decode(Double.self, forKey: .metersToNearestMotorway) {
            metersToNearestMotorway = metres
        } else {
            let spelled = try c.decode(String.self, forKey: .metersToNearestMotorway)
            guard spelled == "Infinity" else {
                throw DecodingError.dataCorruptedError(forKey: .metersToNearestMotorway, in: c,
                                                       debugDescription: "unknown distance \(spelled)")
            }
            metersToNearestMotorway = .infinity
        }
    }
}
