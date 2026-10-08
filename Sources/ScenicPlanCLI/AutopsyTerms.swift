import Foundation
import ScenicKit

/// The per-way input `ops/route-autopsy --terms` reads: each way's OSM tags and its scoring terms.
///
/// ## Why this is a file and not the graph
///
/// The served graph and every recording carry `scenic_score` as a 0..10 integer, `road_class` and
/// `osm_way_id` - never a term, a tag or a gate (T-0327 m3). The quantised score cannot be inverted into M
/// and E, so the GATE/M/E columns are computed by ScenicKit from THIS file (`Gates.decide` over `tags`,
/// `SegmentScore` over `terms`), and a way the file does not carry prints `-`. The shape:
///
///     {"source": "...", "ways": {"<osm_way_id>": {"tags": {"highway": "...", ...},
///                                                "terms": {"curvature": 0.4, ..., "bywayTier": "none",
///                                                          "tunnelMeters": 0, "metersToNearestMotorway": null}}}}
///
/// Term names are `SegmentTerms`' own; `highway` and `surface` are read from `tags` so a way has one road
/// class. `metersToNearestMotorway: null` is "no motorway nearby" (`.infinity`). Anything else malformed is
/// refused by name: a guessed term is a guessed score, which is the defect an autopsy exists to find.
public struct AutopsyTerms {

    public struct Way {
        public let tags: [String: String]
        public let terms: SegmentTerms
    }

    public struct Failure: Error, CustomStringConvertible {
        public let description: String
    }

    /// The ten `0...1` terms, by `SegmentTerms`' names.
    static let unitTermNames = ["curvature", "elevationGain", "speedFit", "sinuosity", "canopy", "relief",
                                "impervious", "pointsOfInterest", "water", "furniture"]

    public let source: String
    public let ways: [Int: Way]

    public static func load(_ url: URL) throws -> AutopsyTerms {
        guard let data = FileManager.default.contents(atPath: url.path) else {
            throw Failure(description: "no terms file at \(url.path)")
        }
        return try decode(data)
    }

    static func decode(_ data: Data) throws -> AutopsyTerms {
        guard let root = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] else {
            throw Failure(description: "the terms file is not a JSON object")
        }
        guard let source = root["source"] as? String else {
            throw Failure(description: "the terms file has no \"source\" string saying where its numbers came from")
        }
        guard let rawWays = root["ways"] as? [String: Any] else {
            throw Failure(description: "the terms file has no \"ways\" object")
        }
        var ways: [Int: Way] = [:]
        for (key, raw) in rawWays {
            guard let id = Int(key) else { throw Failure(description: "way key \(key) is not an OSM way id") }
            ways[id] = try way(id, raw)
        }
        return AutopsyTerms(source: source, ways: ways)
    }

    static func way(_ id: Int, _ raw: Any) throws -> Way {
        guard let entry = raw as? [String: Any], let tags = entry["tags"] as? [String: String],
              let terms = entry["terms"] as? [String: Any] else {
            throw Failure(description: "way \(id) needs a \"tags\" map of strings and a \"terms\" object")
        }
        guard let highway = tags["highway"] else { throw Failure(description: "way \(id) has no highway tag") }
        var unit: [String: Double] = [:]
        for name in unitTermNames {
            guard let value = terms[name] as? Double else {
                throw Failure(description: "way \(id) term \(name) is not a number")
            }
            unit[name] = value
        }
        guard let tierName = terms["bywayTier"] as? String, let tier = BywayTier(rawValue: tierName) else {
            throw Failure(description: "way \(id) bywayTier is not one of none, eligible, designated")
        }
        guard let tunnel = terms["tunnelMeters"] as? Double else {
            throw Failure(description: "way \(id) tunnelMeters is not a number")
        }
        let motorway: Double
        switch terms["metersToNearestMotorway"] {
        case is NSNull: motorway = .infinity
        case let value as Double: motorway = value
        default: throw Failure(description: "way \(id) metersToNearestMotorway is not a number or null")
        }
        return Way(tags: tags, terms: SegmentTerms(
            curvature: unit["curvature"]!, elevationGain: unit["elevationGain"]!, speedFit: unit["speedFit"]!,
            sinuosity: unit["sinuosity"]!, canopy: unit["canopy"]!, relief: unit["relief"]!,
            impervious: unit["impervious"]!, pointsOfInterest: unit["pointsOfInterest"]!, water: unit["water"]!,
            furniture: unit["furniture"]!, bywayTier: tier, highway: highway, surface: tags["surface"],
            tunnelMeters: tunnel, metersToNearestMotorway: motorway))
    }
}
