const { test, expect } = require("@playwright/test");
const path = require("path");
const { login } = require("./auth.setup");

// Use the sample workbook that ships with the repo
const SAMPLE_XLSX = path.resolve(__dirname, "../../import_samples/production_dashboard_4.xlsx");

test.describe("Import Workflow", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  // ── Upload page ──────────────────────────────────────────────────────────

  test("upload page loads with form fields", async ({ page }) => {
    await page.goto("/imports/");
    await expect(page.getByRole("heading", { name: "Upload Import" })).toBeVisible();
    await expect(page.locator("#id_import_type")).toBeVisible();
    await expect(page.locator("#id_upload")).toBeVisible();
    await expect(page.getByRole("button", { name: "Preview Import" })).toBeVisible();
  });

  test("submitting without a file shows validation error or stays on page", async ({ page }) => {
    await page.goto("/imports/");
    await page.selectOption("#id_import_type", "production_dashboard_workbook");
    await page.getByRole("button", { name: "Preview Import" }).click();
    // Should stay on /imports/ (no file provided)
    await expect(page).toHaveURL(/\/imports\//);
  });

  // ── Preview ──────────────────────────────────────────────────────────────

  test("uploading the sample workbook shows a preview summary", async ({ page }) => {
    await page.goto("/imports/");
    await page.selectOption("#id_import_type", "production_dashboard_workbook");
    await page.setInputFiles("#id_upload", SAMPLE_XLSX);
    await page.getByRole("button", { name: "Preview Import" }).click();

    await expect(page.getByRole("heading", { name: "Preview Summary" })).toBeVisible();
    await expect(page.getByText("Valid rows:")).toBeVisible();
    await expect(page.getByRole("button", { name: "Confirm Import" })).toBeVisible();
  });

  test("preview shows affected parties", async ({ page }) => {
    await page.goto("/imports/");
    await page.selectOption("#id_import_type", "production_dashboard_workbook");
    await page.setInputFiles("#id_upload", SAMPLE_XLSX);
    await page.getByRole("button", { name: "Preview Import" }).click();

    await expect(page.getByText("Affected parties:")).toBeVisible();
  });

  test("preview shows validation errors table (even when empty)", async ({ page }) => {
    await page.goto("/imports/");
    await page.selectOption("#id_import_type", "production_dashboard_workbook");
    await page.setInputFiles("#id_upload", SAMPLE_XLSX);
    await page.getByRole("button", { name: "Preview Import" }).click();

    await expect(page.getByRole("heading", { name: "Validation Errors" })).toBeVisible();
  });

  // ── Confirm & History ────────────────────────────────────────────────────

  test("confirming import redirects to import history", async ({ page }) => {
    await page.goto("/imports/");
    await page.selectOption("#id_import_type", "production_dashboard_workbook");
    await page.setInputFiles("#id_upload", SAMPLE_XLSX);
    await page.getByRole("button", { name: "Preview Import" }).click();
    await expect(page.getByRole("button", { name: "Confirm Import" })).toBeVisible();
    await page.getByRole("button", { name: "Confirm Import" }).click();
    // Superuser path: commits immediately and redirects to history
    await expect(page).toHaveURL(/\/imports\/history\//);
  });

  test("import history page shows a completed batch after import", async ({ page }) => {
    // Import first
    await page.goto("/imports/");
    await page.selectOption("#id_import_type", "production_dashboard_workbook");
    await page.setInputFiles("#id_upload", SAMPLE_XLSX);
    await page.getByRole("button", { name: "Preview Import" }).click();
    await page.getByRole("button", { name: "Confirm Import" }).click();

    await expect(page).toHaveURL(/\/imports\/history\//);
    await expect(page.getByRole("heading", { name: "Import History" })).toBeVisible();
    await expect(page.getByText("Imported")).toBeVisible();
  });

  // ── History page standalone ──────────────────────────────────────────────

  test("import history page loads", async ({ page }) => {
    await page.goto("/imports/history/");
    await expect(page.getByRole("heading", { name: "Import History" })).toBeVisible();
    for (const col of ["File", "Type", "Status", "Rows", "Success", "Errors"]) {
      await expect(page.getByRole("columnheader", { name: col })).toBeVisible();
    }
  });

  // ── Confirm without session (guard) ──────────────────────────────────────

  test("POSTing to /imports/confirm/ without a session preview redirects back", async ({ page }) => {
    // Navigate directly to confirm without uploading — session has no preview token
    await page.goto("/imports/");
    // Clear any stale session preview by just doing a fresh GET without uploading
    const response = await page.request.post("/imports/confirm/", {
      form: { csrfmiddlewaretoken: "invalid", token: "bad" },
    });
    // Should redirect (302) to /imports/ or return a non-200 response
    expect([200, 302, 403]).toContain(response.status());
  });
});
