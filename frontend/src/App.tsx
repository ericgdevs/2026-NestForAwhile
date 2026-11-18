import { lazy, Suspense, useEffect, type ReactElement } from "react";
import { Agentation } from "agentation";

import AppShell from "./components/AppShell";
import VisitGate from "./components/VisitGate";
import { AuthProvider, ProtectedRoute, useAuth } from "./lib/auth";
import { onLinkClick, usePath } from "./lib/navigate";
import { canVisit } from "./lib/roles";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Signup from "./pages/Signup";

const Analytics = lazy(() => import("./pages/Analytics"));
const Approvals = lazy(() => import("./pages/Approvals"));
const Audit = lazy(() => import("./pages/Audit"));
const Cart = lazy(() => import("./pages/Cart"));
const Checkout = lazy(() => import("./pages/Checkout"));
const Labels = lazy(() => import("./pages/Labels"));
const Lots = lazy(() => import("./pages/Lots"));
const Profile = lazy(() => import("./pages/Profile"));
const Recipes = lazy(() => import("./pages/Recipes"));
const Replenishment = lazy(() => import("./pages/Replenishment"));
const Reports = lazy(() => import("./pages/Reports"));
const Scan = lazy(() => import("./pages/Scan"));
const ShoppingList = lazy(() => import("./pages/ShoppingList"));

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
  "/labels": () => <Labels />,
};

function Router() {
  const { user, loading } = useAuth();
  const path = usePath();
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
  const home = user.role === "Client" ? <Home householdSize={user.Household_Size} /> : <Overview />;
  // Screens load as separate chunks, so the first visit downloads only what it shows.
  const page = <Suspense fallback={<p className="empty">Loading…</p>}>{screen ? screen() : home}</Suspense>;
  // Clients see shopping screens only during an active visit; Household stays reachable.
  const gated = user.role === "Client" && path !== "/profile" ? <VisitGate>{page}</VisitGate> : page;
  return <ProtectedRoute>{gated}</ProtectedRoute>;
}

export default function App() {
  // Links move around inside the app, so a click never reloads it and refetches the session.
  useEffect(() => {
    document.addEventListener("click", onLinkClick);
    return () => document.removeEventListener("click", onLinkClick);
  }, []);
  return (
    <AuthProvider>
      <AppShell>
        <Router />
      </AppShell>
      {import.meta.env.DEV && import.meta.env.MODE !== "test" && <Agentation />}
    </AuthProvider>
  );
}
