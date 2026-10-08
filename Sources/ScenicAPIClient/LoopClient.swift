import Foundation
import ScenicKit

/// POST /loop (T-0314 R1, R2). One request per call and no retries: the body is validated on the device first (a
/// refusal sends nothing), sent once with the install id PlanClient sends, and the reply read once through
/// LoopReplyReader. A transport throw is routingOffline.
public struct LoopClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let installID: (any InstallIDProvider)?

    public init(base: URL, transport: any PlanTransport, installID: (any InstallIDProvider)?) {
        self.base = base
        self.transport = transport
        self.installID = installID
    }

    public func loop(from start: Coordinate, minutes: Int,
                     vehicle: VehicleProfile = .standard) async throws(LoopError) -> LoopResponse {
        guard let installID else { throw .refusedOnDevice(.noInstallID) }
        let body: LoopRequestBody
        switch LoopRequestBody.validated(start: start, minutes: minutes, vehicle: vehicle) {
        case .failure(let refusal):
            throw .refusedOnDevice(refusal)
        case .success(let validated):
            body = validated
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        guard let bytes = try? encoder.encode(body) else { throw .refusedOnDevice(.startOutOfRange) }

        let request = PlanHTTPRequest(url: base.appendingPathComponent("loop"), method: "POST",
                                      headers: ["content-type": "application/json",
                                                "x-scenic-device": installID.installID().uuidString.lowercased()],
                                      body: bytes)
        let reply: PlanHTTPReply
        do {
            reply = try await transport.send(request)
        } catch {
            throw .routingOffline
        }
        switch LoopReplyReader.read(reply) {
        case .success(let loop):
            return loop
        case .failure(let error):
            throw error
        }
    }
}
