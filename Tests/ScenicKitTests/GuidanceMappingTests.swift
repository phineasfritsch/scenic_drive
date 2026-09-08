import Foundation
import Testing
@testable import ScenicKit

/// Two separate claims are tested here and they must not be allowed to prove each other.
///
///   1. the INTEGERS are the ones GraphHopper 11.0 declares, and
///   2. each integer produces the manoeuvre a driver should be given.
///
/// So the expected values below are written out as LITERALS, transcribed from
/// `web-api/src/main/java/com/graphhopper/util/Instruction.java` at tag 11.0 (commit 69e50f6e, blob 1638c71b).
/// Nothing here reads `GuidanceSign.rawValue` to decide what `rawValue` should be, and nothing loops over
/// `allCases` comparing the mapping to itself. This repository has shipped that defect eleven times in one
/// session, four of them inside tests written to close a previous instance.
@Suite("Guidance sign mapping")
struct GuidanceMappingTests {

    // MARK: - the integers, transcribed from upstream

    @Test("every sign carries the integer GraphHopper 11.0 declares")
    func rawValuesMatchUpstream() {
        #expect(GuidanceSign.unknown.rawValue == -99)
        #expect(GuidanceSign.uTurnUnknown.rawValue == -98)
        #expect(GuidanceSign.uTurnLeft.rawValue == -8)
        #expect(GuidanceSign.keepLeft.rawValue == -7)
        #expect(GuidanceSign.leaveRoundabout.rawValue == -6)
        #expect(GuidanceSign.turnSharpLeft.rawValue == -3)
        #expect(GuidanceSign.turnLeft.rawValue == -2)
        #expect(GuidanceSign.turnSlightLeft.rawValue == -1)
        #expect(GuidanceSign.continueOnStreet.rawValue == 0)
        #expect(GuidanceSign.turnSlightRight.rawValue == 1)
        #expect(GuidanceSign.turnRight.rawValue == 2)
        #expect(GuidanceSign.turnSharpRight.rawValue == 3)
        #expect(GuidanceSign.finish.rawValue == 4)
        #expect(GuidanceSign.reachedVia.rawValue == 5)
        #expect(GuidanceSign.useRoundabout.rawValue == 6)
        #expect(GuidanceSign.keepRight.rawValue == 7)
        #expect(GuidanceSign.uTurnRight.rawValue == 8)
        #expect(GuidanceSign.ferry.rawValue == 9)
        #expect(GuidanceSign.ptStartTrip.rawValue == 101)
        #expect(GuidanceSign.ptTransfer.rawValue == 102)
        #expect(GuidanceSign.ptEndTrip.rawValue == 103)
    }

    @Test("IGNORE is Java's Integer.MIN_VALUE, not a mistyped ten-digit literal")
    func ignoreIsJavaIntMin() {
        // Upstream writes `Integer.MIN_VALUE`; Swift will not accept that as a raw value, so the source carries
        // the digits. Checked against Int32.min rather than by re-typing the same number a second time - a
        // second transcription of a ten-digit literal would repeat the typo it is meant to catch.
        #expect(GuidanceSign.ignore.rawValue == Int(Int32.min))
        #expect(GuidanceSign.ignore.rawValue != Int.min, "Java's int is 32-bit; Int.min is a different number")
    }

    @Test("the sign set is exactly the 22 constants upstream declares")
    func signCount() {
        #expect(GuidanceSign.allCases.count == 22)
    }

    // MARK: - the gaps, which are the reason a range check is not a validity check

