import Foundation
import ScenicAPIClient
import ScenicKit

/// The tests' one way to drive the shipping entry point, `PlanClient.plan`, against a counting fake, and their
/// one way to read the Worker-recorded replies under Tests/Fixtures/t0251 (T-0251 R7; services/api/test/
/// planWire.test.ts holds the Worker to these same bytes).
enum PlanWire {
    static let directory = URL(fileURLWithPath: #filePath)   // Tests/ScenicAPIClientTests/<this file>
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .appendingPathComponent("Fixtures/t0251")

    static let base = URL(string: "https://scenic-api.test")!
    /// Santa Monica, at 2 dp - the origin T-0248's recording was planned from.
    static let santaMonica = Coordinate(latitude: 34.02, longitude: -118.49)

    static func fixture(_ name: String) throws -> Data {
        try Data(contentsOf: directory.appendingPathComponent("\(name).json"))
    }

    /// The fixture as the Worker sent it: its status is the file name's first three characters.
    static func recordedReply(_ name: String) throws -> PlanHTTPReply {
        PlanHTTPReply(status: Int(name.prefix(3))!, body: try fixture(name))
    }

    /// One plan through a fresh counting fake that answers `reply`: the outcome, and the fake to count.
    static func plan(answering reply: PlanHTTPReply, from origin: Coordinate = santaMonica, to place: Int64 = 42,
                     budgetMinutes: Int = 25, departsAt: Date? = nil)
        async -> (outcome: Result<PlanResponse, PlanError>, fake: CountingPlanTransport) {
        let fake = CountingPlanTransport(reply: reply)
        let outcome = await plan(through: fake, from: origin, to: place, budgetMinutes: budgetMinutes,
                                 departsAt: departsAt)
        return (outcome, fake)
    }

    static func plan(through transport: any PlanTransport, base: URL = base, from origin: Coordinate = santaMonica,
                     to place: Int64 = 42, budgetMinutes: Int = 25, departsAt: Date? = nil)
        async -> Result<PlanResponse, PlanError> {
        let client = PlanClient(base: base, transport: transport)
        do {
            return .success(try await client.plan(from: origin, to: place, budgetMinutes: budgetMinutes,
                                                  departsAt: departsAt))
        } catch {
            return .failure(error)
        }
    }

    /// The error a plan ended in, or nil when it returned a route.
    static func error(_ outcome: Result<PlanResponse, PlanError>) -> PlanError? {
        if case .failure(let error) = outcome { return error }
        return nil
    }
}
