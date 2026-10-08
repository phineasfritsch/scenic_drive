import CoreLocation
import FerrostarCore
import FerrostarCoreFFI
import Foundation

/// The location provider Ferrostar is handed (T-0321 R2): CoreLocation's, with every update handed to
/// DriveNavigator BEFORE Ferrostar sees it, so no fix reaches the map without reaching DriveController.
///
/// CoreLocationProvider delivers on the main thread (its CLLocationManager is made there), which is what
/// `MainActor.assumeIsolated` asserts.
final class DriveLocationTap: NSObject, LocationProviding, LocationManagingDelegate {
    weak var delegate: LocationManagingDelegate?
    var onLocations: (@MainActor ([UserLocation]) -> Void)?
    private let inner: LocationProviding

    init(inner: LocationProviding) {
        self.inner = inner
        super.init()
    }

    var authorizationStatus: CLAuthorizationStatus { inner.authorizationStatus }
    var lastLocation: UserLocation? { inner.lastLocation }
    var lastHeading: Heading? { inner.lastHeading }

    func startUpdating() {
        inner.delegate = self
        inner.startUpdating()
    }

    func stopUpdating() {
        inner.stopUpdating()
        inner.delegate = nil
    }

    func locationManager(_ manager: LocationProviding, didUpdateLocations locations: [UserLocation]) {
        if let onLocations {
            MainActor.assumeIsolated { onLocations(locations) }
        }
        delegate?.locationManager(self, didUpdateLocations: locations)
    }

    func locationManager(_ manager: LocationProviding, didUpdateHeading newHeading: Heading) {
        delegate?.locationManager(self, didUpdateHeading: newHeading)
    }

    func locationManager(_ manager: LocationProviding, didFailWithError error: Error) {
        delegate?.locationManager(self, didFailWithError: error)
    }
}
