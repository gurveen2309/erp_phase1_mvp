const { test, expect } = require("@playwright/test");
const { login } = require("./auth.setup");

// These JSON endpoints require a logged-in session (Django session auth).
// We log in first, then fetch via page.request which carries the session cookie.

test.describe("JSON API Endpoints", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("GET /reports/api/production/daily/ returns 200 with JSON array", async ({ page }) => {
    const response = await page.request.get("/reports/api/production/daily/");
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toMatch(/application\/json/);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
  });

  test("daily API response objects have expected shape", async ({ page }) => {
    const response = await page.request.get("/reports/api/production/daily/");
    const body = await response.json();
    // We seeded a challan so the array should be non-empty
    expect(body.length).toBeGreaterThan(0);
    const first = body[0];
    expect(first).toHaveProperty("date");
    expect(first).toHaveProperty("total_challans");
    expect(first).toHaveProperty("total_weight");
    expect(first).toHaveProperty("amount");
  });

  test("GET /reports/api/production/monthly/ returns 200 with JSON array", async ({ page }) => {
    const response = await page.request.get("/reports/api/production/monthly/");
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
  });

  test("monthly API response objects have month and total_amount", async ({ page }) => {
    const response = await page.request.get("/reports/api/production/monthly/");
    const body = await response.json();
    if (body.length > 0) {
      expect(body[0]).toHaveProperty("month");
      expect(body[0]).toHaveProperty("total_amount");
    }
  });

  test("GET /reports/api/production/top-parties/ returns 200 with JSON array", async ({ page }) => {
    const response = await page.request.get("/reports/api/production/top-parties/");
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
  });

  test("top-parties API response objects have party_name, total_amount, and percentage", async ({ page }) => {
    const response = await page.request.get("/reports/api/production/top-parties/");
    const body = await response.json();
    expect(body.length).toBeGreaterThan(0);
    const first = body[0];
    expect(first).toHaveProperty("party_name");
    expect(first).toHaveProperty("total_amount");
    expect(first).toHaveProperty("percentage");
    // Percentages must be numeric and sum near 100
    const total = body.reduce((s, r) => s + r.percentage, 0);
    expect(total).toBeCloseTo(100, 0);
  });

  test("daily API respects date range filter params", async ({ page }) => {
    // Very old date range — should return empty array
    const response = await page.request.get(
      "/reports/api/production/daily/?start_date=2000-01-01&end_date=2000-01-31"
    );
    const body = await response.json();
    expect(body).toEqual([]);
  });
});
