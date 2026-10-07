/**
 * T-0288 rv4 B1 (c): the /config oracle's intrinsics, captured when THIS module is evaluated - before any src module -
 * so a request-time patch of JSON.stringify / JSON.parse in src rewrites the answer and never the expectation built
 * from it. Every test file that builds or reads a /config expectation imports this module FIRST (ESM evaluates imports
 * in source order, depth first, so it runs before ../src/index loads). BASELINE is the intrinsics snapshot at the
 * same moment: configSweep.test.ts compares the post-sweep snapshot to it, so load-time and request-time patches both
 * show against one pre-src population.
 */
import { snapshot } from "./intrinsicsSnapshot";

export const STRINGIFY: typeof JSON.stringify = JSON.stringify;
export const PARSE: typeof JSON.parse = JSON.parse;
export const BASELINE = snapshot();
