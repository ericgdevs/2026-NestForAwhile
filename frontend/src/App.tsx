import { useEffect, useState } from "react";
import { Agentation } from "agentation";

import { getCapacity } from "./api/client";
import AppShell from "./components/AppShell";
import { AuthProvider, ProtectedRoute, useAuth } from "./lib/auth";
import { canVisit } from "./lib/roles";
import Analytics from "./pages/Analytics";
import Audit from "./pages/Audit";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Lots from "./pages/Lots";
import Profile from "./pages/Profile";
import Recipes from "./pages/Recipes";
import Replenishment from "./pages/Replenishment";
import Reports from "./pages/Reports";
import Scan from "./pages/Scan";
import Waiting from "./pages/Waiting";

function StaffHome() {
  const { user } = useAuth();
  const [capacity, setCapacity] = useState<{ Active_Floor_Shoppers: number } | null>(null);

  useEffect(() => {
    if (user?.role !== "Client") {
      getCapacity().then(setCapacity).catch(() => setCapacity(null));
    }
  }, [user?.role]);

  return (
    <div>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Operations overview</span>
          <h1 className="page-title">Keep the floor<br />moving.</h1>
          <p className="page-subtitle">A quick view of today’s grocery support work for the Epic-Cure team.</p>
        </div>
      </div>
      {capacity && (
        <div className="stat-grid" style={{ maxWidth: "24rem" }}>
          <div className="stat-tile stat-tile-blue">
            <span className="stat-label">Live capacity</span>
            <p className="stat-number">{capacity.Active_Floor_Shoppers}</p>
            <p className="stat-caption">Active shoppers: {capacity.Active_Floor_Shoppers} on the floor</p>
          </div>
        </div>
      )}
    </div>
  );
}

function Router() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="ui-card" style={{ maxWidth: "24rem", margin: "3rem auto", textAlign: "center" }}>
        <p style={{ color: "var(--text-muted)", margin: 0 }}>Checking your sign-in…</p>
      </div>
    );
  }
  if (!user) {
    return <Login />;
  }
  if (!canVisit(user.role, window.location.pathname)) {
    return (
      <div className="ui-card" style={{ maxWidth: "32rem", margin: "2rem auto", textAlign: "center" }}>
        <h1 className="page-title" style={{ fontSize: "1.75rem" }}>Unauthorized</h1>
        <p className="page-subtitle" style={{ margin: "0.75rem auto 0" }}>This screen is not available for your role.</p>
      </div>
    );
  }
  if (window.location.pathname === "/profile") {
    return (
      <ProtectedRoute>
        <Profile />
      </ProtectedRoute>
    );
  }
  if (window.location.pathname === "/scan") {
    return (
      <ProtectedRoute>
        <Scan />
      </ProtectedRoute>
    );
  }
  if (window.location.pathname === "/cart") {
    return (
      <ProtectedRoute>
        <Cart />
      </ProtectedRoute>
    );
  }
  if (window.location.pathname === "/recipes") {
    return (
      <ProtectedRoute>
        <Recipes />
      </ProtectedRoute>
    );
  }
  if (window.location.pathname === "/checkout") {
    return (
      <ProtectedRoute>
        <Checkout />
      </ProtectedRoute>
    );
  }
  const screens: Record<string, JSX.Element> = {
    "/audit": <Audit />,
    "/replenishment": <Replenishment />,
    "/lots": <Lots />,
    "/waiting": <Waiting />,
    "/analytics": <Analytics />,
    "/reports": <Reports />,
  };
  if (screens[window.location.pathname]) {
    return <ProtectedRoute>{screens[window.location.pathname]}</ProtectedRoute>;
  }
  return window.location.pathname === "/login" ? (
    <Login />
  ) : (
    <ProtectedRoute>
      {window.location.pathname === "/" ? <Home /> : <StaffHome />}
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell>
        <Router />
      </AppShell>
      {import.meta.env.DEV && import.meta.env.MODE !== "test" && <Agentation />}
    </AuthProvider>
  );
}
