import Foundation
import Dispatch
import ScenicKit
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// Routes from a GraphHopper `/route` endpoint.
///
/// ## Which GraphHopper, and which model
///
/// Ours, over HTTP, with the SAME per-request custom model the Worker's `buildCustomModel` emits - built
/// here by `LambdaCustomModel`, the single Swift copy, held to the TypeScript by a byte-equality golden.
/// The safety gates (`road_access`, `surface`, `road_class == TRACK`) are NOT sent: they live in
/// car_scenic_base.json on the server, where a per-request body cannot relax them.
///
/// ## What has and has not been exercised
///
/// This transport is not exercised against a served graph by this task, and says so rather than implying
/// otherwise: T-0213's image has no HTTP surface (no Dropwizard `server:` section, graphhopper-core only),
/// so the golden and the smoke run off recorded responses from that graph. T-0221 is the served run, and
/// it is this type's first live request. What IS tested here is the request BODY - the bytes that go on
/// the wire - because that is the part a recording cannot check and the part the safety property is about.
public struct GraphHopperRouteSource: RouteSource {

    /// Holds one response across the semaphore. `URLSession`'s completion handler runs on another thread,
    /// so the value cannot simply be captured: under Swift 6 that is a data race, and under any language
    /// mode it is one.
    final class ResponseBox: @unchecked Sendable {
        private let lock = NSLock()
        private var value: Result<Data, Error>?

        func set(_ result: Result<Data, Error>) {
            lock.lock()
            defer { lock.unlock() }
            value = result
        }

        func take() -> Result<Data, Error>? {
            lock.lock()
            defer { lock.unlock() }
            return value
        }
    }

    /// The path details the table needs. `time` is asked for too - a served graph can answer it, and when
    /// it does the table stops apportioning seconds by metres.
    public static let details = ["scenic_score", "road_class", "osm_way_id"]

    public let baseURL: URL
    public let fastProfile: String
    public let scenicProfile: String
    public let timeout: TimeInterval

    public init(baseURL: URL, fastProfile: String = "car_fast",
                scenicProfile: String = "car_scenic", timeout: TimeInterval = 30) {
        self.baseURL = baseURL
        self.fastProfile = fastProfile
        self.scenicProfile = scenicProfile
        self.timeout = timeout
    }

    public var describedSource: String { "graphhopper \(baseURL.absoluteString)" }

    public func fastest(from origin: Coordinate, to destination: Coordinate) throws -> RoutePath {
        try RoutePath.decode(try send(body(origin, destination, profile: fastProfile, model: nil)))
    }

    public func scenic(from origin: Coordinate, to destination: Coordinate,
                       lambda: Double) throws -> RoutePath {
        let model = try LambdaCustomModel.json(for: lambda)
        let body = body(origin, destination, profile: scenicProfile, model: model)
        return try RoutePath.decode(try send(body))
    }

    /// The request body, as text.
    ///
    /// `points_encoded: false` because the table and the pins read real coordinates; `ch.disable: true`
    /// because a per-request custom model is only legal on a flexible query; `instructions: false` because
    /// nothing here reads them and they are most of the bytes.
    func body(_ origin: Coordinate, _ destination: Coordinate,
              profile: String, model: String?) -> String {
        let points = "[[\(origin.longitude), \(origin.latitude)], "
            + "[\(destination.longitude), \(destination.latitude)]]"
        let details = Self.details.map { "\"\($0)\"" }.joined(separator: ", ")
        var lines = [
            "  \"points\": \(points)",
            "  \"profile\": \"\(profile)\"",
            "  \"points_encoded\": false",
            "  \"instructions\": false",
            "  \"ch.disable\": true",
            "  \"details\": [\(details)]",
        ]
        if let model {
            lines.append("  \"custom_model\": \(model.replacingOccurrences(of: "\n", with: "\n  "))")
        }
        return "{\n" + lines.joined(separator: ",\n") + "\n}"
    }

    func send(_ body: String) throws -> Data {
        var request = URLRequest(url: baseURL.appendingPathComponent("route"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = Data(body.utf8)
        request.timeoutInterval = timeout

        let box = ResponseBox()
        let waiter = DispatchSemaphore(value: 0)
        let task = URLSession.shared.dataTask(with: request) { data, _, error in
            if let error {
                box.set(.failure(error))
            } else {
                box.set(.success(data ?? Data()))
            }
            waiter.signal()
        }
        task.resume()
        if waiter.wait(timeout: .now() + timeout + 1) == .timedOut {
            task.cancel()
            throw PlanFailure.routerRefused("no answer from \(baseURL.absoluteString) in \(timeout) s")
        }
        switch box.take() {
        case let .success(data): return data
        case let .failure(error): throw PlanFailure.routerRefused("\(error)")
        case nil: throw PlanFailure.routerRefused("the request finished with neither data nor an error")
        }
    }
}
