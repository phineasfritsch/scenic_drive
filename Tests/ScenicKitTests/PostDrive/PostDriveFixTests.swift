@testable import ScenicKit
import Foundation
import Testing

/// T-0366 R3: the one-shot fix's surface - every bound of the speed, its accuracy and the fix's age, the whole cross
/// product through the shipping `PostDriveFix.surface`, with the expected surface typed here per input.
@Suite("PostDriveFixTests")
struct PostDriveFixTests {
    static let speeds: [Double] = [-1, (0.0).nextDown, -0.0, 0, 4.5, (4.5).nextUp, 30, .nan, .infinity, -.infinity]
    static let accuracies: [Double] = [-1, (0.0).nextDown, 0, 1, 1e9, .nan, .infinity]
    static let ages: [Double] = [-1, (0.0).nextDown, 0, 10, (10.0).nextUp, 3600, .nan, .infinity]

    /// Typed: a speed is known only with a finite, non-negative accuracy; a fix is fresh only at an age in [0, 10] s;
    /// only a known, fresh speed in [0, 4.5] m/s is the full surface. Everything else is moving (P-SAFE-09).
    static func full(speed: Double, accuracy: Double, age: Double) -> Bool {
        let known = accuracy >= 0 && accuracy < .infinity
        let fresh = age >= 0 && age <= 10
        let slow = speed >= 0 && speed <= 4.5
        return known && fresh && slow
    }

    @Test("T-0366 R3: every speed x accuracy x age bound - full exactly on the typed rows, else minimal")
    func everyBound() {
        var got: [String: DriveSurface] = [:]
        var want: [String: DriveSurface] = [:]
        for speed in Self.speeds {
            for accuracy in Self.accuracies {
                for age in Self.ages {
                    let key = "speed=\(speed.bitPattern) accuracy=\(accuracy.bitPattern) age=\(age.bitPattern)"
                    got[key] = PostDriveFix(speedMetersPerSecond: speed, speedAccuracy: accuracy, ageSeconds: age).surface
                    want[key] = Self.full(speed: speed, accuracy: accuracy, age: age) ? .full : .minimal
                }
            }
        }
        #expect(got.count == Self.speeds.count * Self.accuracies.count * Self.ages.count)
        #expect(got == want)
        #expect(want.values.contains(.full) && want.values.contains(.minimal))
        #expect(PostDriveFix.maxAgeSeconds == 10)
    }

    @Test("T-0366 R3: no input is ignored - each of speed, accuracy and age flips some row")
    func noInputIgnored() {
        func surface(_ s: Double, _ a: Double, _ g: Double) -> DriveSurface {
            PostDriveFix(speedMetersPerSecond: s, speedAccuracy: a, ageSeconds: g).surface
        }
        #expect(surface(0, 1, 0) == .full)
        #expect(surface((4.5).nextUp, 1, 0) == .minimal)
        #expect(surface(0, (0.0).nextDown, 0) == .minimal)
        #expect(surface(0, 1, (10.0).nextUp) == .minimal)
        #expect(surface(0, 1, (0.0).nextDown) == .minimal)
    }
}
