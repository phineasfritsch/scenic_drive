import Foundation
import Testing
@testable import ScenicKit

/// The Swift port of the Worker's `buildCustomModel` against the Worker's own bytes.
///
/// There are two copies of this function in the repository and there is no compiler between them: the
/// Worker's TypeScript one serves the app, and this Swift one serves `ops/plan`, which has to run where
/// GraphHopper runs without a node toolchain. Two copies of an arithmetic function drift - that is the
/// defect this repository keeps re-filing - so the golden under Tests/Fixtures/custom-model/ is the output
/// node printed from services/api/src/customModel.ts, and these tests hold the port to it BYTE FOR BYTE.
///
/// Not "the same model": the same bytes. GraphHopper takes `multiply_by` as a string, so `"1"` and
/// `"1.000000"` are the same number and different requests, and a key order is a thing a fixture records.
@Suite("Lambda custom model parity")
struct LambdaCustomModelParityTests {

    /// Tests/Fixtures/custom-model, from this file's own path. The fixtures sit outside both test targets
    /// so either can read them; SwiftPM compiles neither.
    static let fixtures = URL(fileURLWithPath: #filePath)   // Tests/ScenicKitTests/<this file>
        .deletingLastPathComponent()                        // Tests/ScenicKitTests
        .deletingLastPathComponent()                        // Tests
        .appendingPathComponent("Fixtures/custom-model")

    static let recorded: [(lambda: Double, file: String)] = [
        (0, "lambda-0.json"), (1, "lambda-1.json"), (2.5, "lambda-2.5.json"),
        (7.75, "lambda-7.75.json"), (8, "lambda-8.json"),
    ]

    static func golden(_ file: String) throws -> String {
        let url = fixtures.appendingPathComponent(file)
        guard let data = FileManager.default.contents(atPath: url.path) else {
            throw PlanFailure.malformedResponse("the golden \(file) is missing at \(url.path)")
        }
        return String(decoding: data, as: UTF8.self)
    }

    @Test("every recorded lambda reproduces the Worker's bytes exactly")
    func bytesMatchTheWorker() throws {
        for (lambda, file) in Self.recorded {
            // The golden carries the trailing newline a committed text file has; the model does not.
            #expect(try LambdaCustomModel.json(for: lambda) + "\n" == Self.golden(file),
                    "lambda \(lambda) does not reproduce \(file)")
        }
    }

    @Test("the model never names a safety gate")
    func theSafetyGatesStayOnTheServer() throws {
        // The property customModel.ts states and rejectCustomModel enforces on the Worker: the per-request
        // model may not mention `road_access` or `surface` ANYWHERE, because a request that can name them
        // is a request that can relax them. Asserted over the serialised text, case-insensitively, at
        // every lambda the bisection can reach - including the bracket ends.
        for tenths in 0...80 {
            let text = try LambdaCustomModel.json(for: Double(tenths) / 10).lowercased()
            #expect(!text.contains("road_access"))
            #expect(!text.contains("surface"))
        }
    }

    @Test("lambda outside the bracket is refused, never clamped")
    func lambdaOutOfRangeIsRefused() throws {
        #expect(throws: PlanFailure.lambdaOutOfRange(8.0001)) { try LambdaCustomModel.json(for: 8.0001) }
        #expect(throws: PlanFailure.lambdaOutOfRange(-0.5)) { try LambdaCustomModel.json(for: -0.5) }
        // NaN is matched by TYPE, not by value: `PlanFailure` is Equatable and NaN != NaN, so an
        // expectation spelled with the payload fails against the very error it asked for.
        #expect(throws: PlanFailure.self) { try LambdaCustomModel.bands(.nan) }
    }

    @Test("multipliers are printed the way JavaScript prints them")
    func multipliersAreTrimmedToSixDecimals() {
        // Number(x.toFixed(6)).toString(): trailing zeros gone, six decimals kept, no locale anywhere.
        #expect(LambdaCustomModel.multiplier(1) == "1")
        #expect(LambdaCustomModel.multiplier(0.2) == "0.2")
        #expect(LambdaCustomModel.multiplier(1.0 / 9) == "0.111111")
        #expect(LambdaCustomModel.multiplier(1.0 / 8.75) == "0.114286")
        #expect(LambdaCustomModel.multiplier(0) == "0")
    }

    @Test("the bands only ever fall, and never below the high band")
    func bandsFallWithLambda() throws {
        var previous = try LambdaCustomModel.bands(0)
        for tenths in 1...80 {
            let band = try LambdaCustomModel.bands(Double(tenths) / 10)
            #expect(band.high == 1)                 // a high-scoring road is never penalised, at any lambda
            #expect(band.mid <= previous.mid)
            #expect(band.low <= previous.low)
            #expect(band.low <= band.mid)           // dull is always penalised at least as hard as middling
            previous = band
        }
    }
}
