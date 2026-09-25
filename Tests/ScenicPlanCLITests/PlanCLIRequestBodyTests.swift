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
