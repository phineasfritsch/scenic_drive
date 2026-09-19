# services/routing — GraphHopper with `scenic_score`

First slice of T-0031. What is here proves one property over one real extract: `scenic_score` survives the
import as a GraphHopper encoded value, and a per-request custom model referencing it moves the route in a
direction the budget search can bisect on.

    wsl -e bash -lc "cd /mnt/c/.../scenic_drive/.worktrees/T-0031 && bash services/routing/build-slice.sh"
    cd services/routing && python -m pytest tests -rs -s

`build-slice.sh` tags the manifest-pinned Vermont extract, builds both images and imports the graph into
`work/graph-cache/`. The pytest skips with a reason when that graph or the image is missing, so it is safe
on a box without docker. Everything it writes lands in `work/`, which is ignored.

T-0213 added the second, REAL input and the one import recipe both paths use:

    bash services/routing/import-graph.sh <tagged.osm.pbf> <graph-dir> [image]
    docker run ... scenic-routing:t0213 --config /app/config.yml --graph /graph --mode probe --probe-ways 74344132

`--mode probe` walks the built graph and prints `PROBE way=<osm way id> edges=<n> scenic_score=<v>`, which is
how `tests/test_scenic_score_readback.py` checks a NAMED way's real score instead of a snapped coordinate's.
It needs `osm_way_id` in `config.yml`'s `graph.encoded_values`, which is why it is there.

**The image tag moves with `config.yml`.** A graph carries the encoded-value list it was built with, so an
image whose config names a different list cannot load it: `scenic-routing:t0031` is the T-0031 config and the
Vermont graph built under it, `scenic-routing:t0213` adds `osm_way_id`. Changing `graph.encoded_values` means
re-importing every graph and bumping the tag - never reusing one.

`ops/deploy-routing <graph-dir>` ships a built graph to the routing box (new release dir, atomic symlink
flip, restart, the 2 newest releases kept). It refuses without `SCENIC_ROUTING_HOST`, `SCENIC_ROUTING_USER`,
`SCENIC_ROUTING_KEY`, `SCENIC_ROUTING_ROOT`, and refuses unless HEAD is on origin.
`SCENIC_ROUTING_REHEARSE=<dir>` runs the same code against a local directory - no ssh, no rsync, no box.

## What is real and what is a stand-in

| Piece | Status |
|---|---|
| `plugins/scenic-score-parser` | Real. `scenic_score`, unsigned, 4 bits, 0..10; no tag means 0. |
| `profiles/car_scenic_base.json` | Real. Safety gates only: private/no access, the unpaved surfaces, track. Motorway and trunk are **not** gated — they carry score 0 and are penalized by the request model. |
| `config.yml` | Real, and read by the runner, so the profile under test is the profile that ships. No `server:` section yet: there is no HTTP surface in this slice. |
| `profiles/car_scenic_request.json` + `scenic_lambda_bands.json` | The five plan lambdas as data. In production `services/api/src/customModel.ts` builds this body per request; GraphHopper's expression compiler refuses `/` inside `multiply_by`, which is why both carry numbers rather than `1 / (1 + λ)`. |
| `tools/synthetic_scenic_tags.py` | **SYNTHETIC.** `way_id % 11` on every highway way, stamped into the output PBF's header. Not a scenic index. T-0168 owns the real writer. |
| Serving, rsync, symlink flip, LA and Bay Area graphs | Not here. Second half of T-0031, behind T-0168. |
