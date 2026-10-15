import Foundation
import ScenicKit

/// The app's client for the Worker's POST /waitlist (T-0360): "count this area" from a start outside the served region.
///
/// R2: the body is exactly `{"cell":"<cell>"}`, the H3 resolution-5 cell `cellOf` names for the start ROUNDED TO 2
/// DECIMALS - `cellOf` is Telemetry's H3Cell in the app, injected because this target does not depend on Telemetry.
/// No coordinate leaves the device. The headers are exactly the JSON content type and `x-scenic-device`, the Worker's
/// dedupe bucket. A start that is not finite or is outside [-90, 90] x [-180, 180] (checked before rounding), or a
/// cell that is not fifteen lowercase hex digits (h3Res5.ts's first test), is refused with zero requests.
/// R3: a cell this install already counted answers `alreadyJoined` with zero requests; only a 200 {"waitlisted":true}
/// is remembered. One call is at most one request - nothing is retried.
public struct WaitlistClient: WaitlistJoining {
    public let base: URL
    let transport: any PlanTransport
    let installID: any InstallIDProvider
    let memory: any WaitlistMemory
    let cellOf: @Sendable (Double, Double) -> String?

    public init(base: URL, transport: any PlanTransport, installID: any InstallIDProvider,
                memory: any WaitlistMemory, cellOf: @escaping @Sendable (Double, Double) -> String?) {
        self.base = base
        self.transport = transport
        self.installID = installID
        self.memory = memory
        self.cellOf = cellOf
    }

    public func joinWaitlist(near start: Coordinate) async -> WaitlistAnswer {
        guard start.latitude >= -90, start.latitude <= 90, start.longitude >= -180, start.longitude <= 180 else {
            return .refusedOnDevice
        }
        guard let cell = cellOf(Self.twoDecimals(start.latitude), Self.twoDecimals(start.longitude)),
              Self.isCellText(cell) else { return .refusedOnDevice }
        if memory.hasJoined(cell) { return .alreadyJoined }
        let request = PlanHTTPRequest(url: base.appendingPathComponent("waitlist"), method: "POST",
                                      headers: ["content-type": "application/json",
                                                IdentityHeaders.deviceHeader:
                                                    installID.installID().uuidString.lowercased()],
                                      body: Data("{\"cell\":\"\(cell)\"}".utf8))
        let answer: WaitlistAnswer
        do {
            answer = WaitlistReplyReader.read(try await transport.send(request))
        } catch {
            return .offline
        }
        if answer == .joined { memory.rememberJoined(cell) }
        return answer
    }

    /// The 2-decimal value of `degrees`, half away from zero (R2). NaN never reaches here: the range guard refuses it.
    static func twoDecimals(_ degrees: Double) -> Double {
        (degrees * 100).rounded() / 100
    }

    /// Fifteen digits, each 0-9 or a-f: what h3Res5.ts HEX15 admits.
    static func isCellText(_ cell: String) -> Bool {
        let hex = Array(cell.utf8)
        return hex.count == 15 && hex.allSatisfy { (48...57).contains($0) || (97...102).contains($0) }
    }
}
