const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

const PARTY = "PW Test Party";

async function selectTestParty(page) {
  await page.selectOption("#id_party", { label: PARTY });
}

test.describe("Combined Process + Inspection Report Form", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("form page loads with all expected sections", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await expect(
      page.getByRole("heading", { name: "Generate Process + Inspection Reports" })
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "Header" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Process — Job Details" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Process — Cycle Parameters" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Inspection — Job Details" })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: /Inspection — Parameters/i })
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "Inspection — Bottom" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Generate Reports" })).toBeVisible();
  });

  test("observation table has correct structure", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    const rows = page.locator(".card table tbody tr");
    await expect(rows).toHaveCount(5);
    const firstRowCells = rows.nth(0).locator("td");
    await expect(firstRowCells).toHaveCount(10);
  });

  test("submitting requires a party (form fails without it)", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await page.getByRole("button", { name: "Generate Reports" }).click();
    await expect(page).toHaveURL(/\/reports\/templates\/process\//);
  });

  test("submitting with party only downloads a zip", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await selectTestParty(page);
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate Reports" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("reports.zip");
  });

  test("filled form fields produce a sizeable zip", async ({ page }) => {
    await page.goto("/reports/templates/process/");

    await selectTestParty(page);
    // Header (shared)
    await page.fill("#id_ref_no", "REF-COMBO-001");
    await page.fill("#id_dated", "2024-06-01");
    await page.fill("#id_date", "2024-06-15");
    await page.fill("#id_part_name", "Bearing Race");
    await page.fill("#id_material_grade", "EN31");

    // Process
    await page.fill("#id_hardness", "62 HRC");
    await page.fill("#id_sample_id", "S-001");
    await page.fill("#id_size", "25mm");
    await page.fill("#id_hardening_temp", "820C");
    await page.fill("#id_hardening_speed", "1.2 m/min");
    await page.fill("#id_hardening_hrc", "60-63 HRC");
    await page.fill("#id_quenching_media", "Oil");
    await page.fill("#id_quenching_temp", "60C");
    await page.fill("#id_tempering_temp", "200C");
    await page.fill("#id_tempering_speed", "1.5 m/min");
    await page.fill("#id_tempering_hrc", "58-62 HRC");

    // Inspection
    await page.fill("#id_no", "IR-2024-042");
    await page.fill("#id_lot_qty", "500");
    await page.fill("#id_supplier_tc_received", "Yes");
    await page.fill("#id_process_done", "Case Hardening");
    await page.fill("#id_ht", "HT-07");
    await page.fill("#id_hardness_spec", "58-62 HRC");
    await page.fill("#id_hardness_obs_1", "60");
    await page.fill("#id_hardness_obs_2", "61");
    await page.fill("#id_qty_checked", "25");
    await page.fill("#id_qty", "500");

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate Reports" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("reports.zip");

    const stream = await download.createReadStream();
    const chunks = [];
    for await (const chunk of stream) chunks.push(chunk);
    const size = Buffer.concat(chunks).length;
    expect(size).toBeGreaterThan(10_000);
  });

  test("submission creates linked ProcessReport and InspectionReport records", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await selectTestParty(page);
    await page.fill("#id_ref_no", "REF-DB-LINK");
    await page.fill("#id_no", "IR-DB-LINK");
    await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate Reports" }).click(),
    ]);

    await page.goto("/admin/production/processreport/?q=REF-DB-LINK");
    await expect(page.locator("#result_list tbody tr")).toHaveCount(1);

    await page.goto("/admin/production/inspectionreport/?q=IR-DB-LINK");
    await expect(page.locator("#result_list tbody tr")).toHaveCount(1);
  });

  test("Cancel link returns to templates library", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await page.getByRole("link", { name: "Cancel" }).click();
    await expect(page).toHaveURL(/\/reports\/templates\//);
  });

  test("inspection-form URL is gone (404)", async ({ page }) => {
    const response = await page.goto("/reports/templates/inspection/");
    expect(response.status()).toBe(404);
  });
});
