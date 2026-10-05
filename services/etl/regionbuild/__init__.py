"""The region build that makes `<region>-tagged.osm.pbf`: T-0208's pipeline, committed (T-0242).

A sibling of the `etl` package rather than a part of it: nothing here computes a score. Every number in
the artifact comes from `etl`'s own entry points - `python -m etl.waydoc`, `python -m etl.assemble
--reference`, `python -m etl.tagwriter` - and from `etl.region_reference`; this package cuts tiles, runs
those N at a time, merges the rows by way_id and refuses a build whose seam ways disagree.
"""
