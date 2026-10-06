/**
 * T-0276 R1-R5: the LCS D7 parse. The recorded response (Tests/Fixtures/t0276, fetched 2026-10-06T08:06:07Z) is held
 * WHOLE to Tests/Fixtures/t0276/oracle.py's independent reading; then one row at a time, every field the parse reads
 * refused by name, every range at its bound, the active window at its bounds, the chord at 500 m and the cap.
 */
import { describe, expect, it } from "vitest";
import feedRaw from "../../../Tests/Fixtures/t0276/lcsStatusD07.json?raw";
import expectedRaw from "../../../Tests/Fixtures/t0276/expected.json?raw";
import { closuresVersion } from "../src/closuresCron";
import { capClosures, parseLcsFeed, type ActiveClosure } from "../src/lcsFeed";

const FEED = (JSON.parse(feedRaw) as { data: unknown[] }).data;
const EXPECTED = JSON.parse(expectedRaw) as { now_s: number };
const NOW = 1500;

type Row = { lcs: Record<string, any> };
function base(): Row {
  return { lcs: {
    index: "T-1",
    location: { begin: { beginLongitude: "-118.4", beginLatitude: "34.0" }, end: { endLongitude: "-118.4", endLatitude: "34.0" } },
    closure: {
      typeOfClosure: "Full", facility: "On Ramp",
      closureTimestamp: { closureStartEpoch: "1000", closureEndEpoch: "2000", isClosureEndIndefinite: "false" },
      code1097: { isCode1097: "false" }, code1098: { isCode1098: "false" }, code1022: { isCode1022: "false" },
    },
  } };
}

/** The base row with `path` set to `value` (undefined deletes it). */
function variant(changes: [string, unknown][]): Row {
  const row = base();
  for (const [path, value] of changes) {
    const keys = path.split(".");
    let here: Record<string, any> = row.lcs;
    for (const key of keys.slice(0, -1)) here = here[key];
    if (value === undefined) delete here[keys[keys.length - 1]!];
    else here[keys[keys.length - 1]!] = value;
  }
  return row;
}

const B = 30;
/** The zero-length closure's square at (lon, lat): the 2B square on the 110946 / 91961 plane. */
const square = (lon: number, lat: number) => {
  const p = (x: number, y: number) => [lon + x / 91961, lat + y / 110946];
  return [p(-B, -B), p(B, -B), p(B, B), p(-B, B), p(-B, -B)];
};
const ACTIVE = (over: Partial<ActiveClosure> = {}) =>
  ({ index: "T-1", confirmed: false, facility: "On Ramp", rings: [square(-118.4, 34.0)], ...over });
const parsed = (closures: unknown[], refused: unknown[] = [], full = 1) =>
  ({ rows: 1, full, active: closures.length, refused, closures });

describe("the recorded D7 response (R1-R6)", () => {
  it("parses, caps and versions to the Python oracle's answer, whole", async () => {
    const parse = parseLcsFeed(FEED, EXPECTED.now_s);
    const cap = capClosures(parse.closures);
    expect({ now_s: EXPECTED.now_s, parse, cap, version: await closuresVersion(cap.geojson) }).toEqual(EXPECTED);
  });

  it("holds the measured counts: 2808 rows, 1708 Full, 163 active, 0 refused, 42 kept in 50 polygons, 121 dropped", () => {
    const parse = parseLcsFeed(FEED, EXPECTED.now_s);
    const cap = capClosures(parse.closures);
    expect([parse.rows, parse.full, parse.active, parse.refused.length, cap.kept, cap.geojson.features.length, cap.dropped])
      .toEqual([2808, 1708, 163, 0, 42, 50, 121]);
  });
});

