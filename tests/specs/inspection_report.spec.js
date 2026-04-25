const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

const PARTY = "PW Test Party";

async function selectTestParty(page) {
  await page.selectOption("#id_party", { label: PARTY });
}

test.describe("Inspection Report Form", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("form page loads with all expected sections", async ({ page }) => {
    await page.goto("/reports/templates/inspection/");
    await expect(page.getByRole("heading", { name: "Inspection Report" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Header" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Inspection Parameters/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Bottom" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Generate PDF" })).toBeVisible();
  });

  test("observation table has correct structure", async ({ page }) => {
    await page.goto("/reports/templates/inspection/");
    const rows = page.locator(".card table tbody tr");
    await expect(rows).toHaveCount(5);
    const firstRowCells = rows.nth(0).locator("td");
    await expect(firstRowCells).toHaveCount(10);
  });

  test("submitting with party only downloads a PDF", async ({ page }) => {
    await page.goto("/reports/templates/inspection/");
    await selectTestParty(page);
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate PDF" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("inspection_report.pdf");
  });

  test("filled form fields produce a sizeable PDF", async ({ page }) => {
    await page.goto("/reports/templates/inspection/");

    await selectTestParty(page);
    await page.fill("#id_date", "2024-06-15");
    await page.fill("#id_part_name", "Bearing Race");
    await page.fill("#id_no", "IR-2024-042");
    await page.fill("#id_lot_qty", "500");
    await page.fill("#id_material_grade", "EN31");
    await page.fill("#id_supplier_tc_received", "Yes");
    await page.fill("#id_process_done", "Case Hardening");
    await page.fill("#id_ht", "HT-07");

    await page.fill("#id_hardness_spec", "58-62 HRC");
    await page.fill("#id_micro_structure_spec", "Martensite");
    await page.fill("#id_grain_size_spec", "ASTM 7-8");

    await page.fill("#id_hardness_obs_1", "60");
    await page.fill("#id_hardness_obs_2", "61");
    await page.fill("#id_hardness_obs_3", "59");
    await page.fill("#id_hardness_obs_4", "62");

    await page.fill("#id_qty_checked", "25");
    await page.fill("#id_qty", "500");

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate PDF" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("inspection_report.pdf");

    const stream = await download.createReadStream();
    const chunks = [];
    for await (const chunk of stream) chunks.push(chunk);
    const size = Buffer.concat(chunks).length;
    expect(size).toBeGreaterThan(5_000);
  });

  test("submission creates an InspectionReport record", async ({ page }) => {
    await page.goto("/reports/templates/inspection/");
    await selectTestParty(page);
    await page.fill("#id_no", "IR-DB-CHECK");
    await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate PDF" }).click(),
    ]);

    await page.goto("/admin/production/inspectionreport/?q=IR-DB-CHECK");
    await expect(page.locator("#result_list tbody tr")).toHaveCount(1);
  });

  test("Cancel link returns to templates library", async ({ page }) => {
    await page.goto("/reports/templates/inspection/");
    await page.getByRole("link", { name: "Cancel" }).click();
    await expect(page).toHaveURL(/\/reports\/templates\//);
  });
});
