package com.scenicdrive.routing;

import com.graphhopper.reader.ReaderWay;
import com.graphhopper.routing.ev.BooleanEncodedValue;
import com.graphhopper.routing.ev.EdgeIntAccess;
import com.graphhopper.routing.util.parsers.TagParser;
import com.graphhopper.storage.IntsRef;
import java.util.function.Predicate;

/** Writes one GateFacts boolean onto every edge of a way: true exactly when the fact holds for its tags. */
public final class GateFactParser implements TagParser {

    private final BooleanEncodedValue fact;
    private final Predicate<ReaderWay> holds;

    public GateFactParser(BooleanEncodedValue fact, Predicate<ReaderWay> holds) {
        this.fact = fact;
        this.holds = holds;
    }

    @Override
    public void handleWayTags(int edgeId, EdgeIntAccess edgeIntAccess, ReaderWay way, IntsRef relationFlags) {
        fact.setBool(false, edgeId, edgeIntAccess, holds.test(way));
    }
}
