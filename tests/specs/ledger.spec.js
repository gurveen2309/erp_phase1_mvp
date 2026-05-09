const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

const PARTY = "PW Test Party";

test.describe("Party Ledger", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("ledger page loads with party selector form", async ({ page }) => {
    await page.goto("/reports/ledger/");
    await expect(page.getByRole("heading", { name: "Party Ledger" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Load Ledger" })).toBeVisible();
  });

  test("no entries shown before a party is selected", async ({ page }) => {
    await page.goto("/reports/ledger/");
    await expect(page.getByText("Download PDF Statement")).not.toBeVisible();
  });

  test("selecting a party loads ledger entries", async ({ page }) => {
    await page.goto("/reports/ledger/");
    await page.selectOption("#id_party", { label: PARTY });
    await page.getByRole("button", { name: "Load Ledger" }).click();
    // Party name appears as section heading
    await expect(page.getByRole("heading", { name: PARTY })).toBeVisible();
    // Ledger table columns
    await expect(page.getByRole("columnheader", { name: "Date" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "Running Balance" })).toBeVisible();
  });

  test("Download PDF Statement button is present after loading ledger", async ({ page }) => {
    await page.goto("/reports/ledger/");
    await page.selectOption("#id_party", { label: PARTY });
    await page.getByRole("button", { name: "Load Ledger" }).click();
    await expect(page.getByRole("link", { name: "Download PDF Statement" })).toBeVisible();
  });

  test("PDF statement download returns a PDF file", async ({ page }) => {
    await page.goto("/reports/ledger/");
    await page.selectOption("#id_party", { label: PARTY });
    await page.getByRole("button", { name: "Load Ledger" }).click();
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("link", { name: "Download PDF Statement" }).click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.pdf$/i);
  });

  test("ledger PDF endpoint returns 400 when no party param", async ({ page }) => {
    const response = await page.goto("/reports/ledger/pdf/");
    expect(response.status()).toBe(400);
  });

  test("date filters are applied to the ledger query string", async ({ page }) => {
    await page.goto("/reports/ledger/");
    await page.selectOption("#id_party", { label: PARTY });
    await page.fill("#id_start_date", "2024-01-01");
    await page.fill("#id_end_date", "2024-12-31");
    await page.getByRole("button", { name: "Load Ledger" }).click();
    expect(page.url()).toMatch(/start_date=2024-01-01/);
    expect(page.url()).toMatch(/end_date=2024-12-31/);
  });
});
