import { describe, expect, it } from "vitest";
import { formatZAR, priorityColor } from "@/lib/api";

describe("formatZAR", () => {
  it("formats billions", () => {
    expect(formatZAR(4_600_000_000)).toBe("R4.60bn");
  });
  it("formats millions", () => {
    expect(formatZAR(12_500_000)).toBe("R12.5m");
  });
  it("formats small values", () => {
    expect(formatZAR(4200)).toBe("R4,200");
  });
});

describe("priorityColor", () => {
  it("maps critical to the danger palette", () => {
    expect(priorityColor("critical")).toContain("striops-bad");
  });
  it("maps low to a muted palette", () => {
    expect(priorityColor("low")).toContain("white/60");
  });
});
