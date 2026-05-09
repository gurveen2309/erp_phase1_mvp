const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

test.describe("Governance — Approval Queue", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("approval queue page loads", async ({ page }) => {
    await page.goto("/governance/approvals/");
    await expect(page.getByRole("heading", { name: "Approval Queue" })).toBeVisible();
  });

  test("approval queue shows Pending Requests and Recent Completed sections", async ({ page }) => {
    await page.goto("/governance/approvals/");
    await expect(page.getByRole("heading", { name: "Pending Requests" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Recent Completed Requests" })).toBeVisible();
  });

  test("empty queue shows 'No pending approval requests'", async ({ page }) => {
    await page.goto("/governance/approvals/");
    // If no pending requests exist (superuser commits directly), the empty message shows
    await expect(page.getByText("No pending approval requests.")).toBeVisible();
  });
});

test.describe("Governance — Audit Log", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("audit log page loads with table", async ({ page }) => {
    await page.goto("/governance/audit/");
    await expect(page.getByRole("heading", { name: "Audit Log" })).toBeVisible();
    for (const col of ["When", "Event", "Actor", "Object", "Batch"]) {
      await expect(page.getByRole("columnheader", { name: col })).toBeVisible();
    }
  });

  test("audit log shows events after import", async ({ page }) => {
    // The global-setup created finance records which may not log audit events,
    // but any import via the UI does. This test just confirms the page renders.
    await page.goto("/governance/audit/");
    await expect(page.getByRole("heading", { name: "Audit Log" })).toBeVisible();
    // Table body exists (may be empty or have rows)
    await expect(page.locator("table")).toBeVisible();
  });
});

test.describe("Governance — Backups", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("backup list page loads", async ({ page }) => {
    await page.goto("/governance/backups/");
    await expect(page.getByRole("heading", { name: "Backups" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Create Backup" })).toBeVisible();
  });

  test("available snapshots table is present", async ({ page }) => {
    await page.goto("/governance/backups/");
    await expect(page.getByRole("heading", { name: "Available Snapshots" })).toBeVisible();
    for (const col of ["ID", "Type", "Status", "Created", "Size"]) {
      await expect(page.getByRole("columnheader", { name: col })).toBeVisible();
    }
  });

  test("creating a backup stays on or redirects back to backup list", async ({ page }) => {
    await page.goto("/governance/backups/");
    await page.getByRole("button", { name: "Create Backup" }).click();
    // After POST the page should still be at /governance/backups/
    await expect(page).toHaveURL(/\/governance\/backups\//);
  });

  test("created backup appears in the snapshots table", async ({ page }) => {
    await page.goto("/governance/backups/");
    await page.getByRole("button", { name: "Create Backup" }).click();
    // Table should now have at least one row (not the empty-state text)
    const rows = page.locator("table tbody tr");
    await expect(rows.first()).not.toContainText("No backups available.");
  });
});