describe("one row, refused by name (R3)", () => {
  const refusals: [string, unknown, string | null, string][] = [
    ["a null row", null, null, "row_not_object"],
    ["lcs an array", { lcs: [] }, null, "row_not_object"],
    ["no typeOfClosure", variant([["closure.typeOfClosure", undefined]]), "T-1", "type_missing"],
    ["typeOfClosure a number", variant([["closure.typeOfClosure", 7]]), "T-1", "type_missing"],
    ["no index", variant([["index", undefined]]), null, "index_missing"],
    ["an empty index", variant([["index", ""]]), "", "index_missing"],
    ["a numeric index", variant([["index", 5]]), null, "index_missing"],
    ["isCode1097 TRUE", variant([["closure.code1097.isCode1097", "TRUE"]]), "T-1", "code_not_boolean"],
    ["no isCode1098", variant([["closure.code1098.isCode1098", undefined]]), "T-1", "code_not_boolean"],
    ["isCode1022 a boolean", variant([["closure.code1022.isCode1022", true]]), "T-1", "code_not_boolean"],
    ["an empty start", variant([["closure.closureTimestamp.closureStartEpoch", ""]]), "T-1", "start_not_epoch"],
    ["an 11-digit start", variant([["closure.closureTimestamp.closureStartEpoch", "10000000000"]]), "T-1", "start_not_epoch"],
    ["a negative start", variant([["closure.closureTimestamp.closureStartEpoch", "-5"]]), "T-1", "start_not_epoch"],
    ["a fractional start", variant([["closure.closureTimestamp.closureStartEpoch", "1000.5"]]), "T-1", "start_not_epoch"],
    ["a numeric start", variant([["closure.closureTimestamp.closureStartEpoch", 1000]]), "T-1", "start_not_epoch"],
    ["indefinite yes", variant([["closure.closureTimestamp.isClosureEndIndefinite", "yes"]]), "T-1", "indefinite_not_boolean"],
    ["no indefinite", variant([["closure.closureTimestamp.isClosureEndIndefinite", undefined]]), "T-1", "indefinite_not_boolean"],
    ["an empty end, not indefinite", variant([["closure.closureTimestamp.closureEndEpoch", ""]]), "T-1", "end_not_epoch"],
    ["an 11-digit end", variant([["closure.closureTimestamp.closureEndEpoch", "20000000000"]]), "T-1", "end_not_epoch"],
    ["end one second before start", variant([["closure.closureTimestamp.closureEndEpoch", "999"]]), "T-1", "window_inverted"],
    ["no facility", variant([["closure.facility", undefined]]), "T-1", "facility_missing"],
    ["an empty facility", variant([["closure.facility", ""]]), "T-1", "facility_missing"],
    ["a numeric begin longitude", variant([["location.begin.beginLongitude", -118.4]]), "T-1", "position_not_decimal"],
    ["a 4-digit begin longitude", variant([["location.begin.beginLongitude", "-1118.4"]]), "T-1", "position_not_decimal"],
    ["9 decimals of begin latitude", variant([["location.begin.beginLatitude", "34.000000001"]]), "T-1", "position_not_decimal"],
    ["no end latitude", variant([["location.end.endLatitude", undefined]]), "T-1", "position_not_decimal"],
    ["a junk end longitude", variant([["location.end.endLongitude", "-118.4x"]]), "T-1", "position_not_decimal"],
    ["begin (0, 0)", variant([["location.begin.beginLongitude", "0"], ["location.begin.beginLatitude", "0"]]), "T-1", "position_outside_d7"],
    ["begin lon just west of -119.5", variant([["location.begin.beginLongitude", "-119.50000001"]]), "T-1", "position_outside_d7"],
    ["begin lon just east of -117.6", variant([["location.begin.beginLongitude", "-117.59999999"]]), "T-1", "position_outside_d7"],
    ["end lat just south of 33.7", variant([["location.end.endLatitude", "33.69999999"]]), "T-1", "position_outside_d7"],
    ["end lat just north of 34.9", variant([["location.end.endLatitude", "34.90000001"]]), "T-1", "position_outside_d7"],
    ["end lon just west of -119.5", variant([["location.end.endLongitude", "-119.50000001"]]), "T-1", "position_outside_d7"],
    ["begin lat just north of 34.9", variant([["location.begin.beginLatitude", "34.90000001"]]), "T-1", "position_outside_d7"],
  ];
  for (const [name, row, index, reason] of refusals) {
    it(`${name} is refused as ${reason}`, () => {
      const full = reason === "row_not_object" || reason === "type_missing" ? 0 : 1;
      expect(parseLcsFeed([row], NOW)).toEqual(parsed([], [{ index, reason }], full));
    });
  }

  it("a row that is not Full is skipped, never refused, with every other field broken", () => {
    for (const kind of ["Lane", "Moving", "One-Way Traffic", "Traffic Break", "full", "FULL"]) {
      const row = { lcs: { closure: { typeOfClosure: kind }, index: 9 } };
      expect(parseLcsFeed([row], NOW)).toEqual({ rows: 1, full: 0, active: 0, refused: [], closures: [] });
    }
  });
});

