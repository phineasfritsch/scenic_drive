package com.scenicdrive.routing;

import com.graphhopper.routing.ev.DefaultImportRegistry;
import com.graphhopper.routing.ev.ImportRegistry;
import com.graphhopper.routing.ev.ImportUnit;
import com.graphhopper.routing.ev.IntEncodedValueImpl;

/**
 * The one registration point GraphHopper gives a third-party encoded value: graph.encoded_values names
 * scenic_score, the import asks this registry for it, and everything GraphHopper already knows is answered
 * by its own registry. Registering scenic_score anywhere else is not possible from configuration alone.
 */
public final class ScenicScoreImportRegistry implements ImportRegistry {

    private final ImportRegistry graphHopperDefaults = new DefaultImportRegistry();

    @Override
    public ImportUnit createImportUnit(String name) {
        if (!ScenicScoreParser.KEY.equals(name)) return graphHopperDefaults.createImportUnit(name);
        return ImportUnit.create(ScenicScoreParser.KEY,
                props -> new IntEncodedValueImpl(ScenicScoreParser.KEY, ScenicScoreParser.BITS, false),
                (lookup, props) -> new ScenicScoreParser(lookup.getIntEncodedValue(ScenicScoreParser.KEY)));
    }
}