    @Test("-4 and -5 are not signs, even though they sit inside the declared range")
    func gapsInTheSignSpace() {
        // GraphHopper 11.0 declares -8, -7, -6 and then jumps to -3. Anything that decided a sign was valid
        // because it fell between the extremes would accept these.
        #expect(GuidanceSign(rawValue: -4) == nil)
        #expect(GuidanceSign(rawValue: -5) == nil)
        #expect(throws: GuidanceDecodingError.unrecognisedSign(-4)) {
            _ = try GuidanceMapping.maneuver(forRawSign: -4)
        }
        #expect(throws: GuidanceDecodingError.unrecognisedSign(-5)) {
            _ = try GuidanceMapping.maneuver(forRawSign: -5)
        }
    }

    @Test("an unrecognised sign throws and carries the raw value; it never becomes 'carry straight on'")
    func unknownSignThrows() {
        // The failure this whole type exists to prevent: a code nobody mapped arriving at a junction as
        // silence. 10 is the next integer after ferry=9 and is the shape a new GraphHopper release takes.
        #expect(throws: GuidanceDecodingError.unrecognisedSign(10)) {
            _ = try GuidanceMapping.maneuver(forRawSign: 10)
        }
        #expect(throws: GuidanceDecodingError.unrecognisedSign(-100)) {
            _ = try GuidanceMapping.maneuver(forRawSign: -100)
        }
        #expect(throws: GuidanceDecodingError.unrecognisedSign(104)) {
            _ = try GuidanceMapping.maneuver(forRawSign: 104)
        }
    }

    // MARK: - the mapping, one written-out expectation per sign

    @Test("turns keep their side and their sharpness as separate, correct axes")
    func turnsMapExactly() {
        #expect(GuidanceMapping.maneuver(for: .turnSlightLeft)  == .turn(side: .left,  sharpness: .slight))
        #expect(GuidanceMapping.maneuver(for: .turnLeft)        == .turn(side: .left,  sharpness: .normal))
        #expect(GuidanceMapping.maneuver(for: .turnSharpLeft)   == .turn(side: .left,  sharpness: .sharp))
        #expect(GuidanceMapping.maneuver(for: .turnSlightRight) == .turn(side: .right, sharpness: .slight))
        #expect(GuidanceMapping.maneuver(for: .turnRight)       == .turn(side: .right, sharpness: .normal))
        #expect(GuidanceMapping.maneuver(for: .turnSharpRight)  == .turn(side: .right, sharpness: .sharp))
    }

    @Test("left is never right: the six turns are six distinct manoeuvres")
    func turnsAreNotAliased() {
        // A mapping that collapsed sharpness, or swapped a side, would still pass a test that only asserted
        // "it is a turn". Written out as an explicit inequality set rather than as a Set count, so a failure
        // names the pair that collided.
        let sharpL = GuidanceMapping.maneuver(for: .turnSharpLeft)
        let normL = GuidanceMapping.maneuver(for: .turnLeft)
        let slightL = GuidanceMapping.maneuver(for: .turnSlightLeft)
        let sharpR = GuidanceMapping.maneuver(for: .turnSharpRight)
        let normR = GuidanceMapping.maneuver(for: .turnRight)
        let slightR = GuidanceMapping.maneuver(for: .turnSlightRight)
        #expect(sharpL != normL)
        #expect(normL != slightL)
        #expect(sharpL != slightL)
        #expect(sharpR != normR)
        #expect(normR != slightR)
        #expect(sharpR != slightR)
        #expect(normL != normR, "a left turn and a right turn must never be the same instruction")
        #expect(sharpL != sharpR)
        #expect(slightL != slightR)
    }

    @Test("keep-left and keep-right are forks, not turns")
    func keepsMapExactly() {
        #expect(GuidanceMapping.maneuver(for: .keepLeft)  == .keep(side: .left))
        #expect(GuidanceMapping.maneuver(for: .keepRight) == .keep(side: .right))
        #expect(GuidanceMapping.maneuver(for: .keepLeft)  != .turn(side: .left, sharpness: .slight))
    }

    @Test("a U-turn of unknown side says nothing about the side rather than guessing one")
    func uTurnsMapExactly() {
        #expect(GuidanceMapping.maneuver(for: .uTurnLeft)    == .uTurn(side: .left))
        #expect(GuidanceMapping.maneuver(for: .uTurnRight)   == .uTurn(side: .right))
        #expect(GuidanceMapping.maneuver(for: .uTurnUnknown) == .uTurn(side: nil))
        // Putting a wrong word in a driver's ear is worse than putting none there.
        #expect(GuidanceMapping.maneuver(for: .uTurnUnknown) != .uTurn(side: .left))
        #expect(GuidanceMapping.maneuver(for: .uTurnUnknown) != .uTurn(side: .right))
    }

    @Test("roundabouts, ferries and route events map to their own manoeuvres")
    func routeEventsMapExactly() {
        #expect(GuidanceMapping.maneuver(for: .useRoundabout)   == .enterRoundabout)
        #expect(GuidanceMapping.maneuver(for: .leaveRoundabout) == .exitRoundabout)
        #expect(GuidanceMapping.maneuver(for: .ferry)           == .ferry)
        #expect(GuidanceMapping.maneuver(for: .reachedVia)      == .reachedWaypoint)
        #expect(GuidanceMapping.maneuver(for: .finish)          == .arrive)
        #expect(GuidanceMapping.maneuver(for: .continueOnStreet) == .continueStraight)
    }

    @Test("entering and leaving a roundabout are not the same instruction")
    func roundaboutDirectionsAreDistinct() {
        #expect(GuidanceMapping.maneuver(for: .useRoundabout) != GuidanceMapping.maneuver(for: .leaveRoundabout))
    }

    @Test("the router's own UNKNOWN is honest information, not a decode failure")
    func routerUnknownIsNotAnError() {
        // GraphHopper saying "I do not know" and this build failing to recognise an integer are different
        // facts, and collapsing them would hide the second behind the first.
        #expect(GuidanceMapping.maneuver(for: .unknown) == .routerSaidUnknown)
        #expect(GuidanceMapping.maneuver(for: .unknown) != .continueStraight)
        #expect(GuidanceMapping.maneuver(for: .ignore)  == .ignore)
        #expect(GuidanceMapping.maneuver(for: .ignore)  != .routerSaidUnknown)
    }

    @Test("a transit leg is recognised and refused, never folded into 'carry straight on'")
    func transitLegsAreExplicit() {
        #expect(GuidanceMapping.maneuver(for: .ptStartTrip) == .notApplicableToDriving)
        #expect(GuidanceMapping.maneuver(for: .ptTransfer)  == .notApplicableToDriving)
        #expect(GuidanceMapping.maneuver(for: .ptEndTrip)   == .notApplicableToDriving)
        #expect(GuidanceMapping.maneuver(for: .ptStartTrip) != .continueStraight,
                "telling a driver to carry on where the router boarded a train is the failure to avoid")
    }

    // MARK: - the raw decode path agrees with the typed one

    @Test("decoding an integer gives the same manoeuvre as the typed sign, on a spot check")
    func rawDecodeAgrees() throws {
        // Spot-checked against LITERAL integers, not against GuidanceSign.rawValue - reading the raw value to
        // build the input would make this test pass for any integers at all.
        #expect(try GuidanceMapping.maneuver(forRawSign: -2) == .turn(side: .left, sharpness: .normal))
        #expect(try GuidanceMapping.maneuver(forRawSign: 2)  == .turn(side: .right, sharpness: .normal))
        #expect(try GuidanceMapping.maneuver(forRawSign: 0)  == .continueStraight)
        #expect(try GuidanceMapping.maneuver(forRawSign: 4)  == .arrive)
        #expect(try GuidanceMapping.maneuver(forRawSign: 6)  == .enterRoundabout)
        #expect(try GuidanceMapping.maneuver(forRawSign: 9)  == .ferry)
        #expect(try GuidanceMapping.maneuver(forRawSign: -99) == .routerSaidUnknown)
    }

    // MARK: - provenance is a value, not a comment

    @Test("the table records which upstream artifact it was read from")
    func provenanceIsPinned() {
        // CLAUDE.md: never anchor a check on a comment. These are identifiers, so a check can assert them and
        // a future routing task can compare its pinned image version against sourceRelease.
        #expect(GuidanceSign.sourceRelease == "11.0")
        #expect(GuidanceSign.sourcePath == "web-api/src/main/java/com/graphhopper/util/Instruction.java")
        #expect(GuidanceSign.sourceCommit == "69e50f6e2cfaf0a8e69752df9953ee5f1ac276a4")
        #expect(GuidanceSign.sourceBlob == "1638c71bfd6537d9a57ad0f24fec334e2122eaab")
        #expect(GuidanceSign.requiresRoutingServiceVersion == "11.0")
    }
}
