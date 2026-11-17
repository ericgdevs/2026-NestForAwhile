import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import StatGrid from "./StatGrid";

const stat = (value: number | string | null) => [{ label: "Families served", value, icon: "home" as const, tone: "blue" as const }];

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

test("shows the final value straight away where counting is unavailable", () => {
  render(<StatGrid stats={stat(1250)} />);
  expect(screen.getByText("1,250")).toBeInTheDocument();
});

test("counts up from zero when scrolled into view and keeps the % sign", () => {
  vi.stubGlobal(
    "IntersectionObserver",
    class {
      constructor(private callback: (entries: { isIntersecting: boolean }[]) => void) {}
      observe() { this.callback([{ isIntersecting: true }]); }
      disconnect() {}
    },
  );
  render(<StatGrid stats={stat("50%")} />);
  expect(screen.getByText("0%")).toBeInTheDocument();

  act(() => void vi.advanceTimersByTime(1000));
  expect(screen.getByText("50%")).toBeInTheDocument();
});

test("a missing value stays a dash", () => {
  render(<StatGrid stats={stat(null)} />);
  expect(screen.getByText("—")).toBeInTheDocument();
});
