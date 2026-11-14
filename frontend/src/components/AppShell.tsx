import type { ReactNode } from "react";

import { useAuth } from "../lib/auth";

const clientLinks = [
  { href: "/", label: "Home", icon: "⌂" },
  { href: "/scan", label: "Scan", icon: "▣" },
  { href: "/cart", label: "Cart", icon: "＋" },
  { href: "/recipes", label: "Recipes", icon: "✦" },
];

export default function AppShell({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return <>{children}</>;

  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="brand-lockup" href="/">
          <span className="brand-mark" aria-hidden="true">N</span>
          <span>
            <strong>Epic-Cure</strong>
            <small>MTG warehouse</small>
          </span>
        </a>
        <div className="header-chip">
          <span className="status-dot" aria-hidden="true" />
          {user.role}
        </div>
      </header>
      <div className="app-content">{children}</div>
      <nav className="bottom-nav" aria-label="Primary navigation">
        {clientLinks.map((link) => (
          <a
            className={window.location.pathname === link.href ? "nav-item nav-item-active" : "nav-item"}
            href={link.href}
            key={link.href}
          >
            <span className="nav-icon" aria-hidden="true">{link.icon}</span>
            <span>{link.label}</span>
          </a>
        ))}
      </nav>
    </div>
  );
}
