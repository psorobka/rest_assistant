import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 360_000,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: "list",
  use: { browserName: "chromium", headless: true, locale: "pl-PL" },
});
