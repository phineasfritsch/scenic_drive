package com.scenicdrive.record;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphhopper.GHRequest;
import com.graphhopper.GHResponse;
import com.graphhopper.GraphHopper;
import com.graphhopper.GraphHopperConfig;
import com.graphhopper.ResponsePath;
import com.graphhopper.jackson.Jackson;
import com.graphhopper.util.CustomModel;
import com.graphhopper.util.PointList;
import com.graphhopper.util.details.PathDetail;
import com.graphhopper.util.shapes.GHPoint;
import com.scenicdrive.routing.ScenicScoreImportRegistry;
import org.yaml.snakeyaml.Yaml;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Stream;

/**
 * Records real GraphHopper responses off a built graph, in the documented points_encoded=false /route
 * shape, so Linux tests can run the engine over numbers a router actually produced.
 *
 * WHY THIS EXISTS AND WHAT IT IS NOT. T-0213's image has no HTTP surface - no Dropwizard `server:`
 * section, graphhopper-core only, and ScenicRouterMain has modes import|probe|route and no server - so
 * there is no /route endpoint to curl and no served response to save. The serving half is T-0209. This
 * recorder is compiled against the SHIPPED jar (extracted from scenic-routing:t0213) and loads the SAME
 * graph with the SAME ImportRegistry and the SAME config.yml, so every number it writes - time, distance,
 * geometry, path details - is GraphHopper 11.0's own answer over the real canyon-window graph.
 *
 * The ENVELOPE, however, is this file's: graphhopper-web's ResponsePathSerializer is in a module the
 * router jar does not carry, so the shape is written out here from the documented API. The fixture header
 * says so in its own field. Nobody may read these fixtures as "a served response".
 *
 *   javac -cp scenic-router.jar -d classes Recorder.java
 *   java -cp scenic-router.jar:classes com.scenicdrive.record.Recorder \
 *       --config /app/config.yml --graph /graph --from LAT,LON --to LAT,LON \
 *       --models /models --out /out --provenance "image=scenic-routing:t0213;jar_sha256=..."
 *
 * Without --out it routes and prints one summary line per model, which is how a pair is chosen.
 *
 * `--alternatives on` (T-0239, rulings R1 and R7) records the MENU's population instead: beside the plain
 * fastest.json it writes alternatives-fastest.json (car_fast) and alternatives-<model>.json (car_scenic per
 * model), each carrying EVERY path alternative_route returned under ALTERNATIVE_HINTS in `paths[]`, and every
 * file in that mode also asks for the `street_name` detail so a menu row can name its roads from the graph.
 */
public final class Recorder {

    private static final List<String> DETAILS = List.of("scenic_score", "road_class", "osm_way_id");
    private static final List<String> WITH_NAMES = List.of("scenic_score", "road_class", "osm_way_id",
            "street_name");
    /** T-0239's R1, fixed here and written into every header recorded under it. */
    private static final Object[][] ALTERNATIVE_HINTS = {
            {"alternative_route.max_paths", 4}, {"alternative_route.max_weight_factor", 2.0},
            {"alternative_route.max_share_factor", 0.7}, {"alternative_route.max_exploration_factor", 2.0}};

    public static void main(String[] args) throws Exception {
        Map<String, String> cli = parseArgs(args);
        GraphHopperConfig config = readConfig(Path.of(required(cli, "--config")));
        config.putObject("graph.location", required(cli, "--graph"));
        config.putObject("datareader.file", "");

        GraphHopper hopper = new GraphHopper();
        hopper.setImportRegistry(new ScenicScoreImportRegistry());
        hopper.init(config);
        hopper.importOrLoad();
        try {
            GHPoint from = point(required(cli, "--from"));
            GHPoint to = point(required(cli, "--to"));
            String out = cli.get("--out");
            if (out != null) Files.createDirectories(Path.of(out));
            String provenance = cli.getOrDefault("--provenance", "");
            boolean alternatives = "on".equals(cli.get("--alternatives"));
            List<String> details = alternatives ? WITH_NAMES : DETAILS;

            record(hopper, "car_fast", from, to, null, "-", out, "fastest.json", provenance, details, false);
            if (alternatives) {
                record(hopper, "car_fast", from, to, null, "-", out, "alternatives-fastest.json", provenance,
                        details, true);
            }
            for (Path model : modelFiles(Path.of(required(cli, "--models")))) {
                CustomModel requestModel = Jackson.newObjectMapper()
                        .readValue(model.toFile(), CustomModel.class);
                String name = model.getFileName().toString();
                String file = alternatives ? "alternatives-" + name : name;
                record(hopper, "car_scenic", from, to, requestModel, name, out, file, provenance, details,
                        alternatives);
            }
        } finally {
            hopper.close();
        }
    }

