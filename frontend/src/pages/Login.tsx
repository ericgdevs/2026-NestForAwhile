import { FormEvent, useState } from "react";

import { useAuth } from "../lib/auth";

export default function Login() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await signIn(email, password);
      window.history.replaceState({}, "", "/");
      window.dispatchEvent(new PopStateEvent("popstate"));
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "";
      setError(
        message.toLowerCase().includes("active")
          ? "This client account is not active yet. Please ask staff for help."
          : "We couldn't sign you in. Check your email and password and try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "1.5rem",
        backgroundColor: "var(--bg-canvas)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1020px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "2rem",
          alignItems: "center",
        }}
      >
        {/* Left Branding Showcase Card */}
        <section
          style={{
            background: "linear-gradient(145deg, #121622, #1b2333)",
            color: "#ffffff",
            borderRadius: "var(--radius-xl)",
            padding: "2.75rem 2.25rem",
            boxShadow: "var(--shadow-floating)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            minHeight: "360px",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "2rem" }}>
              <span className="brand-icon" aria-hidden="true">E</span>
              <span style={{ fontSize: "1.25rem", fontWeight: 700, letterSpacing: "-0.02em" }}>Epic-Cure</span>
            </div>
            <span
              style={{
                display: "inline-block",
                padding: "0.3rem 0.75rem",
                borderRadius: "var(--radius-pill)",
                background: "rgba(56, 189, 248, 0.15)",
                color: "#7dd3fc",
                fontSize: "0.78rem",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "1rem",
              }}
            >
              Medically tailored groceries
            </span>
            <h1
              style={{
                fontSize: "2.5rem",
                fontWeight: 800,
                lineHeight: 1.1,
                letterSpacing: "-0.04em",
                margin: "0 0 1.25rem",
              }}
            >
              Food support that feels human.
            </h1>
          </div>
          <p style={{ color: "#94a3b8", fontSize: "0.95rem", lineHeight: 1.6, margin: 0 }}>
            Find food that fits your household, understand what works for you, and shop with confidence.
          </p>
        </section>

        {/* Right Form Card */}
        <form
          className="ui-card"
          style={{
            padding: "2.5rem 2rem",
            boxShadow: "var(--shadow-floating)",
            display: "flex",
            flexDirection: "column",
            gap: "1.25rem",
          }}
          onSubmit={handleSubmit}
        >
          <div>
            <span className="eyebrow-chip" style={{ marginBottom: "0.5rem" }}>Welcome back</span>
            <h1
              aria-label="Sign in"
              className="page-title"
              style={{ fontSize: "1.85rem", margin: "0.25rem 0 0" }}
            >
              Sign in to continue.
            </h1>
            <p className="page-subtitle" style={{ margin: "0.4rem 0 0" }}>
              Use your Epic-Cure account to continue.
            </p>
          </div>

          <label className="form-group">
            <span className="form-label">Email</span>
            <input
              className="form-input"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@example.test"
            />
          </label>

          <label className="form-group">
            <span className="form-label">Password</span>
            <span style={{ position: "relative", display: "block" }}>
              <input
                className="form-input"
                style={{ paddingRight: "2.75rem" }}
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter password"
              />
              <button
                aria-label={showPassword ? "Hide password" : "Show password"}
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                style={{
                  position: "absolute",
                  right: "0.75rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  padding: "0.25rem",
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <svg
                  aria-hidden="true"
                  style={{ width: "1.25rem", height: "1.25rem" }}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  {showPassword ? (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.8}
                      d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M9.9 5.2A10.7 10.7 0 0112 5c5.2 0 8.7 4.5 9.8 7a11.8 11.8 0 01-3.1 4.2M6.2 6.2C3.9 7.8 2.7 10.1 2.2 12c.5 1.4 1.9 4.2 5.4 6.1A10.7 10.7 0 0012 19c1.1 0 2.1-.2 3-.5"
                    />
                  ) : (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.8}
                      d="M2.2 12C3.3 9.5 6.8 5 12 5s8.7 4.5 9.8 7c-1.1 2.5-4.6 7-9.8 7s-8.7-4.5-9.8-7zM12 15a3 3 0 100-6 3 3 0 000 6z"
                    />
                  )}
                </svg>
              </button>
            </span>
          </label>

          {error && (
            <div
              style={{
                background: "var(--pastel-rose-bg)",
                border: "1px solid var(--pastel-rose-border)",
                color: "var(--pastel-rose-text)",
                padding: "0.75rem 1rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.88rem",
                fontWeight: 500,
              }}
            >
              {error}
            </div>
          )}

          <button
            className="btn btn-primary"
            style={{ width: "100%", padding: "0.85rem", marginTop: "0.5rem" }}
            type="submit"
            disabled={submitting}
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>

          <button
            className="btn btn-secondary"
            style={{ width: "100%", padding: "0.85rem" }}
            type="button"
            onClick={() => setError("Please ask staff to create your account.")}
          >
            Create Account
          </button>
        </form>
      </div>
    </main>
  );
}
