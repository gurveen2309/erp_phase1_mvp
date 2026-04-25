/**
 * Shared login helper used by all test specs.
 */
const { expect } = require("@playwright/test");

const TEST_USER = "pw_testuser";
const TEST_PASS = "pw_testpass";

async function login(page) {
  await page.goto("/admin/login/");
  await page.fill("#id_username", TEST_USER);
  await page.fill("#id_password", TEST_PASS);
  await page.click("[type=submit]");
  await expect(page).not.toHaveURL(/\/admin\/login/);
}

module.exports = { login };
