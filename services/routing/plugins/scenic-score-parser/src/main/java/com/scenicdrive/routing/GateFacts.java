package com.scenicdrive.routing;

import com.graphhopper.reader.ReaderWay;
import java.util.Map;
import java.util.Set;
import java.util.function.Predicate;

/**
 * The three way-level safety facts GraphHopper 11 has no encoded value for (T-0381 R3-R5), each a boolean the
 * base profile gates on. They restate Gates.swift's sets and compare EXACTLY, as Gates.verdict does: positive
 * evidence only, so a way without the tag is false, and ford=Yes or locked=true are not the fact.
 *
 * road_environment == FORD is deliberately not used for the ford: GraphHopper sets it on ANY ford value,
 * ford=no included. A node-level locked barrier stays GraphHopper's own car-access concern.
 */
public final class GateFacts {

    public static final String LOCKED_BARRIER = "gate_locked_barrier";
    public static final String FORD = "gate_ford";
    public static final String SERVICE_WAY = "gate_service_way";

    static final String YES = "yes";
    static final String SERVICE_HIGHWAY = "service";
    static final Set<String> REFUSABLE_BARRIERS = Set.of("gate");
    static final Set<String> REFUSED_SERVICE_VALUES =
            Set.of("driveway", "parking_aisle", "drive-through", "emergency_access");

    private static final Map<String, Predicate<ReaderWay>> BY_KEY = Map.of(
            LOCKED_BARRIER, way -> REFUSABLE_BARRIERS.contains(tag(way, "barrier")) && YES.equals(tag(way, "locked")),
            FORD, way -> YES.equals(tag(way, "ford")),
            SERVICE_WAY, way -> SERVICE_HIGHWAY.equals(tag(way, "highway"))
                    && REFUSED_SERVICE_VALUES.contains(tag(way, "service")));

    private GateFacts() {
    }

    /** The fact named `key`, or null when `key` is not one of the three. */
    public static Predicate<ReaderWay> forKey(String key) {
        return BY_KEY.get(key);
    }

    /** Every key, for the registry and the tests. */
    public static Set<String> keys() {
        return BY_KEY.keySet();
    }

    private static String tag(ReaderWay way, String key) {
        Object value = way.getTag(key);
        return value instanceof String ? (String) value : "";
    }
}
