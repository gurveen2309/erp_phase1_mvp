const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

test.describe("Templates Library", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("shows combined Fill & Download tile and both blank PDF links", async ({ page }) => {
    await page.goto("/reports/templates/");
    await expect(page.getByRole("heading", { name: "Report Templates" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Fill & Download" })).toHaveCount(1);
    await expect(page.getByRole("link", { name: "Blank Process PDF" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Blank Inspection PDF" })).toBeVisible();
  });

  test("blank process PDF link returns a PDF", async ({ page }) => {
    await page.goto("/reports/templates/");
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("link", { name: "Blank Process PDF" }).click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });

  test("blank inspection PDF link returns a PDF", async ({ page }) => {
    await page.goto("/reports/templates/");
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("link", { name: "Blank Inspection PDF" }).click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });
});
