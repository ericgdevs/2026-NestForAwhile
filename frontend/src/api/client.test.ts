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

test("adding a recipe asks the server to diff it, skipping the scanned item", async () => {
  const { addRecipeToList } = await import("./client");
  const result = { added: [], blocked: [], in_cart: 0, already_on_list: 0 };
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(result), { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
  const recipe = { title: "Oats", ingredients: [{ name: "Oats", product_id: 1 }], steps: ["Cook."] };
  await expect(addRecipeToList(recipe, 1)).resolves.toEqual(result);
  expect(String(fetchMock.mock.calls[0][0])).toContain("/shopping-list/from-recipe");
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ recipe, skip_product_id: 1 });
  vi.unstubAllGlobals();
});
