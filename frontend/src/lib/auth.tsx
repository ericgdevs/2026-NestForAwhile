import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import type { components } from "../api/generated";
import { apiRequest, getMe, login } from "../api/client";

type UserSession = components["schemas"]["Client"] & {
  role: components["schemas"]["Role"];
};

type AuthContextValue = {
  user: UserSession | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then((profile) => setUser({ ...profile, role: "Client" }))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      async signIn(email, password) {
        const session = await login({ email, password });
        const profile = await getMe();
        setUser({ ...profile, role: session.role });
      },
      async signOut() {
        await apiRequest("/auth/logout", { method: "POST" });
        setUser(null);
      },
    }),
    [loading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { loading, user } = useAuth();
  if (loading) {
    return <p className="p-6 text-slate-600">Checking your sign-in…</p>;
  }
  if (!user) {
    window.history.replaceState({}, "", "/login");
    return <p className="p-6 text-slate-600">Please sign in to continue.</p>;
  }
  return children;
}
