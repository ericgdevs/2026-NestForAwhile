import { FormEvent, useState } from "react";

import { useAuth } from "../lib/auth";

export default function Login() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
    <main className="flex min-h-screen items-center justify-center p-6">
      <form className="soft-card w-full max-w-md space-y-6 p-7 sm:p-9" onSubmit={handleSubmit}>
        <div className="space-y-4">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-stone-500">A gentler grocery visit</p>
          <h1 aria-label="Sign in" className="display-title">Sign in<br />to continue.</h1>
          <p className="text-stone-500">Sign in to find food that fits your household.</p>
        </div>
        <label className="block text-sm font-medium">
          Email
          <input
            className="soft-input mt-2 w-full px-4 py-3"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="block text-sm font-medium">
          Password
          <input
            className="soft-input mt-2 w-full px-4 py-3"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}
        <button
          className="accent-button w-full px-4 py-3 disabled:opacity-50"
          type="submit"
          disabled={submitting}
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
        <button
          className="w-full rounded-full border border-stone-300 px-4 py-3 font-semibold text-stone-700 transition hover:border-stone-500"
          type="button"
          onClick={() => setError("Please ask staff to create your account.")}
        >
          Create Account
        </button>
      </form>
    </main>
  );
}
