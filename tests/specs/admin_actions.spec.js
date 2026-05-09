const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

// Helper: select all records in an admin changelist and pick an action
async function runAdminAction(page, url, actionValue) {
  await page.goto(url);
  // Select all rows using the "select all" checkbox in the header
  await page.locator("#action-toggle").click();
  await page.selectOption("select[name=action]", actionValue);
  await page.locator("[type=submit][name=index]").click();
}

test.describe("Django Admin — List Views", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("Party admin list loads and shows PW Test Party", async ({ page }) => {
    await page.goto("/admin/masters/party/");
    await expect(page.getByRole("heading", { name: /Select party/i })).toBeVisible();
    await expect(page.getByText("PW Test Party")).toBeVisible();
  });

  test("Challan admin list loads and shows PW-CH-001", async ({ page }) => {
    await page.goto("/admin/production/challan/");
    await expect(page.getByRole("heading", { name: /Select challan/i })).toBeVisible();
    await expect(page.getByText("PW-CH-001")).toBeVisible();
  });

  test("Invoice admin list loads and shows PW-INV-001", async ({ page }) => {
    await page.goto("/admin/finance/invoice/");
    await expect(page.getByRole("heading", { name: /Select invoice/i })).toBeVisible();
    await expect(page.getByText("PW-INV-001")).toBeVisible();
  });

  test("Payment admin list loads and shows PW-PAY-001", async ({ page }) => {
    await page.goto("/admin/finance/payment/");
    await expect(page.getByRole("heading", { name: /Select payment/i })).toBeVisible();
    await expect(page.getByText("PW-PAY-001")).toBeVisible();
  });

  test("ProcessReport admin list loads and shows setup report", async ({ page }) => {
    await page.goto("/admin/production/processreport/");
    await expect(page.getByRole("heading", { name: /Select process report/i })).toBeVisible();
    await expect(page.getByText("PW-SETUP-REF")).toBeVisible();
  });

  test("InspectionReport admin list loads", async ({ page }) => {
    await page.goto("/admin/production/inspectionreport/");
    await expect(page.getByRole("heading", { name: /Select inspection report/i })).toBeVisible();
  });

  test("OpeningBalance admin list loads", async ({ page }) => {
    await page.goto("/admin/finance/openingbalance/");
    await expect(page.getByRole("heading", { name: /Select opening balance/i })).toBeVisible();
  });

  test("MigrationBatch admin list loads", async ({ page }) => {
    await page.goto("/admin/migration_app/migrationbatch/");
    await expect(page.getByRole("heading", { name: /Select migration batch/i })).toBeVisible();
  });

  test("ApprovalRequest admin list loads (read-only)", async ({ page }) => {
    await page.goto("/admin/governance/approvalrequest/");
    await expect(page.getByRole("heading", { name: /Select approval request/i })).toBeVisible();
  });

  test("AuditEvent admin list loads (read-only)", async ({ page }) => {
    await page.goto("/admin/governance/auditevent/");
    await expect(page.getByRole("heading", { name: /Select audit event/i })).toBeVisible();
  });

  test("BackupSnapshot admin list loads", async ({ page }) => {
    await page.goto("/admin/governance/backupsnapshot/");
    await expect(page.getByRole("heading", { name: /Select backup snapshot/i })).toBeVisible();
  });
});

test.describe("Django Admin — Custom Actions", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("ProcessReport: download_pdfs action is available in action dropdown", async ({ page }) => {
    await page.goto("/admin/production/processreport/");
    const options = await page.locator("select[name=action] option").allTextContents();
    expect(options.some((o) => /download.*pdf/i.test(o))).toBe(true);
  });

  test("ProcessReport: regenerate_pdfs action is available in action dropdown", async ({ page }) => {
    await page.goto("/admin/production/processreport/");
    const options = await page.locator("select[name=action] option").allTextContents();
    expect(options.some((o) => /regenerate.*pdf/i.test(o))).toBe(true);
  });

  test("InspectionReport: download_pdfs action is available in action dropdown", async ({ page }) => {
    await page.goto("/admin/production/inspectionreport/");
    const options = await page.locator("select[name=action] option").allTextContents();
    expect(options.some((o) => /download.*pdf/i.test(o))).toBe(true);
  });

  test("ProcessReport: running download_pdfs on a record returns a ZIP download", async ({ page }) => {
    await page.goto("/admin/production/processreport/");
    // Select all, pick download_pdfs action
    await page.locator("#action-toggle").click();
    await page.selectOption("select[name=action]", "download_pdfs");
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 15_000 }),
      page.locator("[type=submit][name=index]").click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.zip$/i);
  });

  test("ProcessReport: regenerate_pdfs action completes without error", async ({ page }) => {
    await page.goto("/admin/production/processreport/");
    await page.locator("#action-toggle").click();
    await page.selectOption("select[name=action]", "regenerate_pdfs");
    await page.locator("[type=submit][name=index]").click();
    // After regenerating, should stay in admin (no 500 error)
    await expect(page).not.toHaveURL(/\/500/);
    await expect(page.getByRole("heading", { name: /process report/i })).toBeVisible();
  });
});

test.describe("Django Admin — Receipt PDF Downloads", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("challan receipt PDF returns a PDF for PW-CH-001", async ({ page }) => {
    // Get the challan ID via admin search
    await page.goto("/admin/production/challan/?q=PW-CH-001");
    const row = page.locator("#result_list tbody tr").first();
    const link = row.locator("a").first();
    const href = await link.getAttribute("href");
    // Extract challan ID from the edit URL e.g. /admin/production/challan/42/change/
    const match = href.match(/\/challan\/(\d+)\//);
    if (!match) throw new Error("Challan ID not found in admin URL");
    const challanId = match[1];

    const response = await page.goto(`/reports/challans/${challanId}/receipt.pdf`);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toMatch(/pdf/);
  });

  test("invoice receipt PDF returns a PDF for PW-INV-001", async ({ page }) => {
    await page.goto("/admin/finance/invoice/?q=PW-INV-001");
    const row = page.locator("#result_list tbody tr").first();
    const link = row.locator("a").first();
    const href = await link.getAttribute("href");
    const match = href.match(/\/invoice\/(\d+)\//);
    if (!match) throw new Error("Invoice ID not found in admin URL");
    const invoiceId = match[1];

    const response = await page.goto(`/reports/invoices/${invoiceId}/receipt.pdf`);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toMatch(/pdf/);
  });

  test("non-existent challan receipt returns 404", async ({ page }) => {
    const response = await page.goto("/reports/challans/999999/receipt.pdf");
    expect(response.status()).toBe(404);
  });

  test("non-existent invoice receipt returns 404", async ({ page }) => {
    const response = await page.goto("/reports/invoices/999999/receipt.pdf");
    expect(response.status()).toBe(404);
  });
});
