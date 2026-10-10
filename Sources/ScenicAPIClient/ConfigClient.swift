import Foundation
import ScenicKit

/// The app's client for the Worker's GET /config (T-0357): one request, no headers and no body - the Worker's handler
/// reads no request, so nothing identifying the device is sent (R3) - and the answer through ConfigReader, or nil.
/// Nothing is retried; a transport that throws (no reply at all) is nil.
public struct ConfigClient: Sendable {
    public let base: URL
    let transport: any PlanTransport

    public init(base: URL, transport: any PlanTransport) {
        self.base = base
        self.transport = transport
    }

    public func fetch() async -> RemoteConfig? {
        let request = PlanHTTPRequest(url: base.appendingPathComponent("config"), method: "GET", headers: [:],
                                      body: Data())
        guard let reply = try? await transport.send(request) else { return nil }
        return ConfigReader.read(reply)
    }
}
