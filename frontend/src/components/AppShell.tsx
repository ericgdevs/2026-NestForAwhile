import type { ReactNode } from "react";

import { useAuth } from "../lib/auth";
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
  const { user, signOut } = useAuth();
  if (!user) return <>{children}</>;
  const links = navFor(user.role);
  const isClient = user.role === "Client";

  async function handleSignOut() {
    try {
      await signOut();
      window.history.replaceState({}, "", "/login");
    } catch {
      window.alert("We couldn't sign you out. Please try again.");
    }
  }

  // Bottom of the sidebar on desktop; the top bar on phones and tablets, where there's no sidebar.
  const account = (
    <>
      {isClient ? (
        <a className="signout" href="/profile">
          <Icon name="profile" />
          <span>Household</span>
        </a>
      ) : (
        <span className="role-tag">{user.role}</span>
      )}
      <button className="signout" type="button" onClick={() => void handleSignOut()}>
        <Icon name="logout" />
        <span>Sign out</span>
      </button>
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
        <div className="sidebar-account">{account}</div>
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
