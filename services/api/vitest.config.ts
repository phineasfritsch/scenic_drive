import { cloudflareTest } from "@cloudflare/vitest-pool-workers";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.jsonc" },
      // Tests must never see production: every binding here is local Miniflare state.
      miniflare: { d1Databases: { DB: "scenic-test" } },
    }),
  ],
});
