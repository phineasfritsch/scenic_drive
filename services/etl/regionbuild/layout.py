"""Where every stage of a region build reads and writes, under ONE work store.

The store is the only path a stage is given. On the Windows box it is WSL-native ext4 mounted into the
ETL image at /work: T-0208 measured ten tiles over the 9p mount of C: completing nothing in nine minutes,
because the DEM and WorldCover rasters are re-read on every batch. The clip goes in as
`<region>-filtered.osm.pbf` and the region's inputs (DEM, WorldCover, byways) as `inputs/`.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Layout:
    work: pathlib.Path
    region: str

    def _named(self, suffix: str) -> pathlib.Path:
        return self.work / ("%s-%s" % (self.region, suffix))

    @property
    def clip(self) -> pathlib.Path:
        return self._named("filtered.osm.pbf")

    @property
    def source(self) -> pathlib.Path:
        return self.work / ("%s.osm.pbf" % self.region)

    @property
    def places_pbf(self) -> pathlib.Path:
        return self._named("places.osm.pbf")

    @property
    def places_xml(self) -> pathlib.Path:
        return self._named("places.osm.xml")

    @property
    def fallback(self) -> pathlib.Path:
        return self._named("corpus-fallback.sqlite")

    @property
    def corpus_doc(self) -> pathlib.Path:
        return self._named("corpus-doc.json")

    @property
    def corpus_extract(self) -> pathlib.Path:
        return self._named("corpus-extract.json")

    @property
    def corpus(self) -> pathlib.Path:
        return self._named("corpus.sqlite")

    @property
    def clip_xml(self) -> pathlib.Path:
        return self._named("filtered.osm.xml")

    @property
    def motorways_pbf(self) -> pathlib.Path:
        return self._named("motorways.osm.pbf")

    @property
    def motorways(self) -> pathlib.Path:
        return self._named("motorways.osm.xml")

    @property
    def reference(self) -> pathlib.Path:
        return self._named("reference.json")

    @property
    def merged_table(self) -> pathlib.Path:
        return self._named("merged-table.json")

    @property
    def merged_doc(self) -> pathlib.Path:
        return self._named("merged-doc.json")

    @property
    def tagged_xml(self) -> pathlib.Path:
        return self._named("tagged.osm.xml")

    @property
    def tagged(self) -> pathlib.Path:
        return self._named("tagged.osm.pbf")

    @property
    def readback(self) -> pathlib.Path:
        return self._named("readback.osm.xml")

    @property
    def tiles(self) -> pathlib.Path:
        return self.work / "tiles"

    @property
    def configs(self) -> pathlib.Path:
        return self.work / "configs"

    @property
    def docs(self) -> pathlib.Path:
        return self.work / "docs"

    @property
    def scored(self) -> pathlib.Path:
        return self.work / "scored"

    @property
    def windows(self) -> pathlib.Path:
        return self.work / "windows"

    def tile_pbf(self, tile: str) -> pathlib.Path:
        return self.tiles / ("%s.osm.pbf" % tile)

    def tile_xml(self, tile: str) -> pathlib.Path:
        return self.tiles / ("%s.osm.xml" % tile)

    def doc_of(self, tile: str) -> pathlib.Path:
        return self.docs / ("%s-doc.json" % tile)

    def scored_of(self, tile: str) -> pathlib.Path:
        return self.scored / ("%s-scored.json" % tile)
