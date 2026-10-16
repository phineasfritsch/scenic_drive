@testable import ScenicKit
import Foundation
import Testing

/// T-0366 R1: the handoff marker is set by the homeMoments reporter the shell builds - exactly on the two successful
/// handoff moments - and every moment still reaches the inner reporter unchanged. The device store holds one Int.
@Suite("HandoffMarkingMomentsTests")
struct HandoffMarkingMomentsTests {
    static var everyMoment: [AppMoment] {
        [.planPreviewOnScreen, .driveHandedToAppleMaps, .surpriseHandedToAppleMaps, .guidanceBegan,
         .guidanceEnded(arrived: true, fractionDriven: 1, offRouteCount: 0),
         .guidanceEnded(arrived: false, fractionDriven: 0.25, offRouteCount: 2)]
            + SurpriseFeedback.Reason.allCases.map { AppMoment.surpriseDeclined($0) }
    }

    @Test("T-0366 R1: every moment x a stored marker x an inner reporter or none - the marker after and what the inner heard")
    func everyMomentTable() {
        var got: [String: String] = [:]
        var want: [String: String] = [:]
        for moment in Self.everyMoment {
            for stored in [0, 1, 3, -1] {
                for hasInner in [true, false] {
                    let key = "\(moment) stored=\(stored) inner=\(hasInner)"
                    let marker = MemoryMarker(stored)
                    let inner = RecordingMoments()
                    HandoffMarkingMoments(inner: hasInner ? inner : nil, marker: marker).report(moment)
                    got[key] = "stored=\(marker.value) heard=\(inner.heard)"
                    let handoff = moment == .driveHandedToAppleMaps || moment == .surpriseHandedToAppleMaps
                    want[key] = "stored=\(handoff ? 3 : stored) heard=\(hasInner ? [moment] : [])"
                }
            }
        }
        #expect(got.count == Self.everyMoment.count * 8 && got == want)
    }

    @Test("T-0366 R1: the device store keeps exactly one Int under one key - its whole domain after a handoff and an open")
    @MainActor
    func defaultsDomainIsOneInt() async throws {
        let suite = "t0366-\(UUID().uuidString)"
        let defaults = try #require(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let marker = DefaultsHandoffMarker(suiteName: suite)
        #expect(marker.opensLeft() == 0)
        HandoffMarkingMoments(inner: nil, marker: marker).report(.surpriseHandedToAppleMaps)
        #expect(marker.opensLeft() == 3)
        #expect(defaults.dictionaryRepresentation()[DefaultsHandoffMarker.key] as? Int == 3)
        _ = await PostDriveNextOpen.opened(marker: marker, fix: CountingFix(nil))
        #expect(marker.opensLeft() == 2)
        let domain = defaults.persistentDomain(forName: suite) ?? [:]
        #expect(Set(domain.keys) == ["postDrive.handoffOpensLeft"])
        #expect(domain.compactMapValues { $0 as? Int } == ["postDrive.handoffOpensLeft": 2])
        #expect(DefaultsHandoffMarker.key == "postDrive.handoffOpensLeft")
    }
}

/// Records every moment it is handed.
final class RecordingMoments: AppMomentReporting, @unchecked Sendable {
    private(set) var heard: [AppMoment] = []
    func report(_ moment: AppMoment) { heard.append(moment) }
}
