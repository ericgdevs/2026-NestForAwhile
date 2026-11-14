import type { components } from "../api/generated";

export type AppRole = components["schemas"]["Role"];

export const clientPaths = ["/profile", "/scan", "/cart", "/recipes"] as const;
export const checkoutRoles: AppRole[] = ["Volunteer", "Warehouse Manager"];
export const warehousePaths = ["/audit", "/replenishment", "/lots"] as const;
export const managementPaths = ["/analytics", "/reports"] as const;

export function canVisit(role: AppRole, path: string): boolean {
  if (clientPaths.includes(path as (typeof clientPaths)[number])) return role === "Client";
  if (path === "/checkout") return checkoutRoles.includes(role);
  if (warehousePaths.includes(path as (typeof warehousePaths)[number])) {
    return role === "Warehouse Staff" || role === "Warehouse Manager";
  }
  if (managementPaths.includes(path as (typeof managementPaths)[number])) {
    return role === "Warehouse Manager" || role === "Director";
  }
  if (path === "/waiting") return role === "Client";
  return true;
}
