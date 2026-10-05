import Foundation
import ScenicAPIClient
import ScenicKit
import XCTest

/// T-0251 rv1 B1, closed as a class: a 200 body whose every decoded value differs from both recorded plans, so a
/// field hard-coded to the recorded value cannot decode equal; and a table that removes, then wrong-types, every
/// key PlanResponse reads, so `decodeIfPresent ?? default` and `(try? ...) ?? default` are refused key by key.
/// Every plan goes through the shipping entry point, `PlanClient.plan`, over the counting fake.
final class PlanResponseDecodeTests: XCTestCase {
    static let url = "https://maps.apple.com/directions?source=34.12000,-118.38000&destination=34.38000,-118.13000"
        + "&waypoint=34.25000,-118.25000&mode=driving"

    /// Only keys PlanResponse reads; every value differs from 200-plan and 200-plan-hazards.
    static let body = #"{"route":{"coordinates":[[-118.375,34.125],[-118.25,34.25],[-118.125,34.375]],"#
        + #""distance_m":4321.5},"eta_s":987.25,"fastest_eta_s":812.5,"ceiling_s":1712.5,"budget_s":900,"#
        + #""lambda":3.5,"evaluations":11,"used_budget":true,"eta_is_estimate":false,"#
        + #""hazards":[{"kind":"surface","value":"dirt","from_index":0,"to_index":2}],"#
        + #""waypoints":[{"lat":34.25,"lon":-118.25}],"apple_maps_url":""# + url + #""}"#

    static let expected = PlanResponse(
        route: [Coordinate(latitude: 34.125, longitude: -118.375), Coordinate(latitude: 34.25, longitude: -118.25),
                Coordinate(latitude: 34.375, longitude: -118.125)],
        distanceMeters: 4321.5, etaSeconds: 987.25, fastestEtaSeconds: 812.5, ceilingSeconds: 1712.5,
        budgetSeconds: 900, lambda: 3.5, evaluations: 11, usedBudget: true, etaIsEstimate: false,
        hazards: [PlanHazard(kind: "surface", value: "dirt", fromIndex: 0, toIndex: 2)],
        waypoints: [Coordinate(latitude: 34.25, longitude: -118.25)], appleMapsURL: URL(string: url)!)

    /// Every key the body carries, by path ("0" is an array's first element) - each one PlanResponse requires.
    static let requiredKeys: Set<String> = [
        "route", "route.coordinates", "route.distance_m", "eta_s", "fastest_eta_s", "ceiling_s", "budget_s",
        "lambda", "evaluations", "used_budget", "eta_is_estimate", "hazards", "hazards.0.kind", "hazards.0.value",
        "hazards.0.from_index", "hazards.0.to_index", "waypoints", "waypoints.0.lat", "waypoints.0.lon",
        "apple_maps_url",
    ]

    private func plan(_ data: Data) async -> Result<PlanResponse, PlanError> {
        let (outcome, fake) = await PlanWire.plan(answering: PlanHTTPReply(status: 200, body: data))
        let count = await fake.count
        XCTAssertEqual(count, 1)
        return outcome
    }

    func test200EveryFieldDistinctFromTheRecordedPlansDecodesWhole() async throws {
        let decoded = try await plan(Data(Self.body.utf8)).get()
        XCTAssertEqual(decoded, Self.expected)
    }

    /// The premise of the test above, held: no field of the literal equals that field of either recorded plan.
    func testTheDistinctBodySharesNoFieldWithARecordedPlan() async throws {
        for name in ["200-plan", "200-plan-hazards"] {
            let recorded = try await plan(try PlanWire.fixture(name)).get()
            XCTAssertEqual(Self.sharedFields(Self.expected, recorded), [], name)
        }
    }

