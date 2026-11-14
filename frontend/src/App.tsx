import { AuthProvider, ProtectedRoute } from "./lib/auth";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Home from "./pages/Home";
import Scan from "./pages/Scan";
import Cart from "./pages/Cart";
import Recipes from "./pages/Recipes";
import Checkout from "./pages/Checkout";
import Audit from "./pages/Audit";
import Replenishment from "./pages/Replenishment";
import Lots from "./pages/Lots";
import Waiting from "./pages/Waiting";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import { useAuth } from "./lib/auth";
import { getCapacity } from "./api/client";
import { useEffect, useState } from "react";
import { canVisit } from "./lib/roles";
import { Agentation } from "agentation";
import AppShell from "./components/AppShell";

function StaffHome() {
  const { user } = useAuth();
  const [capacity, setCapacity] = useState<{ Active_Floor_Shoppers: number } | null>(null);

  useEffect(() => {
    if (user?.role !== "Client") {
      getCapacity().then(setCapacity).catch(() => setCapacity(null));
    }
  }, [user?.role]);

  return (
    <main className="space-y-8">
      <div>
        <p className="eyebrow">Operations overview</p>
        <h1 className="display-title mt-3">Keep the floor<br />moving.</h1>
        <p className="mt-4 max-w-xl text-slate-600">A quick view of today’s grocery support work for the Epic-Cure team.</p>
      </div>
      {capacity && (
        <section className="soft-card max-w-xl p-6">
          <p className="eyebrow">Live capacity</p>
          <p className="mt-3 text-4xl font-bold tracking-tight text-[#173a5a]">{capacity.Active_Floor_Shoppers}</p>
          <p className="mt-1 text-sm text-slate-500">active shoppers on the floor</p>
        </section>
      )}
    </main>
  );
}

function Router() {
  const { user, loading } = useAuth();
  if (loading) {
    return <p className="p-6 text-slate-600">Checking your sign-in…</p>;
  }
  if (!user) {
    return <Login />;
  }
  if (!canVisit(user.role, window.location.pathname)) {
    return <main className="p-6"><h1 className="text-2xl font-semibold">Unauthorized</h1><p className="mt-2">This screen is not available for your role.</p></main>;
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
