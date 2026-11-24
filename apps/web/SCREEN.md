# SCREEN: Plan a drive (web)

## Job
The owner, or a demo viewer, picks a drive, sets how much extra time to spend, and sees the most scenic route that
fits. They compare it with the other routes and open it in a map app. This is the only screen. A demo session
uses it a handful of times.

## Data on screen
For each drive (corridor): from/to names, the fastest route, and the distinct scenic alternatives. For each route:
`timeS`, `distanceM`, `score.value` (RouteScore 0..1, shown as 0-100), the per-stretch scenic runs, named roads,
overlap with the fastest route, and decision points (used for the Google Maps link). Also the curated scenic stops
(name, hook).

Clutter pass:
- Kept: time, extra minutes, distance, score, and roads (as "via X & Y").
- Kept as a visual: the per-stretch runs, drawn as the scenic strip and as the line colour on the map.
- Collapsed into hover on the map: stop hooks.
- Dropped: motorway metres, way overlap % (it was a stat-row sub-line that wrapped and decided nothing), episodes
  and dud fraction (already inside the score).

## References (C:\Users\phineasf\Documents\GitHub\smiling-plug-company\ui-reference\library\...)
| id | what we took |
|---|---|
| web/pampam/jun-2025/0002 | Layout: a floating rounded panel at top left over a full-bleed, quiet Protomaps basemap. Attribution text on the map. |
| ios/strava/jul-2026/0033 | Stat row: big tabular numbers with small labels under them. One full-width pill primary action. |
| web/airbnb/jun-2025/0109 | Round white map controls at top right (zoom pair stacked, single actions separate). |
| web/mindtrip/aug-2025/0027 | Trip-planner tone: big friendly headline, plain-language subcopy, map as the companion surface. |
| web/apple/nov-2024/0013 | Calm map palette that lets markers and lines carry the colour. |

## Rules applied (ux-principles)
- P15: one primary action per view, "Open in Google Maps", pinned at the panel's bottom (`route.css` `.panel-cta`).
  The recommended route is marked once.
- P14: two drives shown as radio cards, no dropdown. Over-budget routes are dimmed and labelled "Needs +N min".
- P16: the slider re-plans synchronously on input, and the map and card update in the same frame. No spinner, because there is no network.
- P12: every control is at least 44 px (map controls 44x44, slider 44 px tall, route rows 56 px, buttons 48 px).
- P8/P18/P5: press 120 ms, hover and fill 150 ms, gate opens in 250 ms ease-out. Tokens are in `tokens.css`, and
  reduced motion zeroes them.
- P20 camera: changing the drive flies the map to the new drive in 450 ms (orientation: where the new drive is).
  Zoom takes 200 ms and "show whole drive" 350 ms. With prefers-reduced-motion the camera jumps instead
  (`MapView.tsx` `ms()`).

## Our screenshots
Taken with Playwright against `npm run dev`. On 2026-11-24 they were saved to the session scratchpad (not committed):
desktop 1280x800 light and dark, mobile 390x844, the safety gate, and the zero-budget honest fallback.

## Independent match check
One checker (a separate agent that did not build the screen), 2026-11-24. It opened the four reference PNGs beside
our six screenshots.

Round 1 found:
- The safety line and the result were below the fold (1280x800 and 390 px).
- The sticky button covered the slider scale.
- Route labels repeated ("Fastest Fastest route", "Mulholland Hwy & Mulholland Hwy (The Snake)", four identical rows).
- The planned route was drawn behind the safety gate.
- Unguarded `localStorage`.
- Camera moves ignored reduced motion, and the drive change took 600 ms.
- Stop hooks were hover-only.
- A ticket id appeared in user-facing copy.
- There were 11 font sizes.
- Small things: the sparkle eyebrow, the dashed box, flags clipped into the row border, and the origin glyph differed between panel and map.

All fixed in round 1:
- Solid footer holding the safety line and the action.
- Mobile hides the intro.
- `via()` picks a pair of roads no other route shares (`format.test.ts`, seen red at 4/5 distinct, then green).
- The map draws no plan until the gate is accepted.
- Storage is guarded.
- `ms()` handles reduced motion, and the drive change is now 450 ms.
- Stops open on tap.
- Provenance copy no longer names tickets.
- Five font sizes (11/13/15/20/28).
- Flags inline, hollow origin ring on both panel and map, and stops drawn as rings.

| Ship checklist | Result | Evidence |
|---|---|---|
| 1 reason per animation | pass (after fix) | Rules applied above, including camera |
| 2 P8 durations | pass (after fix) | `MapView.tsx` 450/350/200 ms; tokens 120/150/250 ms |
| 3 close faster than open | pass | gate 250 ms in, closes instantly (`tokens.css` --dur-close 110 ms) |
| 4 grows from trigger | n/a | the gate opens on load, with no trigger |
| 5 interruptible | pass | CSS transitions and MapLibre camera only; input never blocked |
| 6 100 ms response | pass (from code) | slider calls setState synchronously; `choose` is pure and memoised |
| 7 44 px targets | pass | controls 44, slider 44, rows 56, drive cards 52, buttons 48/44 |
| 8 reduced motion | pass (after fix) | tokens zeroed, gate fades, camera jumps (`ms()`) |
| 9 no native menus | pass | drive picker is a radiogroup; no select or datalist |
| 10 one primary action | pass | one orange action, at most 6 routes, 2 drives |
| 11 success moment | pass | the hero card plus the action, both visible at 1280x800 after the fix |
| 13 no linear easing | pass | cubic-bezier everywhere |

Invariants: attribution pass; disclaimer gate pass (after fix); safety line visible pass (after fix); ETA ceiling pass;
no-traffic badge pass.
