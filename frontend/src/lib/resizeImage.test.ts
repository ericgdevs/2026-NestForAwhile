import { expect, test } from "vitest";

import { fitWithin } from "./resizeImage";

test("shrinks big photos to a 1600px long edge and leaves small ones alone", () => {
  expect(fitWithin(4032, 3024)).toEqual({ width: 1600, height: 1200 });
  expect(fitWithin(3024, 4032)).toEqual({ width: 1200, height: 1600 });
  expect(fitWithin(800, 600)).toEqual({ width: 800, height: 600 });
});
