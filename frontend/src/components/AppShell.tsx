import type { ReactNode } from "react";

import { useAuth } from "../lib/auth";

const clientLinks = [
  { href: "/", label: "Home", icon: "⌂" },
  { href: "/scan", label: "Scan", icon: "▣" },
  { href: "/cart", label: "Cart", icon: "＋" },
  { href: "/recipes", label: "Recipes", icon: "✦" },
  { href: "/profile", label: "Profile", icon: "⚙" },
];

const staffLinks = [
  { href: "/", label: "Overview", icon: "⌂" },
  { href: "/lots", label: "Inventory", icon: "▣" },
  { href: "/waiting", label: "Queue", icon: "◷" },
  { href: "/replenishment", label: "Restock", icon: "⇪" },
  { href: "/reports", label: "Reports", icon: "▤" },
];

export default function AppShell({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return <>{children}</>;
  const links = user.role === "Client" ? clientLinks : staffLinks;

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="brand-wrapper">
          <a href="/" style={{ display: "flex", alignItems: "center", gap: "0.85rem", textDecoration: "none" }}>
            <span className="brand-icon" aria-hidden="true">E</span>
            <span className="brand-title">
              <strong style={{ color: "#ffffff" }}>Epic-Cure</strong>
              <span className="brand-subtitle">MTG warehouse</span>
            </span>
          </a>
        </div>
        <nav className="header-nav" aria-label="Primary navigation">
          {links.map((link) => {
            const isActive = window.location.pathname === link.href;
            return (
              <a
                aria-current={isActive ? "page" : undefined}
                className={`nav-pill ${isActive ? "nav-pill-active" : ""}`}
                href={link.href}
                key={link.href}
              >
                <span aria-hidden="true">{link.icon}</span>
                <span>{link.label}</span>
              </a>
            );
          })}
        </nav>
        <div className="role-pill">
          <span className="role-indicator" aria-hidden="true" />
          <span>{user.role}</span>
        </div>
      </header>
      <div className="main-canvas">{children}</div>
      <nav className="bottom-nav" aria-label="Primary mobile navigation">
        {links.map((link) => {
          const isActive = window.location.pathname === link.href;
          return (
            <a
              aria-current={isActive ? "page" : undefined}
              className={`bottom-nav-item ${isActive ? "bottom-nav-item-active" : ""}`}
              href={link.href}
              key={link.href}
            >
              <span aria-hidden="true">{link.icon}</span>
              <span>{link.label}</span>
            </a>
          );
        })}
      </nav>
    </div>
  );
}