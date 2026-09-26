import Foundation
import Testing
import ScenicKit
@testable import ScenicPlanCLI

/// The bytes that go on the wire, and the refusal that stands in front of them.
///
/// GraphHopperRouteSource's own doc comment claimed "what IS tested here is the request BODY"; T-0182's
/// pre-review pass found `body(_:_:profile:model:)` was called by no test at all, and the safety property
/// was asserted one level down, over `LambdaCustomModel`'s output. That is a true statement about the
/// MODEL and an unsupported one about the REQUEST: the body is assembled here, and what is assembled here
/// is what a GraphHopper would act on.
///
/// Two things are asserted, in the two places they can go wrong:
///   1. the body names neither `road_access` nor `surface` at any lambda the bisection can reach, and the
///      model it embeds is `LambdaCustomModel`'s bytes exactly - not a re-serialisation of them;
///   2. `send` REFUSES a body that names one, before a socket is opened. The base URL below is a port
///      nothing listens on: without the refusal the failure is `routerRefused`, with it the failure is
///      `modelTouchesSafetyGate` and no request was attempted.
@Suite("ops/plan request body")
struct PlanCLIRequestBodyTests {

    /// Port 9 is discard, and nothing on this box listens there: a request that gets past the refusal
    /// fails LOUDLY and differently, which is what makes the second test a test of the refusal.
    /// Computed, not stored: the transport holds a `URLSession`'s worth of the world and is deliberately
    /// not `Sendable`, so a `static let` of it would be shared mutable state under Swift 6.
    static var source: GraphHopperRouteSource {
        GraphHopperRouteSource(baseURL: URL(string: "http://127.0.0.1:9")!, timeout: 2)
    }
    static let origin = Coordinate(latitude: 34.0944, longitude: -118.6013)
    static let destination = Coordinate(latitude: 34.0365, longitude: -118.6870)

    /// T-0244 round 2 B1-points: `origin` and `destination` above, TYPED OUT rather than read back through them -
    /// GraphHopper's `points` is origin first, each pair [longitude, latitude].
    static let typedPoints: [[Double]] = [[-118.6013, 34.0944], [-118.687, 34.0365]]

    /// The `points` array of a decoded request, as numbers; nil if it is missing or not an array of pairs.
    static func points(_ request: [String: Any]) -> [[Double]]? {
        guard let pairs = request["points"] as? [Any] else { return nil }
        var decoded: [[Double]] = []
        for pair in pairs {
            guard let values = pair as? [Any] else { return nil }
            let numbers = values.compactMap { ($0 as? NSNumber)?.doubleValue }
            guard numbers.count == values.count else { return nil }
            decoded.append(numbers)
        }
        return decoded
    }

    /// The body `send` would have put on the wire, caught at the transport seam.
    static func sentRequest(_ call: (GraphHopperRouteSource) throws -> RoutePath) throws -> [String: Any] {
        var source = Self.source
        source.post = { body in throw PlanFailure.routerRefused(body) }
        var sent: String?
        do {
            _ = try call(source)
        } catch PlanFailure.routerRefused(let body) {
            sent = body
        }
        let body = try #require(sent, "the entry point reached no transport")
        return try #require(try JSONSerialization.jsonObject(with: Data(body.utf8)) as? [String: Any])
    }

    @Test("the bytes on the wire never name a safety gate, at any lambda")
    func theRequestBodyNeverNamesASafetyGate() throws {
        for tenths in 0...80 {
            let model = try LambdaCustomModel.json(for: Double(tenths) / 10)
            let body = Self.source.body(Self.origin, Self.destination,
                                        profile: "car_scenic", model: model).lowercased()
            #expect(!body.contains("road_access"))
            #expect(!body.contains("surface"))
        }
    }

    @Test("the model the body embeds is LambdaCustomModel's own bytes")
    func theBodyEmbedsTheModelVerbatim() throws {
        let model = try LambdaCustomModel.json(for: 7.75)
        let body = Self.source.body(Self.origin, Self.destination, profile: "car_scenic", model: model)

        // The body indents the model by two spaces per line to sit inside the request object; undo that
        // and what is left must be the model, byte for byte, plus the request's own closing brace.
        let marker = "  \"custom_model\": "
        let inserted = try #require(body.range(of: marker))
        let embedded = String(body[inserted.upperBound...])
            .replacingOccurrences(of: "\n  ", with: "\n")
        #expect(embedded == model + "\n}")

        // And the fastest request carries no model at all - the fast profile is not the scenic one.
        let fastest = Self.source.body(Self.origin, Self.destination, profile: "car_fast", model: nil)
        #expect(!fastest.contains("custom_model"))
    }

