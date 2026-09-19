package com.scenicdrive.routing;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphhopper.GHRequest;
import com.graphhopper.GHResponse;
import com.graphhopper.GraphHopper;
import com.graphhopper.GraphHopperConfig;
import com.graphhopper.ResponsePath;
import com.graphhopper.jackson.Jackson;
import com.graphhopper.routing.ev.IntEncodedValue;
import com.graphhopper.routing.util.AllEdgesIterator;
import com.graphhopper.util.CustomModel;
import com.graphhopper.util.shapes.GHPoint;
import org.yaml.snakeyaml.Yaml;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeSet;
import java.util.stream.Stream;

/**
 * Imports the tagged PBF with scenic_score registered as an encoded value, then answers one fixed pair once
 * per per-request custom model. It reads the same config.yml the served router will read - its graphhopper:
 * node - because a profile that is only exercised through a test harness is not the profile that ships.
 *
 *   --config /app/config.yml --graph /graph [--osm /data/x.pbf] --mode import
 *   --config /app/config.yml --graph /graph --mode route --from LAT,LON --to LAT,LON
 *       --fast-profile car_fast --scenic-profile car_scenic --models /models
 *   --config /app/config.yml --graph /graph --mode probe --probe-ways 74344132,10715427
 */
public final class ScenicRouterMain {

    /** GraphHopper's own encoded value, named in config.yml's graph.encoded_values so --mode probe can bind
     *  an encoded scenic_score to the OSM way it came from. */
    public static final String OSM_WAY_ID = "osm_way_id";

    public static void main(String[] args) throws Exception {
        Map<String, String> cli = parseArgs(args);
        GraphHopperConfig config = readConfig(Path.of(required(cli, "--config")));
        config.putObject("graph.location", required(cli, "--graph"));
        if (cli.containsKey("--osm")) config.putObject("datareader.file", cli.get("--osm"));

        // GraphHopper.init resolves custom_model_files against custom_models.directory itself, and refuses a
        // profile that arrives with both the file list and an already-loaded model. So the profiles go in as
        // config.yml wrote them.
        GraphHopper hopper = new GraphHopper();
        hopper.setImportRegistry(new ScenicScoreImportRegistry());
        hopper.init(config);
        hopper.importOrLoad();
        try {
            System.out.println("SCENIC_EV present=" + hopper.getEncodingManager().hasEncodedValue(ScenicScoreParser.KEY)
                    + " bits=" + ScenicScoreParser.BITS + " max=" + ScenicScoreParser.MAX);
            System.out.println("GRAPH nodes=" + hopper.getBaseGraph().getNodes()
                    + " edges=" + hopper.getBaseGraph().getEdges());
            String mode = cli.getOrDefault("--mode", "route");
            if ("probe".equals(mode)) {
                probe(hopper, required(cli, "--probe-ways"));
                return;
            }
            if (!"route".equals(mode)) return;
            route(hopper, required(cli, "--fast-profile"), point(required(cli, "--from")),
                    point(required(cli, "--to")), null, "-");
            for (Path model : modelFiles(Path.of(required(cli, "--models")))) {
                CustomModel requestModel = Jackson.newObjectMapper().readValue(model.toFile(), CustomModel.class);
                route(hopper, required(cli, "--scenic-profile"), point(required(cli, "--from")),
                        point(required(cli, "--to")), requestModel, model.getFileName().toString());
            }
        } finally {
            hopper.close();
        }
    }

    private static void route(GraphHopper hopper, String profile, GHPoint from, GHPoint to,
                              CustomModel requestModel, String label) {
        GHRequest request = new GHRequest(from, to).setProfile(profile);
        request.putHint("ch.disable", true);
        if (requestModel != null) request.setCustomModel(requestModel);
        GHResponse response = hopper.route(request);
        if (response.hasErrors()) throw new IllegalStateException("profile=" + profile + " model=" + label
                + " errors=" + response.getErrors());
        ResponsePath best = response.getBest();
        System.out.printf(Locale.ROOT, "ROUTE profile=%s model=%s time_ms=%d distance_m=%.1f%n",
                profile, label, best.getTime(), best.getDistance());
    }

