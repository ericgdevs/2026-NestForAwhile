import { FormEvent, useState } from "react";

import Icon from "../components/Icon";
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
    <main className="login">
      <header className="login-topbar">
        <span className="wordmark">
          <strong>Epic-Cure</strong>
          <span>MTG Warehouse</span>
        </span>
      </header>

      <div className="login-form-wrap">
        <form className="login-form" onSubmit={handleSubmit}>
          <h1>Sign in</h1>

          <label className="field">
            <span className="field-label">Email</span>
            <input
              autoComplete="email"
              className="input"
              placeholder="name@example.test"
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="field">
            <span className="field-label">Password</span>
            <span className="password-wrap">
              <input
                autoComplete="current-password"
                className="input"
                placeholder="Enter password"
                required
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              <button
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="password-toggle"
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
              >
                <Icon name={showPassword ? "eyeOff" : "eye"} />
              </button>
            </span>
          </label>

          {error && (
            <p className="alert alert-danger" role="alert">
              <Icon name="alert" />
              {error}
            </p>
          )}

          <button className="btn btn-primary btn-block" disabled={submitting} type="submit">
            {submitting ? "Signing in…" : "Sign in"}
          </button>
          <a className="btn btn-secondary btn-block" href="/signup">
            Create Account
          </a>
        </form>
      </div>
    </main>
  );
}
