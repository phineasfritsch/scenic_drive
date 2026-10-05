"""Regenerates pentagon05points.txt (T-0265): points around the twelve H3 resolution-5 pentagons, each with the
cell uber/h3's own library assigns it. Not run by any test - the committed output is the fixture.

    python -m pip install h3==4.1.2      # h3-py 4.1.2, a binding of uber/h3's C library v4.1.0
    python Tests/TelemetryTests/Fixtures/make_pentagon05points.py > Tests/TelemetryTests/Fixtures/pentagon05points.txt

Why it exists: rand05centers.txt (5000 published random cell centers) never reaches the pentagon k-axis
correction in `_faceIjkToH3` - measured by ops/mutate/telemetry.py, where removing that correction left all
5000 rows green. These points ring every pentagon at 1-40 km, every 7.5 degrees of bearing, so the deleted
k-axis sector of each pentagon is crossed on every face it touches. Format is rand05centers.txt's:
`h3index lat lng`, degrees, six decimals.
"""
import math

import h3

R_KM = 6371.007180918475
rows = []
for pentagon in sorted(h3.get_pentagons(5)):
    lat0, lng0 = h3.cell_to_latlng(pentagon)
    p0, l0 = math.radians(lat0), math.radians(lng0)
    for km in (1, 3, 6, 10, 15, 20, 25, 30, 40):
        d = km / R_KM
        for step in range(48):
            b = math.radians(step * 7.5)
            p = math.asin(math.sin(p0) * math.cos(d) + math.cos(p0) * math.sin(d) * math.cos(b))
            lng = l0 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p0), math.cos(d) - math.sin(p0) * math.sin(p))
            lat_s = "%.6f" % math.degrees(p)
            lng_s = "%.6f" % math.degrees(lng)
            rows.append("%s %s %s" % (h3.latlng_to_cell(float(lat_s), float(lng_s), 5), lat_s, lng_s))
print("\n".join(rows))
