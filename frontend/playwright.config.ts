import { defineConfig } from "@playwright/test";

// Smoke test for the executive homepage. Assumes backend (:8000) and frontend
// (:3000) are running — e.g. `docker compose up`, then `npm run test:e2e`.
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:3000",
    headless: true,
  },
});
