import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * /api proxies to the deployed Worker, so the browser talks same-origin: the Worker sends no CORS headers.
 * Dev only. SCENIC_API_URL points it elsewhere (a `wrangler dev` on :8787, say).
 */
const api = process.env.SCENIC_API_URL ?? "https://scenic-api.phineas-fritsch.workers.dev";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: api, changeOrigin: true, rewrite: (path) => path.replace(/^\/api/, "") },
    },
  },
});
