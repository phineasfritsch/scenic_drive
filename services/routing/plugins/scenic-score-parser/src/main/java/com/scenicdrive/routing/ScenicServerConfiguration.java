package com.scenicdrive.routing;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.graphhopper.GraphHopperConfig;
import com.graphhopper.http.GraphHopperBundleConfiguration;
import com.graphhopper.http.RealtimeConfiguration;
import io.dropwizard.core.Configuration;
import jakarta.validation.constraints.NotNull;

/**
 * config.yml as the served router reads it: the `graphhopper:` node the import also reads, plus Dropwizard's own
 * `server:` section. The same shape as GraphHopper 11.0's GraphHopperServerConfiguration, which lives in the
 * graphhopper-web application module this jar does not ship.
 */
public final class ScenicServerConfiguration extends Configuration implements GraphHopperBundleConfiguration {

    @NotNull
    @JsonProperty
    private final GraphHopperConfig graphhopper = new GraphHopperConfig();

    @JsonProperty
    private final RealtimeConfiguration gtfsRealtime = new RealtimeConfiguration();

    @Override
    public GraphHopperConfig getGraphHopperConfiguration() {
        return graphhopper;
    }

    @Override
    public RealtimeConfiguration gtfsrealtime() {
        return gtfsRealtime;
    }
}
