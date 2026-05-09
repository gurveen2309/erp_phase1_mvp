const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

test.describe("Production Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("page loads with all three reporting sections", async ({ page }) => {
    await page.goto("/reports/production/");
    await expect(page.getByRole("heading", { name: /Production.*Dashboard/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Daily Production Summary" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Monthly Invoice Summary" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Top Parties" })).toBeVisible();
  });

  test("date filter form is present", async ({ page }) => {
    await page.goto("/reports/production/");
    await expect(page.getByRole("button", { name: "Apply Date Filter" })).toBeVisible();
  });

  test("date filter submits and reflects params in URL", async ({ page }) => {
    await page.goto("/reports/production/");
    await page.fill("#id_start_date", "2024-01-01");
    await page.fill("#id_end_date", "2024-12-31");
    await page.getByRole("button", { name: "Apply Date Filter" }).click();
    expect(page.url()).toMatch(/start_date=2024-01-01/);
    expect(page.url()).toMatch(/end_date=2024-12-31/);
  });

  test("daily production table shows test challan data", async ({ page }) => {
    await page.goto("/reports/production/");
    // PW-CH-001 challan was created on 2024-04-01 for PW Test Party
    await expect(page.getByText("2024-04-01")).toBeVisible();
  });

  test("top parties table shows PW Test Party", async ({ page }) => {
    await page.goto("/reports/production/");
    await expect(page.getByText("PW Test Party")).toBeVisible();
  });

  test("no rows message shown when date range has no data", async ({ page }) => {
    await page.goto("/reports/production/?start_date=2000-01-01&end_date=2000-01-31");
    await expect(page.getByText("No production rows for the selected range.")).toBeVisible();
  });
});
