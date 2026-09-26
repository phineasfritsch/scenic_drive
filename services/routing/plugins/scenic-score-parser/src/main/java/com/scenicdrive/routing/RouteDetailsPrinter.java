package com.scenicdrive.routing;

import com.graphhopper.ResponsePath;
import com.graphhopper.util.details.PathDetail;

import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * {@code --mode route-details}: one {@code EDGE} row per routed edge, so a residential or service RUN (consecutive
 * edges of one class, in metres, with the OSM ways it crossed) can be measured on a real route. T-0224 could not
 * measure a single run because the image printed only {@code ROUTE ... time_ms distance_m} and nothing asked
 * GraphHopper for path details.
 *
 * The rows come from GraphHopper's own path details - the same {@code details=road_class&details=osm_way_id&
 * details=distance} the served {@code /route} answers - not from a second walk of the graph: {@code distance} is
 * emitted once per edge, and {@code road_class} / {@code osm_way_id} are intervals of route points that are
 * aligned to each edge by the edge's first point. The sum of the rows' distance_m is the route's distance.
 *
 *   EDGE model=lambda-8.json seq=0 road_class=primary osm_way_id=74344132 distance_m=123.456
 */
public final class RouteDetailsPrinter {

    /** What the request asks for; ScenicRouterMain.route sets exactly these on a route-details request. */
    public static final List<String> DETAILS = List.of("road_class", ScenicRouterMain.OSM_WAY_ID, "distance");

    /** Prints the EDGE rows of one routed path and returns how many there were. */
    public static int print(String label, ResponsePath path) {
        Map<String, List<PathDetail>> details = path.getPathDetails();
        List<PathDetail> edges = required(details, "distance", label);
        List<PathDetail> classes = required(details, "road_class", label);
        List<PathDetail> ways = required(details, ScenicRouterMain.OSM_WAY_ID, label);
        int classIndex = 0;
        int wayIndex = 0;
        for (int seq = 0; seq < edges.size(); seq++) {
            PathDetail edge = edges.get(seq);
            classIndex = covering(classes, classIndex, edge.getFirst(), "road_class", label);
            wayIndex = covering(ways, wayIndex, edge.getFirst(), ScenicRouterMain.OSM_WAY_ID, label);
            System.out.printf(Locale.ROOT, "EDGE model=%s seq=%d road_class=%s osm_way_id=%s distance_m=%.3f%n",
                    label, seq, classes.get(classIndex).getValue(), ways.get(wayIndex).getValue(),
                    ((Number) edge.getValue()).doubleValue());
        }
        return edges.size();
    }

    /**
     * The interval that holds the edge starting at {@code point}. Intervals are contiguous and sorted, and an
     * interval ending at point p hands p to the next one, so the walk moves forward while the current interval
     * ends at or before the point. It never moves back, which keeps the whole route one linear pass.
     */
    private static int covering(List<PathDetail> intervals, int from, int point, String name, String label) {
        int index = from;
        while (index + 1 < intervals.size() && intervals.get(index).getLast() <= point) index++;
        PathDetail interval = intervals.get(index);
        if (interval.getFirst() > point || interval.getLast() < point) {
            throw new IllegalStateException("model=" + label + ": no " + name + " interval covers route point "
                    + point + " (nearest is [" + interval.getFirst() + "," + interval.getLast() + "])");
        }
        return index;
    }

    private static List<PathDetail> required(Map<String, List<PathDetail>> details, String name, String label) {
        List<PathDetail> list = details.get(name);
        if (list == null || list.isEmpty()) {
            throw new IllegalStateException("model=" + label + ": GraphHopper returned no '" + name
                    + "' path details (asked for " + DETAILS + ", got " + details.keySet() + ")");
        }
        return list;
    }

    private RouteDetailsPrinter() {
    }
}
