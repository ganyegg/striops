import { expect, test } from "@playwright/test";

test("executive homepage shows an intelligence-first briefing", async ({ page }) => {
  await page.goto("/");

  // Brand + tagline.
  await expect(page.getByText("Helm").first()).toBeVisible();
  await expect(page.getByText("Trusted with foresight")).toBeVisible();

  // Intelligence-first: wins + risks, not a chart-first dashboard.
  await expect(page.getByRole("heading", { name: /What's working/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Top risks/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Recommended decisions/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Command centre/i })).toBeVisible();

  // Run a simulation and see a recommendation.
  await page.getByRole("button", { name: /Run Simulation/i }).click();
  await expect(page.getByText(/Recommendation/i).first()).toBeVisible();
});
