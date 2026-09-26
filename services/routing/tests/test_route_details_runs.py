"""tools/route_details.py - the parser and the RUN arithmetic T-0209's rat-run verdict is read from.

No docker: typed EDGE rows in, runs out. The LA verdict (a residential run of 813.9 m on 7th Street at lambda 8,
T-0209 Log) is computed by `longest_run` over `parse`d output, so a run that is split early, never flushed at
the end of a route, or summed over the wrong class would move that verdict without any container noticing.
"""

import pytest

from tools.route_details import MINOR_CLASSES, class_metres, longest_run, parse, runs
from tools.route_la_pairs import LAMBDAS, report_pair

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


# The longest run in METRES is the one with the fewest edges: three 10 m service edges, then one 500 m edge.
FEW_LONG = (("service", 11, 10.0), ("service", 12, 10.0), ("service", 13, 10.0), ("primary", 20, 100.0),
            ("service", 21, 500.0))


def _six_routes(rows):
    """car_fast and the five lambdas, each over `rows` - the shape route_la_pairs.report_pair refuses without."""
    text = ""
    for profile, model in (("car_fast", "-"),) + tuple(("car_scenic", label) for label in LAMBDAS):
        text += f"ROUTE profile={profile} model={model} time_ms=60000 distance_m=630.0\n"
        text += "".join(f"EDGE model={model} seq={seq} road_class={road_class} osm_way_id={way} distance_m={m:.3f}\n"
                        for seq, (road_class, way, m) in enumerate(rows))
    return parse(text)


def test_the_reported_longest_run_is_longest_in_metres_not_in_edges(capsys):
    """The Log's runs verdict is read off report_pair's RUNS lines (route_la_pairs --reuse). A longest run chosen
    by edge count prints the 30 m run here, as it printed 48.8 m for Santa Monica -> Topanga's 174.8 m."""
    routes = _six_routes(FEW_LONG)
    _, _, (worst_m, _, worst) = report_pair("few-long", "0,0", "1,1", routes)
    lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip().startswith("RUNS")]
    assert len(lines) == 6, lines
    for line in lines:
        assert "service=500.0m[21]" in line and "mixed=500.0m['service'][21]" in line, line
    assert (worst_m, worst["ways"]) == (500.0, [21])
    assert longest_run(routes[0]["edges"], ("service",)) == {"m": 500.0, "ways": [21], "classes": ["service"], "edges": 1}


def test_class_metres_sums_every_edge():
    assert class_metres(_edges()) == {"primary": 150.0, "residential": 860.0, "service": 60.0}
