/**
 * T-0403: a router whose every request takes exactly T ms on a VIRTUAL clock. Not a test file.
 *
 * It wraps a harness's fetchImpl: each request records its start, waits until the clock reaches start + T, records
 * its end and only then answers from the harness's recording. `drive` runs the plan and advances the clock: after
 * every macrotask (all microtasks drained, so every request the plan can issue now has been issued) it jumps to the
 * earliest pending wake time. Wall time is the clock when the answer resolves - deterministic, no real timers in it.
 */
import type { Harness } from "./planHarness";

export interface Timed {
  start: number;
  end: number;
}

export interface TimedRouter {
  calls: Timed[];
  peakInFlight: () => number;
  drive<T>(run: () => Promise<T>): Promise<{ value: T; wall: number }>;
}

export function timedRouter(h: Harness, perCallMs: number): TimedRouter {
  const inner = h.deps.upstream.fetchImpl;
  const calls: Timed[] = [];
  const sleepers: { at: number; wake: () => void }[] = [];
  let now = 0;
  let inFlight = 0;
  let peak = 0;
  h.deps.upstream.fetchImpl = async (url, init) => {
    const start = now;
    inFlight += 1;
    peak = Math.max(peak, inFlight);
    await new Promise<void>((wake) => sleepers.push({ at: start + perCallMs, wake }));
    inFlight -= 1;
    calls.push({ start, end: now });
    return inner(url, init);
  };
  return {
    calls,
    peakInFlight: () => peak,
    async drive(run) {
      let settled = false;
      const result = run().finally(() => {
        settled = true;
      });
      result.catch(() => undefined);
      for (let idle = 0; !settled && idle < 10_000; idle += 1) {
        await new Promise((tick) => setTimeout(tick, 0));
        if (settled || sleepers.length === 0) continue;
        const at = Math.min(...sleepers.map((s) => s.at));
        now = at;
        for (const due of sleepers.filter((s) => s.at === at)) {
          sleepers.splice(sleepers.indexOf(due), 1);
          due.wake();
        }
      }
      return { value: await result, wall: now };
    },
  };
}
