import Foundation
import Network

/// Reachability for the drive (T-0321): each path update, on the main queue, as online or not. Edges are
/// DriveSession's to find; this reports every update, repeats included.
final class DriveConnectivity {
    var onChange: (@MainActor (Bool) -> Void)?
    private let monitor = NWPathMonitor()

    func start() {
        monitor.pathUpdateHandler = { [weak self] path in
            let online = path.status == .satisfied
            MainActor.assumeIsolated { self?.onChange?(online) }
        }
        monitor.start(queue: .main)
    }

    func stop() {
        monitor.cancel()
    }
}