describe("the bounds a row is ACCEPTED at (R2-R4)", () => {
  const box = (lon: string, lat: string) => [["location.begin.beginLongitude", lon], ["location.begin.beginLatitude", lat],
    ["location.end.endLongitude", lon], ["location.end.endLatitude", lat]] as [string, unknown][];
  const kept: [string, [string, unknown][], number, number][] = [
    ["the south-west corner", box("-119.5", "33.7"), -119.5, 33.7],
    ["the north-east corner", box("-117.6", "34.9"), -117.6, 34.9],
    ["8 decimals", box("-118.12345678", "34.12345678"), -118.12345678, 34.12345678],
  ];
  for (const [name, changes, lon, lat] of kept) {
    it(`${name} is kept`, () => {
      expect(parseLcsFeed([variant(changes)], NOW)).toEqual(parsed([ACTIVE({ rings: [square(lon, lat)] })]));
    });
  }

  const ts = "closure.closureTimestamp.";
  const windows: [string, [string, unknown][], boolean, boolean][] = [
    ["start == now", [[`${ts}closureStartEpoch`, "1500"]], true, false],
    ["start == now + 1", [[`${ts}closureStartEpoch`, "1501"], [`${ts}closureEndEpoch`, "2000"]], false, false],
    ["end == now", [[`${ts}closureEndEpoch`, "1500"]], true, false],
    ["end == now - 1", [[`${ts}closureEndEpoch`, "1499"]], false, false],
    ["end == start (not inverted)", [[`${ts}closureStartEpoch`, "1500"], [`${ts}closureEndEpoch`, "1500"]], true, false],
    ["a 10-digit start in the future", [[`${ts}closureStartEpoch`, "9999999999"], [`${ts}closureEndEpoch`, "9999999999"]], false, false],
    ["indefinite with no end", [[`${ts}isClosureEndIndefinite`, "true"], [`${ts}closureEndEpoch`, undefined]], true, false],
    ["indefinite starting now + 1", [[`${ts}isClosureEndIndefinite`, "true"], [`${ts}closureStartEpoch`, "1501"],
      [`${ts}closureEndEpoch`, "1501"]], false, false],
    ["10-97 placed before its start", [["closure.code1097.isCode1097", "true"], [`${ts}closureStartEpoch`, "1501"],
      [`${ts}closureEndEpoch`, "2000"]], true, true],
    ["10-97 placed after its end", [["closure.code1097.isCode1097", "true"], [`${ts}closureEndEpoch`, "1499"]], true, true],
    ["10-97 then 10-98 picked up", [["closure.code1097.isCode1097", "true"], ["closure.code1098.isCode1098", "true"]], false, false],
    ["10-97 then 10-22 cancelled", [["closure.code1097.isCode1097", "true"], ["closure.code1022.isCode1022", "true"]], false, false],
    ["in its window but 10-22", [["closure.code1022.isCode1022", "true"]], false, false],
    ["in its window but 10-98", [["closure.code1098.isCode1098", "true"]], false, false],
  ];
  for (const [name, changes, active, confirmed] of windows) {
    it(`${name} is ${active ? "active" : "not active"}`, () => {
      expect(parseLcsFeed([variant(changes)], NOW)).toEqual(parsed(active ? [ACTIVE({ confirmed })] : []));
    });
  }

  it("a chord of 499.9992 m is one rectangle; 500.0003 m is two gate squares at begin and end (R4)", () => {
    const short = parseLcsFeed([variant([["location.end.endLatitude", "34.00450669"]])], NOW).closures[0]!.rings;
    const long = parseLcsFeed([variant([["location.end.endLatitude", "34.0045067"]])], NOW).closures[0]!.rings;
    const p = (x: number, y: number) => [-118.4 + x / 91961, 34.0 + y / 110946];
    const length = (34.00450669 - 34.0) * 110946;
    expect(short).toEqual([[p(B, -B), p(B, length + B), p(-B, length + B), p(-B, -B), p(B, -B)]]);
    const dy = (34.0045067 - 34.0) * 110946;
    expect(long).toEqual([square(-118.4, 34.0), [p(-B, dy - B), p(B, dy - B), p(B, dy + B), p(-B, dy + B), p(-B, dy - B)]]);
  });
});

