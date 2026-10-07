import PlaceStore
import Testing

/// T-0306 acceptance 3, the last hop of R2: a SavedDraft's already-rounded doubles become the T-0290 value through
/// the shipping `SavedDrive.unresolved`, every segment id `SavedSegment.unplaced` until the resolver places it.
/// Full equality of the whole SavedDrive and of the stored integers. Not GRDB-gated. A value with more than 5 dp is
/// REFUSED here, never rounded a second time.
@Suite("SavedDriveUnresolvedTests")
struct SavedDriveUnresolvedTests {
    enum Outcome: Equatable {
        case stored(SavedDrive)
        case refused(SavedDriveError)
        case otherError
    }

    static func unresolved(_ points: [(latitude: Double, longitude: Double)], lambda: Double) -> Outcome {
        do {
            return .stored(try SavedDrive.unresolved(name: "El Matador", points: points, lambda: lambda,
                                                     budgetMinutes: 45, createdAt: 1_760_000_000))
        } catch let error as SavedDriveError {
            return .refused(error)
        } catch {
            return .otherError
        }
    }

    @Test("5-dp points become unplaced segments in order, the whole drive and its integers equal")
    func stored() throws {
        let got = Self.unresolved([(34.09312, -118.60071), (34, -118.12346), (34.04079, -118.68511)], lambda: 0.33333)
        let want = try SavedDrive(name: "El Matador", segments: [
            SavedSegment(segmentID: -1, midpoint: try SavedMidpoint(latitude: 34.09312, longitude: -118.60071)),
            SavedSegment(segmentID: -1, midpoint: try SavedMidpoint(latitude: 34, longitude: -118.12346)),
            SavedSegment(segmentID: -1, midpoint: try SavedMidpoint(latitude: 34.04079, longitude: -118.68511)),
        ], lambda: 0.33333, budgetMinutes: 45, createdAt: 1_760_000_000)
        #expect(got == .stored(want))
        guard case .stored(let drive) = got else { return }
        #expect(drive.segments.map { [$0.segmentID, Int64($0.midpoint.latE5), Int64($0.midpoint.lonE5)] }
                == [[-1, 3_409_312, -11_860_071], [-1, 3_400_000, -11_812_346], [-1, 3_404_079, -11_868_511]])
        #expect(drive.lambdaE5 == 33_333)
        #expect(drive.id == nil)
        #expect(drive.needsReplan == false)
        #expect(SavedSegment.unplaced == -1)
    }

    @Test("no points is a drive with no segments")
    func empty() throws {
        #expect(Self.unresolved([], lambda: 0)
                == .stored(try SavedDrive(name: "El Matador", segments: [], lambda: 0, budgetMinutes: 45,
                                          createdAt: 1_760_000_000)))
    }

    @Test("more than 5 dp is refused by field, never rounded a second time")
    func refused() {
        #expect(Self.unresolved([(34.093124, -118.60071)], lambda: 0) == .refused(.moreThanFiveDecimals(.latitude)))
        #expect(Self.unresolved([(34.09312, -118.600714)], lambda: 0) == .refused(.moreThanFiveDecimals(.longitude)))
        #expect(Self.unresolved([(34.09312, -118.60071)], lambda: 0.333333) == .refused(.moreThanFiveDecimals(.lambda)))
    }
}
