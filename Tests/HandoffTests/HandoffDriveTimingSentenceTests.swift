import Foundation
import Testing
@testable import Handoff

/// The two timing sentences the app shows - the home screen's and the failure card's - and the paste
/// that carries one of them.
///
/// ## Why this suite exists
///
/// T-0210 split the timing line by surface and ruled NO NUMBER on either. Both rulings lived in literals
/// inside `FeatureScenicHome`, an Apple-only target with no test bundle, and the pre-review mutant pass on
/// PR #121 shipped two defects through every gate: M3a typed "about 3 hours" into the home sentence, M3b
/// made the failure card's sentence identical to the home one - the card that exists because Apple Maps
/// did NOT open, promising that Apple Maps will give you the real time when it opens. `linux-core`,
/// `ios-compile` and `ops/lib/check-safety-disclaimer` were all green on both.
///
/// So the words moved here, to `HandoffDrive`, and this suite is what a wrong word fails. It binds to the
/// shipping symbols - `timingSentence`, `failureTimingSentence`, `realTimePromise`, the properties
/// `DriveFacts` and `HandoffFailureCard` now render and `HandoffFailureCard.clipboardText` pastes - never
/// to a literal copied out of a view (CLAUDE.md: a test named for a defect binds to the shipping symbol).
///
/// Every test ranges over `HandoffDrive.allCases`, not over a drive the test chooses: M1a's defect was a
/// card that copied the drive the SOURCE named instead of the one the screen selected, and a suite that
/// picks its own drive cannot see that class at all.
@Suite("The timing sentences of the two drives")
struct HandoffDriveTimingSentenceTests {

    // MARK: - The other two lines of the paste, as this suite types them

    static let roads = "Sunset Boulevard west, PCH north, Topanga Canyon Boulevard up."
    static let straightLine = "About 29 miles as the crow flies, pin to pin. The roads are longer."

    // MARK: - The words

    @Test("the home sentence carries no digit, for every drive", arguments: HandoffDrive.allCases)
    func theHomeSentenceCarriesNoNumber(drive: HandoffDrive) {
        let sentence = drive.timingSentence
        #expect(!sentence.contains(where: { $0.isNumber }),
                "a figure nobody in this repository has measured: \(sentence)")
    }

    @Test("the failure card's sentence carries no digit, for every drive",
          arguments: HandoffDrive.allCases)
    func theCardSentenceCarriesNoNumber(drive: HandoffDrive) {
        let sentence = drive.failureTimingSentence
        #expect(!sentence.contains(where: { $0.isNumber }),
                "a figure nobody in this repository has measured: \(sentence)")
    }

    @Test("the card's sentence is no drive's home sentence", arguments: HandoffDrive.allCases)
    func theCardSentenceIsNotAHomeSentence(drive: HandoffDrive) {
        let card = drive.failureTimingSentence
        #expect(card != drive.timingSentence, "both surfaces say the same thing: \(card)")
        for other in HandoffDrive.allCases {
            #expect(card != other.timingSentence,
                    "the failure card says \(other)'s home sentence: \(card)")
        }
    }

    @Test("the promise of a real time lives on the home surface and never on the card",
          arguments: HandoffDrive.allCases)
    func theCardSentenceMakesNoTimePromise(drive: HandoffDrive) {
        #expect(drive.timingSentence.contains(HandoffDrive.realTimePromise),
                "the home sentence never says where the real number comes from: \(drive.timingSentence)")
        #expect(!drive.failureTimingSentence.contains(HandoffDrive.realTimePromise),
                "the card promises a time from the app that just refused to open: "
                    + drive.failureTimingSentence)
    }

    // MARK: - The paste, composed the way the card composes it

    @Test("the paste opens with THIS drive's own directions URL and ends with its home sentence",
          arguments: HandoffDrive.allCases)
    func thePasteCarriesThisDrivesOwnURLAndSentence(drive: HandoffDrive) throws {
        // Every argument read off `drive`, which is what HandoffFailureCard.clipboardText does. The URL
        // is compared to `directions.url()` - the builder SkylineHandoff.directions(for:) forwards to and
        // SkylineHandoff.open( leaves through - so the pasted link and the tapped link are one drive.
        let payload = drive.clipboardPayload(roadList: Self.roads,
                                             straightLine: Self.straightLine,
                                             timing: drive.timingSentence)
        let lines = payload.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)
        let opened = try drive.directions.url().absoluteString
        #expect(lines.count == 4, "got \(lines)")
        #expect(lines.first == opened, "the paste opens with \(lines.first ?? "nothing"), not \(opened)")
        #expect(lines.last == drive.timingSentence,
                "the paste ends with \(lines.last ?? "nothing"), not this drive's home sentence")
    }
}
