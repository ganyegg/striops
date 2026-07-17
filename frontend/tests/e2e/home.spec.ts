import { expect, test } from "@playwright/test";

test("executive homepage shows an intelligence-first briefing", async ({ page }) => {
  await page.goto("/");

  // Brand + tagline.
  await expect(page.getByText("Helm").first()).toBeVisible();
  await expect(page.getByText("Think Ahead")).toBeVisible();

  // Intelligence-first: wins + risks, not a chart-first dashboard.
  await expect(page.getByRole("heading", { name: /Today's Wins/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Today's Top Risks/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Recommended Decisions/i })).toBeVisible();
  await expect(page.getByText(/City health at a glance/i)).toBeVisible();

  // Run a simulation and see a recommendation.
  await page.getByRole("button", { name: /Run Simulation/i }).click();
  await expect(page.getByText(/Recommendation/i).first()).toBeVisible();
});
