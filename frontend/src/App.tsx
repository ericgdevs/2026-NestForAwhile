import { AuthProvider, ProtectedRoute } from "./lib/auth";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import { useAuth } from "./lib/auth";
import { getCapacity } from "./api/client";
import { useEffect, useState } from "react";

function Home() {
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
  if (window.location.pathname === "/profile") {
    return (
      <ProtectedRoute>
        <Profile />
      </ProtectedRoute>
    );
  }
  return window.location.pathname === "/login" ? (
    <Login />
  ) : (
    <ProtectedRoute>
      <Home />
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router />
    </AuthProvider>
  );
}
