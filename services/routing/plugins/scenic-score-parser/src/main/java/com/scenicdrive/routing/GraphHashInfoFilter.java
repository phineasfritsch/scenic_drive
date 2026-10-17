package com.scenicdrive.routing;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.graphhopper.resources.InfoResource;
import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerResponseContext;
import jakarta.ws.rs.container.ContainerResponseFilter;
import jakarta.ws.rs.core.MediaType;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

/**
 * P-PROD-04's served half: GraphHopper's own /info answer, every upstream field kept, plus `graph_hash` - the
 * sha256 of the served graph's `properties` file, the value import-graph.sh prints for the graph it built. It
 * moves with every import (import date, data date, encoded values, profile hashes).
 */
public final class GraphHashInfoFilter implements ContainerResponseFilter {

    /** The /info field. */
    public static final String FIELD = "graph_hash";

    private final String graphHash;
    private final ObjectMapper mapper;

    public GraphHashInfoFilter(String graphHash, ObjectMapper mapper) {
        this.graphHash = graphHash;
        this.mapper = mapper;
    }

    /** sha256 hex of `<graphDir>/properties`; throws when the graph has none - an unhashed graph is not served. */
    public static String hashOf(Path graphDir) throws IOException {
        Path properties = graphDir.resolve("properties");
        if (!Files.isRegularFile(properties)) {
            throw new IOException(properties + " does not exist - import the graph before serving it (import-graph.sh)");
        }
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(properties)));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }

    @Override
    public void filter(ContainerRequestContext request, ContainerResponseContext response) {
        if (!(response.getEntity() instanceof InfoResource.Info info)) return;
        ObjectNode node = mapper.valueToTree(info);
        node.put(FIELD, graphHash);
        response.setEntity(node, response.getEntityAnnotations(), MediaType.APPLICATION_JSON_TYPE);
    }
}