    func test200MissingAnyRequiredKeyIsUnexpectedResponse() async throws {
        let tree = try Self.tree()
        XCTAssertEqual(Set(Self.keyPaths(tree).map { $0.joined(separator: ".") }), Self.requiredKeys)
        let control = await plan(try JSONSerialization.data(withJSONObject: tree))
        XCTAssertEqual(try control.get(), Self.expected, "the re-serialized body, unedited")
        for key in Self.requiredKeys.sorted() {
            let edited = Self.replacing(tree, at: key.split(separator: ".").map(String.init)[...], with: nil)
            let outcome = await plan(try JSONSerialization.data(withJSONObject: edited))
            XCTAssertEqual(PlanWire.error(outcome), .unexpectedResponse(status: 200), "removed \(key)")
        }
    }

    func test200WrongTypedAnyRequiredKeyIsUnexpectedResponse() async throws {
        let tree = try Self.tree()
        var rows: [(String, Any)] = Self.requiredKeys.sorted().map { key in
            let path = key.split(separator: ".").map(String.init)
            return (key, Self.value(tree, at: path[...]) is String ? 7 as Any : "x" as Any)
        }
        rows.append(("evaluations", 11.5))
        rows.append(("route.coordinates.0", [-118.375, 34.125, 0.0]))
        for (key, wrong) in rows {
            let edited = Self.replacing(tree, at: key.split(separator: ".").map(String.init)[...], with: wrong)
            let outcome = await plan(try JSONSerialization.data(withJSONObject: edited))
            XCTAssertEqual(PlanWire.error(outcome), .unexpectedResponse(status: 200), "\(key) = \(wrong)")
        }
    }

    private static func tree() throws -> Any {
        try JSONSerialization.jsonObject(with: Data(body.utf8))
    }

    private static func keyPaths(_ node: Any, _ prefix: [String] = []) -> [[String]] {
        if let object = node as? [String: Any] {
            return object.keys.sorted().flatMap { [prefix + [$0]] + keyPaths(object[$0]!, prefix + [$0]) }
        }
        if let array = node as? [Any], let first = array.first, first is [String: Any] {
            return keyPaths(first, prefix + ["0"])
        }
        return []
    }

    private static func value(_ node: Any, at path: ArraySlice<String>) -> Any? {
        guard let head = path.first else { return node }
        if let object = node as? [String: Any] { return object[head].flatMap { value($0, at: path.dropFirst()) } }
        guard let array = node as? [Any], let index = Int(head), array.indices.contains(index) else { return nil }
        return value(array[index], at: path.dropFirst())
    }

    /// `node` with the value at `path` replaced by `new`; nil removes an object's key.
    private static func replacing(_ node: Any, at path: ArraySlice<String>, with new: Any?) -> Any {
        let head = path.first!
        let last = path.count == 1
        if var object = node as? [String: Any] {
            object[head] = last ? new : replacing(object[head]!, at: path.dropFirst(), with: new)
            return object
        }
        var array = node as! [Any]
        let index = Int(head)!
        array[index] = last ? new! : replacing(array[index], at: path.dropFirst(), with: new)
        return array
    }

    private static func sharedFields(_ a: PlanResponse, _ b: PlanResponse) -> [String] {
        var shared: [String] = []
        if a.route == b.route { shared.append("route") }
        if a.distanceMeters == b.distanceMeters { shared.append("distanceMeters") }
        if a.etaSeconds == b.etaSeconds { shared.append("etaSeconds") }
        if a.fastestEtaSeconds == b.fastestEtaSeconds { shared.append("fastestEtaSeconds") }
        if a.ceilingSeconds == b.ceilingSeconds { shared.append("ceilingSeconds") }
        if a.budgetSeconds == b.budgetSeconds { shared.append("budgetSeconds") }
        if a.lambda == b.lambda { shared.append("lambda") }
        if a.evaluations == b.evaluations { shared.append("evaluations") }
        if a.usedBudget == b.usedBudget { shared.append("usedBudget") }
        if a.etaIsEstimate == b.etaIsEstimate { shared.append("etaIsEstimate") }
        if a.hazards == b.hazards { shared.append("hazards") }
        if a.waypoints == b.waypoints { shared.append("waypoints") }
        if a.appleMapsURL == b.appleMapsURL { shared.append("appleMapsURL") }
        return shared
    }
}
