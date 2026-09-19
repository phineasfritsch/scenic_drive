"""Write a SYNTHETIC scenic_score onto every highway way of a PBF.

THESE SCORES ARE NOT A SCENIC INDEX. They are a deterministic stand-in - way id modulo 11 - so that the
FIRST SLICE of T-0031 can prove what it is about: that scenic_score survives the import as an encoded value
and that a per-request custom model referencing it moves the route. T-0168 and T-0146 own the real value.

The stand-in is recorded in the output file's own header generator string, not in a comment, so `osmium
fileinfo` on the artifact says what it is long after this script is out of sight.
"""

import argparse

import osmium

SOURCE_STAMP = "SYNTHETIC-T-0031-wayid-mod-11"
MODULUS = 11
TAG = "scenic_score"


def synthetic_score(way_id):
    """way id modulo 11 - deterministic, 0..10 inclusive, and uncorrelated with anything scenic."""
    return way_id % MODULUS


class SyntheticScenicTagger(osmium.SimpleHandler):
    """Copies a PBF through, adding the synthetic tag to ways that carry a highway tag."""

    def __init__(self, writer):
        super().__init__()
        self.writer = writer
        self.ways = 0
        self.tagged = 0

    def node(self, n):
        self.writer.add_node(n)

    def way(self, w):
        self.ways += 1
        if w.tags.get("highway") is None:
            self.writer.add_way(w)
            return
        tags = dict(w.tags)
        tags[TAG] = str(synthetic_score(w.id))
        self.tagged += 1
        self.writer.add_way(w.replace(tags=tags))

    def relation(self, r):
        self.writer.add_relation(r)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    header = osmium.io.Header()
    header.set("generator", "scenic-drive " + SOURCE_STAMP)
    writer = osmium.SimpleWriter(args.output, 4096, header)
    tagger = SyntheticScenicTagger(writer)
    tagger.apply_file(args.input)
    writer.close()
    print("TAGGED ways=%d tagged=%d stamp=%s out=%s" % (tagger.ways, tagger.tagged, SOURCE_STAMP, args.output))


if __name__ == "__main__":
    main()
