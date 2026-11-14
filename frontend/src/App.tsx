import { AuthProvider, ProtectedRoute } from "./lib/auth";
import Login from "./pages/Login";

function Home() {
  return (
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <h1 className="text-2xl font-semibold">NestForAwhile MTG Warehouse</h1>
      <p className="mt-2 text-slate-600">Welcome to the grocery support workspace.</p>
    </main>
  );
}

function Router() {
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
