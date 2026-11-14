import { render, screen } from "@testing-library/react";

import App from "./App";

test("renders the warehouse shell", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: /mtg warehouse/i })).toBeInTheDocument();
});
