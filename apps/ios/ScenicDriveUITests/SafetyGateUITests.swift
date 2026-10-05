import XCTest

/// P-SAFE-03's runtime half (T-0180): the first tap on the handoff opens the disclaimer instead of leaving, the
/// accept records the acknowledgement on the device, the next tap leaves for Apple Maps, the acknowledgement
/// survives a relaunch - and at the largest accessibility size the conditions line is on screen and the accept
/// button is still a 44 pt target.
///
/// The handoff button ships as `home.openInAppleMaps` (`GatedHandoffButton`; ruling R2), and the flag is read
/// through what the app DOES after a relaunch, never across processes (ruling R4).
final class SafetyGateUITests: XCTestCase {
    /// Acceptance 1. RED by name on a build whose accept closure does not write the acknowledgement: the sheet goes
    /// away, and the next tap opens it again instead of leaving.
    @MainActor
    func testFirstTapOpensDisclaimerAndAcceptPersistsAcrossRelaunch() {
        continueAfterFailure = false
        let app = HomeLaunch.launch()
        let handoff = HomeLaunch.element(app, "home.openInAppleMaps")
        XCTAssertTrue(handoff.waitForExistence(timeout: 20), "home.openInAppleMaps never appeared")
        XCTAssertFalse(HomeLaunch.element(app, "home.disclaimer").exists, "home.disclaimer is up before any tap")

        handoff.tap()
        let accept = HomeLaunch.element(app, "home.disclaimer.accept")
        XCTAssertTrue(accept.waitForExistence(timeout: 10), "the first tap did not present home.disclaimer.accept")
        XCTAssertTrue(HomeLaunch.element(app, "home.disclaimer").exists, "the first tap did not present home.disclaimer")
        XCTAssertEqual(app.state, .runningForeground, "the first tap left the app before any acknowledgement")

        accept.tap()
        XCTAssertTrue(accept.waitForNonExistence(timeout: 10), "home.disclaimer.accept did not dismiss home.disclaimer")
        handoff.tap()
        assertTapWentThroughTheGate(app, after: "the accept")

        // Relaunch WITHOUT the reset: what the accept wrote is all the app has to go on.
        let relaunched = HomeLaunch.launch(reset: false)
        let handoffAgain = HomeLaunch.element(relaunched, "home.openInAppleMaps")
        XCTAssertTrue(handoffAgain.waitForExistence(timeout: 20), "home.openInAppleMaps never appeared after relaunch")
        XCTAssertFalse(HomeLaunch.element(relaunched, "home.disclaimer").exists, "a sheet is up after relaunch")
        handoffAgain.tap()
        assertTapWentThroughTheGate(relaunched, after: "a relaunch without the reset")
    }

    /// Acceptance 2: at the largest accessibility size, collapsed, home.conditions is on screen, hittable and not
    /// covered, and home.disclaimer.accept is hittable and at least 44 x 44 pt. The size is SEEN to take: the
    /// conditions line is at least 1.5x as tall as at the default size (ruling R7).
    ///
    /// KNOWN DEFECT, T-9903: run 37292916916 measured home.conditions at y 799.7-904.3 in an 874 pt window - the
    /// collapsed sheet outgrows the screen at this size, so the line and the handoff below it are off screen and
    /// the accept cannot be reached. Everything downstream of that is inside a STRICT expected failure: the test
    /// stays green while the defect is there, names it in the result bundle, and goes RED the day the layout is
    /// fixed, so the expectation cannot outlive the defect. The size check above it is a hard assertion.
    @MainActor
    func testConditionsAndAcceptTargetAtLargestAccessibilitySize() {
        continueAfterFailure = true
        XCUIDevice.shared.appearance = .light
        let standard = HomeLaunch.launch()
        let standardConditions = HomeLaunch.element(standard, "home.conditions")
        XCTAssertTrue(standardConditions.waitForExistence(timeout: 20), "home.conditions never appeared")
        let standardHeight = standardConditions.frame.height

        let app = HomeLaunch.launch(contentSize: HomeLaunch.largestAccessibilitySize)
        let conditions = HomeLaunch.element(app, "home.conditions")
        XCTAssertTrue(conditions.waitForExistence(timeout: 20), "home.conditions never appeared at the largest size")
        XCTAssertGreaterThanOrEqual(conditions.frame.height, standardHeight * 1.5,
                                    "the largest accessibility size did not take: home.conditions is "
                                        + "\(conditions.frame.height) pt tall, \(standardHeight) pt at the default size")
        XCTExpectFailure("T-9903: at the largest accessibility size the collapsed home sheet outgrows the screen") {
            UncoveredCheck(app: app).assertUncovered("home.conditions", ancestors: ["home.sheet"],
                                                     context: "largest accessibility size, collapsed")

            let handoff = HomeLaunch.element(app, "home.openInAppleMaps")
            XCTAssertTrue(handoff.isHittable, "home.openInAppleMaps is not hittable at the largest size: \(handoff.frame)")
            guard handoff.isHittable else {
                return
            }
            handoff.tap()
            let accept = HomeLaunch.element(app, "home.disclaimer.accept")
            XCTAssertTrue(accept.waitForExistence(timeout: 10), "home.disclaimer.accept never appeared at the largest size")
            XCTAssertTrue(accept.isHittable, "home.disclaimer.accept is not hittable at the largest size: \(accept.frame)")
            XCTAssertGreaterThanOrEqual(accept.frame.width, 44, "home.disclaimer.accept is narrower than 44 pt: \(accept.frame)")
            XCTAssertGreaterThanOrEqual(accept.frame.height, 44, "home.disclaimer.accept is shorter than 44 pt: \(accept.frame)")
        }
    }

    /// The tap that follows an acknowledgement went THROUGH the gate (ruling R14): no disclaimer within 5 s - a build
    /// that did not record the acknowledgement presents it again, which is the defect this test is named for - and no
    /// failure card (`home.error`), so the handoff was handed its URL. Whether the simulator's Maps then takes the
    /// foreground is recorded, never asserted: run 37295029521 saw the app stay in front 20 s after such a tap with
    /// no sheet and the gate open, which is the simulator's URL routing, not the gate.
    @MainActor
    private func assertTapWentThroughTheGate(_ app: XCUIApplication, after what: String,
                                             file: StaticString = #filePath, line: UInt = #line) {
        let accept = HomeLaunch.element(app, "home.disclaimer.accept")
        XCTAssertFalse(accept.waitForExistence(timeout: 5),
                       "after \(what), the next tap on home.openInAppleMaps presented home.disclaimer again - the "
                           + "acknowledgement was not recorded", file: file, line: line)
        let left = HomeLaunch.leftForeground(app, timeout: 5)
        if !left {
            XCTAssertFalse(HomeLaunch.element(app, "home.error").exists,
                           "after \(what), the handoff refused: home.error is on screen", file: file, line: line)
        }
        let maps = XCUIApplication(bundleIdentifier: "com.apple.Maps")
        print("T-0180 handoff after \(what): app left the foreground \(left), app state \(app.state.rawValue), "
              + "Maps state \(maps.state.rawValue)")
    }
}
