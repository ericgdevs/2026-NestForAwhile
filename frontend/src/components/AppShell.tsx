import type { ReactNode } from "react";

import { demoRoles, useAuth } from "../lib/auth";
import { navFor, type NavLink } from "../lib/roles";
import Icon from "./Icon";

function Links({ links }: { links: NavLink[] }) {
  return (
    <>
      {links.map((link) => (
        <a
          aria-current={window.location.pathname === link.href ? "page" : undefined}
          href={link.href}
          key={link.href}
        >
          <Icon name={link.icon} />
          <span>{link.label}</span>
        </a>
      ))}
    </>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, switchRole } = useAuth();
  if (!user) return <>{children}</>;
  const links = navFor(user.role);
  const isClient = user.role === "Client";

  async function handleSwitch(role: typeof demoRoles[number]) {
    try {
      await switchRole(role);
    } catch {
      window.alert("We couldn't switch views. Please try again.");
    }
  }

  // Bottom of the sidebar on desktop; the top bar on phones and tablets, where there's no sidebar.
  const account = (
    <>
      {isClient && (
        <a className="signout" href="/profile">
          <Icon name="profile" />
          <span>Household</span>
        </a>
      )}
      <select
        aria-label="Demo role"
        className="signout"
        value={user.role}
        onChange={(event) => void handleSwitch(event.target.value as typeof demoRoles[number])}
      >
        {demoRoles.map((role) => (
          <option key={role} value={role}>
            {role === "Client" ? "Customer" : role}
          </option>
        ))}
      </select>
    </>
  );

  const wordmark = (
    <a className="wordmark" href="/">
      <strong>Epic-Cure</strong>
      <span>MTG Warehouse</span>
    </a>
  );

  return (
    <div className={`shell ${isClient ? "shell-client" : ""}`}>
      <aside className="sidebar">
        {wordmark}
        <nav aria-label="Primary navigation">
          <Links links={links} />
        </nav>
        <div className="sidebar-account">
          {account}
          <p className="role-hint">
            <svg aria-hidden="true" fill="none" height="30" viewBox="0 0 34 30" width="34">
              <path
                d="M32 24 Q9 24 9 8 M3 13 L9 6 L15 13"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
              />
            </svg>
            Change Roles Here
          </p>
        </div>
      </aside>
      <header className="topbar">
        {wordmark}
        <div className="topbar-meta">{account}</div>
      </header>
      {!isClient && (
        <nav aria-label="Section navigation" className="navrow">
          <Links links={links} />
        </nav>
      )}
      <div className="main">
        {children}
      </div>
      {isClient && (
        <nav aria-label="Mobile navigation" className="tabbar">
          <Links links={links.filter((link) => link.href !== "/profile")} />
        </nav>
      )}
    </div>
  );
}
