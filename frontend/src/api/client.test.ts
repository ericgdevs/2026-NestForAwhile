import { afterEach, expect, test, vi } from "vitest";

import { apiRequest } from "./client";

const reply = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body)));

afterEach(() => vi.unstubAllGlobals());

test("two identical GETs at the same moment share one network request", async () => {
  const fetchMock = vi.fn(() => reply({ ok: true }));
  vi.stubGlobal("fetch", fetchMock);
  const [a, b] = await Promise.all([apiRequest("/me/household"), apiRequest("/me/household")]);
  expect(a).toEqual({ ok: true });
  expect(b).toEqual({ ok: true });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  await apiRequest("/me/household"); // finished requests are never reused: data stays fresh
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

test("changes and cancellable requests are never shared", async () => {
  const fetchMock = vi.fn(() => reply({}));
  vi.stubGlobal("fetch", fetchMock);
  await Promise.all([apiRequest("/cart/items", { method: "POST", body: {} }), apiRequest("/cart/items", { method: "POST", body: {} })]);
  const controller = new AbortController();
  await Promise.all([apiRequest("/p", { signal: controller.signal }), apiRequest("/p", { signal: controller.signal })]);
  expect(fetchMock).toHaveBeenCalledTimes(4);
});
