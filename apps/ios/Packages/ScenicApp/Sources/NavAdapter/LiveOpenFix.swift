import CoreLocation
import Foundation
import ScenicKit

/// The app-open fix after a handoff (T-0366 R3): one `requestLocation()` on a CLLocationManager of its own, and only
/// when When In Use or Always is already granted (an in-app drive asked for it). It never asks for a permission: any
/// other status is no fix, and no fix is moving. The reading becomes a PostDriveFix and is dropped by ScenicKit.
///
/// Made on the main thread (the shell's state), so CoreLocation calls the delegate there, which `assumeIsolated`
/// asserts; every waiter is resumed exactly once, by the one answer to the one request in flight.
public final class LiveOpenFix: NSObject, OpenFixReading, CLLocationManagerDelegate, @unchecked Sendable {
    private let manager = CLLocationManager()
    private var waiting: [CheckedContinuation<PostDriveFix?, Never>] = []

    public override init() {
        super.init()
        manager.delegate = self
    }

    @MainActor
    public func read() async -> PostDriveFix? {
        switch manager.authorizationStatus {
        case .authorizedWhenInUse, .authorizedAlways:
            break
        case .notDetermined, .restricted, .denied:
            return nil
        @unknown default:
            return nil
        }
        return await withCheckedContinuation { continuation in
            waiting.append(continuation)
            if waiting.count == 1 { manager.requestLocation() }
        }
    }

    public func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        let fix = locations.last.map {
            PostDriveFix(speedMetersPerSecond: $0.speed, speedAccuracy: $0.speedAccuracy,
                         ageSeconds: -$0.timestamp.timeIntervalSinceNow)
        }
        MainActor.assumeIsolated { finish(fix) }
    }

    public func locationManager(_ manager: CLLocationManager, didFailWithError error: any Error) {
        MainActor.assumeIsolated { finish(nil) }
    }

    @MainActor
    private func finish(_ fix: PostDriveFix?) {
        let done = waiting
        waiting = []
        for continuation in done { continuation.resume(returning: fix) }
    }
}
