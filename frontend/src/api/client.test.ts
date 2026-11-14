import { beforeEach, expect, test, vi } from "vitest";

import { getCapacity } from "./client";

beforeEach(() => {
  vi.restoreAllMocks();
});

test("API requests include cookies and return typed JSON", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({
        Active_Floor_Shoppers: 1,
        Max_Floor_Capacity: 4,
        Queue_Waiting: 0,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    ),
  );

  await expect(getCapacity()).resolves.toEqual({
    Active_Floor_Shoppers: 1,
    Max_Floor_Capacity: 4,
    Queue_Waiting: 0,
  });
  expect(fetch).toHaveBeenCalledWith(
    "/capacity",
    expect.objectContaining({ credentials: "include" }),
  );
});

test("adding a recipe that only uses the scanned item sends nothing", async () => {
  const { addRecipeToList } = await import("./client");
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const recipe = { title: "Oats", ingredients: [{ name: "Oats", product_id: 1 }], steps: ["Cook."] };
  await expect(addRecipeToList(recipe, 1)).resolves.toBeNull();
  expect(fetchMock).not.toHaveBeenCalled();
  vi.unstubAllGlobals();
});
