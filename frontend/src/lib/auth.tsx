import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import type { components } from "../api/generated";
import { apiRequest, getMe, login, type Me } from "../api/client";
import { navigate } from "./navigate";

type UserSession = Me & {
  role: components["schemas"]["Role"];
};

type AuthContextValue = {
  user: UserSession | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  switchRole: (role: UserSession["role"]) => Promise<void>;
  refresh: () => Promise<void>;
};

// Public demo: one synthetic account per role so visitors switch views without a login.
const DEMO_PASSWORD = "demo-password";
const DEMO_EMAIL: Partial<Record<UserSession["role"], string>> = {
  Client: "client.active@example.test",
  Volunteer: "volunteer@example.test",
  "Warehouse Manager": "warehouse.manager@example.test",
  Director: "director@example.test",
};
export const demoRoles = Object.keys(DEMO_EMAIL) as UserSession["role"][];

async function signInDemo(role: UserSession["role"]): Promise<UserSession> {
  const session = await login({ email: DEMO_EMAIL[role]!, password: DEMO_PASSWORD });
  return { ...(await getMe()), role: session.role };
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then((profile) =>
        setUser({
          ...profile,
          role: profile.role ?? "Client",
        }),
      )
      .catch(() => signInDemo("Client").then(setUser)) // first visit: land on the customer view
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
      async refresh() {
        const profile = await getMe();
        setUser({ ...profile, role: profile.role ?? "Client" });
      },
      async switchRole(role) {
        await apiRequest("/auth/logout", { method: "POST" }).catch(() => undefined);
        navigate("/", true); // the old path may be off-limits for the new role
        setUser(await signInDemo(role));
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
    return <p>Checking your sign-in…</p>;
  }
  if (!user) {
    window.history.replaceState({}, "", "/login");
    return <p>Please sign in to continue.</p>;
  }
  return children;
}
