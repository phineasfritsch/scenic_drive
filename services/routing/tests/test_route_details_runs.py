"""tools/route_details.py - the parser and the RUN arithmetic T-0209's rat-run verdict is read from.

No docker: typed EDGE rows in, runs out. The LA verdict (a residential run of 813.9 m on 7th Street at lambda 8,
T-0209 Log) is computed by `longest_run` over `parse`d output, so a run that is split early, never flushed at
the end of a route, or summed over the wrong class would move that verdict without any container noticing.
"""

import pytest

from tools.route_details import MINOR_CLASSES, class_metres, longest_run, parse, runs

OUTPUT = """SCENIC_EV present=true bits=4 max=10
ROUTE profile=car_scenic model=lambda-8.json time_ms=60000 distance_m=1070.0
EDGE model=lambda-8.json seq=0 road_class=primary osm_way_id=1 distance_m=100.000
EDGE model=lambda-8.json seq=1 road_class=residential osm_way_id=2 distance_m=300.000
EDGE model=lambda-8.json seq=2 road_class=residential osm_way_id=2 distance_m=200.000
EDGE model=lambda-8.json seq=3 road_class=residential osm_way_id=3 distance_m=350.000
EDGE model=lambda-8.json seq=4 road_class=primary osm_way_id=4 distance_m=50.000
EDGE model=lambda-8.json seq=5 road_class=service osm_way_id=5 distance_m=60.000
EDGE model=lambda-8.json seq=6 road_class=residential osm_way_id=6 distance_m=10.000
"""


def _edges():
    (route,) = parse(OUTPUT)
    return route["edges"]


def test_parse_reads_route_and_edge_rows():
    (route,) = parse(OUTPUT)
    assert (route["profile"], route["model"], route["time_ms"], route["distance_m"]) == (
        "car_scenic", "lambda-8.json", 60000, 1070.0)
    assert [edge["seq"] for edge in route["edges"]] == list(range(7))
    assert route["edges"][1] == {"seq": 1, "road_class": "residential", "way": 2, "m": 300.0}


def test_parse_refuses_an_edge_row_that_does_not_follow_its_route():
    with pytest.raises(ValueError):
        parse("ROUTE profile=car_fast model=- time_ms=1 distance_m=1.0\n"
              "EDGE model=lambda-0.json seq=0 road_class=primary osm_way_id=1 distance_m=1.000\n")


def test_a_run_joins_consecutive_edges_of_one_class_across_ways():
    found = runs(_edges(), ("residential",))
    assert [(run["m"], run["ways"], run["edges"]) for run in found] == [(850.0, [2, 3], 3), (10.0, [6], 1)]


def test_a_run_that_ends_the_route_is_counted():
    assert runs(_edges(), ("residential",))[-1]["ways"] == [6]


def test_longest_run_per_class_and_mixed():
    assert longest_run(_edges(), ("residential",))["m"] == 850.0
    assert longest_run(_edges(), ("service",))["m"] == 60.0
    mixed = runs(_edges(), MINOR_CLASSES)
    assert [(run["m"], run["classes"]) for run in mixed] == [
        (850.0, ["residential"]), (70.0, ["residential", "service"])]
    assert longest_run(_edges(), ("living_street",)) == {"m": 0.0, "ways": [], "classes": [], "edges": 0}


def test_class_metres_sums_every_edge():
    assert class_metres(_edges()) == {"primary": 150.0, "residential": 860.0, "service": 60.0}
