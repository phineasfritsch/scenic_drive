package com.scenicdrive.routing;

import com.graphhopper.reader.ReaderWay;
import com.graphhopper.routing.ev.EdgeIntAccess;
import com.graphhopper.routing.ev.IntEncodedValue;
import com.graphhopper.routing.util.parsers.TagParser;
import com.graphhopper.storage.IntsRef;

/**
 * Reads the ETL's scenic_score=0..10 way tag into an unsigned 4-bit encoded value so custom models can say
 * scenic_score >= 7. A way with no tag gets 0: no tag is no evidence, never an average (T-0168's REFUSED
 * ruling). Out of range or unparsable is the same as no evidence, except that a value above the contract's
 * ceiling clamps to it rather than losing the whole way.
 */
public final class ScenicScoreParser implements TagParser {

    public static final String KEY = "scenic_score";
    public static final int BITS = 4;
    public static final int MAX = 10;

    private final IntEncodedValue scenicScore;

    public ScenicScoreParser(IntEncodedValue scenicScore) {
        this.scenicScore = scenicScore;
    }

    @Override
    public void handleWayTags(int edgeId, EdgeIntAccess edgeIntAccess, ReaderWay way, IntsRef relationFlags) {
        scenicScore.setInt(false, edgeId, edgeIntAccess, parse(way.getTag(KEY, "")));
    }

    static int parse(String raw) {
        if (raw == null || raw.isBlank()) return 0;
        try {
            int value = Integer.parseInt(raw.trim());
            if (value <= 0) return 0;
            return Math.min(value, MAX);
        } catch (NumberFormatException unparsable) {
            return 0;
        }
    }
}
