import Foundation
import ScenicAPIClient
import ScenicKit
import Telemetry

/// The waitlist as the app runs it (T-0360 R2): ScenicAPIClient's WaitlistClient on LivePlanner's https base, the
/// install id, the on-device memory of counted cells, and Telemetry's H3Cell as the cell of the 2-dp start. Nil
/// without an https base: then nothing is sent.
enum LiveWaitlist {
    static func make() -> (any WaitlistJoining)? {
        guard let text = UserDefaults.standard.string(forKey: LivePlanner.baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return nil }
        return WaitlistClient(base: base, transport: URLSessionPlanTransport(), installID: StoredInstallID(),
                              memory: DefaultsWaitlistMemory(),
                              cellOf: { H3Cell.containing(latitudeDegrees: $0, longitudeDegrees: $1)?.hexString })
    }
}
