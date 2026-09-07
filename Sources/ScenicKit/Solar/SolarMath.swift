import Foundation

/// Solar position equations from the NOAA Solar Calculator (Meeus, *Astronomical Algorithms*, ch. 25).
/// Accurate to about a minute for |latitude| < 72°, which is what the golden-hour and twilight
/// features need. Pure functions of the Julian century so they test without a clock.
///
/// Angles are degrees in and out; the Julian century `t` is (JD − 2451545) / 36525.
public enum SolarMath {
    public static func julianCentury(julianDay jd: Double) -> Double { (jd - 2_451_545.0) / 36_525.0 }

    /// Geometric mean longitude of the Sun, degrees in [0, 360).
    public static func meanLongitude(_ t: Double) -> Double {
        (280.46646 + t * (36_000.76983 + t * 0.000_3032)).truncatingRemainder(dividingBy: 360).positiveDegrees
    }

    /// Geometric mean anomaly of the Sun, degrees.
    public static func meanAnomaly(_ t: Double) -> Double { 357.52911 + t * (35_999.05029 - 0.000_1537 * t) }

    /// Eccentricity of Earth's orbit.
    public static func eccentricity(_ t: Double) -> Double { 0.016_708_634 - t * (0.000_042_037 + 0.000_000_1267 * t) }

    /// Sun's equation of center, degrees.
    public static func equationOfCenter(_ t: Double) -> Double {
        let m = meanAnomaly(t).radians
        return sin(m) * (1.914602 - t * (0.004817 + 0.000014 * t)) + sin(2 * m) * (0.019993 - 0.000101 * t) + sin(3 * m) * 0.000289
    }

    /// Apparent longitude of the Sun (true longitude corrected for nutation and aberration), degrees.
    public static func apparentLongitude(_ t: Double) -> Double {
        let omega = (125.04 - 1934.136 * t).radians
        return meanLongitude(t) + equationOfCenter(t) - 0.00569 - 0.00478 * sin(omega)
    }

    /// Obliquity of the ecliptic corrected for nutation, degrees.
    public static func obliquity(_ t: Double) -> Double {
        let seconds = 21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))
        let mean = 23 + (26 + seconds / 60) / 60
        let omega = (125.04 - 1934.136 * t).radians
        return mean + 0.00256 * cos(omega)
    }

    /// Solar declination, degrees.
    public static func declination(_ t: Double) -> Double {
        asin(sin(obliquity(t).radians) * sin(apparentLongitude(t).radians)).degrees
    }

    /// Equation of time, minutes (apparent solar time minus mean solar time).
    public static func equationOfTime(_ t: Double) -> Double {
        let eps = obliquity(t).radians
        let l0 = meanLongitude(t).radians
        let e = eccentricity(t)
        let m = meanAnomaly(t).radians
        let y = tan(eps / 2) * tan(eps / 2)
        let value = y * sin(2 * l0) - 2 * e * sin(m) + 4 * e * y * sin(m) * cos(2 * l0)
            - 0.5 * y * y * sin(4 * l0) - 1.25 * e * e * sin(2 * m)
        return 4 * value.degrees
    }

    /// Hour angle (degrees, positive) at which the Sun's center reaches `zenith` degrees for a latitude and
    /// declination. `nil` when the Sun never reaches that zenith on this day (polar day/night for that threshold).
    public static func hourAngle(zenith: Double, latitude: Double, declination: Double) -> Double? {
        let lat = latitude.radians, dec = declination.radians
        let cosHA = cos(zenith.radians) / (cos(lat) * cos(dec)) - tan(lat) * tan(dec)
        guard cosHA >= -1, cosHA <= 1 else { return nil }
        return acos(cosHA).degrees
    }

    /// Sun elevation above the horizon (degrees, geometric — no refraction) at a UTC instant.
    public static func elevation(at date: Date, coordinate: Coordinate) -> Double {
        let jd = date.timeIntervalSince1970 / 86_400 + 2_440_587.5
        let t = julianCentury(julianDay: jd)
        let minutesUTC = (jd + 0.5 - (jd + 0.5).rounded(.down)) * 1440
        let trueSolarMinutes = (minutesUTC + equationOfTime(t) + 4 * coordinate.longitude).truncatingRemainder(dividingBy: 1440).positiveMinutes
        let hourAngle = (trueSolarMinutes / 4 - 180).radians
        let lat = coordinate.latitude.radians, dec = declination(t).radians
        let cosZenith = sin(lat) * sin(dec) + cos(lat) * cos(dec) * cos(hourAngle)
        return 90 - acos(max(-1, min(1, cosZenith))).degrees
    }
}

extension Double {
    var positiveDegrees: Double { self < 0 ? self + 360 : self }
    var positiveMinutes: Double { self < 0 ? self + 1440 : self }
}
