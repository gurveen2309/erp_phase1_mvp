const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

test.describe("Reports History", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("history page loads", async ({ page }) => {
    await page.goto("/reports/history/");
    await expect(page.getByRole("heading", { name: "Reports History" })).toBeVisible();
  });

  test("nav link is present", async ({ page }) => {
    await page.goto("/reports/templates/");
    await expect(page.getByRole("link", { name: "Reports History" })).toBeVisible();
  });
});
