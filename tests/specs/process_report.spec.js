const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

const PARTY = "PW Test Party";

async function selectTestParty(page) {
  await page.selectOption("#id_party", { label: PARTY });
}

test.describe("Process Report Form", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("form page loads with all expected sections", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await expect(page.getByRole("heading", { name: "Process Report" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Header" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Job Details" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Cycle Parameters" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Generate PDF" })).toBeVisible();
  });

  test("submitting requires a party (form fails without it)", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await page.getByRole("button", { name: "Generate PDF" }).click();
    // Browser-side required validation will block submission; URL stays on form
    await expect(page).toHaveURL(/\/reports\/templates\/process\//);
  });

  test("submitting with party only downloads a PDF", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await selectTestParty(page);
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate PDF" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("process_report.pdf");
  });

  test("filled form fields produce a sizeable PDF", async ({ page }) => {
    await page.goto("/reports/templates/process/");

    await selectTestParty(page);
    await page.fill("#id_ref_no", "REF-001");
    await page.fill("#id_part_name", "Bearing Shaft");
    await page.fill("#id_hardness", "62 HRC");
    await page.fill("#id_material_grade", "EN31");
    await page.fill("#id_size", "25mm");
    await page.fill("#id_hardening_temp", "820C");
    await page.fill("#id_hardening_speed", "1.2 m/min");
    await page.fill("#id_hardening_hrc", "60-63 HRC");
    await page.fill("#id_quenching_media", "Oil");
    await page.fill("#id_quenching_temp", "60C");
    await page.fill("#id_tempering_temp", "200C");
    await page.fill("#id_tempering_speed", "1.5 m/min");
    await page.fill("#id_tempering_hrc", "58-62 HRC");

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate PDF" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("process_report.pdf");
    const stream = await download.createReadStream();
    const chunks = [];
    for await (const chunk of stream) chunks.push(chunk);
    const size = Buffer.concat(chunks).length;
    expect(size).toBeGreaterThan(5_000);
  });

  test("submission creates a ProcessReport record", async ({ page, request }) => {
    await page.goto("/reports/templates/process/");
    await selectTestParty(page);
    await page.fill("#id_ref_no", "REF-DB-CHECK");
    await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Generate PDF" }).click(),
    ]);

    // Verify by hitting the admin changelist filtered by ref_no
    await page.goto("/admin/production/processreport/?q=REF-DB-CHECK");
    await expect(page.locator("#result_list tbody tr")).toHaveCount(1);
  });

  test("Cancel link returns to templates library", async ({ page }) => {
    await page.goto("/reports/templates/process/");
    await page.getByRole("link", { name: "Cancel" }).click();
    await expect(page).toHaveURL(/\/reports\/templates\//);
  });
});
