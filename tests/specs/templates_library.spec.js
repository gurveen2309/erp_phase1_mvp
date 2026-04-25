const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

test.describe("Templates Library", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("shows Fill & Download links for both reports", async ({ page }) => {
    await page.goto("/reports/templates/");
    await expect(page.getByRole("heading", { name: "Report Templates" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Fill & Download" })).toHaveCount(2);
    await expect(page.getByRole("link", { name: "Blank PDF" })).toHaveCount(2);
  });

  test("blank process PDF link returns a PDF", async ({ page }) => {
    await page.goto("/reports/templates/");
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("link", { name: "Blank PDF" }).first().click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });

  test("blank inspection PDF link returns a PDF", async ({ page }) => {
    await page.goto("/reports/templates/");
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("link", { name: "Blank PDF" }).nth(1).click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });
});
