# syntax=docker/dockerfile:1
# The router image: GraphHopper 11.0 with OUR scenic_score encoded value compiled in. There is no upstream
# image that carries a third-party TagParser, so the jar is built here - inside the builder stage, because
# there is no java on the WSL host and none is wanted.
#
# Both stages are pinned BY DIGEST for the reason services/etl/Dockerfile gives: a tag moves, and a moving
# toolchain is a silent change no diff shows.
#
#   docker build -t scenic-routing:t0213 services/routing
#   docker run --rm scenic-routing:t0213 --config /app/config.yml --graph /graph --mode import --osm /data/x.pbf
#
FROM maven:3.9-eclipse-temurin-21@sha256:c2a2c58516d160f43b50f12baa427ca86989e0bc942609e04aff61da5d9a7d74 AS build
WORKDIR /src
COPY plugins/scenic-score-parser/pom.xml /src/pom.xml
COPY plugins/scenic-score-parser/src /src/src
RUN --mount=type=cache,target=/root/.m2 mvn -B -DskipTests package

FROM eclipse-temurin:21-jre@sha256:49e21e16e3c86eb7816a44a67549910ed090fbeb40c29c525d58bf5e02e91b0f
COPY --from=build /src/target/scenic-router.jar /app/scenic-router.jar
COPY config.yml /app/config.yml
COPY profiles /app/profiles
# Heap is set per run with JAVA_TOOL_OPTIONS: the import wants several GB, a query wants far less, and the
# VPS in this task's second half has 4 GB for everything.
ENTRYPOINT ["java", "-jar", "/app/scenic-router.jar"]
