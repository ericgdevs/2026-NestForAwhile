import type { components } from "../api/generated";

export type AppRole = components["schemas"]["Role"];

export const clientPaths = ["/profile", "/scan", "/cart", "/recipes"] as const;
export const checkoutRoles: AppRole[] = ["Volunteer", "Warehouse Manager"];

export function canVisit(role: AppRole, path: string): boolean {
  if (clientPaths.includes(path as (typeof clientPaths)[number])) return role === "Client";
  if (path === "/checkout") return checkoutRoles.includes(role);
  return true;
}
