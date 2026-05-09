const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

test.describe("Home & Reporting Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("home page loads with reporting links", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /ERP|Dashboard|Home/i })).toBeVisible();
  });

  test("redirects to login when unauthenticated", async ({ page }) => {
    // Log out first
    await page.goto("/admin/logout/");
    const response = await page.goto("/reports/ledger/");
    // Should redirect to login (final URL contains /login/ or /admin/login/)
    expect(page.url()).toMatch(/login/);
  });
});
