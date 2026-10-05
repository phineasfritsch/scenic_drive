import Foundation
import Testing
@testable import ScenicKit

/// The Swift half of the shared retrace fixture (T-0252 R7): Tests/Fixtures/t0252/loops.json is read by this
/// suite AND by services/api/test/retraceParity.test.ts, and both assert the same IEEE-754 bit pattern of the
/// fraction and the same verdict. Two green suites over one file are the proof that the Worker's port and
/// this original agree by exact equality. Points are integer microdegrees, divided by 1e6 here as there.
@Suite("Loop retrace parity")
struct LoopRetraceParityTests {

    struct Fixture: Decodable {
        let loops: [Loop]
    }

    struct Loop: Decodable {
        let name: String
        let fraction_bits: String
        let acceptable: Bool?
        let max_ulps: Int
        let points: [[Int]]
    }

    static let file = URL(fileURLWithPath: #filePath)   // Tests/ScenicKitTests/<this file>
        .deletingLastPathComponent()                    // Tests/ScenicKitTests
        .deletingLastPathComponent()                    // Tests
        .appendingPathComponent("Fixtures/t0252/loops.json")

    static func fixture() throws -> Fixture {
        guard let data = FileManager.default.contents(atPath: file.path) else {
            throw PlanFailure.malformedResponse("the shared fixture is missing at \(file.path)")
        }
        return try JSONDecoder().decode(Fixture.self, from: data)
    }

    static func coordinates(_ loop: Loop) -> [Coordinate] {
        loop.points.map { Coordinate(latitude: Double($0[0]) / 1_000_000, longitude: Double($0[1]) / 1_000_000) }
    }

    static func bits(_ value: Double) -> String {
        let hex = String(value.bitPattern, radix: 16)
        return String(repeating: "0", count: 16 - hex.count) + hex
    }

    /// The distance in ulps between two finite doubles of the same sign, from their bit patterns.
    static func ulps(_ bits: String, _ recorded: String) -> Int {
        guard let a = UInt64(bits, radix: 16), let b = UInt64(recorded, radix: 16) else { return Int.max }
        return a > b ? Int(a - b) : Int(b - a)
    }

    @Test("the shared fixture carries at least five loops, both verdicts among them")
    func theFixtureIsBigEnough() throws {
        let loops = try Self.fixture().loops
        #expect(loops.count >= 5)
        // Five loops with a non-zero fraction are held to EXACT bits; an allowance needs a witnessed libm call.
        #expect(loops.filter { $0.max_ulps == 0 && $0.fraction_bits != String(repeating: "0", count: 16) }.count >= 5)
        #expect(loops.contains { $0.acceptable == true })
        #expect(loops.contains { $0.acceptable == false })
    }

    @Test("every shared loop gives the recorded fraction bits and verdict")
    func everyLoopMatchesTheRecord() throws {
        for loop in try Self.fixture().loops {
            let points = Self.coordinates(loop)
            let fraction = try #require(RetraceDetector.retraceFraction(points), "\(loop.name) has no fraction")
            #expect(Self.ulps(Self.bits(fraction), loop.fraction_bits) <= loop.max_ulps,
                    "\(loop.name): swift fraction \(fraction) bits \(Self.bits(fraction)) acceptable \(RetraceDetector.isAcceptableLoop(points))")
            #expect(RetraceDetector.isAcceptableLoop(points) == loop.acceptable, "\(loop.name): verdict")
        }
    }
}
