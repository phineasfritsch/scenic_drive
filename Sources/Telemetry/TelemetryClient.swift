import Foundation

/// The device's POST /telemetry (T-0355). It takes only a `TelemetryEvent`, so nothing but the closed enum's coarse
/// payload can be sent (P-PRIV-05), and it is fail-quiet (R3): `record` never throws, at most `capacity` events wait
/// behind a post in flight (one more is dropped), each post carries everything waiting, and whatever a post's
/// outcome - a thrown error or any status - that batch is gone: no retry, nothing kept on the device.
public actor TelemetryClient {
    /// The Worker's MAX_TELEMETRY_EVENTS_PER_REQUEST: a batch is never one the Worker refuses for its size.
    public static let capacity = 20

    private let url: URL
    private let headers: [String: String]
    private let transport: any TelemetryTransport
    private var waiting: [TelemetryEvent] = []
    private var isSending = false

    public init(base: URL, device: UUID, transport: any TelemetryTransport) {
        url = base.appendingPathComponent("telemetry")
        headers = ["content-type": "application/json", "x-scenic-device": device.uuidString.lowercased()]
        self.transport = transport
    }

    /// Queue `event` and, unless a post is already in flight, post until nothing waits. Returns when this call's
    /// posts are done; a caller that must not wait hands it to a Task.
    public func record(_ event: TelemetryEvent) async {
        guard waiting.count < Self.capacity else { return }
        waiting.append(event)
        guard !isSending else { return }
        isSending = true
        while !waiting.isEmpty {
            let batch = waiting
            waiting = []
            guard let body = try? TelemetryRequestBody.encode(batch) else { continue }
            _ = try? await transport.send(TelemetryRequest(url: url, method: "POST", headers: headers, body: body))
        }
        isSending = false
    }
}
