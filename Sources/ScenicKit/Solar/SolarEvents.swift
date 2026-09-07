import Foundation

/// Sunrise, sunset, twilight and golden-hour instants for one local calendar day at one place.
///
/// "Local day" means the solar day centred on local solar noon for that longitude — no time zones, no
/// DST, no Foundation `Calendar`. All instants are UTC `Date`s. Events the Sun does not reach on that day
/// (polar night, midnight sun, or a twilight threshold never crossed) are `nil`, never a fake value.
public struct SolarEvents: Sendable, Equatable {
    /// Sun's upper limb touching the horizon, standard refraction (zenith 90.833°).
    public static let horizonZenith = 90.833
    /// Civil twilight: Sun's centre 6° below the horizon.
    public static let civilZenith = 96.0
    /// Golden hour, as used for "west-facing overlook at golden hour": Sun between +6° and −4° elevation.
    public static let goldenHourUpperZenith = 84.0
    public static let goldenHourLowerZenith = 94.0

    public let date: CivilDate
    public let coordinate: Coordinate
    public let solarNoon: Date
    public let sunrise: Date?
    public let sunset: Date?
    public let civilDawn: Date?
    public let civilDusk: Date?
    /// Evening golden hour: from Sun at +6° down to −4° elevation.
    public let goldenHourEvening: ClosedRange<Date>?
    /// Morning golden hour: from Sun at −4° up to +6° elevation.
    public let goldenHourMorning: ClosedRange<Date>?

    /// Civil twilight ends `civilDusk`; after it a road with no lighting is dark. Nil means the Sun never set.
    public var isDarkAfter: Date? { civilDusk }

    public static func compute(on date: CivilDate, at coordinate: Coordinate) -> SolarEvents {
        let jd0 = date.julianDayAtMidnightUTC
        let midnight = date.midnightUTC
        // First pass at local solar noon; each event is then refined once at its own estimated time.
        let noonJD = jd0 + 0.5 - coordinate.longitude / 360
        let noonMinutes = solarNoonMinutesUTC(julianDay: noonJD, longitude: coordinate.longitude)
        func instant(_ minutes: Double) -> Date { midnight.addingTimeInterval(minutes * 60) }
        func event(zenith: Double, evening: Bool) -> Date? {
            guard var minutes = eventMinutes(zenith: zenith, evening: evening, guess: noonMinutes, jd0: jd0, coordinate: coordinate) else { return nil }
            if let refined = eventMinutes(zenith: zenith, evening: evening, guess: minutes, jd0: jd0, coordinate: coordinate) {
                minutes = refined
            }
            return instant(minutes)
        }
        let sunrise = event(zenith: horizonZenith, evening: false)
        let sunset = event(zenith: horizonZenith, evening: true)
        let civilDawn = event(zenith: civilZenith, evening: false)
        let civilDusk = event(zenith: civilZenith, evening: true)
        let eveningStart = event(zenith: goldenHourUpperZenith, evening: true)
        let eveningEnd = event(zenith: goldenHourLowerZenith, evening: true)
        let morningStart = event(zenith: goldenHourLowerZenith, evening: false)
        let morningEnd = event(zenith: goldenHourUpperZenith, evening: false)
        return SolarEvents(
            date: date, coordinate: coordinate, solarNoon: instant(noonMinutes),
            sunrise: sunrise, sunset: sunset, civilDawn: civilDawn, civilDusk: civilDusk,
            goldenHourEvening: range(eveningStart, eveningEnd), goldenHourMorning: range(morningStart, morningEnd)
        )
    }

    // MARK: - internals

    /// UTC minutes after 0h of solar noon, using the equation of time at `julianDay`.
    static func solarNoonMinutesUTC(julianDay: Double, longitude: Double) -> Double {
        720 - 4 * longitude - SolarMath.equationOfTime(SolarMath.julianCentury(julianDay: julianDay))
    }

    /// UTC minutes after 0h of the moment the Sun reaches `zenith`, evaluated with declination and equation
    /// of time at `guess` (minutes). Returns nil when the Sun never reaches that zenith.
    static func eventMinutes(zenith: Double, evening: Bool, guess: Double, jd0: Double, coordinate: Coordinate) -> Double? {
        let t = SolarMath.julianCentury(julianDay: jd0 + guess / 1440)
        guard let ha = SolarMath.hourAngle(zenith: zenith, latitude: coordinate.latitude, declination: SolarMath.declination(t)) else { return nil }
        let noon = 720 - 4 * coordinate.longitude - SolarMath.equationOfTime(t)
        return evening ? noon + 4 * ha : noon - 4 * ha
    }

    private static func range(_ a: Date?, _ b: Date?) -> ClosedRange<Date>? {
        guard let a, let b, a <= b else { return nil }
        return a...b
    }
}
