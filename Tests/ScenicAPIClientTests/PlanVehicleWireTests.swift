import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0311 R6/R7: the plan request carries the vehicle profile. Every case drives `PlanClient.plan`, the entry point
/// the app calls, through a counting fake, and compares what reached the transport whole against a body recomputed
/// here from the same inputs. A disabled profile is refused on the device with zero requests.
@Suite struct PlanVehicleWireTests {
    /// The Worker's table in services/api/test/vehicleWire.test.ts (WIRE_VALUES, ENABLED), as literals.
    static let wireValues = ["standard", "lowClearance", "motorcycle", "trailer", "rv"]
    static let enabled = ["standard"]

    /// The /plan body for these inputs, spelled out: sorted keys, the place as a string, the profile's raw value.
    static func recomputed(budget: Int, place: Int64, lat: String, lon: String, vehicle: String) -> String {
        "{\"budget_minutes\":\(budget),\"destination\":{\"place\":\"\(place)\"},"
            + "\"origin\":{\"lat\":\(lat),\"lon\":\(lon)},\"vehicle\":\"\(vehicle)\"}"
    }

    /// One plan of `profile`: the bodies the transport received, and the device refusal if the client made one.
    static func send(_ profile: VehicleProfile, budget: Int, place: Int64) async -> ([String], PlanRefusal?) {
        let fake = CountingPlanTransport(reply: PlanHTTPReply(status: 200, body: Data()))
        let client = PlanClient(base: PlanWire.base, transport: fake, installID: PlanWire.install, accountToken: nil)
        var refusal: PlanRefusal?
        do {
            _ = try await client.plan(from: PlanWire.santaMonica, to: place, budgetMinutes: budget, vehicle: profile)
        } catch {
            if case .refusedOnDevice(let why) = error { refusal = why }
        }
        let bodies = await fake.requests.map { String(decoding: $0.body, as: UTF8.self) }
        return (bodies, refusal)
    }

    @Test("the wire values are VehicleProfile's raw values in case order, and only standard is enabled")
    func wireValuesAreTheWorkerTable() {
        #expect(VehicleProfile.allCases.map(\.rawValue) == Self.wireValues)
        #expect(VehicleProfile.allCases.filter(\.isEnabled).map(\.rawValue) == Self.enabled)
    }

    @Test("every profile: an enabled one is sent as its raw value, the body equal to its recomputation; a disabled one is refused with zero requests")
    func everyProfileWhole() async {
        for (budget, place) in [(25, Int64(42)), (0, Int64(1_234_567_890_123)), (180, Int64(7))] {
            var seen: [String] = []
            var expected: [String] = []
            for profile in VehicleProfile.allCases {
                let (bodies, refusal) = await Self.send(profile, budget: budget, place: place)
                seen.append("\(profile.rawValue) \(bodies) \(String(describing: refusal))")
                let wanted = Self.enabled.contains(profile.rawValue)
                    ? [Self.recomputed(budget: budget, place: place, lat: "34.02", lon: "-118.49",
                                       vehicle: profile.rawValue)]
                    : []
                let why: PlanRefusal? = wanted.isEmpty ? .vehicleNotEnabled : nil
                expected.append("\(profile.rawValue) \(wanted) \(String(describing: why))")
            }
            #expect(seen == expected)
        }
    }

    @Test("a plan that names no vehicle is sent as standard")
    func defaultIsStandard() async throws {
        let fake = CountingPlanTransport(reply: PlanHTTPReply(status: 200, body: Data()))
        let client = PlanClient(base: PlanWire.base, transport: fake, installID: PlanWire.install, accountToken: nil)
        _ = try? await client.plan(from: PlanWire.santaMonica, to: 42, budgetMinutes: 25)
        let bodies = await fake.requests.map { String(decoding: $0.body, as: UTF8.self) }
        #expect(bodies == [Self.recomputed(budget: 25, place: 42, lat: "34.02", lon: "-118.49", vehicle: "standard")])
    }
}
