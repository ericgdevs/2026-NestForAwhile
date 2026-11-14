import type { ReactElement } from "react";
import { Agentation } from "agentation";

import AppShell from "./components/AppShell";
import VisitGate from "./components/VisitGate";
import { AuthProvider, ProtectedRoute, useAuth } from "./lib/auth";
import { canVisit } from "./lib/roles";
import Analytics from "./pages/Analytics";
import Approvals from "./pages/Approvals";
import Audit from "./pages/Audit";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Lots from "./pages/Lots";
import Overview from "./pages/Overview";
import Profile from "./pages/Profile";
import Recipes from "./pages/Recipes";
import Replenishment from "./pages/Replenishment";
import Reports from "./pages/Reports";
import Scan from "./pages/Scan";
import ShoppingList from "./pages/ShoppingList";
import Signup from "./pages/Signup";

const screens: Record<string, () => ReactElement> = {
  "/profile": () => <Profile />,
  "/scan": () => <Scan />,
  "/list": () => <ShoppingList />,
  "/cart": () => <Cart />,
  "/recipes": () => <Recipes />,
  "/checkout": () => <Checkout />,
  "/audit": () => <Audit />,
  "/replenishment": () => <Replenishment />,
  "/lots": () => <Lots />,
  "/analytics": () => <Analytics />,
  "/reports": () => <Reports />,
  "/approvals": () => <Approvals />,
};

function Router() {
  const { user, loading } = useAuth();
  const path = window.location.pathname;
  if (loading) {
    return <p className="empty centered">Checking your sign-in…</p>;
  }
  if (!user) {
    return path === "/signup" ? <Signup /> : <Login />;
  }
  if (!canVisit(user.role, path)) {
    return (
      <div className="panel centered">
        <h1 style={{ fontSize: "1.75rem", fontWeight: 900 }}>Unauthorized</h1>
        <p className="panel-sub">This screen is not available for your role.</p>
        <a className="btn btn-secondary" href="/" style={{ marginTop: "1rem" }}>
          Back to start
        </a>
      </div>
    );
  }
  if (path === "/login") return <Login />;
  const screen = screens[path];
  const page = screen ? screen() : user.role === "Client" ? <Home householdSize={user.Household_Size} /> : <Overview />;
  // Clients see shopping screens only during an active visit; Household stays reachable.
  const gated = user.role === "Client" && path !== "/profile" ? <VisitGate>{page}</VisitGate> : page;
  return <ProtectedRoute>{gated}</ProtectedRoute>;
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
