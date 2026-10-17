package com.scenicdrive.routing;

import com.graphhopper.GraphHopper;
import com.graphhopper.http.GraphHopperBundle;
import com.graphhopper.http.GraphHopperManaged;
import io.dropwizard.core.Application;
import io.dropwizard.core.setup.Bootstrap;
import io.dropwizard.core.setup.Environment;
import io.dropwizard.lifecycle.JettyManaged;
import org.eclipse.jetty.util.component.LifeCycle;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * The served router (T-0392): GraphHopper 11.0's own Dropwizard bundle - /route, /isochrone, /info exactly as
 * upstream serves them - over the graph ScenicRouterMain imported, read from the same config.yml.
 *
 *   java -cp /app/scenic-router.jar com.scenicdrive.routing.ScenicServerApplication server /app/config.yml
 *
 * Two additions, both made before the lifecycle starts (Dropwizard runs every bundle, then this run(), then the
 * managed objects): the bundle's GraphHopper gets our ScenicScoreImportRegistry - GraphHopper consults a registry
 * only at import, so a box that ever imports does it with scenic_score and the gate facts - and /info gets
 * `graph_hash` (GraphHashInfoFilter). It refuses to start when it cannot find exactly one GraphHopperManaged or
 * the graph has no properties file to hash.
 */
public final class ScenicServerApplication extends Application<ScenicServerConfiguration> {

    public static void main(String[] args) throws Exception {
        new ScenicServerApplication().run(args);
    }

    @Override
    public void initialize(Bootstrap<ScenicServerConfiguration> bootstrap) {
        bootstrap.addBundle(new GraphHopperBundle());
    }

    @Override
    public void run(ScenicServerConfiguration configuration, Environment environment) throws Exception {
        GraphHopper hopper = bundleGraphHopper(environment);
        hopper.setImportRegistry(new ScenicScoreImportRegistry());
        String graphLocation = configuration.getGraphHopperConfiguration().getString("graph.location", "");
        if (graphLocation.isEmpty()) throw new IllegalStateException("config.yml names no graph.location");
        String hash = GraphHashInfoFilter.hashOf(Path.of(graphLocation));
        environment.jersey().register(new GraphHashInfoFilter(hash, environment.getObjectMapper()));
        System.out.println("SCENIC_SERVER graph=" + graphLocation + " graph_hash=" + hash);
    }

    /** The one GraphHopper GraphHopperBundle registered as a managed object. */
    static GraphHopper bundleGraphHopper(Environment environment) {
        List<GraphHopper> found = new ArrayList<>();
        for (LifeCycle managed : environment.lifecycle().getManagedObjects()) {
            if (managed instanceof JettyManaged jetty && jetty.getManaged() instanceof GraphHopperManaged gh) {
                found.add(gh.getGraphHopper());
            }
        }
        if (found.size() != 1) {
            throw new IllegalStateException("expected exactly one GraphHopperManaged from GraphHopperBundle, found " + found.size());
        }
        return found.get(0);
    }
}