describe("the cap (R5)", () => {
  const one = (index: string, rings = 1, over: Partial<ActiveClosure> = {}): ActiveClosure =>
    ({ index, confirmed: false, facility: "On Ramp", rings: Array.from({ length: rings }, () => [[0, 0], [1, 0], [1, 1], [0, 0]]), ...over });
  const ids = (n: number, rings = 1) => Array.from({ length: n }, (_, i) => one(`c${String(i).padStart(3, "0")}`, rings));

  it("50 single polygons are all kept; a 51st is dropped and counted", () => {
    expect([capClosures(ids(50)).kept, capClosures(ids(50)).dropped, capClosures(ids(50)).geojson.features.length]).toEqual([50, 0, 50]);
    expect([capClosures(ids(51)).kept, capClosures(ids(51)).dropped, capClosures(ids(51)).geojson.features.length]).toEqual([50, 1, 50]);
  });

  it("greedy: at 49, a two-gate closure is dropped whole and the next single still fits", () => {
    const capped = capClosures([...ids(49), one("gate", 2), one("last")]);
    expect([capped.kept, capped.dropped, capped.geojson.features.map((f) => f.properties!.lcs_index).slice(48)])
      .toEqual([50, 1, ["c048", "last"]]);
  });

  it("each feature is the closure's ring, tagged with its index, whole", () => {
    expect(capClosures([one("a")]).geojson).toEqual({ type: "FeatureCollection", features: [{ type: "Feature",
      properties: { lcs_index: "a" }, geometry: { type: "Polygon", coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] } }] });
  });

  it("the order: 10-97 first, then facility rank, an unknown facility last, then index", () => {
    const rows = [["z", "Off Ramp", "false"], ["y", "Bridge", "false"], ["x", "Rest Area", "true"], ["w", "Conventional Hwy", "false"],
      ["v", "Mainline", "false"], ["u", "On Ramp", "false"], ["t", "Connector", "false"], ["s", "HOV", "false"], ["r", "Collector", "false"],
      ["q", "HOV Connector", "false"], ["p", "Rest Area", "false"], ["b", "Mainline", "false"], ["a", "Mainline", "true"]]
      .map(([index, facility, placed]) => variant([["index", index], ["closure.facility", facility], ["closure.code1097.isCode1097", placed]]));
    expect(parseLcsFeed(rows, NOW).closures.map((c) => c.index)).toEqual(["a", "x", "w", "b", "v", "s", "r", "t", "q", "u", "z", "p", "y"]);
  });
});
