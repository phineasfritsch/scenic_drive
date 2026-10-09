import Foundation

/// The icosahedron of uber/h3 v4.1.0 (src/h3lib/lib/faceijk.c): which face a point falls on, and where on that
/// face, as `_geoToClosestFace`, `_geoToHex2d` and `_geoToFaceIjk`. The three tables are generated from that
/// file and not retyped. Apache-2.0, see CorridorCell.swift (a copy of Telemetry's file of this name, T-0325 R1).
enum H3FaceProjection {
    /// `faceCenterGeo`: each face center as (latitude, longitude) in radians.
    static let centerGeo: [(latitude: Double, longitude: Double)] = [
        (0.803582649718989942, 1.248397419617396099),
        (1.307747883455638156, 2.536945009877921159),
        (1.054751253523952054, -1.347517358900396623),
        (0.600191595538186799, -0.450603909469755746),
        (0.491715428198773866, 0.401988202911306943),
        (0.172745327415618701, 1.678146885280433686),
        (0.605929321571350690, 2.953923329812411617),
        (0.427370518328979641, -1.888876200336285401),
        (-0.079066118549212831, -0.733429513380867741),
        (-0.230961644455383637, 0.506495587332349035),
        (0.079066118549212831, 2.408163140208925497),
        (0.230961644455383637, -2.635097066257444203),
        (-0.172745327415618701, -1.463445768309359553),
        (-0.605929321571350690, -0.187669323777381622),
        (-0.427370518328979641, 1.252716453253507838),
        (-0.600191595538186799, 2.690988744120037492),
        (-0.491715428198773866, -2.739604450678486295),
        (-0.803582649718989942, -1.893195233972397139),
        (-1.307747883455638156, -0.604647643711872080),
        (-1.054751253523952054, 1.794075294689396615),
    ]

    /// `faceCenterPoint`: each face center as x, y, z on the unit sphere.
    static let centerPoint: [(x: Double, y: Double, z: Double)] = [
        (0.2199307791404606, 0.6583691780274996, 0.7198475378926182),
        (-0.2139234834501421, 0.1478171829550703, 0.9656017935214205),
        (0.1092625278784797, -0.4811951572873210, 0.8697775121287253),
        (0.7428567301586791, -0.3593941678278028, 0.5648005936517033),
        (0.8112534709140969, 0.3448953237639384, 0.4721387736413930),
        (-0.1055498149613921, 0.9794457296411413, 0.1718874610009365),
        (-0.8075407579970092, 0.1533552485898818, 0.5695261994882688),
        (-0.2846148069787907, -0.8644080972654206, 0.4144792552473539),
        (0.7405621473854482, -0.6673299564565524, -0.0789837646326737),
        (0.8512303986474293, 0.4722343788582681, -0.2289137388687808),
        (-0.7405621473854481, 0.6673299564565524, 0.0789837646326737),
        (-0.8512303986474292, -0.4722343788582682, 0.2289137388687808),
        (0.1055498149613919, -0.9794457296411413, -0.1718874610009365),
        (0.8075407579970092, -0.1533552485898819, -0.5695261994882688),
        (0.2846148069787908, 0.8644080972654204, -0.4144792552473539),
        (-0.7428567301586791, 0.3593941678278027, -0.5648005936517033),
        (-0.8112534709140971, -0.3448953237639382, -0.4721387736413930),
        (-0.2199307791404607, -0.6583691780274996, -0.7198475378926182),
        (0.2139234834501420, -0.1478171829550704, -0.9656017935214205),
        (-0.1092625278784796, 0.4811951572873210, -0.8697775121287253),
    ]

    /// `faceAxesAzRadsCII[face][0]`: the azimuth from each face center to its i axis, in radians. The
    /// j and k columns of that table are not read by `latLngToCell` and are not copied.
    static let iAxisAzimuth: [Double] = [
        5.619958268523939882,
        5.760339081714187279,
        0.780213654393430055,
        0.430469363979999913,
        6.130269123335111400,
        2.692877706530642877,
        2.982963003477243874,
        3.532912002790141181,
        3.494305004259568154,
        3.003214169499538391,
        5.930472956509811562,
        0.138378484090254847,
        0.448714947059150361,
        0.158629650112549365,
        5.891865957979238535,
        2.711123289609793325,
        3.294508837434268316,
        3.804819692245439833,
        3.664438879055192436,
        2.361378999196363184,
    ]

    /// `M_AP7_ROT_RADS`: the rotation between a Class II grid and the Class III grid of the next resolution.
    static let apertureSevenRotation = 0.333473172251832115336090755351601070065900389
    /// `RES0_U_GNOMONIC`: the length of a resolution-0 unit vector in the gnomonic projection.
    static let res0UnitGnomonic = 0.38196601125010500003
    /// `M_SQRT7`: each resolution scales the grid by the square root of seven.
    static let sqrt7 = 2.6457513110645905905016157536392604257102
    /// `M_2PI`.
    static let twoPi = 6.28318530717958647692528676655900576839433

    /// `_geoToFaceIjk`: the face and the ijk+ coordinates of the cell containing a point given in RADIANS.
    static func faceIJK(latitude: Double, longitude: Double, resolution: Int) -> (face: Int, coord: H3CoordIJK) {
        // _geoToVec3d, then _geoToClosestFace by the smallest squared chord (_pointSquareDist).
        let cosLat = cos(latitude)
        let x = cos(longitude) * cosLat
        let y = sin(longitude) * cosLat
        let z = sin(latitude)
        var face = 0
        var sqd = 5.0
        for candidate in 0..<centerPoint.count {
            let c = centerPoint[candidate]
            let d = (c.x - x) * (c.x - x) + (c.y - y) * (c.y - y) + (c.z - z) * (c.z - z)
            if d < sqd {
                face = candidate
                sqd = d
            }
        }
        // _geoToHex2d. cos(r) = 1 - sqd / 2 for the chord between two points of the unit sphere.
        var r = acos(1 - sqd / 2)
        if r < 0.0000000000000001 {
            return (face, H3CoordIJK(hex2dX: 0, y: 0))
        }
        let center = centerGeo[face]
        var theta = positiveAngle(iAxisAzimuth[face]
            - positiveAngle(azimuth(from: center, toLatitude: latitude, longitude: longitude)))
        if resolution % 2 == 1 {
            theta = positiveAngle(theta - apertureSevenRotation)
        }
        r = tan(r) / res0UnitGnomonic
        for _ in 0..<resolution {
            r *= sqrt7
        }
        return (face, H3CoordIJK(hex2dX: r * cos(theta), y: r * sin(theta)))
    }

    /// `_geoAzimuthRads` (latLng.c): the azimuth from `start` to a point, both in radians.
    static func azimuth(from start: (latitude: Double, longitude: Double), toLatitude latitude: Double,
                        longitude: Double) -> Double {
        atan2(cos(latitude) * sin(longitude - start.longitude),
              cos(start.latitude) * sin(latitude)
                - sin(start.latitude) * cos(latitude) * cos(longitude - start.longitude))
    }

    /// `_posAngleRads` (latLng.c): an angle normalized into [0, 2 pi).
    static func positiveAngle(_ rads: Double) -> Double {
        var result = rads < 0.0 ? rads + twoPi : rads
        if rads >= twoPi {
            result -= twoPi
        }
        return result
    }
}