    /// T-0244 pre-review B1: ruling (b) - distance_influence 0, so T(lambda) is non-decreasing - held on the
    /// request ops/plan SENDS, not on a model this test builds itself. `scenic` is driven through the transport
    /// seam, which hands the body back inside the error, at every lambda step of 0.1 in the bracket.
    @Test("scenic(from:to:lambda:) sends distance_influence 0 and LambdaCustomModel.json(for: lambda), at every step")
    func theScenicRequestCarriesTheLambdaModelWithDistanceInfluenceZero() throws {
        var source = Self.source
        source.post = { body in throw PlanFailure.routerRefused(body) }
        for tenths in 0...80 {
            let lambda = Double(tenths) / 10
            var sent: String?
            do {
                _ = try source.scenic(from: Self.origin, to: Self.destination, lambda: lambda)
            } catch PlanFailure.routerRefused(let body) {
                sent = body
            }
            let body = try #require(sent, "scenic() at lambda \(lambda) reached no transport")
            let request = try #require(try JSONSerialization.jsonObject(with: Data(body.utf8)) as? [String: Any])
            #expect(request["profile"] as? String == "car_scenic", "lambda \(lambda)")
            #expect(Self.points(request) == Self.typedPoints, "lambda \(lambda)")
            let model = try #require(request["custom_model"] as? [String: Any], "lambda \(lambda)")
            #expect((model["distance_influence"] as? NSNumber)?.doubleValue == 0, "lambda \(lambda)")
            let inserted = try #require(body.range(of: "  \"custom_model\": "))
            let embedded = String(body[inserted.upperBound...]).replacingOccurrences(of: "\n  ", with: "\n")
            #expect(embedded == (try LambdaCustomModel.json(for: lambda)) + "\n}", "lambda \(lambda)")
        }
    }

    /// T-0244 round 1 B1 (P-SAFE-04): the ceiling is fastest.duration + budget, so the fastest request is the
    /// baseline the budget is a ceiling OVER. A fastest() that asked for the scenic profile, or carried a
    /// per-request model, would raise that baseline and let a route past fastest + budget through. Driven
    /// through the transport seam: the typed-out fast profile, a whitelist of keys, and no model at all.
    @Test("fastest(from:to:) sends car_fast with no custom_model and no distance_influence")
    func theFastestRequestIsTheBareFastProfile() throws {
        var source = Self.source
        source.post = { body in throw PlanFailure.routerRefused(body) }
        var sent: String?
        do {
            _ = try source.fastest(from: Self.origin, to: Self.destination)
        } catch PlanFailure.routerRefused(let body) {
            sent = body
        }
        let body = try #require(sent, "fastest() reached no transport")
        let request = try #require(try JSONSerialization.jsonObject(with: Data(body.utf8)) as? [String: Any])
        #expect(request["profile"] as? String == "car_fast")
        #expect(Set(request.keys) == ["points", "profile", "points_encoded", "instructions", "ch.disable", "details"])
        #expect(!body.contains("custom_model"))
        #expect(!body.contains("distance_influence"))
        // Round 2 B1-points: the KEY was checked and its VALUE was not - a baseline routed destination -> origin
        // is a different fastest duration, hence a different ceiling. Origin first, [lon, lat], typed out.
        #expect(Self.points(request) == Self.typedPoints)
    }

    /// T-0244 round 2 B1-points (P-SAFE-04): the budget is a ceiling over fastest(from:to:) only if scenic()
    /// asks for the SAME trip. Both shipping entry points, driven through the transport seam, must send one
    /// `points` array - the typed origin-first pairs, in that order.
    @Test("fastest(from:to:) and scenic(from:to:lambda:) send the same points, origin first")
    func fastestAndScenicSendTheSameTripOriginFirst() throws {
        let fastest = try Self.sentRequest { try $0.fastest(from: Self.origin, to: Self.destination) }
        let scenic = try Self.sentRequest { try $0.scenic(from: Self.origin, to: Self.destination, lambda: 4) }
        let fastestPoints = try #require(Self.points(fastest), "fastest() sent no points array")
        let scenicPoints = try #require(Self.points(scenic), "scenic() sent no points array")
        #expect(fastestPoints == scenicPoints)
        #expect(fastestPoints == Self.typedPoints)
        #expect(scenicPoints == Self.typedPoints)
    }

    @Test("a body naming a safety gate is refused before any request is sent")
    func aBodyNamingASafetyGateIsRefusedBeforeSending() throws {
        let relaxed = """
        {
          "priority": [
            { "if": "road_access == PRIVATE", "multiply_by": "1" }
          ]
        }
        """
        let poisoned = Self.source.body(Self.origin, Self.destination,
                                        profile: "car_scenic", model: relaxed)
        #expect(throws: PlanFailure.modelTouchesSafetyGate("road_access")) {
            try Self.source.send(poisoned)
        }

        let unpaved = Self.source.body(Self.origin, Self.destination, profile: "car_scenic",
                                       model: "{ \"priority\": [{ \"if\": \"surface == DIRT\" }] }")
        #expect(throws: PlanFailure.modelTouchesSafetyGate("surface")) {
            try Self.source.send(unpaved)
        }
    }
}
