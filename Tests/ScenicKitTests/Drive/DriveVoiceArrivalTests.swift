@testable import ScenicKit
import Foundation
import Testing

/// T-0358 R8: DriveVoice's arrival, read by DriveNavigator into DriveDisplay.arrived - false until the arrival line is
/// said, true from that input on, and false again on a taken reroute's new line.
@Suite("DriveVoiceArrivalTests")
struct DriveVoiceArrivalTests {
    @Test("T-0358 R8: hasArrived after every input of a drive that arrives, rejoins and takes a new line")
    func hasArrivedAlongADrive() throws {
        let line = [DriveVoiceTests.east(0), DriveVoiceTests.east(0.01)]
        var session = try #require(DriveSession(line: line, waypoints: [], lambda: 0.5, online: true))
        var voice = DriveVoice(session: session)
        #expect(voice.hasArrived == false)
        var got: [Bool] = []
        var said: [[String]] = []
        let away = DriveVoiceTests.east(0.0095, north: 0.002)
        let steps: [(inout DriveSession) -> Void] = [
            DriveVoiceTests.at(DriveVoiceTests.east(0.005), 0),
            DriveVoiceTests.at(DriveVoiceTests.east(0.0099), 1),
            DriveVoiceTests.at(DriveVoiceTests.east(0.0095), 2),
            DriveVoiceTests.at(away, 3),
            DriveVoiceTests.at(away, 8),
            { _ = $0.rerouteArrived(line: [away, DriveVoiceTests.east(0.02)], waypoints: []) },
        ]
        for step in steps {
            step(&session)
            said.append(voice.utterances(after: session))
            got.append(voice.hasArrived)
        }
        #expect(said[1] == [DriveVoice.arrivalLine] && session.mode == .guiding && session.line.coordinates.first == away)
        #expect(got == [false, true, true, true, true, false])
    }
}
