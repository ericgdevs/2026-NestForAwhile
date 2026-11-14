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
    <main className="grid min-h-screen items-center gap-8 p-5 md:grid-cols-[minmax(0,1fr)_minmax(25rem,30rem)] md:gap-16 md:p-10 lg:mx-auto lg:max-w-7xl">
      <section className="hidden rounded-[2rem] bg-[#173a5a] p-10 text-white md:block lg:p-14">
        <div className="flex h-full min-h-[32rem] flex-col justify-between">
          <div>
            <div className="mb-12 flex items-center gap-3">
              <span className="brand-mark bg-[#72b3ed] text-[#173a5a]" aria-hidden="true">E</span>
              <span className="text-lg font-bold tracking-tight">Epic-Cure</span>
            </div>
            <p className="eyebrow text-[#a9d8fa]">Medically tailored groceries</p>
            <h1 className="mt-5 max-w-lg text-5xl font-bold leading-[0.95] tracking-[-0.06em] lg:text-7xl">
              Food support that feels human.
            </h1>
          </div>
          <p className="max-w-sm text-sm leading-6 text-blue-100">
            Find food that fits your household, understand what works for you, and shop with confidence.
          </p>
        </div>
      </section>
      <form className="soft-card w-full space-y-6 p-6 sm:p-9" onSubmit={handleSubmit}>
        <div className="space-y-3">
          <p className="eyebrow">Welcome back</p>
          <h1 aria-label="Sign in" className="text-4xl font-bold tracking-[-0.06em] text-[#10283f]">Sign in to continue.</h1>
          <p className="text-sm leading-6 text-slate-500">Use your Epic-Cure account to continue.</p>
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
          <span className="relative mt-2 block">
            <input
              className="soft-input w-full px-4 py-3 pr-12"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute inset-y-0 right-0 flex items-center px-4 text-stone-500 transition hover:text-stone-800"
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
            >
              <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {showPassword ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M9.9 5.2A10.7 10.7 0 0112 5c5.2 0 8.7 4.5 9.8 7a11.8 11.8 0 01-3.1 4.2M6.2 6.2C3.9 7.8 2.7 10.1 2.2 12c.5 1.4 1.9 4.2 5.4 6.1A10.7 10.7 0 0012 19c1.1 0 2.1-.2 3-.5" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M2.2 12C3.3 9.5 6.8 5 12 5s8.7 4.5 9.8 7c-1.1 2.5-4.6 7-9.8 7s-8.7-4.5-9.8-7zM12 15a3 3 0 100-6 3 3 0 000 6z" />
                )}
              </svg>
            </button>
          </span>
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
