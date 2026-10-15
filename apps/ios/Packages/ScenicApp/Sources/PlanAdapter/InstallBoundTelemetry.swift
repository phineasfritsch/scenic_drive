import Foundation
import Telemetry

/// LiveTelemetry's client, bound to the install id (T-0356 rv1, P-PRIV-04 R3): the id is read at EACH record and the
/// TelemetryClient is rebuilt when it differs from the one the client was built with, so after a confirmed deletion
/// (which erases the install id) no event later in the same launch carries the deleted id as x-scenic-device. Within
/// one id the one client keeps T-0355 R3's batching and capacity.
actor InstallBoundTelemetry {
    private let base: URL
    private var device: UUID?
    private var client: TelemetryClient?

    init(base: URL) {
        self.base = base
    }

    func record(_ event: TelemetryEvent) async {
        let id = StoredInstallID().installID()
        let current: TelemetryClient
        if let client, device == id {
            current = client
        } else {
            current = TelemetryClient(base: base, device: id, transport: URLSessionTelemetryTransport())
            client = current
            device = id
        }
        await current.record(event)
    }
}
