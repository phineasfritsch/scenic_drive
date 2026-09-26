"""T-0209: geocode the five named LA places of acceptance clause 4 ONCE, so the pairs are typed, not prose.

    python services/routing/tools/geocode_la_places.py

One Nominatim search per place, 1.1 s apart (Nominatim's usage policy is at most one request per second),
first hit only, printed as `PLACE <name> lat=<> lon=<> osm=<type>/<id> display=<>`. The Log quotes the
output and the measurement (tools/route_la_pairs.py) carries the coordinates as typed literals rounded to
4 decimals - this script is the provenance of those literals, not something a test calls.
"""

import json
import time
import urllib.parse
import urllib.request

PLACES = (
    ("Westwood", "Westwood, Los Angeles, California, USA"),
    ("Malibu", "Malibu, California, USA"),
    ("Woodland Hills", "Woodland Hills, Los Angeles, California, USA"),
    ("Santa Monica", "Santa Monica, California, USA"),
    ("Topanga", "Topanga, California, USA"),
)

USER_AGENT = "scenic-drive-T-0209-measurement/1.0 (one-off geocode of five place names)"


def geocode(query):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "us"}
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        hits = json.load(response)
    if not hits:
        raise SystemExit(f"Nominatim found nothing for {query!r}")
    return hits[0]


def main():
    for index, (name, query) in enumerate(PLACES):
        if index:
            time.sleep(1.1)
        hit = geocode(query)
        print(
            f"PLACE {name} lat={float(hit['lat']):.4f} lon={float(hit['lon']):.4f} "
            f"osm={hit.get('osm_type')}/{hit.get('osm_id')} display={hit.get('display_name')}"
        )


if __name__ == "__main__":
    main()
