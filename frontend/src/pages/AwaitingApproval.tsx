import { useState } from "react";

import Icon from "../components/Icon";

// Epic 1: no shopping session until a Warehouse Manager approves a new (Pending) account.
export default function AwaitingApproval({ onCheckAgain }: { onCheckAgain?: () => Promise<boolean> }) {
  const [stillWaiting, setStillWaiting] = useState(false);
  const [checking, setChecking] = useState(false);

  async function checkAgain() {
    if (!onCheckAgain) return;
    setChecking(true);
    setStillWaiting(!(await onCheckAgain()));
    setChecking(false);
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Almost ready</h1>
          <p>Your account is waiting for staff approval.</p>
        </div>
      </header>
      <section className="label-panel stack" style={{ maxWidth: "36rem" }}>
        <p className="status-badge status-badge-capped status-bar">
          <Icon name="queue" /> Waiting for staff approval
        </p>
        <ol className="steps">
          <li>Show a staff member your ID at the front desk.</li>
          <li>Once they approve your account, tap Check again to start shopping.</li>
        </ol>
        {onCheckAgain && (
          <button className="btn btn-primary" disabled={checking} type="button" onClick={() => void checkAgain()}>
            {checking ? "Checking…" : "Check again"}
          </button>
        )}
        {stillWaiting && (
          <p className="alert alert-info" role="status">
            <Icon name="alert" />
            Not approved yet. Please check with staff at the front desk.
          </p>
        )}
        <a className="btn btn-secondary" href="/profile">
          <Icon name="profile" /> Review your household
        </a>
      </section>
    </main>
  );
}
