import Foundation

/// The /telemetry body, exactly `{"events": [point, ...]}` (T-0279 R2): the Worker refuses any other key.
struct TelemetryRequestBody: Encodable {
    let events: [TelemetryDataPoint]

    /// The body's bytes: keys sorted, so a point is blobs, doubles, indexes - the Worker's rebuilt order.
    static func encode(_ events: [TelemetryEvent]) throws -> Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        return try encoder.encode(TelemetryRequestBody(events: events.map(\.dataPoint)))
    }
}
