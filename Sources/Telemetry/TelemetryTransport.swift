import Foundation

/// The client's one network seam (T-0355 R1): send a request, answer its HTTP status or throw. The client reads
/// neither - every outcome drops the batch (R3) - so a transport never needs to read the reply body.
public protocol TelemetryTransport: Sendable {
    func send(_ request: TelemetryRequest) async throws -> Int
}
