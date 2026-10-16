package com.scenicdrive.routing;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphhopper.reader.ReaderWay;
import com.graphhopper.routing.ev.ArrayEdgeIntAccess;
import com.graphhopper.routing.ev.BooleanEncodedValue;
import com.graphhopper.routing.ev.EdgeIntAccess;
import com.graphhopper.routing.ev.EncodedValue;
import com.graphhopper.routing.ev.EnumEncodedValue;
import com.graphhopper.routing.ev.SimpleBooleanEncodedValue;
import com.graphhopper.routing.ev.Smoothness;
import com.graphhopper.routing.ev.TrackType;
import com.graphhopper.routing.util.parsers.OSMSmoothnessParser;
import com.graphhopper.routing.util.parsers.OSMTrackTypeParser;
import com.graphhopper.routing.util.parsers.TagParser;
import com.graphhopper.storage.IntsRef;
import com.graphhopper.util.PMap;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import org.junit.jupiter.api.Test;

/**
 * T-0381 R7: GraphHopper's own track_type and smoothness parsers and our three GateFacts parsers, over the one
 * table (gate_encoding.json) that services/etl/tests/test_profilegate.py also holds etl.profilegate.encode to.
 * Every row is compared whole, so a parser that encodes one more or one fewer fact than the table says is red.
 */
class GateEncodingTest {

    private static JsonNode rows() throws Exception {
        try (InputStream in = GateEncodingTest.class.getResourceAsStream("/gate_encoding.json")) {
            return new ObjectMapper().readTree(in).get("rows");
        }
    }

    private static Map<String, String> encode(JsonNode tags) {
        EncodedValue.InitializerConfig config = new EncodedValue.InitializerConfig();
        EnumEncodedValue<TrackType> trackType = TrackType.create();
        EnumEncodedValue<Smoothness> smoothness = Smoothness.create();
        trackType.init(config);
        smoothness.init(config);
        Map<String, BooleanEncodedValue> facts = new TreeMap<>();
        List<TagParser> parsers = new ArrayList<>(List.of(new OSMTrackTypeParser(trackType),
                new OSMSmoothnessParser(smoothness)));
        for (String key : GateFacts.keys()) {
            BooleanEncodedValue fact = new SimpleBooleanEncodedValue(key);
            fact.init(config);
            facts.put(key, fact);
            parsers.add(new GateFactParser(fact, GateFacts.forKey(key)));
        }
        ReaderWay way = new ReaderWay(1);
        Iterator<Map.Entry<String, JsonNode>> fields = tags.fields();
        while (fields.hasNext()) {
            Map.Entry<String, JsonNode> field = fields.next();
            way.setTag(field.getKey(), field.getValue().asText());
        }
        EdgeIntAccess edges = new ArrayEdgeIntAccess(2);
        for (TagParser parser : parsers) parser.handleWayTags(0, edges, way, new IntsRef(2));
        Map<String, String> out = new TreeMap<>();
        out.put(TrackType.KEY, trackType.getEnum(false, 0, edges).name());
        out.put(Smoothness.KEY, smoothness.getEnum(false, 0, edges).name());
        for (Map.Entry<String, BooleanEncodedValue> fact : facts.entrySet()) {
            out.put(fact.getKey(), String.valueOf(fact.getValue().getBool(false, 0, edges)));
        }
        return out;
    }

    @Test
    void everyRowEncodesExactlyItsTable() throws Exception {
        int seen = 0;
        for (JsonNode row : rows()) {
            Map<String, String> want = new TreeMap<>();
            Iterator<Map.Entry<String, JsonNode>> fields = row.get("encoded").fields();
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> field = fields.next();
                want.put(field.getKey(), field.getValue().asText());
            }
            assertEquals(want, encode(row.get("tags")), row.get("tags").toString());
            seen++;
        }
        assertEquals(1395, seen);
    }

    private static String nameOf(ScenicScoreImportRegistry registry, String key) {
        return registry.createImportUnit(key).getCreateEncodedValue().apply(new PMap()).getName();
    }

    @Test
    void theRegistryAnswersExactlyTheThreeFacts() {
        assertEquals(Set.of("gate_locked_barrier", "gate_ford", "gate_service_way"), GateFacts.keys());
        assertNull(GateFacts.forKey("road_environment"));
        ScenicScoreImportRegistry registry = new ScenicScoreImportRegistry();
        for (String key : GateFacts.keys()) assertEquals(key, nameOf(registry, key));
        assertEquals(TrackType.KEY, nameOf(registry, TrackType.KEY));
    }
}
