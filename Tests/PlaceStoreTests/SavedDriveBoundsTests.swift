import PlaceStore
import Testing

/// The five-decimal gate through the two public initialisers that take a Double - `SavedMidpoint(latitude:
/// longitude:)` and `SavedDrive(...lambda:...)` - over every bound of T-0290 R4/R4a. Not GRDB-gated. Accepted rows
/// compare the whole stored integers to literals; refused rows compare the whole typed error.
@Suite("SavedDrive five-decimal bounds")
struct SavedDriveBoundsTests {
    enum Outcome: Equatable {
        case stored([Int])
        case refused(SavedDriveError)
        case otherError
    }

    static func midpoint(_ latitude: Double, _ longitude: Double) -> Outcome {
        do {
            let point = try SavedMidpoint(latitude: latitude, longitude: longitude)
            return .stored([point.latE5, point.lonE5])
        } catch let error as SavedDriveError {
            return .refused(error)
        } catch {
            return .otherError
        }
    }

    static func lambda(_ value: Double) -> Outcome {
        do {
            return .stored([try SavedDrive(name: "n", segments: [], lambda: value, budgetMinutes: 30,
                                           createdAt: 0).lambdaE5])
        } catch let error as SavedDriveError {
            return .refused(error)
        } catch {
            return .otherError
        }
    }

    static let notFiniteValues: [Double] = [.nan, .infinity, -.infinity]

    @Test("latitude: both exact bounds accepted, nextafter outward out of range, nextafter inward not 5 dp")
    func latitudeBounds() {
        #expect(Self.midpoint(90, 12.5) == .stored([9_000_000, 1_250_000]))
        #expect(Self.midpoint(-90, 12.5) == .stored([-9_000_000, 1_250_000]))
        #expect(Self.midpoint(Double(90).nextUp, 12.5) == .refused(.outOfRange(.latitude)))
        #expect(Self.midpoint(Double(-90).nextDown, 12.5) == .refused(.outOfRange(.latitude)))
        #expect(Self.midpoint(Double(90).nextDown, 12.5) == .refused(.moreThanFiveDecimals(.latitude)))
        #expect(Self.midpoint(Double(-90).nextUp, 12.5) == .refused(.moreThanFiveDecimals(.latitude)))
        for value in Self.notFiniteValues {
            #expect(Self.midpoint(value, 12.5) == .refused(.notFinite(.latitude)))
        }
    }

    @Test("longitude: both exact bounds accepted, nextafter outward out of range, nextafter inward not 5 dp")
    func longitudeBounds() {
        #expect(Self.midpoint(34.5, 180) == .stored([3_450_000, 18_000_000]))
        #expect(Self.midpoint(34.5, -180) == .stored([3_450_000, -18_000_000]))
        #expect(Self.midpoint(34.5, Double(180).nextUp) == .refused(.outOfRange(.longitude)))
        #expect(Self.midpoint(34.5, Double(-180).nextDown) == .refused(.outOfRange(.longitude)))
        #expect(Self.midpoint(34.5, Double(180).nextDown) == .refused(.moreThanFiveDecimals(.longitude)))
        #expect(Self.midpoint(34.5, Double(-180).nextUp) == .refused(.moreThanFiveDecimals(.longitude)))
        for value in Self.notFiniteValues {
            #expect(Self.midpoint(34.5, value) == .refused(.notFinite(.longitude)))
        }
    }

    @Test("five decimals are stored as their e5 integers; a sixth is refused, never rounded")
    func fiveDecimals() {
        #expect(Self.midpoint(34.09012, -118.65432) == .stored([3_409_012, -11_865_432]))
        #expect(Self.midpoint(0.00001, -0.00001) == .stored([1, -1]))
        #expect(Self.midpoint(-0.0, 0) == .stored([0, 0]))
        #expect(Self.midpoint(34.090121, -118.65432) == .refused(.moreThanFiveDecimals(.latitude)))
        #expect(Self.midpoint(34.09012, -118.654321) == .refused(.moreThanFiveDecimals(.longitude)))
        #expect(Self.midpoint(0.000005, 0) == .refused(.moreThanFiveDecimals(.latitude)))
        #expect(Self.midpoint(0, -0.000015) == .refused(.moreThanFiveDecimals(.longitude)))
    }

    @Test("check order: latitude before longitude; per field finite, then range, then decimals")
    func checkOrder() {
        #expect(Self.midpoint(.nan, .nan) == .refused(.notFinite(.latitude)))
        #expect(Self.midpoint(91, .nan) == .refused(.outOfRange(.latitude)))
        #expect(Self.midpoint(34.090121, .infinity) == .refused(.moreThanFiveDecimals(.latitude)))
        #expect(Self.midpoint(90.000001, 0) == .refused(.outOfRange(.latitude)))
        #expect(Self.midpoint(0, -180.000001) == .refused(.outOfRange(.longitude)))
    }

    @Test("lambda: [0, 1000] exact bounds accepted, nextafter outward out of range, inward not 5 dp")
    func lambdaBounds() {
        #expect(Self.lambda(0) == .stored([0]))
        #expect(Self.lambda(-0.0) == .stored([0]))
        #expect(Self.lambda(1000) == .stored([100_000_000]))
        #expect(Self.lambda(Double(0).nextDown) == .refused(.outOfRange(.lambda)))
        #expect(Self.lambda(Double(1000).nextUp) == .refused(.outOfRange(.lambda)))
        #expect(Self.lambda(Double(0).nextUp) == .refused(.moreThanFiveDecimals(.lambda)))
        #expect(Self.lambda(Double(1000).nextDown) == .refused(.moreThanFiveDecimals(.lambda)))
        #expect(Self.lambda(-1) == .refused(.outOfRange(.lambda)))
        #expect(Self.lambda(1e300) == .refused(.outOfRange(.lambda)))
        #expect(Self.lambda(2.5) == .stored([250_000]))
        #expect(Self.lambda(0.00001) == .stored([1]))
        #expect(Self.lambda(2.123456) == .refused(.moreThanFiveDecimals(.lambda)))
        for value in Self.notFiniteValues {
            #expect(Self.lambda(value) == .refused(.notFinite(.lambda)))
        }
    }

    @Test("the degree accessors return exactly the accepted Doubles")
    func degreesRoundTrip() throws {
        let point = try SavedMidpoint(latitude: 34.09012, longitude: -118.65432)
        #expect([point.latitude, point.longitude] == [34.09012, -118.65432])
        #expect(try SavedDrive(name: "n", segments: [], lambda: 2.75, budgetMinutes: 0, createdAt: 0).lambda == 2.75)
    }
}
