/**
 * Cold-start behaviour against Render's free tier.
 *
 * The homepage loads four endpoints with Promise.all. When the API is asleep,
 * Render's edge answers the burst with 429 rather than 5xx, and 429 was not in
 * the retry set — so the site showed "Striops is waking up: snapshot failed:
 * 429" instead of waiting out the ~60s wake.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const ORIGINAL_ENV = { ...process.env };

/** Import a fresh copy of the client — retry budgets are read at module load. */
async function loadApi(env: Record<string, string> = {}) {
  vi.resetModules();
  Object.assign(process.env, {
    STRIOPS_SSR_DELAY_MS: "1",
    STRIOPS_SSR_MAX_DELAY_MS: "1",
    ...env,
  });
  return import("@/lib/api");
}

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

beforeEach(() => {
  process.env = { ...ORIGINAL_ENV };
});

afterEach(() => {
  vi.unstubAllGlobals();
  process.env = { ...ORIGINAL_ENV };
});

describe("retryable statuses", () => {
  it("treats a rate limit as a wake signal, not a failure", async () => {
    const { RETRY_STATUSES } = await loadApi();
    expect(RETRY_STATUSES.has(429)).toBe(true);
  });

  it("still retries the spin-up gateway errors", async () => {
    const { RETRY_STATUSES } = await loadApi();
    for (const status of [502, 503, 504]) {
      expect(RETRY_STATUSES.has(status)).toBe(true);
    }
  });

  it("does not retry a genuine server error", async () => {
    const { RETRY_STATUSES } = await loadApi();
    expect(RETRY_STATUSES.has(500)).toBe(false);
    expect(RETRY_STATUSES.has(404)).toBe(false);
  });
});

describe("retryDelayMs", () => {
  it("honours Retry-After when the edge sends one", async () => {
    const { retryDelayMs } = await loadApi({
      STRIOPS_SSR_DELAY_MS: "2000",
      STRIOPS_SSR_MAX_DELAY_MS: "20000",
    });
    expect(retryDelayMs(0, 5)).toBe(5000);
  });

  it("caps Retry-After so one header cannot stall the page", async () => {
    const { retryDelayMs } = await loadApi({
      STRIOPS_SSR_DELAY_MS: "2000",
      STRIOPS_SSR_MAX_DELAY_MS: "20000",
    });
    expect(retryDelayMs(0, 600)).toBe(20000);
  });

  it("backs off exponentially, capped", async () => {
    const { retryDelayMs } = await loadApi({
      STRIOPS_SSR_DELAY_MS: "2000",
      STRIOPS_SSR_MAX_DELAY_MS: "20000",
    });
    // rand() = 1 gives the top of each jitter window, i.e. the raw curve
    expect(retryDelayMs(0, null, () => 1)).toBe(2000);
    expect(retryDelayMs(1, null, () => 1)).toBe(4000);
    expect(retryDelayMs(2, null, () => 1)).toBe(8000);
    expect(retryDelayMs(9, null, () => 1)).toBe(20000);
  });

  it("jitters so parallel calls do not retry in lockstep", async () => {
    const { retryDelayMs } = await loadApi({
      STRIOPS_SSR_DELAY_MS: "2000",
      STRIOPS_SSR_MAX_DELAY_MS: "20000",
    });
    expect(retryDelayMs(1, null, () => 0)).toBe(2000); // half the window
    expect(retryDelayMs(1, null, () => 1)).toBe(4000); // all of it
  });
});

describe("a cold page load", () => {
  it("waits out a rate-limited wake and then renders", async () => {
    const fetchMock = vi.fn(async () => {
      if (fetchMock.mock.calls.length < 3) {
        return new Response("rate limited", { status: 429 });
      }
      return jsonResponse({ data_through: "August 2026" });
    });
    vi.stubGlobal("fetch", fetchMock);

    const { getSnapshot } = await loadApi();
    const snapshot = await getSnapshot();

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(snapshot.data_through).toBe("August 2026");
  });

  it("gives up honestly, naming the status, once the budget is spent", async () => {
    const fetchMock = vi.fn(async () => new Response("rate limited", { status: 429 }));
    vi.stubGlobal("fetch", fetchMock);

    const { getSnapshot } = await loadApi({ STRIOPS_SSR_RETRIES: "2" });

    await expect(getSnapshot()).rejects.toThrow("snapshot failed: 429");
    expect(fetchMock).toHaveBeenCalledTimes(3); // initial + 2 retries
  });

  it("stops retrying when the overall budget is exhausted", async () => {
    const fetchMock = vi.fn(async () => new Response("waking", { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);

    const { getSnapshot } = await loadApi({
      STRIOPS_SSR_RETRIES: "50",
      STRIOPS_SSR_DELAY_MS: "40",
      STRIOPS_SSR_MAX_DELAY_MS: "40",
      STRIOPS_SSR_BUDGET_MS: "100",
    });

    await expect(getSnapshot()).rejects.toThrow("snapshot failed: 503");
    // the budget, not the retry count, is what stops it
    expect(fetchMock.mock.calls.length).toBeLessThan(20);
  });

  it("does not retry a 404 — that is an answer, not a wake", async () => {
    const fetchMock = vi.fn(async () => new Response("nope", { status: 404 }));
    vi.stubGlobal("fetch", fetchMock);

    const { getSnapshot } = await loadApi();

    await expect(getSnapshot()).rejects.toThrow("snapshot failed: 404");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
