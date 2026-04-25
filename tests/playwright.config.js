const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./specs",
  timeout: 30_000,
  retries: 0,
  workers: 1,
  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:8000",
    headless: false,
    launchOptions: {
      slowMo: 500,
    },
    screenshot: "only-on-failure",
    video: "off",
  },
  globalSetup: "./global-setup.js",
  globalTeardown: "./global-teardown.js",
});
