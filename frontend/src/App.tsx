import { AuthProvider, ProtectedRoute } from "./lib/auth";

function Home() {
  return (
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <h1 className="text-2xl font-semibold">NestForAwhile MTG Warehouse</h1>
      <p className="mt-2 text-slate-600">Welcome to the grocery support workspace.</p>
    </main>
  );
}

function LoginPlaceholder() {
  return (
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      <p className="mt-2 text-slate-600">Your sign-in form will appear here.</p>
    </main>
  );
}

function Router() {
  return window.location.pathname === "/login" ? (
    <LoginPlaceholder />
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
