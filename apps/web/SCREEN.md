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

## Our screenshots
Taken with Playwright against `npm run dev`. On 2026-11-24 they were saved to the session scratchpad (not committed):
desktop 1280x800 light and dark, mobile 390x844, the safety gate, and the zero-budget honest fallback.

## Independent match check
_Pending: one checker that did not build the screen._
