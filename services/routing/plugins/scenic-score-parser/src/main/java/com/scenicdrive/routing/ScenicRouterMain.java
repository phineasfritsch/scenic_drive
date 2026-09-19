package com.scenicdrive.routing;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphhopper.GHRequest;
import com.graphhopper.GHResponse;
import com.graphhopper.GraphHopper;
import com.graphhopper.GraphHopperConfig;
import com.graphhopper.ResponsePath;
import com.graphhopper.jackson.Jackson;
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
import java.util.stream.Stream;

/**
 * Imports the tagged PBF with scenic_score registered as an encoded value, then answers one fixed pair once
 * per per-request custom model. It reads the same config.yml the served router will read - its graphhopper:
 * node - because a profile that is only exercised through a test harness is not the profile that ships.
 *
 *   --config /app/config.yml --graph /graph [--osm /data/x.pbf] --mode import
 *   --config /app/config.yml --graph /graph --mode route --from LAT,LON --to LAT,LON
 *       --fast-profile car_fast --scenic-profile car_scenic --models /models
 */
public final class ScenicRouterMain {

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
            if (!"route".equals(cli.getOrDefault("--mode", "route"))) return;
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