    /**
     * Reads back, for each NAMED OSM way, what the import actually encoded. GraphHopper does not index by way
     * id, so osm_way_id (config.yml's graph.encoded_values) is carried on every edge and the whole edge set is
     * walked once: way id -> scenic_score, out of the built graph, with no coordinate and no snap in the loop.
     * A way that reached no edge prints edges=0, which is the honest answer for a way the import dropped.
     */
    private static void probe(GraphHopper hopper, String wayIds) {
        IntEncodedValue wayIdValue = hopper.getEncodingManager().getIntEncodedValue(OSM_WAY_ID);
        IntEncodedValue scoreValue = hopper.getEncodingManager().getIntEncodedValue(ScenicScoreParser.KEY);
        Map<Integer, Integer> edgeCounts = new LinkedHashMap<>();
        Map<Integer, TreeSet<Integer>> scores = new LinkedHashMap<>();
        for (String raw : wayIds.split(",")) {
            int wayId = Integer.parseInt(raw.trim());
            edgeCounts.put(wayId, 0);
            scores.put(wayId, new TreeSet<>());
        }
        AllEdgesIterator edges = hopper.getBaseGraph().getAllEdges();
        while (edges.next()) {
            int wayId = edges.get(wayIdValue);
            if (!edgeCounts.containsKey(wayId)) continue;
            edgeCounts.put(wayId, edgeCounts.get(wayId) + 1);
            scores.get(wayId).add(edges.get(scoreValue));
        }
        for (Map.Entry<Integer, Integer> entry : edgeCounts.entrySet()) {
            TreeSet<Integer> seen = scores.get(entry.getKey());
            String encoded = seen.isEmpty() ? "-" : seen.stream().map(String::valueOf).reduce((a, b) -> a + "," + b).get();
            System.out.println("PROBE way=" + entry.getKey() + " edges=" + entry.getValue()
                    + " scenic_score=" + encoded);
        }
    }

    private static GraphHopperConfig readConfig(Path configPath) throws Exception {
        try (InputStream in = Files.newInputStream(configPath)) {
            Map<String, Object> document = new Yaml().load(in);
            Object graphhopper = document.get("graphhopper");
            if (graphhopper == null) throw new IllegalArgumentException(configPath + " has no graphhopper: node");
            ObjectMapper mapper = Jackson.newObjectMapper();
            return mapper.convertValue(graphhopper, GraphHopperConfig.class);
        }
    }

    private static List<Path> modelFiles(Path directory) throws Exception {
        try (Stream<Path> entries = Files.list(directory)) {
            List<Path> models = new ArrayList<>(entries
                    .filter(p -> p.getFileName().toString().endsWith(".json")).sorted().toList());
            if (models.isEmpty()) throw new IllegalArgumentException("no request models in " + directory);
            return models;
        }
    }

    private static GHPoint point(String latLon) {
        String[] parts = latLon.split(",");
        if (parts.length != 2) throw new IllegalArgumentException("expected LAT,LON but got " + latLon);
        return new GHPoint(Double.parseDouble(parts[0].trim()), Double.parseDouble(parts[1].trim()));
    }

    private static Map<String, String> parseArgs(String[] args) {
        Map<String, String> parsed = new LinkedHashMap<>();
        for (int i = 0; i < args.length; i++) {
            if (!args[i].startsWith("--")) throw new IllegalArgumentException("unexpected argument " + args[i]);
            if (i + 1 >= args.length) throw new IllegalArgumentException("missing value for " + args[i]);
            parsed.put(args[i], args[++i]);
        }
        return parsed;
    }

    private static String required(Map<String, String> cli, String key) {
        String value = cli.get(key);
        if (value == null) throw new IllegalArgumentException("missing required argument " + key);
        return value;
    }

    private ScenicRouterMain() {
    }
}
