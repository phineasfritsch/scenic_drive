import Foundation

/// One routed path, decoded from GraphHopper's documented `points_encoded=false` response body.
///
/// The shape is the wire shape, not a convenience of ours: `paths[0]` with `time` in MILLISECONDS,
/// `distance` in metres, `points` as a GeoJSON `LineString` of `[lon, lat]` pairs, and `details` as a map
/// from an encoded-value name to runs of `[fromIndex, toIndex, value]` over that point list. Everything
/// downstream - the per-edge table, the waypoint pins, the ceiling - reads this and nothing else, so the
/// only place the response format is known is here.
///
/// Decoded with `JSONSerialization` rather than `Codable` on purpose: a detail run is a heterogeneous
/// array (`[0, 3, "primary"]`, `[3, 7, 8]`, `[7, 9, null]`) and a `Decodable` conformance for that is a
/// pile of single-value containers that fails in a less legible place than this does.
public struct RoutePath: Sendable, Equatable {

    /// One run of a path detail: the points `[from, to]` of the path's own point list, and the value the
    /// router reported over them. `to` is the index of the LAST point of the run, so a run covers the
    /// segment from `from` to `to` and consecutive runs share an index.
    public struct DetailRun: Sendable, Equatable {
        public let from: Int
        public let to: Int
        public let value: Value

        public init(from: Int, to: Int, value: Value) {
            self.from = from
            self.to = to
            self.value = value
        }
    }

    /// A detail value. `missing` is JSON `null`, which GraphHopper emits for a stretch where the encoded
    /// value has nothing to say; it is kept rather than defaulted, because a way with no scenic score and a
    /// way scored 0 are different facts and the table must not print them the same.
    public enum Value: Sendable, Equatable {
        case number(Double)
        case text(String)
        case missing

        public var number: Double? {
            if case let .number(v) = self { return v }
            return nil
        }

        public var text: String? {
            switch self {
            case let .text(v): return v
            case let .number(v): return v == v.rounded() ? String(Int(v)) : String(v)
            case .missing: return nil
            }
        }
    }

    public let durationMilliseconds: Int
    public let distanceMeters: Double
    public let coordinates: [Coordinate]
    public let details: [String: [DetailRun]]

    public init(durationMilliseconds: Int, distanceMeters: Double,
                coordinates: [Coordinate], details: [String: [DetailRun]]) {
        self.durationMilliseconds = durationMilliseconds
        self.distanceMeters = distanceMeters
        self.coordinates = coordinates
        self.details = details
    }

    /// Seconds, which is what every duration in ScenicKit is. GraphHopper answers in milliseconds.
    public var duration: TimeInterval { Double(durationMilliseconds) / 1000 }

    /// Decode `paths[0]`, or refuse by name. Never a partial value: a body missing `time`, `distance` or
    /// `points` is a body we cannot plan from, and guessing one of them would put an invented ETA on a
    /// screen.
    public static func decode(_ data: Data) throws -> RoutePath {
        let object: Any
        do {
            object = try JSONSerialization.jsonObject(with: data)
        } catch {
            throw PlanFailure.malformedResponse("not JSON: \(error)")
        }
        guard let root = object as? [String: Any] else {
            throw PlanFailure.malformedResponse("the response body is not a JSON object")
        }
        if let message = root["message"] as? String, root["paths"] == nil {
            throw PlanFailure.routerRefused(message)
        }
        guard let paths = root["paths"] as? [[String: Any]], let path = paths.first else {
            throw PlanFailure.malformedResponse("the response carries no paths[0]")
        }
        guard let time = path["time"] as? Int else {
            throw PlanFailure.malformedResponse("paths[0].time is not an integer count of milliseconds")
        }
        guard let distance = path["distance"] as? Double else {
            throw PlanFailure.malformedResponse("paths[0].distance is not a number of metres")
        }
        guard let points = path["points"] as? [String: Any],
              let positions = points["coordinates"] as? [[Double]] else {
            throw PlanFailure.malformedResponse(
                "paths[0].points is not a GeoJSON LineString - request points_encoded=false")
        }
        return RoutePath(
            durationMilliseconds: time,
            distanceMeters: distance,
            coordinates: try positions.map(coordinate(from:)),
            details: try runs(from: path["details"])
        )
    }

    /// `[lon, lat]`, in that order, which is GeoJSON's order and the reverse of every label in this app.
    static func coordinate(from position: [Double]) throws -> Coordinate {
        guard position.count >= 2 else {
            throw PlanFailure.malformedResponse("a point is not a [lon, lat] pair")
        }
        return Coordinate(latitude: position[1], longitude: position[0])
    }

    static func runs(from raw: Any?) throws -> [String: [DetailRun]] {
        guard let raw else { return [:] }
        guard let details = raw as? [String: [[Any]]] else {
            throw PlanFailure.malformedResponse("paths[0].details is not a map of runs")
        }
        var decoded: [String: [DetailRun]] = [:]
        for (key, entries) in details {
            decoded[key] = try entries.map { entry in
                guard entry.count == 3, let from = entry[0] as? Int, let to = entry[1] as? Int else {
                    throw PlanFailure.malformedResponse("a \(key) run is not [from, to, value]")
                }
                return DetailRun(from: from, to: to, value: value(of: entry[2]))
            }
        }
        return decoded
    }

    static func value(of raw: Any) -> Value {
        if let text = raw as? String { return .text(text) }
        if let number = raw as? Int { return .number(Double(number)) }
        if let number = raw as? Double { return .number(number) }
        return .missing
    }
}
