import { FormEvent, useState } from "react";

import { signup } from "../api/client";
import HouseholdEditor from "../components/HouseholdEditor";
import Icon from "../components/Icon";
import { useAuth } from "../lib/auth";
import { emptyMember, toMemberInput, type MemberDraft } from "../lib/household";

const STEPS = ["Your account", "Your household", "Check and finish"] as const;

export default function Signup() {
  const { refresh } = useAuth();
  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [members, setMembers] = useState<MemberDraft[]>([emptyMember()]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (step === 0 && password.length < 8) {
      setError("Use at least 8 characters for your password.");
    } else if (step < STEPS.length - 1) {
      setStep((current) => current + 1);
    } else {
      void finish();
    }
  }

  async function finish() {
    setSubmitting(true);
    try {
      await signup({ email, password, name, members: members.map(toMemberInput) });
      await refresh();
      window.history.replaceState({}, "", "/");
      window.dispatchEvent(new PopStateEvent("popstate"));
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "";
      setError(
        message.includes("already")
          ? "That email already has an account. Try signing in."
          : "We couldn't create your account. Check your details and try again.",
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
        <form className="login-form signup-form" onSubmit={handleSubmit}>
          <p className="field-label" aria-live="polite">
            Step {step + 1} of {STEPS.length}: {STEPS[step]}
          </p>
          <h1>Create account</h1>

          {step === 0 && (
            <>
              <label className="field">
                <span className="field-label">Your name</span>
                <input autoComplete="name" className="input" required value={name} onChange={(e) => setName(e.target.value)} />
                <span className="panel-sub">Only staff see this, to approve your account.</span>
              </label>
              <label className="field">
                <span className="field-label">Email</span>
                <input autoComplete="email" className="input" required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </label>
              <label className="field">
                <span className="field-label">Password</span>
                <input autoComplete="new-password" className="input" minLength={8} required type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
              </label>
            </>
          )}

          {step === 1 && (
            <>
              <p className="panel-sub">
                Add everyone you shop for. Health conditions are optional. We keep them private and
                encrypted, and only use them to pick safe food rules.
              </p>
              <HouseholdEditor members={members} onChange={setMembers} showConditions />
            </>
          )}

          {step === 2 && (
            <div className="stack">
              <p>
                <strong>{members.length}</strong> {members.length === 1 ? "person" : "people"} in your household.
              </p>
              <p className="alert alert-info">
                <Icon name="alert" />
                Staff will approve your account at the warehouse. Then sign in again to start shopping.
              </p>
            </div>
          )}

          {error && (
            <p className="alert alert-danger" role="alert">
              <Icon name="alert" />
              {error}
            </p>
          )}

          <div className="row">
            {step > 0 ? (
              <button className="btn btn-secondary" type="button" onClick={() => setStep((current) => current - 1)}>
                Back
              </button>
            ) : (
              <a className="btn btn-secondary" href="/login">
                Back to sign in
              </a>
            )}
            <button className="btn btn-primary" disabled={submitting} type="submit">
              {step < 2 ? "Next" : submitting ? "Creating…" : "Create account"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
