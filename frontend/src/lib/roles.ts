import type { components } from "../api/generated";
import type { IconName } from "../components/Icon";

export type AppRole = components["schemas"]["Role"];

export const clientPaths = ["/profile", "/scan", "/list", "/cart", "/recipes"] as const;
export const checkoutRoles: AppRole[] = ["Volunteer", "Warehouse Manager", "Director"];
export const warehousePaths = ["/audit", "/replenishment", "/lots"] as const;
export const managementPaths = ["/analytics"] as const;

export function canVisit(role: AppRole, path: string): boolean {
  if (clientPaths.includes(path as (typeof clientPaths)[number])) return role === "Client";
  if (path === "/checkout") return checkoutRoles.includes(role);
  if (warehousePaths.includes(path as (typeof warehousePaths)[number])) {
    return role === "Warehouse Staff" || role === "Warehouse Manager";
  }
  if (managementPaths.includes(path as (typeof managementPaths)[number])) {
    return role === "Warehouse Manager" || role === "Director";
  }
  if (path === "/labels") return role === "Warehouse Manager";
  if (path === "/approvals") return role === "Warehouse Manager";
  return true;
}

export type NavLink = { href: string; label: string; icon: IconName };

const allLinks: NavLink[] = [
  { href: "/scan", label: "Scan", icon: "scan" },
  { href: "/list", label: "List", icon: "list" },
  { href: "/cart", label: "Cart", icon: "cart" },
  { href: "/recipes", label: "Recipes", icon: "recipes" },
  { href: "/profile", label: "Profile", icon: "profile" },
  { href: "/checkout", label: "Checkout", icon: "checkout" },
  { href: "/audit", label: "Audit", icon: "audit" },
  { href: "/replenishment", label: "Restock", icon: "restock" },
  { href: "/lots", label: "Lots", icon: "lots" },
  { href: "/labels", label: "Labels", icon: "scan" },
  { href: "/approvals", label: "Approvals", icon: "profile" },
  { href: "/analytics", label: "Analytics", icon: "analytics" },
];

// Nav comes from canVisit so a role never sees a link it cannot open.
export function navFor(role: AppRole): NavLink[] {
  const home: NavLink = { href: "/", label: role === "Client" ? "Home" : "Overview", icon: "home" };
  return [home, ...allLinks.filter((link) => canVisit(role, link.href))];
}
