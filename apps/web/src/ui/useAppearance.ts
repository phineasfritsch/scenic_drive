import { useSyncExternalStore } from "react";
import type { Appearance } from "../map/basemap";

const query = () => window.matchMedia("(prefers-color-scheme: dark)");

export function useAppearance(): Appearance {
  return useSyncExternalStore(
    (notify) => {
      const q = query();
      q.addEventListener("change", notify);
      return () => q.removeEventListener("change", notify);
    },
    () => (query().matches ? "dark" : "light"),
  );
}
