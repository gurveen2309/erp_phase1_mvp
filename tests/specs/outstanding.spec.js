const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

test.describe("Outstanding Summary", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("page loads with heading and table columns", async ({ page }) => {
    await page.goto("/reports/outstanding/");
    await expect(page.getByRole("heading", { name: "Outstanding Summary" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "Party" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "Outstanding" })).toBeVisible();
  });

  test("test party appears in outstanding table", async ({ page }) => {
    await page.goto("/reports/outstanding/");
    // PW Test Party has an invoice and a payment, so it should appear
    await expect(page.getByText("PW Test Party")).toBeVisible();
  });

  test("all expected columns are present", async ({ page }) => {
    await page.goto("/reports/outstanding/");
    for (const col of ["Party", "Opening Balance", "Invoices", "Payments", "Outstanding"]) {
      await expect(page.getByRole("columnheader", { name: col })).toBeVisible();
    }
  });
});
