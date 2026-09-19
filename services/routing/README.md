# services/routing — GraphHopper with `scenic_score`

First slice of T-0031. What is here proves one property over one real extract: `scenic_score` survives the
import as a GraphHopper encoded value, and a per-request custom model referencing it moves the route in a
direction the budget search can bisect on.

    wsl -e bash -lc "cd /mnt/c/.../scenic_drive/.worktrees/T-0031 && bash services/routing/build-slice.sh"
    cd services/routing && python -m pytest tests -rs -s

`build-slice.sh` tags the manifest-pinned Vermont extract, builds both images and imports the graph into
`work/graph-cache/`. The pytest skips with a reason when that graph or the image is missing, so it is safe
on a box without docker. Everything it writes lands in `work/`, which is ignored.

## What is real and what is a stand-in

| Piece | Status |
|---|---|
| `plugins/scenic-score-parser` | Real. `scenic_score`, unsigned, 4 bits, 0..10; no tag means 0. |
| `profiles/car_scenic_base.json` | Real. Safety gates only: private/no access, the unpaved surfaces, track. Motorway and trunk are **not** gated — they carry score 0 and are penalized by the request model. |
| `config.yml` | Real, and read by the runner, so the profile under test is the profile that ships. No `server:` section yet: there is no HTTP surface in this slice. |
| `profiles/car_scenic_request.json` + `scenic_lambda_bands.json` | The five plan lambdas as data. In production `services/api/src/customModel.ts` builds this body per request; GraphHopper's expression compiler refuses `/` inside `multiply_by`, which is why both carry numbers rather than `1 / (1 + λ)`. |
| `tools/synthetic_scenic_tags.py` | **SYNTHETIC.** `way_id % 11` on every highway way, stamped into the output PBF's header. Not a scenic index. T-0168 owns the real writer. |
| Serving, rsync, symlink flip, LA and Bay Area graphs | Not here. Second half of T-0031, behind T-0168. |
