import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { navigate, onLinkClick, usePath } from "./navigate";

function Path() {
  return <p>at {usePath()}</p>;
}

afterEach(() => {
  document.removeEventListener("click", onLinkClick);
  window.history.replaceState({}, "", "/");
});

test("navigate changes the path and re-renders without a page load", () => {
  render(<Path />);
  act(() => navigate("/cart"));
  expect(screen.getByText("at /cart")).toBeInTheDocument();
  expect(window.location.pathname).toBe("/cart");
});

test("the back button updates the path too", () => {
  render(<Path />);
  act(() => navigate("/scan"));
  window.history.replaceState({}, "", "/list");
  act(() => {
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  expect(screen.getByText("at /list")).toBeInTheDocument();
});

test("a plain click on a same-site link is handled in the app; other clicks are left alone", () => {
  document.addEventListener("click", onLinkClick);
  render(
    <>
      <Path />
      <a href="/recipes?x=1">Recipes</a>
      <a href="https://elsewhere.test/">Away</a>
      <a href="/files" download>
        File
      </a>
    </>,
  );
  fireEvent.click(screen.getByText("Recipes"));
  expect(window.location.pathname + window.location.search).toBe("/recipes?x=1");

  fireEvent.click(screen.getByText("Recipes"), { ctrlKey: true });
  fireEvent.click(screen.getByText("File"));
  expect(window.location.pathname).toBe("/recipes"); // the ctrl-click and the download did not navigate
});