    private static void record(GraphHopper hopper, String profile, GHPoint from, GHPoint to,
                               CustomModel requestModel, String label, String out, String file,
                               String provenance, List<String> details, boolean alternatives)
            throws Exception {
        GHRequest request = new GHRequest(from, to).setProfile(profile);
        request.putHint("ch.disable", true);
        request.putHint("instructions", false);
        request.setPathDetails(details);
        if (alternatives) {
            request.setAlgorithm("alternative_route");
            for (Object[] hint : ALTERNATIVE_HINTS) request.putHint((String) hint[0], hint[1]);
        }
        if (requestModel != null) request.setCustomModel(requestModel);
        GHResponse response = hopper.route(request);
        if (response.hasErrors()) {
            throw new IllegalStateException("profile=" + profile + " model=" + label
                    + " errors=" + response.getErrors());
        }
        List<ResponsePath> paths = alternatives ? response.getAll() : List.of(response.getBest());
        for (int index = 0; index < paths.size(); index++) {
            ResponsePath best = paths.get(index);
            List<PathDetail> ways = best.getPathDetails().getOrDefault("osm_way_id", List.of());
            System.out.printf(Locale.ROOT, "ROUTE profile=%s model=%s path=%d time_ms=%d distance_m=%.1f "
                            + "points=%d way_runs=%d%n", profile, label, index, best.getTime(),
                    best.getDistance(), best.getPoints().size(), ways.size());
        }
        if (out == null) return;
        String json = json(paths, profile, from, to, label, provenance, details, alternatives);
        Files.writeString(Path.of(out, file), json, StandardCharsets.UTF_8);
        System.out.println("WROTE " + file + " " + json.getBytes(StandardCharsets.UTF_8).length + " bytes");
    }

    /** The documented response shape, plus a `recorded` header this repository's fixtures carry. */
    private static String json(List<ResponsePath> paths, String profile, GHPoint from, GHPoint to,
                               String model, String provenance, List<String> details,
                               boolean alternatives) {
        StringBuilder out = new StringBuilder();
        out.append("{\n  \"recorded\": {");
        out.append("\n    \"envelope\": \"written by Tests/Fixtures/t0182-recorder/Recorder.java, NOT by ")
                .append("graphhopper-web: this slice of the router has no HTTP surface (T-0209 owns it). ")
                .append("Every NUMBER below is GraphHopper 11.0's over the real graph.\"");
        out.append(",\n    \"profile\": \"").append(profile).append('"');
        out.append(",\n    \"model\": \"").append(model).append('"');
        out.append(",\n    \"from\": \"").append(from.lat).append(',').append(from.lon).append('"');
        out.append(",\n    \"to\": \"").append(to.lat).append(',').append(to.lon).append('"');
        out.append(",\n    \"details\": \"").append(String.join(",", details)).append('"');
        if (alternatives) {
            out.append(",\n    \"algorithm\": \"alternative_route");
            for (Object[] hint : ALTERNATIVE_HINTS) out.append(';').append(hint[0]).append('=').append(hint[1]);
            out.append('"');
        }
        for (String field : provenance.split(";")) {
            int split = field.indexOf('=');
            if (split <= 0) continue;
            out.append(",\n    \"").append(field, 0, split).append("\": \"")
                    .append(field.substring(split + 1)).append('"');
        }
        out.append("\n  },\n  \"paths\": [\n");
        for (int index = 0; index < paths.size(); index++) {
            if (index > 0) out.append(",\n");
            path(out, paths.get(index));
        }
        out.append("\n  ]\n}\n");
        return out.toString();
    }

    private static void path(StringBuilder out, ResponsePath best) {
        out.append("    {\n");
        out.append("      \"distance\": ").append(number(best.getDistance())).append(",\n");
        out.append("      \"time\": ").append(best.getTime()).append(",\n");
        out.append("      \"points_encoded\": false,\n");
        out.append("      \"points\": ").append(lineString(best.getPoints())).append(",\n");
        out.append("      \"snapped_waypoints\": ").append(lineString(best.getWaypoints())).append(",\n");
        out.append("      \"details\": {\n");
        List<String> keys = new ArrayList<>(best.getPathDetails().keySet());
        for (int index = 0; index < keys.size(); index++) {
            String key = keys.get(index);
            out.append("        \"").append(key).append("\": [");
            List<PathDetail> runs = best.getPathDetails().get(key);
            for (int run = 0; run < runs.size(); run++) {
                PathDetail detail = runs.get(run);
                if (run > 0) out.append(", ");
                out.append('[').append(detail.getFirst()).append(", ").append(detail.getLast())
                        .append(", ").append(value(detail.getValue())).append(']');
            }
            out.append(']').append(index == keys.size() - 1 ? "\n" : ",\n");
        }
        out.append("      }\n    }");
    }

    /** Six decimals, which is the precision GraphHopper's own API publishes geometry at. */
    private static String lineString(PointList points) {
        StringBuilder out = new StringBuilder("{\"type\": \"LineString\", \"coordinates\": [");
        for (int index = 0; index < points.size(); index++) {
            if (index > 0) out.append(", ");
            out.append('[').append(String.format(Locale.ROOT, "%.6f", points.getLon(index))).append(", ")
                    .append(String.format(Locale.ROOT, "%.6f", points.getLat(index))).append(']');
        }
        return out.append("]}").toString();
    }

    private static String number(double value) {
        return String.format(Locale.ROOT, "%.3f", value);
    }

    private static String value(Object raw) {
        if (raw == null) return "null";
        if (raw instanceof Number) return raw.toString();
        return '"' + raw.toString().replace("\\", "\\\\").replace("\"", "\\\"") + '"';
    }

    private static GraphHopperConfig readConfig(Path configPath) throws Exception {
        try (InputStream in = Files.newInputStream(configPath)) {
            Map<String, Object> document = new Yaml().load(in);
            Object graphhopper = document.get("graphhopper");
            if (graphhopper == null) throw new IllegalArgumentException(configPath + " has no graphhopper:");
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
            if (!args[i].startsWith("--")) throw new IllegalArgumentException("unexpected " + args[i]);
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

    private Recorder() {
    }
}
