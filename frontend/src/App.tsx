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

function StaffHome() {
  const { user } = useAuth();
  const [capacity, setCapacity] = useState<{ Active_Floor_Shoppers: number } | null>(null);

  useEffect(() => {
    if (user?.role !== "Client") {
      getCapacity().then(setCapacity).catch(() => setCapacity(null));
    }
  }, [user?.role]);

  return (
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <h1 className="text-2xl font-semibold">NestForAwhile MTG Warehouse</h1>
      <p className="mt-2 text-slate-600">Welcome to the grocery support workspace.</p>
      {capacity && (
        <p className="mt-4 rounded-lg bg-white p-4 shadow-sm">
          Active shoppers: <strong>{capacity.Active_Floor_Shoppers}</strong>
        </p>
      )}
    </main>
  );
}

function Router() {
  const { user, loading } = useAuth();
  if (loading || !user) {
    return window.location.pathname === "/login" ? <Login /> : <ProtectedRoute><Home /></ProtectedRoute>;
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
      <Router />
      {import.meta.env.DEV && import.meta.env.MODE !== "test" && <Agentation />}
    </AuthProvider>
  );
}
